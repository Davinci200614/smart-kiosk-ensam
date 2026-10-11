"""Application entry point for the Smart Kiosk modules."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parent


def initialize_application() -> None:
    """Load configuration for the JSON-backed application."""
    from backend.storage_json import DATA_DIR

    if not DATA_DIR.is_dir():
        raise FileNotFoundError(f"JSON data directory not found: {DATA_DIR}")


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
            [sys.executable, "-m", "streamlit", "run", str(dashboard_path)],
            cwd=PROJECT_ROOT,
            check=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "Streamlit is required to launch the dashboard. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from error


def launch_process(
    interface: str,
    manager_username: str | None = None,
    manager_role: str | None = None,
) -> None:
    """Launch a module from the graphical launcher."""
    try:
        environment = os.environ.copy()
        if manager_username is not None:
            environment["SMART_KIOSK_MANAGER"] = manager_username
        if manager_role is not None:
            environment["SMART_KIOSK_MANAGER_ROLE"] = manager_role
        subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "main.py"), interface],
            cwd=PROJECT_ROOT,
            env=environment,
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
                if interface in {"manager", "dashboard"}:
                    credentials = self.authenticate_manager()
                    if credentials is None:
                        return
                    launch_process(interface, *credentials)
                else:
                    launch_process(interface)
            except RuntimeError as error:
                messagebox.showerror("Erreur de lancement", str(error))

        def authenticate_manager(self) -> str | None:
            from backend.auth_json import verify_user

            login = ctk.CTkToplevel(self)
            login.title("Accès manager")
            login.geometry("360x280")
            login.transient(self)
            login.grab_set()
            result = {"credentials": None}

            ctk.CTkLabel(
                login,
                text="Connexion manager",
                font=("Arial", 22, "bold"),
            ).pack(pady=(25, 15))
            username_entry = ctk.CTkEntry(login, placeholder_text="Nom utilisateur")
            username_entry.pack(padx=35, pady=8, fill="x")
            password_entry = ctk.CTkEntry(
                login,
                placeholder_text="Mot de passe",
                show="*",
            )
            password_entry.pack(padx=35, pady=8, fill="x")
            error_label = ctk.CTkLabel(login, text="", text_color="#ef4444")
            error_label.pack(pady=4)

            def submit() -> None:
                username = username_entry.get().strip()
                user = verify_user(username, password_entry.get())
                if user is not None:
                    result["credentials"] = (user.nom_utilisateur, user.role)
                    login.destroy()
                else:
                    error_label.configure(text="Identifiants manager invalides.")

            ctk.CTkButton(login, text="Se connecter", command=submit).pack(
                padx=35,
                pady=12,
                fill="x",
            )
            password_entry.bind("<Return>", lambda _event: submit())
            self.wait_window(login)
            return result["credentials"]

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
        from frontend.kiosk_ui import KioskApp

        launch_desktop(KioskApp)
    elif args.interface == "manager":
        from frontend.manager_ui import ManagerApp

        manager_username = os.getenv("SMART_KIOSK_MANAGER")
        manager_role = os.getenv("SMART_KIOSK_MANAGER_ROLE")
        if manager_username is None:
            raise RuntimeError("Manager authentication is required from the launcher.")
        launch_desktop(lambda: ManagerApp(manager_username, manager_role or "Manager"))
    else:
        launch_dashboard()


if __name__ == "__main__":
    main()