"""Streamlit managerial dashboard backed by the JSON storage layer."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit may place analytics/ rather than the project root on sys.path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.storage_json import (
    load_inventory,
    load_refill_requests,
    load_transactions,
    save_refill_requests,
)
from backend.auth_json import add_manager, change_manager_password, verify_user
from backend.storage_json import load_users


EXPECTED_COLUMNS = [
    "Order ID",
    "Date",
    "Product",
    "Category",
    "Quantity",
    "Unit Price",
    "Line Total",
    "Status",
]


def get_dashboard_data() -> pd.DataFrame:
    """Load JSON objects and flatten order lines into dashboard rows."""

    commandes, lignes = load_transactions()
    produits = load_inventory()
    commandes_by_id = {commande.id: commande for commande in commandes}
    produits_by_id = {produit.id: produit for produit in produits}

    rows = []
    for ligne in lignes:
        commande = commandes_by_id.get(ligne.commande_id)
        produit = produits_by_id.get(ligne.produit_id)

        # Keep the line visible even if a historical reference is missing.
        rows.append(
            {
                "Order ID": ligne.commande_id,
                "Date": commande.date_heure if commande else None,
                "Product": produit.nom if produit else f"Produit #{ligne.produit_id}",
                "Category": produit.categorie if produit else "Unknown",
                "Quantity": ligne.quantite,
                "Unit Price": ligne.prix_unitaire,
                "Line Total": ligne.quantite * ligne.prix_unitaire,
                "Status": commande.statut if commande else "Unknown",
            }
        )

    dataframe = pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
    if not dataframe.empty:
        dataframe["Date"] = pd.to_datetime(dataframe["Date"], errors="coerce")
        dataframe["Quantity"] = pd.to_numeric(
            dataframe["Quantity"], errors="coerce"
        ).fillna(0)
        dataframe["Unit Price"] = pd.to_numeric(
            dataframe["Unit Price"], errors="coerce"
        ).fillna(0.0)
        dataframe["Line Total"] = pd.to_numeric(
            dataframe["Line Total"], errors="coerce"
        ).fillna(0.0)
    return dataframe


def status_style(status: str) -> str:
    """Return the background style for an order status cell."""

    colors = {
        "Servie": ("#dcfce7", "#166534"),
        "En préparation": ("#fef3c7", "#92400e"),
        "En attente": ("#fee2e2", "#991b1b"),
    }
    background, foreground = colors.get(status, ("#e5e7eb", "#374151"))
    return f"background-color: {background}; color: {foreground}; font-weight: 700"


def render_kpis(dataframe: pd.DataFrame) -> None:
    """Render the four KPI cards for the filtered dataframe."""

    total_revenue = dataframe["Line Total"].sum()
    total_orders = dataframe["Order ID"].nunique()
    average_order_value = total_revenue / total_orders if total_orders else 0.0
    total_items = dataframe["Quantity"].sum()

    columns = st.columns(4)
    metrics = [
        ("Total Revenue", f"{total_revenue:,.2f} DH"),
        ("Total Orders", f"{total_orders:,}"),
        ("Avg Order Value", f"{average_order_value:,.2f} DH"),
        ("Total Items Sold", f"{total_items:,.0f}"),
    ]

    for column, (label, value) in zip(columns, metrics):
        with column:
            with st.container(border=True):
                st.metric(label, value)


def render_visualizations(dataframe: pd.DataFrame) -> None:
    """Render revenue-over-time and sales-by-category charts."""

    columns = st.columns(2)
    if dataframe.empty:
        for column in columns:
            with column:
                st.info("No data matches the current filters.")
        return

    chart_data = dataframe.copy()
    chart_data["Day"] = chart_data["Date"].dt.floor("D")

    with columns[0]:
        st.subheader("Revenue Over Time")
        revenue_by_day = (
            chart_data.groupby("Day", as_index=False)["Line Total"].sum()
        )
        revenue_chart = px.line(
            revenue_by_day,
            x="Day",
            y="Line Total",
            markers=True,
            labels={"Day": "Date", "Line Total": "Revenue (DH)"},
        )
        revenue_chart.update_traces(line_color="#e11d48")
        st.plotly_chart(revenue_chart, use_container_width=True)

    with columns[1]:
        st.subheader("Sales by Category")
        category_sales = (
            chart_data.groupby("Category", as_index=False)["Line Total"].sum()
        )
        category_chart = px.bar(
            category_sales,
            x="Category",
            y="Line Total",
            color="Category",
            labels={"Line Total": "Revenue (DH)"},
        )
        st.plotly_chart(category_chart, use_container_width=True)


def stock_status(stock: int, threshold: int) -> str:
    if stock <= 0:
        return "Rupture"
    if stock <= threshold:
        return "Alerte"
    return "Normal"


def render_manager_profile() -> str:
    with st.sidebar:
        st.markdown("### Manager connecté")
        manager_name = st.session_state["manager_name"]
        st.text_input("Nom", value=manager_name, disabled=True)
        st.caption(f"Rôle : **{st.session_state['manager_role']}**")
    return manager_name


def render_settings_page(manager_role: str) -> None:
    st.header("Gestion des managers")
    if manager_role.lower() != "business manager":
        st.warning(
            "Seuls les Business Managers peuvent gérer les comptes managers."
        )
        return

    st.subheader("Ajouter un manager")
    with st.form("add_manager_form"):
        username = st.text_input("Nom utilisateur")
        password = st.text_input("Mot de passe", type="password")
        confirmation = st.text_input("Confirmer le mot de passe", type="password")
        role = st.selectbox("Rôle", ["Business Manager", "Kitchen Manager"])
        submitted = st.form_submit_button("Créer le compte")
    if submitted:
        if not username.strip() or len(password) < 8:
            st.error("Le nom est obligatoire et le mot de passe doit avoir 8 caractères minimum.")
        elif password != confirmation:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            try:
                add_manager(username.strip(), password, role)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success(f"Compte {role} créé pour {username.strip()}.")

    st.subheader("Changer un mot de passe")
    users = [
        user
        for user in load_users()
        if user.role.lower() in {"business manager", "kitchen manager", "manager"}
    ]
    if not users:
        st.info("Aucun manager enregistré.")
        return
    with st.form("change_password_form"):
        selected_user = st.selectbox(
            "Manager",
            [user.nom_utilisateur for user in users],
        )
        new_password = st.text_input("Nouveau mot de passe", type="password")
        new_confirmation = st.text_input(
            "Confirmer le nouveau mot de passe", type="password"
        )
        change_submitted = st.form_submit_button("Changer le mot de passe")
    if change_submitted:
        if len(new_password) < 8:
            st.error("Le mot de passe doit avoir 8 caractères minimum.")
        elif new_password != new_confirmation:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            change_manager_password(selected_user, new_password)
            st.success(f"Mot de passe changé pour {selected_user}.")


def render_stock_page(manager_name: str) -> None:
    st.header("Stock et alertes")
    products = load_inventory()
    if not products:
        st.info("Aucun produit dans l'inventaire.")
        return

    stock_rows = [
        {
            "Produit": product.nom,
            "Catégorie": product.categorie,
            "Stock actuel": product.stock_actuel,
            "Seuil d'alerte": product.seuil_alerte,
            "État": stock_status(product.stock_actuel, product.seuil_alerte),
        }
        for product in products
    ]
    stock_df = pd.DataFrame(stock_rows)
    status_filter = st.selectbox(
        "Filtrer l'état du stock",
        ["Tous", "Normal", "Alerte", "Rupture"],
    )
    visible_stock = stock_df if status_filter == "Tous" else stock_df[
        stock_df["État"] == status_filter
    ]
    st.dataframe(visible_stock, use_container_width=True, hide_index=True)

    st.subheader("Demander un réapprovisionnement")
    product_by_name = {product.nom: product for product in products}
    with st.form("refill_request_form"):
        product_name = st.selectbox(
            "Produit à réapprovisionner",
            list(product_by_name),
        )
        quantity = st.number_input(
            "Quantité demandée",
            min_value=1,
            value=10,
            step=1,
        )
        submitted = st.form_submit_button("Envoyer la demande")

    if submitted:
        product = product_by_name[product_name]
        requests = load_refill_requests()
        requests.append(
            {
                "Produit": product.nom,
                "Quantité": int(quantity),
                "Demandé par": manager_name,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "État": "Demandée",
            }
        )
        save_refill_requests(requests)
        st.success(
            f"Demande envoyée par {manager_name} pour {int(quantity)} unité(s) de {product.nom}."
        )

    requests = load_refill_requests()
    if requests:
        st.subheader("Demandes de réapprovisionnement")
        st.dataframe(pd.DataFrame(requests), use_container_width=True, hide_index=True)
    else:
        st.info("Aucune demande de réapprovisionnement.")


def render_orders_page() -> None:
    st.header("Commandes")
    dataframe = get_dashboard_data()
    if dataframe.empty:
        st.info("Aucune commande enregistrée.")
        return
    order_summary = (
        dataframe.groupby(["Order ID", "Date", "Status"], as_index=False)
        .agg(
            Produits=("Product", lambda values: ", ".join(values)),
            Total=("Line Total", "sum"),
            Articles=("Quantity", "sum"),
        )
        .sort_values("Date", ascending=False)
    )
    st.dataframe(order_summary, use_container_width=True, hide_index=True)


def render_dashboard_page() -> None:
    dataframe = get_dashboard_data()
    filter_columns = st.columns(2)
    with filter_columns[0]:
        categories = ["All Categories"]
        if not dataframe.empty:
            categories.extend(sorted(dataframe["Category"].dropna().unique()))
        selected_category = st.selectbox("Category Filter", categories)
    with filter_columns[1]:
        order_search = st.text_input(
            "Search by Order ID",
            placeholder="Enter an order ID...",
        )

    filtered_df = dataframe
    if selected_category != "All Categories":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]
    if order_search.strip():
        filtered_df = filtered_df[
            filtered_df["Order ID"].astype(str).str.contains(
                order_search.strip(), case=False, na=False
            )
        ]
    filtered_df = filtered_df.reset_index(drop=True)
    render_kpis(filtered_df)
    render_visualizations(filtered_df)

    st.subheader("Recent Transactions")
    if filtered_df.empty:
        st.info("No transactions found.")
        return
    display_df = filtered_df.sort_values("Date", ascending=False)[
        ["Order ID", "Date", "Product", "Line Total", "Status"]
    ].copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d %H:%M")
    styled_df = display_df.style.map(status_style, subset=["Status"]).format(
        {"Line Total": "{:,.2f} DH"}
    )
    st.dataframe(styled_df, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="Smart Kiosk Dashboard",
        page_icon="📊",
        layout="wide",
    )

    manager_name = os.getenv("SMART_KIOSK_MANAGER")
    manager_role = os.getenv("SMART_KIOSK_MANAGER_ROLE")
    if not manager_name:
        st.title("Connexion manager")
        username = st.text_input("Nom utilisateur")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            user = verify_user(username.strip(), password)
            if user is not None:
                st.session_state["authenticated_manager"] = user.nom_utilisateur
                st.session_state["authenticated_role"] = user.role
                st.rerun()
            else:
                st.error("Identifiants manager invalides.")
        manager_name = st.session_state.get("authenticated_manager")
        manager_role = st.session_state.get("authenticated_role")
        if not manager_name:
            return
    else:
        st.session_state["authenticated_manager"] = manager_name
        st.session_state["authenticated_role"] = manager_role or "Manager"

    manager_role = manager_role or st.session_state.get("authenticated_role", "Manager")
    st.session_state["manager_name"] = manager_name
    st.session_state["manager_role"] = manager_role

    with st.sidebar:
        st.markdown("### Manager connecté")
        st.text_input("Nom", value=manager_name, disabled=True)
        st.caption(f"Rôle : **{manager_role}**")
        if st.button("Se déconnecter"):
            st.session_state.pop("authenticated_manager", None)
            st.session_state.pop("authenticated_role", None)
            os.environ.pop("SMART_KIOSK_MANAGER", None)
            os.environ.pop("SMART_KIOSK_MANAGER_ROLE", None)
            st.rerun()
    with st.sidebar:
        page = st.radio(
            "Navigation",
            ["Dashboard", "Commandes", "Stock et alertes", "Paramètres"],
        )

    st.title("Smart Kiosk Managerial Dashboard")
    st.caption(f"Manager connecté : {manager_name}")

    if page == "Dashboard":
        render_dashboard_page()
    elif page == "Commandes":
        render_orders_page()
    elif page == "Stock et alertes":
        render_stock_page(manager_name)
    else:
        render_settings_page(manager_role)


if __name__ == "__main__":
    main()
