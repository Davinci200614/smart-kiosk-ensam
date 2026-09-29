import customtkinter as ctk
from backend.database import SessionLocal
from backend.models import Commande, LigneCommande

class ManagerApp(ctk.CTk):
    def __init__(self):
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
        
        # Scrollable container for active orders
        self.orders_frame = ctk.CTkScrollableFrame(self, label_text="Commandes Actives")
        self.orders_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        
        # Tracking variables to prevent flickering
        self.refresh_job = None
        self.current_state = {}  # Tracks {order_id: status}
        
        # Load orders immediately and start the auto-refresh loop
        self.load_orders()
        
    def load_orders(self):
        """Fetches active orders and updates UI only if data has changed."""
        # Cancel any pending refresh to prevent overlapping timers
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            
        db = SessionLocal()
        commandes = db.query(Commande).filter(Commande.statut != "Servie").all()
        
        # Create a "snapshot" of the database's current state
        new_state = {cmd.id: cmd.statut for cmd in commandes}
        
        # Only wipe and rebuild the UI if the snapshot is different from what's on screen
        if new_state != self.current_state:
            for widget in self.orders_frame.winfo_children():
                widget.destroy()
                
            for i, cmd in enumerate(commandes):
                card = ctk.CTkFrame(self.orders_frame, corner_radius=10)
                card.grid(row=i, column=0, padx=10, pady=10, sticky="ew")
                self.orders_frame.grid_columnconfigure(0, weight=1)
                
                status_color = "orange" if cmd.statut == "En attente" else "blue"
                info_label = ctk.CTkLabel(card, text=f"Commande #{cmd.id} | {cmd.statut}", 
                                          font=("Arial", 18, "bold"), text_color=status_color)
                info_label.pack(anchor="w", padx=20, pady=(10, 0))
                
                lignes = db.query(LigneCommande).filter(LigneCommande.commande_id == cmd.id).all()
                details_text = "\n".join([f"• {l.quantite}x {l.produit.nom}" for l in lignes])
                
                details_label = ctk.CTkLabel(card, text=details_text, font=("Arial", 16), justify="left")
                details_label.pack(anchor="w", padx=40, pady=10)
                
                btn_text = "Lancer la préparation" if cmd.statut == "En attente" else "Marquer comme Servie"
                btn_color = "orange" if cmd.statut == "En attente" else "green"
                
                action_btn = ctk.CTkButton(card, text=btn_text, fg_color=btn_color, font=("Arial", 14, "bold"),
                                           command=lambda c_id=cmd.id, s=cmd.statut: self.update_status(c_id, s))
                action_btn.pack(side="right", padx=20, pady=10)
                
            # Save the new snapshot as the current state
            self.current_state = new_state
            
        db.close()
        
        # Schedule the next background check
        self.refresh_job = self.after(5000, self.load_orders)
        
    def update_status(self, cmd_id, current_status):
        """Updates the order status in the database and forces an immediate UI refresh."""
        db = SessionLocal()
        cmd = db.query(Commande).filter(Commande.id == cmd_id).first()
        
        if cmd:
            if current_status == "En attente":
                cmd.statut = "En préparation"
            elif current_status == "En préparation":
                cmd.statut = "Servie"
            db.commit()
            
        db.close()
        
        # Force a refresh right after a button click
        self.load_orders()

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = ManagerApp()
    app.mainloop()