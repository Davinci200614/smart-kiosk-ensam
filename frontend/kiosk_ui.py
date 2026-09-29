from backend.crud import create_commande
import customtkinter as ctk
from backend.database import SessionLocal
from backend.models import Produit

class KioskApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Kiosk - Buvette")
        self.geometry("900x600")
        
        # Grid layout: Menu takes 2/3 of the screen, Cart takes 1/3
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # In-memory cart data
        self.panier = []
        self.total = 0.0

        # UI Frames
        self.menu_frame = ctk.CTkScrollableFrame(self, label_text="Menu Buvette", corner_radius=10)
        self.menu_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.cart_frame = ctk.CTkFrame(self, corner_radius=10)
        self.cart_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.build_cart_ui()
        self.load_products()

    def load_products(self):
        """Fetches products from SQLite and creates a button for each."""
        db = SessionLocal()
        produits = db.query(Produit).all()
        db.close()
        
        for i, p in enumerate(produits):
            # Using lambda with default argument captures the specific product 'p' for each button
            btn = ctk.CTkButton(self.menu_frame, text=f"{p.nom} - {p.prix} DH", 
                                font=("Arial", 16), height=50,
                                command=lambda item=p: self.add_to_cart(item))
            btn.grid(row=i, column=0, padx=20, pady=10, sticky="ew")
            
    def build_cart_ui(self):
        """Builds the right-side panel for the cart and total."""
        self.cart_label = ctk.CTkLabel(self.cart_frame, text="Votre Panier", font=("Arial", 20, "bold"))
        self.cart_label.pack(pady=10)
        
        # Textbox to list selected items
        self.cart_items_textbox = ctk.CTkTextbox(self.cart_frame, height=300, state="disabled")
        self.cart_items_textbox.pack(padx=10, pady=10, fill="x")
        
        self.total_label = ctk.CTkLabel(self.cart_frame, text="Total: 0.0 DH", font=("Arial", 22, "bold"))
        self.total_label.pack(pady=20)
        
        self.checkout_btn = ctk.CTkButton(self.cart_frame, text="Valider la commande", 
                                          fg_color="green", hover_color="darkgreen", height=50,
                                          command=self.checkout)
        self.checkout_btn.pack(pady=10, padx=20, fill="x")
        
    def add_to_cart(self, produit):
        """Handles adding an item to the cart and updating the UI."""
        self.panier.append(produit)
        self.total += produit.prix
        self.update_cart_display()
        
    def update_cart_display(self):
        """Refreshes the textbox and total label."""
        self.cart_items_textbox.configure(state="normal")
        self.cart_items_textbox.delete("1.0", "end")
        
        for item in self.panier:
            self.cart_items_textbox.insert("end", f"{item.nom} : {item.prix} DH\n")
            
        self.cart_items_textbox.configure(state="disabled")
        self.total_label.configure(text=f"Total: {self.total} DH")

    def checkout(self):
        """Sends the cart to the database and resets the UI."""
        if not self.panier:
            print("Panier vide, validation annulée.")
            return

        db = SessionLocal()
        # Call the CRUD function to save the order
        commande = create_commande(db, self.panier, mode_paiement="Espèces")
        db.close()

        if commande:
            # Clear the cart memory
            self.panier.append(None) # hack to trigger update before clearing list if needed, or just clear
            self.panier = []
            self.total = 0.0
            
            # Reset the UI display
            self.update_cart_display()
            
            # Change the button temporarily to show success
            self.checkout_btn.configure(text=f"Succès! Cmd #{commande.id}", fg_color="blue")
            self.after(3000, lambda: self.checkout_btn.configure(text="Valider la commande", fg_color="green"))

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = KioskApp()
    app.mainloop()