from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox

from backend.crud import create_commande, get_produits
from backend.database import SessionLocal


BG = "#f5f2eb"
PANEL = "#fffefa"
INK = "#292929"
MUTED = "#68645f"
RED = "#da291c"
RED_HOVER = "#b92117"
YELLOW = "#ffc72c"
BORDER = "#e5dfd1"

@dataclass(frozen=True)
class MenuItem:
    category: str
    name: str
    description: str
    price: float
    product_id: int


def load_menu() -> list[MenuItem]:
    """Read categories and products from the neighboring Markdown menu."""
    menu_path = Path(__file__).with_name("moroccan_buvette_menu.md")
    category = ""
    pending_item: tuple[str, str] | None = None
    items: list[MenuItem] = []

    for line in menu_path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        product = re.match(r"^\s*\*\s+\*\*(.+?)\*\*\s*$", line)
        description = re.match(r"^\s{2,}\*\s+(.+?)\s*$", line)

        if heading:
            category = heading.group(1).strip()
        elif product and category:
            if pending_item:
                name, item_category = pending_item
                items.append(MenuItem(item_category, name, "", 0.0, 0))
            pending_item = (product.group(1).strip(), category)
        elif description and pending_item:
            name, item_category = pending_item
            clean_description = re.sub(r"[*_`]", "", description.group(1)).strip()
            items.append(
                MenuItem(item_category, name, clean_description, 0.0, 0)
            )
            pending_item = None

    if pending_item:
        name, item_category = pending_item
        items.append(MenuItem(item_category, name, "", 0.0, 0))

    with SessionLocal() as db:
        products = {product.nom: product for product in get_produits(db)}
        return [
            MenuItem(
                item.category,
                item.name,
                item.description,
                products[item.name].prix,
                products[item.name].id,
            )
            for item in items
            if item.name in products
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
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)
        self.canvas.bind_all("<MouseWheel>", self._mousewheel)
        self.canvas.bind_all("<Button-4>", self._mousewheel)
        self.canvas.bind_all("<Button-5>", self._mousewheel)
        self.bind("<Destroy>", self._unbind_mousewheel, add="+")

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _mousewheel(self, event: tk.Event) -> None:
        target = self.winfo_containing(event.x_root, event.y_root)
        if target is None or not str(target).startswith(str(self.canvas)):
            return
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")

    def _unbind_mousewheel(self, event: tk.Event) -> None:
        if event.widget is self:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")


class KioskApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Buvette | Smart Kiosk")
        self.configure(bg=BG)
        self.geometry("1280x820")
        self.minsize(900, 620)

        self.menu_items = load_menu()
        self.categories = ["Tout"] + list(dict.fromkeys(item.category for item in self.menu_items))
        self.selected_category = "Tout"
        self.category_var = tk.StringVar(value=self.selected_category)
        self.cart: dict[str, int] = {}
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_menu())
        self._build_header()
        self._build_body()
        self.render_categories()
        self.render_menu()
        self.render_cart()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=RED, padx=26, pady=18)
        header.pack(fill="x")
        tk.Label(
            header,
            text="BUVETTE",
            bg=RED,
            fg=YELLOW,
            font=("Arial", 22, "bold"),
        ).pack(side="left")
        tk.Label(
            header,
            text="ENSAM  /  MENU",
            bg=RED,
            fg="#fffefa",
            font=("Arial", 12, "bold"),
        ).pack(side="right", padx=4)

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
        search = tk.Entry(
            top,
            textvariable=self.search_var,
            font=("Arial", 14),
            relief="solid",
            bd=1,
            bg=PANEL,
            fg=INK,
            insertbackground=INK,
        )
        search.insert(0, "")
        search.grid(row=0, column=1, sticky="e", ipady=10, ipadx=10)
        search.configure(width=24)

        self.category_bar = tk.Frame(catalog, bg=BG)
        self.category_bar.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.menu_view = ScrollableFrame(catalog, bg=BG)
        self.menu_view.grid(row=2, column=0, sticky="nsew")

        basket = tk.Frame(body, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
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
        tk.Frame(footer, bg=BORDER, height=1).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        tk.Label(footer, text="Total", bg=PANEL, fg=MUTED, font=("Arial", 12)).grid(
            row=1, column=0, sticky="w"
        )
        self.total_label = tk.Label(
            footer, text="0.00 MAD", bg=PANEL, fg=INK, font=("Arial", 19, "bold")
        )
        self.total_label.grid(row=1, column=1, sticky="e")
        self.checkout_button = tk.Button(
            footer,
            text="Valider la commande",
            command=self.open_checkout,
            bg=RED,
            fg="white",
            activebackground=RED_HOVER,
            activeforeground="white",
            relief="flat",
            font=("Arial", 15, "bold"),
            cursor="hand2",
            pady=18,
        )
        self.checkout_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 8))
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
            activeforeground=INK,
            relief="flat",
            highlightthickness=0,
            font=("Arial", 12, "bold"),
            padx=12,
            pady=9,
            cursor="hand2",
        )
        selector["menu"].configure(
            bg=PANEL, fg=INK, activebackground=YELLOW, font=("Arial", 12)
        )
        selector.pack(side="left")

    def select_category(self, category: str) -> None:
        self.selected_category = category
        self.render_categories()
        self.render_menu()

    def render_menu(self) -> None:
        for child in self.menu_view.content.winfo_children():
            child.destroy()

        query = self.search_var.get().strip().casefold()
        visible = [
            item
            for item in self.menu_items
            if (self.selected_category == "Tout" or item.category == self.selected_category)
            and (not query or query in item.name.casefold() or query in item.description.casefold())
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
            self.menu_view.content.grid_columnconfigure(index % 2, weight=1, uniform="product")
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
                card,
                text=item.category,
                bg=PANEL,
                fg=RED,
                font=("Arial", 8, "bold"),
                anchor="w",
            ).pack(fill="x")
            tk.Label(
                card,
                text=item.name,
                bg=PANEL,
                fg=INK,
                font=("Arial", 14, "bold"),
                anchor="w",
                justify="left",
                wraplength=300,
            ).pack(fill="x", pady=(4, 3))
            tk.Label(
                card,
                text=item.description,
                bg=PANEL,
                fg=MUTED,
                font=("Arial", 10),
                anchor="w",
                justify="left",
                wraplength=300,
            ).pack(fill="x", pady=(0, 10))
            bottom = tk.Frame(card, bg=PANEL)
            bottom.pack(fill="x")
            tk.Label(
                bottom,
                text=f"{item.price:.2f} MAD",
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
                activeforeground="white",
                relief="flat",
                font=("Arial", 11, "bold"),
                padx=14,
                pady=10,
                cursor="hand2",
            )
            add_button.pack(side="right")
            self._bind_hover(add_button, RED_HOVER, RED)
            for widget in (card, *card.winfo_children()):
                widget.bind("<Enter>", lambda _event, frame=card: frame.configure(highlightbackground=GOLD))
                widget.bind("<Leave>", lambda _event, frame=card: frame.configure(highlightbackground=BORDER))

    def add_item(self, item: MenuItem) -> None:
        self.cart[item.name] = self.cart.get(item.name, 0) + 1
        self.render_cart()

    def change_quantity(self, item_name: str, amount: int) -> None:
        quantity = self.cart.get(item_name, 0) + amount
        if quantity <= 0:
            self.cart.pop(item_name, None)
        else:
            self.cart[item_name] = quantity
        self.render_cart()

    def clear_cart(self) -> None:
        self.cart.clear()
        self.render_cart()

    def render_cart(self) -> None:
        for child in self.cart_view.content.winfo_children():
            child.destroy()
        total = 0.0
        count = sum(self.cart.values())
        self.cart_count.configure(text=f"{count} article{'s' if count != 1 else ''}")
        for name, quantity in self.cart.items():
            item = next(entry for entry in self.menu_items if entry.name == name)
            total += item.price * quantity
            row = tk.Frame(self.cart_view.content, bg=PANEL, pady=10)
            row.pack(fill="x")
            row.grid_columnconfigure(0, weight=1)
            tk.Label(
                row,
                text=name,
                bg=PANEL,
                fg=INK,
                font=("Arial", 10, "bold"),
                anchor="w",
                wraplength=220,
                justify="left",
            ).grid(row=0, column=0, sticky="w")
            tk.Label(
                row,
                text=f"{item.price * quantity:.2f} MAD",
                bg=PANEL,
                fg=INK,
                font=("Arial", 10, "bold"),
            ).grid(row=0, column=1, sticky="e")
            controls = tk.Frame(row, bg=PANEL)
            controls.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
            for label, change in (("−", -1), (str(quantity), 0), ("+", 1)):
                tk.Button(
                    controls,
                    text=label,
                    command=lambda selected=name, delta=change: self.change_quantity(selected, delta) if delta else None,
                    bg="#fff2cc",
                    fg=RED,
                    relief="flat",
                    font=("Arial", 12, "bold"),
                    width=4,
                    height=1,
                    cursor="hand2",
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
        self.total_label.configure(text=f"{total:.2f} MAD")
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
        payment = tk.StringVar(value="Espèces au guichet")
        for method in ("Espèces au guichet", "Carte / Solde étudiant"):
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
                with SessionLocal() as db:
                    products = {
                        product.id: product for product in get_produits(db)
                    }
                    requested = {
                        next(item.product_id for item in self.menu_items if item.name == name): quantity
                        for name, quantity in self.cart.items()
                    }
                    if any(product_id not in products for product_id in requested):
                        raise ValueError("Un produit du panier n'est plus disponible.")

                    panier = [
                        products[product_id]
                        for product_id, quantity in requested.items()
                        for _ in range(quantity)
                    ]
                    payment_method = {
                        "Espèces au guichet": "Espèces",
                        "Carte / Solde étudiant": "Carte / Solde étudiant",
                    }[payment.get()]
                    commande = create_commande(db, panier, payment_method)
                    if commande is None:
                        raise ValueError(
                            "Commande non enregistrée. Vérifiez le stock puis réessayez."
                        )
                    order_number = commande.id
            except Exception as error:
                messagebox.showerror("Commande impossible", str(error), parent=dialog)
                return

            dialog.destroy()
            self.clear_cart()
            messagebox.showinfo(
                "Commande confirmée",
                f"Commande #{order_number:03d}\nPaiement : {payment.get()}",
                parent=self,
            )

        confirm_button = tk.Button(
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
        )
        confirm_button.pack(fill="x", padx=24, pady=20)
        self._bind_hover(confirm_button, RED_HOVER, RED)


def build_kiosk_window() -> KioskApp:
    return KioskApp()


if __name__ == "__main__":
    app = KioskApp()
    app.mainloop()
