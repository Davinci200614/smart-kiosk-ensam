"""Application entry point for the Smart Kiosk modules."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from backend.database import configure_database, init_db

PROJECT_ROOT = Path(__file__).resolve().parent


def initialize_application() -> None:
    """Load configuration and initialize shared application resources."""
    load_dotenv(PROJECT_ROOT / ".env")
    configure_database(os.getenv("DATABASE_URL", "sqlite:///buvette.db"))
    init_db()


def launch_desktop(interface_factory: Callable[[], object]) -> None:
    """Start a CustomTkinter interface after application initialization."""
    import customtkinter as ctk

    ctk.set_appearance_mode(os.getenv("UI_APPEARANCE_MODE", "Dark"))
    app = interface_factory()
    app.mainloop()  # type: ignore[attr-defined]


def launch_dashboard() -> None:
    """Start the Streamlit dashboard as a separate application process."""
    dashboard_path = PROJECT_ROOT / "analytics" / "dashboard.py"
    if not dashboard_path.is_file():
        raise FileNotFoundError(f"Dashboard file not found: {dashboard_path}")

    try:
        subprocess.run(
            ["streamlit", "run", str(dashboard_path)],
            cwd=PROJECT_ROOT,
            check=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "Streamlit is required to launch the dashboard. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from error


def launch_process(interface: str) -> None:
    """Launch a module from the graphical launcher."""
    try:
        subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "main.py"), interface],
            cwd=PROJECT_ROOT,
        )
    except OSError as error:
        raise RuntimeError(f"Unable to launch the {interface} module.") from error


def launch_graphical_menu() -> None:
    """Display the application selector."""
    import customtkinter as ctk
    from tkinter import messagebox

    class LauncherApp(ctk.CTk):
        def __init__(self) -> None:
            super().__init__()
            self.title("Smart Kiosk - Accueil")
            self.geometry("480x420")
            self.minsize(400, 360)

            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=1)

            ctk.CTkLabel(
                self,
                text="Smart Kiosk",
                font=("Arial", 30, "bold"),
            ).grid(row=0, column=0, padx=30, pady=(35, 20))

            menu = ctk.CTkFrame(self)
            menu.grid(row=1, column=0, padx=35, pady=10, sticky="nsew")
            menu.grid_columnconfigure(0, weight=1)

            for row, (label, interface) in enumerate(
                (
                    ("Borne client", "kiosk"),
                    ("Caisse et cuisine", "manager"),
                    ("Dashboard financier", "dashboard"),
                )
            ):
                button = ctk.CTkButton(
                    menu,
                    text=label,
                    height=55,
                    font=("Arial", 17, "bold"),
                    command=lambda selected=interface: self.open_module(selected),
                )
                button.grid(row=row, column=0, padx=25, pady=12, sticky="ew")

            ctk.CTkButton(
                self,
                text="Quitter",
                command=self.destroy,
                fg_color="transparent",
                border_width=1,
            ).grid(row=2, column=0, padx=100, pady=(10, 30), sticky="ew")

        def open_module(self, interface: str) -> None:
            try:
                launch_process(interface)
            except RuntimeError as error:
                messagebox.showerror("Erreur de lancement", str(error))

    LauncherApp().mainloop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch a Smart Kiosk application interface."
    )
    parser.add_argument(
        "interface",
        choices=("kiosk", "manager", "dashboard"),
        nargs="?",
        help="Interface to launch.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    initialize_application()

    if args.interface is None:
        launch_graphical_menu()
    elif args.interface == "kiosk":
        from frontend.kiosk import KioskApp

        launch_desktop(KioskApp)
    elif args.interface == "manager":
        from frontend.kds import ManagerApp

        launch_desktop(ManagerApp)
    else:
        launch_dashboard()


if __name__ == "__main__":
    main()