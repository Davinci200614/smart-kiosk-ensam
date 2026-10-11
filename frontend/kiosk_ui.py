from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox

from backend.crud import create_commande
from backend.models_json import Produit
from backend.seed import MENU_ITEMS
from backend.storage_json import load_inventory


BG = "#f5f2eb"
PANEL = "#fffefa"
INK = "#292929"
MUTED = "#68645f"
RED = "#da291c"
RED_HOVER = "#b92117"
YELLOW = "#ffc72c"
BORDER = "#e5dfd1"
REFRESH_MS = 5_000


@dataclass(frozen=True)
class MenuItem:
    category: str
    name: str
    price: float
    product_id: int
    stock: int


def load_menu() -> list[MenuItem]:
    """Load only products declared by the seed, with current stock values."""
    products_by_name = {product.nom: product for product in load_inventory()}
    return [
        MenuItem(
            category=category,
            name=name,
            price=price,
            product_id=products_by_name[name].id,
            stock=products_by_name[name].stock_actuel,
        )
        for name, category, price in MENU_ITEMS
        if name in products_by_name
    ]


class ScrollableFrame(tk.Frame):
    def __init__(self, parent: tk.Misc, *, bg: str = PANEL) -> None:
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=bg)
        self.window_id = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.content.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(
                self.window_id, width=event.width
            ),
        )


class KioskApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Buvette | Smart Kiosk")
        self.configure(bg=BG)
        self.geometry("1100x720")
        self.minsize(850, 560)

        self.menu_items = load_menu()
        self.categories = ["Tout"] + list(
            dict.fromkeys(item.category for item in self.menu_items)
        )
        self.selected_category = "Tout"
        self.category_var = tk.StringVar(value=self.selected_category)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_menu())
        self.cart: dict[int, int] = {}
        self.refresh_job: str | None = None
        self.stock_labels: dict[int, tk.Label] = {}
        self.add_buttons: dict[int, tk.Button] = {}

        self._build_header()
        self._build_body()
        self.render_categories()
        self.render_menu()
        self.render_cart()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.schedule_refresh()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=RED, padx=26, pady=18)
        header.pack(fill="x")
        tk.Label(
            header, text="BUVETTE", bg=RED, fg=YELLOW, font=("Arial", 22, "bold")
        ).pack(side="left")
        tk.Label(
            header,
            text="ENSAM  /  MENU",
            bg=RED,
            fg=PANEL,
            font=("Arial", 12, "bold"),
        ).pack(side="right")

    def _build_body(self) -> None:
        body = tk.Frame(self, bg=BG, padx=20, pady=18)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3, uniform="main")
        body.grid_columnconfigure(1, weight=2, uniform="main")
        body.grid_rowconfigure(0, weight=1)

        catalog = tk.Frame(body, bg=BG)
        catalog.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        catalog.grid_rowconfigure(2, weight=1)
        catalog.grid_columnconfigure(0, weight=1)

        top = tk.Frame(catalog, bg=BG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.grid_columnconfigure(0, weight=1)
        tk.Label(
            top, text="Au menu", bg=BG, fg=INK, font=("Arial", 22, "bold")
        ).grid(row=0, column=0, sticky="w")
        tk.Entry(
            top,
            textvariable=self.search_var,
            font=("Arial", 14),
            relief="solid",
            bd=1,
            bg=PANEL,
            fg=INK,
            insertbackground=INK,
            width=24,
        ).grid(row=0, column=1, sticky="e", ipady=10, ipadx=10)

        self.category_bar = tk.Frame(catalog, bg=BG)
        self.category_bar.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.menu_view = ScrollableFrame(catalog, bg=BG)
        self.menu_view.grid(row=2, column=0, sticky="nsew")

        basket = tk.Frame(
            body, bg=PANEL, highlightthickness=1, highlightbackground=BORDER
        )
        basket.grid(row=0, column=1, sticky="nsew")
        basket.grid_columnconfigure(0, weight=1)
        basket.grid_rowconfigure(1, weight=1)
        basket_header = tk.Frame(basket, bg=PANEL, padx=18, pady=16)
        basket_header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            basket_header,
            text="Votre commande",
            bg=PANEL,
            fg=INK,
            font=("Arial", 19, "bold"),
        ).pack(anchor="w")
        self.cart_count = tk.Label(
            basket_header, text="0 article", bg=PANEL, fg=MUTED, font=("Arial", 12)
        )
        self.cart_count.pack(anchor="w", pady=(3, 0))

        self.cart_view = ScrollableFrame(basket, bg=PANEL)
        self.cart_view.grid(row=1, column=0, sticky="nsew", padx=12)
        footer = tk.Frame(basket, bg=PANEL, padx=18, pady=16)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        tk.Frame(footer, bg=BORDER, height=1).grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12)
        )
        tk.Label(
            footer, text="Total", bg=PANEL, fg=MUTED, font=("Arial", 12)
        ).grid(row=1, column=0, sticky="w")
        self.total_label = tk.Label(
            footer, text="0.00 DH", bg=PANEL, fg=INK, font=("Arial", 19, "bold")
        )
        self.total_label.grid(row=1, column=1, sticky="e")
        self.checkout_button = tk.Button(
            footer,
            text="Valider la commande",
            command=self.open_checkout,
            bg=RED,
            fg="white",
            activebackground=RED_HOVER,
            relief="flat",
            font=("Arial", 15, "bold"),
            cursor="hand2",
            pady=14,
        )
        self.checkout_button.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(12, 8)
        )
        self._bind_hover(self.checkout_button, RED_HOVER, RED)
        tk.Button(
            footer,
            text="Vider le panier",
            command=self.clear_cart,
            bg=PANEL,
            fg=RED,
            activebackground="#fff2cc",
            relief="flat",
            font=("Arial", 12, "bold"),
            pady=8,
            cursor="hand2",
        ).grid(row=3, column=0, columnspan=2)

    @staticmethod
    def _bind_hover(widget: tk.Widget, hover: str, normal: str) -> None:
        widget.bind("<Enter>", lambda _event: widget.configure(bg=hover))
        widget.bind("<Leave>", lambda _event: widget.configure(bg=normal))

    def schedule_refresh(self) -> None:
        self.refresh_job = self.after(REFRESH_MS, self.refresh_inventory)

    def refresh_inventory(self) -> None:
        """Reload inventory without losing the current cart or search state."""
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = None
        previous_menu = self.menu_items
        current_menu = load_menu()
        if current_menu == previous_menu:
            self.schedule_refresh()
            return
        previous_structure = [
            (item.product_id, item.category, item.name, item.price)
            for item in previous_menu
        ]
        current_structure = [
            (item.product_id, item.category, item.name, item.price)
            for item in current_menu
        ]
        self.menu_items = current_menu
        if current_structure == previous_structure:
            for item in current_menu:
                stock_label = self.stock_labels.get(item.product_id)
                if stock_label is not None and stock_label.winfo_exists():
                    stock_label.configure(text=f"Stock disponible : {item.stock}")
                add_button = self.add_buttons.get(item.product_id)
                if add_button is not None and add_button.winfo_exists():
                    add_button.configure(
                        state="normal" if item.stock > 0 else "disabled"
                    )
            self.render_cart()
            self.schedule_refresh()
            return
        previous_categories = self.categories
        self.categories = ["Tout"] + list(
            dict.fromkeys(item.category for item in self.menu_items)
        )
        if self.selected_category not in self.categories:
            self.selected_category = "Tout"
        if self.categories != previous_categories:
            self.render_categories()
        self.render_menu()
        self.render_cart()
        self.schedule_refresh()

    def render_categories(self) -> None:
        for child in self.category_bar.winfo_children():
            child.destroy()
        tk.Label(
            self.category_bar,
            text="Catégorie",
            bg=BG,
            fg=MUTED,
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=(0, 9))
        self.category_var.set(self.selected_category)
        selector = tk.OptionMenu(
            self.category_bar,
            self.category_var,
            *self.categories,
            command=self.select_category,
        )
        selector.configure(
            bg=YELLOW,
            fg=INK,
            activebackground="#edb817",
            relief="flat",
            font=("Arial", 12, "bold"),
            padx=12,
            pady=9,
            cursor="hand2",
        )
        selector["menu"].configure(bg=PANEL, fg=INK, activebackground=YELLOW)
        selector.pack(side="left")

    def select_category(self, category: str) -> None:
        self.selected_category = category
        self.render_menu()

    def render_menu(self) -> None:
        for child in self.menu_view.content.winfo_children():
            child.destroy()
        self.stock_labels.clear()
        self.add_buttons.clear()
        query = self.search_var.get().strip().casefold()
        visible = [
            item
            for item in self.menu_items
            if (
                self.selected_category == "Tout"
                or item.category == self.selected_category
            )
            and (not query or query in item.name.casefold())
        ]
        if not visible:
            tk.Label(
                self.menu_view.content,
                text="Aucun produit ne correspond à votre recherche.",
                bg=BG,
                fg=MUTED,
                font=("Arial", 12),
                pady=28,
            ).pack(fill="x")
            return

        for index, item in enumerate(visible):
            self.menu_view.content.grid_columnconfigure(
                index % 2, weight=1, uniform="product"
            )
            card = tk.Frame(
                self.menu_view.content,
                bg=PANEL,
                highlightthickness=1,
                highlightbackground=BORDER,
                padx=14,
                pady=12,
            )
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=(0, 8) if index % 2 == 0 else (4, 0),
                pady=(0, 9),
            )
            tk.Label(
                card, text=item.category, bg=PANEL, fg=RED, font=("Arial", 8, "bold")
            ).pack(fill="x")
            tk.Label(
                card,
                text=item.name,
                bg=PANEL,
                fg=INK,
                font=("Arial", 14, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(4, 3))
            stock_label = tk.Label(
                card,
                text=f"Stock disponible : {item.stock}",
                bg=PANEL,
                fg=MUTED,
                font=("Arial", 10),
                anchor="w",
            )
            stock_label.pack(fill="x", pady=(0, 10))
            self.stock_labels[item.product_id] = stock_label
            bottom = tk.Frame(card, bg=PANEL)
            bottom.pack(fill="x")
            tk.Label(
                bottom,
                text=f"{item.price:.2f} DH",
                bg=PANEL,
                fg=INK,
                font=("Arial", 11, "bold"),
            ).pack(side="left")
            add_button = tk.Button(
                bottom,
                text="Ajouter +",
                command=lambda selected=item: self.add_item(selected),
                bg=RED,
                fg="white",
                activebackground=RED_HOVER,
                relief="flat",
                font=("Arial", 11, "bold"),
                padx=14,
                pady=10,
                cursor="hand2",
                state="normal" if item.stock > 0 else "disabled",
            )
            add_button.pack(side="right")
            self.add_buttons[item.product_id] = add_button
            self._bind_hover(add_button, RED_HOVER, RED)

    def add_item(self, item: MenuItem) -> None:
        current = self.cart.get(item.product_id, 0)
        if current >= item.stock:
            messagebox.showwarning(
                "Stock insuffisant",
                f"Il ne reste plus de stock pour {item.name}.",
                parent=self,
            )
            return
        self.cart[item.product_id] = current + 1
        self.render_cart()

    def change_quantity(self, product_id: int, amount: int) -> None:
        quantity = self.cart.get(product_id, 0) + amount
        if quantity <= 0:
            self.cart.pop(product_id, None)
        else:
            self.cart[product_id] = quantity
        self.render_cart()

    def clear_cart(self) -> None:
        self.cart.clear()
        self.render_cart()

    def render_cart(self) -> None:
        for child in self.cart_view.content.winfo_children():
            child.destroy()
        products = {item.product_id: item for item in self.menu_items}
        total = 0.0
        count = sum(self.cart.values())
        self.cart_count.configure(text=f"{count} article{'s' if count != 1 else ''}")
        for product_id, quantity in self.cart.items():
            item = products.get(product_id)
            if item is None:
                continue
            total += item.price * quantity
            row = tk.Frame(self.cart_view.content, bg=PANEL, pady=10)
            row.pack(fill="x")
            tk.Label(
                row,
                text=item.name,
                bg=PANEL,
                fg=INK,
                font=("Arial", 10, "bold"),
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            tk.Label(
                row,
                text=f"{item.price * quantity:.2f} DH",
                bg=PANEL,
                fg=INK,
                font=("Arial", 10, "bold"),
            ).grid(row=0, column=1, sticky="e")
            controls = tk.Frame(row, bg=PANEL)
            controls.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
            for label, change in (("-", -1), (str(quantity), 0), ("+", 1)):
                tk.Button(
                    controls,
                    text=label,
                    command=lambda pid=product_id, delta=change: (
                        self.change_quantity(pid, delta) if delta else None
                    ),
                    bg="#fff2cc",
                    fg=RED,
                    relief="flat",
                    font=("Arial", 12, "bold"),
                    width=4,
                ).pack(side="left", padx=(0, 4))
            tk.Frame(self.cart_view.content, bg=BORDER, height=1).pack(fill="x")
        if not self.cart:
            tk.Label(
                self.cart_view.content,
                text="Votre panier est vide.\nAjoutez un produit pour commencer.",
                bg=PANEL,
                fg=MUTED,
                font=("Arial", 11),
                justify="left",
                pady=18,
            ).pack(anchor="w")
        self.total_label.configure(text=f"{total:.2f} DH")
        self.checkout_button.configure(state="normal" if self.cart else "disabled")

    def open_checkout(self) -> None:
        if not self.cart:
            return
        dialog = tk.Toplevel(self)
        dialog.title("Confirmer la commande")
        dialog.configure(bg=PANEL)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(
            dialog,
            text=f"Total à régler : {self.total_label.cget('text')}",
            bg=PANEL,
            fg=INK,
            font=("Arial", 15, "bold"),
            padx=24,
            pady=18,
        ).pack(anchor="w")
        payment = tk.StringVar(value="Espèces")
        for method in ("Espèces", "Carte / Solde étudiant"):
            tk.Radiobutton(
                dialog,
                text=method,
                variable=payment,
                value=method,
                bg=PANEL,
                fg=INK,
                activebackground=PANEL,
                selectcolor=PANEL,
                font=("Arial", 13),
                padx=24,
            ).pack(anchor="w", pady=8)

        def confirm() -> None:
            try:
                inventory = {
                    product.id: product for product in load_inventory()
                }
                panier: list[Produit] = []
                for product_id, quantity in self.cart.items():
                    product = inventory.get(product_id)
                    if product is None:
                        raise ValueError("Un produit du panier n'est plus disponible.")
                    panier.extend([product] * quantity)
                commande = create_commande(panier, payment.get())
                if commande is None:
                    raise ValueError("La commande n'a pas pu être enregistrée.")
            except (ValueError, OSError) as error:
                messagebox.showerror(
                    "Commande impossible", str(error), parent=dialog
                )
                return

            dialog.destroy()
            self.clear_cart()
            self.refresh_inventory()
            messagebox.showinfo(
                "Commande confirmée",
                f"Commande #{commande.id:03d}\nPaiement : {payment.get()}",
                parent=self,
            )

        tk.Button(
            dialog,
            text="Confirmer",
            command=confirm,
            bg=RED,
            fg="white",
            activebackground=RED_HOVER,
            relief="flat",
            font=("Arial", 14, "bold"),
            padx=20,
            pady=14,
            cursor="hand2",
        ).pack(fill="x", padx=24, pady=20)

    def close(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.destroy()


def build_kiosk_window() -> KioskApp:
    return KioskApp()


if __name__ == "__main__":
    app = KioskApp()
    app.mainloop()
