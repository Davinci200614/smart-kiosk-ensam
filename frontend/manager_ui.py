from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from backend.storage_json import get_active_commandes, update_commande_status


BG = "#171c19"
PANEL = "#222a25"
CARD = "#fffdf8"
INK = "#25332b"
MUTED = "#aeb9b0"
GREEN = "#286447"
GOLD = "#d9a932"
ORANGE = "#bd6b35"
STATUS_COLORS = {
    "En attente": GOLD,
    "En préparation": ORANGE,
    "Servie": "#69776e",
}
STATUS_FLOW = ("En attente", "En préparation", "Servie")
FILTER_OPTIONS = ("Toutes", "En attente", "En préparation")
REFRESH_MS = 5_000


def _parse_order_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return datetime.now()


class ManagerApp(tk.Tk):
    def __init__(self, manager_username: str, manager_role: str = "Manager") -> None:
        super().__init__()
        self.title("Smart Kiosk | Cuisine")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(bg=BG)

        self.manager_username = manager_username
        self.manager_role = manager_role
        self.orders: list[dict[str, object]] = []
        self.filter_status = "Toutes"
        self.refresh_job: str | None = None
        self.clock_job: str | None = None
        self.order_cards: dict[int, dict[str, object]] = {}

        self._build_header()
        self._build_board()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh_orders()
        self._update_clock()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg="#f4f1e8", padx=22, pady=13)
        header.pack(fill="x")
        tk.Label(
            header,
            text="BUVETTE MAROCAINE",
            bg="#f4f1e8",
            fg=INK,
            font=("Arial", 15, "bold"),
        ).pack(side="left")
        tk.Label(
            header,
            text=f"CUISINE  /  {self.manager_role} : {self.manager_username}",
            bg="#f4f1e8",
            fg="#68746c",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=28)
        self.clock_label = tk.Label(
            header, text="", bg="#f4f1e8", fg=INK, font=("Arial", 12, "bold")
        )
        self.clock_label.pack(side="right")

    def _build_board(self) -> None:
        body = tk.Frame(self, bg=BG, padx=22, pady=18)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        toolbar = tk.Frame(body, bg=BG)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        toolbar.grid_columnconfigure(0, weight=1)
        self.active_label = tk.Label(
            toolbar, text="", bg=BG, fg="#f4f1e8", font=("Arial", 21, "bold")
        )
        self.active_label.grid(row=0, column=0, sticky="w")
        self.filter_var = tk.StringVar(value="Toutes")
        self.filter_menu = tk.OptionMenu(
            toolbar,
            self.filter_var,
            *FILTER_OPTIONS,
            command=self.set_filter,
        )
        self.filter_menu.configure(
            bg=PANEL,
            fg="#f4f1e8",
            activebackground="#344139",
            activeforeground="#f4f1e8",
            relief="flat",
            highlightthickness=0,
            font=("Arial", 10, "bold"),
            padx=10,
            pady=5,
        )
        self.filter_menu["menu"].configure(
            bg=PANEL, fg="#f4f1e8", activebackground=GREEN
        )
        self.filter_menu.grid(row=0, column=1, sticky="e")

        board = tk.Frame(body, bg=PANEL, padx=14, pady=14)
        board.grid(row=1, column=0, sticky="nsew")
        board.grid_columnconfigure(0, weight=1)
        board.grid_rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(board, bg=PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(board, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.order_frame = tk.Frame(self.canvas, bg=PANEL)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.order_frame, anchor="nw"
        )
        self.order_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_order_frame)
        self.canvas.bind_all("<MouseWheel>", self._mousewheel)
        self.canvas.bind_all("<Button-4>", self._mousewheel)
        self.canvas.bind_all("<Button-5>", self._mousewheel)

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_order_frame(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

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

    def _update_clock(self) -> None:
        if not self.winfo_exists():
            return
        self.clock_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.clock_job = self.after(1000, self._update_clock)

    def set_filter(self, status: str) -> None:
        self.filter_status = status
        self._render_orders()

    def refresh_orders(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        try:
            records = get_active_commandes()
            new_orders = [
                {
                    "id": commande.id,
                    "number": commande.id,
                    "status": commande.statut,
                    "items": [
                        f"{line.quantite} × {product.nom if product else 'Produit supprimé'}"
                        for line, product in lignes
                    ],
                    "created": _parse_order_datetime(commande.date_heure),
                }
                for commande, lignes in records
            ]
            if new_orders == self.orders:
                self.refresh_job = self.after(REFRESH_MS, self.refresh_orders)
                return
            self.orders = new_orders
        except (OSError, ValueError, TypeError) as error:
            self.active_label.configure(text=f"Erreur de lecture : {error}")
            self.refresh_job = self.after(REFRESH_MS, self.refresh_orders)
            return

        self._render_orders()
        self.refresh_job = self.after(REFRESH_MS, self.refresh_orders)

    def advance_order(self, order: dict[str, object]) -> None:
        current = str(order["status"])
        if current not in STATUS_FLOW or current == STATUS_FLOW[-1]:
            return
        try:
            updated = update_commande_status(int(order["id"]), current)
            if not updated:
                raise ValueError("Cette commande n'existe plus ou son statut est invalide.")
        except (OSError, ValueError, TypeError) as error:
            messagebox.showerror("Mise à jour impossible", str(error), parent=self)
            self.refresh_orders()
            return
        self.refresh_orders()

    def _render_orders(self) -> None:
        active = sum(order["status"] != "Servie" for order in self.orders)
        self.active_label.configure(text=f"Commandes actives  ·  {active}")
        visible = [
            order
            for order in self.orders
            if self.filter_status == "Toutes"
            or order["status"] == self.filter_status
        ]
        visible_ids = {int(order["id"]) for order in visible}
        for order_id, card_data in list(self.order_cards.items()):
            if order_id not in visible_ids:
                card = card_data["card"]
                if isinstance(card, tk.Frame) and card.winfo_exists():
                    card.grid_remove()

        if not visible:
            empty_label = self.order_cards.get(-1, {}).get("card")
            if not isinstance(empty_label, tk.Label) or not empty_label.winfo_exists():
                empty_label = tk.Label(
                    self.order_frame,
                    text="Aucune commande dans cette vue.",
                    bg=PANEL,
                    fg=MUTED,
                    font=("Arial", 13),
                    pady=30,
                )
                self.order_cards[-1] = {"card": empty_label, "snapshot": None}
            empty_label.grid(row=0, column=0, sticky="w")
            return
        empty_label = self.order_cards.pop(-1, {}).get("card")
        if isinstance(empty_label, tk.Label) and empty_label.winfo_exists():
            empty_label.destroy()

        for index, order in enumerate(visible):
            column = index % 2
            row = index // 2
            status = str(order["status"])
            color = STATUS_COLORS.get(status, MUTED)
            self.order_frame.grid_columnconfigure(column, weight=1, uniform="orders")
            order_id = int(order["id"])
            card_data = self.order_cards.get(order_id)
            if card_data is None:
                card = tk.Frame(
                    self.order_frame,
                    bg=CARD,
                    highlightthickness=2,
                    padx=16,
                    pady=14,
                )
                card.grid_columnconfigure(0, weight=1)
                card_data = {"card": card, "snapshot": None}
                self.order_cards[order_id] = card_data
            else:
                card = card_data["card"]
            if not isinstance(card, tk.Frame):
                continue
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, 8) if column == 0 else (4, 0),
                pady=(0, 12),
            )
            if card_data["snapshot"] != order:
                for child in card.winfo_children():
                    child.destroy()
                card.configure(highlightbackground=color)
                self._populate_order_card(card, order, color)
                card_data["snapshot"] = order.copy()

    def _populate_order_card(
        self, card: tk.Frame, order: dict[str, object], color: str
    ) -> None:
        status = str(order["status"])
        created = order["created"]
        elapsed = max(
            0,
            int((datetime.now() - created).total_seconds())
            if isinstance(created, datetime)
            else 0,
        )
        header = tk.Frame(card, bg=CARD)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        tk.Label(
            header,
            text=f"Commande #{order['number']}",
            bg=CARD,
            fg=INK,
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text=f"{elapsed // 60:02d}:{elapsed % 60:02d}",
            bg=CARD,
            fg=MUTED,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=1, sticky="e")
        tk.Label(
            card,
            text=status.upper(),
            bg=color,
            fg="white",
            font=("Arial", 9, "bold"),
            padx=8,
            pady=4,
        ).grid(row=1, column=0, sticky="w", pady=(9, 8))
        for item_index, item in enumerate(order["items"], start=2):
            tk.Label(
                card,
                text=item,
                bg=CARD,
                fg=INK,
                font=("Arial", 11),
                anchor="w",
                justify="left",
                wraplength=460,
            ).grid(row=item_index, column=0, sticky="ew", pady=2)

        next_status = STATUS_FLOW[STATUS_FLOW.index(status) + 1]
        button = tk.Button(
            card,
            text=f"Passer à : {next_status}",
            command=lambda selected=order: self.advance_order(selected),
            bg=color,
            fg="white",
            activebackground=GREEN,
            activeforeground="white",
            relief="flat",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
        )
        button.grid(
            row=len(order["items"]) + 2,
            column=0,
            sticky="ew",
            pady=(12, 0),
        )
        button.bind(
            "<Enter>",
            lambda _event, widget=button: widget.configure(bg=GREEN),
        )
        button.bind(
            "<Leave>",
            lambda _event, widget=button, normal=color: widget.configure(
                bg=normal
            ),
        )

    def close(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        if self.clock_job is not None:
            self.after_cancel(self.clock_job)
            self.clock_job = None
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
        self.destroy()

    logout = close


if __name__ == "__main__":
    app = ManagerApp("local-manager")
    app.mainloop()
