import customtkinter as ctk
from backend.storage_json import get_active_commandes, update_commande_status

class ManagerApp(ctk.CTk):
    def __init__(self, manager_username, manager_role="Manager"):
        super().__init__()
        self.title("Smart Kiosk - Écran Cuisine (KDS)")
        self.geometry("900x600")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header Area
        self.header_frame = ctk.CTkFrame(self, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.header_label = ctk.CTkLabel(self.header_frame, text="Suivi des Commandes - Cuisine", font=("Arial", 24, "bold"))
        self.header_label.pack(pady=15)
        self.manager_label = ctk.CTkLabel(
            self.header_frame,
            text=f"{manager_role} connecté : {manager_username}",
            font=("Arial", 13),
        )
        self.manager_label.pack(pady=(0, 10))
        self.logout_button = ctk.CTkButton(
            self.header_frame,
            text="Se déconnecter",
            width=130,
            command=self.logout,
        )
        self.logout_button.pack(pady=(0, 10))
        
        # Scrollable container for active orders
        self.orders_frame = ctk.CTkScrollableFrame(self, label_text="Commandes Actives")
        self.orders_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        
        # Keep widgets alive so a status change does not rebuild the whole list.
        self.refresh_job = None
        self.order_cards = {}
        
        # Load orders immediately and start the auto-refresh loop
        self.load_orders()
        
    def load_orders(self):
        """Fetches active orders and updates UI only if data has changed."""
        # Cancel any pending refresh to prevent overlapping timers
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            
        active_orders = get_active_commandes()
        active_ids = {commande.id for commande, _ in active_orders}

        # Remove only orders that are no longer active.
        for order_id in set(self.order_cards) - active_ids:
            self.order_cards.pop(order_id)["card"].destroy()

        for row, (commande, lignes) in enumerate(active_orders):
            self._render_order_card(row, commande, lignes)

        # Schedule the next background check
        self.refresh_job = self.after(5000, self.load_orders)

    def _render_order_card(self, row, commande, lignes):
        """Create a card once, then update its contents in place."""
        card_data = self.order_cards.get(commande.id)
        if card_data is None:
            card = ctk.CTkFrame(self.orders_frame, corner_radius=10)
            info_label = ctk.CTkLabel(
                card,
                font=("Arial", 18, "bold"),
            )
            info_label.pack(anchor="w", padx=20, pady=(10, 0))

            details_label = ctk.CTkLabel(
                card,
                font=("Arial", 16),
                justify="left",
            )
            details_label.pack(anchor="w", padx=40, pady=10)

            action_btn = ctk.CTkButton(
                card,
                font=("Arial", 14, "bold"),
            )
            action_btn.pack(side="right", padx=20, pady=10)

            card_data = {
                "card": card,
                "info": info_label,
                "details": details_label,
                "button": action_btn,
            }
            self.order_cards[commande.id] = card_data

        card_data["card"].grid(
            row=row,
            column=0,
            padx=10,
            pady=10,
            sticky="ew",
        )
        self.orders_frame.grid_columnconfigure(0, weight=1)

        status_color = "orange" if commande.statut == "En attente" else "blue"
        card_data["info"].configure(
            text=f"Commande #{commande.id} | {commande.statut}",
            text_color=status_color,
        )
        details_text = "\n".join(
            f"• {line.quantite}x {product.nom if product else 'Produit supprimé'}"
            for line, product in lignes
        )
        card_data["details"].configure(text=details_text)

        button = card_data["button"]
        if commande.statut == "En attente":
            button.configure(
                text="Lancer la préparation",
                fg_color="orange",
                hover_color="#cc8400",
                command=lambda order_id=commande.id: self.update_status(
                    order_id,
                    "En attente",
                ),
            )
        else:
            button.configure(
                text="Marquer comme Servie",
                fg_color="green",
                hover_color="#167a16",
                command=lambda order_id=commande.id: self.update_status(
                    order_id,
                    "En préparation",
                ),
            )
        
    def update_status(self, cmd_id, current_status):
        """Updates the order status in the database and forces an immediate UI refresh."""
        update_commande_status(cmd_id, current_status)
        
        # Force a refresh right after a button click
        self.load_orders()

    def logout(self):
        """Stop refresh callbacks and close the authenticated manager window."""
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.destroy()
