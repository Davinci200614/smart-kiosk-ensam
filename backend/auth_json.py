"""Authentication helpers for JSON-backed manager interfaces."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from backend.models_json import Utilisateur
from backend.storage_json import load_users, save_users


MANAGER_ROLES = {"business manager", "kitchen manager", "manager"}


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000
    ).hex()
    return f"{salt}${digest}"


def verify_user(username: str, password: str) -> Utilisateur | None:
    """Return the matching manager user, or None for invalid credentials."""
    for user in load_users():
        if (
            user.nom_utilisateur != username
            or user.role.lower() not in MANAGER_ROLES
        ):
            continue
        try:
            salt, expected_hash = user.mot_de_passe_hash.split("$", 1)
        except ValueError:
            return None
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            200_000,
        ).hex()
        return user if hmac.compare_digest(actual_hash, expected_hash) else None
    return None


def verify_manager(username: str, password: str) -> bool:
    return verify_user(username, password) is not None


def add_manager(username: str, password: str, role: str) -> None:
    username = username.strip()
    role = role.strip()
    if not username:
        raise ValueError("Le nom utilisateur est obligatoire.")
    if len(password) < 8:
        raise ValueError("Le mot de passe doit avoir 8 caractères minimum.")
    if role.lower() not in {"business manager", "kitchen manager"}:
        raise ValueError("Rôle manager invalide.")
    users = load_users()
    if any(user.nom_utilisateur == username for user in users):
        raise ValueError("Ce nom utilisateur existe déjà.")
    next_id = max((user.id for user in users), default=0) + 1
    users.append(Utilisateur(next_id, username, hash_password(password), role))
    save_users(users)


def change_manager_password(username: str, password: str) -> None:
    if len(password) < 8:
        raise ValueError("Le mot de passe doit avoir 8 caractères minimum.")
    users = load_users()
    for user in users:
        if user.nom_utilisateur == username:
            user.mot_de_passe_hash = hash_password(password)
            save_users(users)
            return
    raise ValueError("Utilisateur introuvable.")
