from __future__ import annotations

import tkinter as tk
from datetime import datetime

from backend.crud import ORDER_STATUSES, get_commandes, update_commande_status
from backend.database import SessionLocal


BG = "#171c19"
PANEL = "#222a25"
CARD = "#fffdf8"
INK = "#25332b"
MUTED = "#aeb9b0"
GREEN = "#286447"
GOLD = "#d9a932"
ORANGE = "#bd6b35"
RED = "#a94237"
STATUS_COLORS = {
    "En attente": GOLD,
    "En préparation": ORANGE,
    "Prête": GREEN,
    "Servie": "#69776e",
}
STATUS_FLOW = ORDER_STATUSES


def _parse_order_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.now()


class ManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Smart Kiosk | Cuisine")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(bg=BG)

        self.orders: list[dict[str, object]] = []
        self.filter_status = "Toutes"
        self.refresh_job: str | None = None
        self._build_header()
        self._build_board()
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
            text="CUISINE  /  SUIVI DES COMMANDES",
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
            "Toutes",
            *STATUS_FLOW,
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
        self.filter_menu["menu"].configure(bg=PANEL, fg="#f4f1e8", activebackground=GREEN)
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
        self.bind("<Destroy>", self._unbind_mousewheel, add="+")

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

    def _unbind_mousewheel(self, event: tk.Event) -> None:
        if event.widget is self:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

    def _update_clock(self) -> None:
        self.clock_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._update_clock)

    def set_filter(self, status: str) -> None:
        self.filter_status = status
        self._render_orders()

    def advance_order(self, order: dict[str, object]) -> None:
        current = str(order["status"])
        next_status = STATUS_FLOW[
            min(STATUS_FLOW.index(current) + 1, len(STATUS_FLOW) - 1)
        ]
        try:
            with SessionLocal() as db:
                updated = update_commande_status(db, int(order["id"]), next_status)
            if updated is None:
                raise ValueError("Cette commande n'existe plus.")
        except Exception as error:
            from tkinter import messagebox

            messagebox.showerror("Mise à jour impossible", str(error), parent=self)
            self.refresh_orders()
            return
        self.refresh_orders()

    def refresh_orders(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        try:
            with SessionLocal() as db:
                records = get_commandes(db)
                self.orders = [
                    {
                        "id": order.id,
                        "number": order.id,
                        "status": order.statut,
                        "items": [
                            f"{line.quantite} × {line.produit.nom}"
                            for line in order.lignes
                            if line.produit is not None
                        ],
                        "created": _parse_order_datetime(order.date_heure),
                    }
                    for order in records
                ]
        except Exception as error:
            self.active_label.configure(text=f"Erreur de base de données: {error}")
            self.refresh_job = self.after(5000, self.refresh_orders)
            return

        self._render_orders()
        self.refresh_job = self.after(5000, self.refresh_orders)

    def _render_orders(self) -> None:
        for child in self.order_frame.winfo_children():
            child.destroy()
        active = sum(order["status"] != "Servie" for order in self.orders)
        self.active_label.configure(text=f"Commandes actives  ·  {active}")
        visible = [
            order
            for order in self.orders
            if self.filter_status == "Toutes" or order["status"] == self.filter_status
        ]
        if not visible:
            tk.Label(
                self.order_frame,
                text="Aucune commande dans cette vue.",
                bg=PANEL,
                fg=MUTED,
                font=("Arial", 13),
                pady=30,
            ).grid(row=0, column=0, sticky="w")
            return

        for index, order in enumerate(visible):
            column = index % 2
            row = index // 2
            self.order_frame.grid_columnconfigure(column, weight=1, uniform="orders")
            card = tk.Frame(
                self.order_frame,
                bg=CARD,
                highlightthickness=2,
                highlightbackground=STATUS_COLORS[str(order["status"])],
                padx=16,
                pady=14,
            )
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, 8) if column == 0 else (4, 0),
                pady=(0, 12),
            )
            card.grid_columnconfigure(0, weight=1)
            elapsed = max(0, int((datetime.now() - order["created"]).total_seconds()))
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
                text=str(order["status"]).upper(),
                bg=STATUS_COLORS[str(order["status"])],
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

            next_status = STATUS_FLOW[
                min(STATUS_FLOW.index(str(order["status"])) + 1, len(STATUS_FLOW) - 1)
            ]
            button_text = "Servie ✓" if order["status"] == "Servie" else f"Passer à : {next_status}"
            button = tk.Button(
                card,
                text=button_text,
                command=lambda selected=order: self.advance_order(selected),
                state="disabled" if order["status"] == "Servie" else "normal",
                bg=STATUS_COLORS[str(order["status"])],
                fg="white",
                activebackground=GREEN,
                activeforeground="white",
                disabledforeground="white",
                relief="flat",
                font=("Arial", 10, "bold"),
                padx=12,
                pady=8,
                cursor="hand2",
            )
            button.grid(row=len(order["items"]) + 2, column=0, sticky="ew", pady=(12, 0))
            if order["status"] != "Servie":
                normal_color = STATUS_COLORS[str(order["status"])]
                button.bind("<Enter>", lambda _event, widget=button: widget.configure(bg=GREEN))
                button.bind("<Leave>", lambda _event, widget=button, color=normal_color: widget.configure(bg=color))
            card.bind("<Enter>", lambda _event, frame=card: frame.configure(highlightbackground="#f0c75e"))
            card.bind(
                "<Leave>",
                lambda _event, frame=card, color=STATUS_COLORS[str(order["status"])]: frame.configure(highlightbackground=color),
            )


if __name__ == "__main__":
    app = ManagerApp()
    app.mainloop()
