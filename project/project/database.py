from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            skills TEXT NOT NULL,
            interest TEXT NOT NULL,
            marks TEXT NOT NULL,
            career TEXT NOT NULL,
            confidence TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    connection.commit()
    connection.close()


def save_user(name: str, email: str, password: str) -> int:
    connection = get_db_connection()
    cursor = connection.cursor()
    existing_user = cursor.execute(
        "SELECT id FROM users WHERE email = ? LIMIT 1",
        (email,),
    ).fetchone()

    if existing_user:
        connection.close()
        return existing_user["id"]

    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, password),
    )
    user_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return user_id


def update_user(user_id: int, name: str, email: str, password: str | None = None) -> None:
    connection = get_db_connection()
    if password:
        cursor = connection.execute(
            "UPDATE users SET name = ?, email = ?, password = ? WHERE id = ?",
            (name, email, password, user_id),
        )
    else:
        cursor = connection.execute(
            "UPDATE users SET name = ?, email = ? WHERE id = ?",
            (name, email, user_id),
        )

    if cursor.rowcount == 0:
        existing_user = connection.execute(
            "SELECT id FROM users WHERE email = ? LIMIT 1",
            (email,),
        ).fetchone()
        if existing_user:
            if password:
                connection.execute(
                    "UPDATE users SET name = ?, password = ? WHERE id = ?",
                    (name, password, existing_user["id"]),
                )
            else:
                connection.execute(
                    "UPDATE users SET name = ? WHERE id = ?",
                    (name, existing_user["id"]),
                )
        else:
            connection.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password or ""),
            )
    connection.commit()
    connection.close()


def update_user_password_by_email(email: str, password: str) -> None:
    connection = get_db_connection()
    cursor = connection.execute(
        "UPDATE users SET password = ? WHERE email = ?",
        (password, email),
    )
    if cursor.rowcount == 0:
        connection.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("User", email, password),
        )
    connection.commit()
    connection.close()


def save_profile(user_id: int, skills: str, interest: str, marks: str, career: str, confidence: str) -> None:
    connection = get_db_connection()
    connection.execute(
        """
        INSERT INTO profile (user_id, skills, interest, marks, career, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, skills, interest, marks, career, confidence),
    )
    connection.commit()
    connection.close()


def fetch_profiles() -> list[sqlite3.Row]:
    connection = get_db_connection()
    rows = connection.execute(
        """
        SELECT skills, interest, marks, career, confidence
        FROM profile
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()
    return rows
