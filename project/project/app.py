from __future__ import annotations

import random
import smtplib
import sqlite3
import sys
from functools import wraps
from pathlib import Path
from email.mime.text import MIMEText

BASE_DIR = Path(__file__).resolve().parent
LOCAL_PACKAGES = BASE_DIR / ".packages"

if LOCAL_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_PACKAGES))

from flask import Flask, redirect, render_template, request, session, url_for
from database import (
    fetch_profiles,
    init_database as init_user_database,
    save_profile,
    save_user,
    update_user,
    update_user_password_by_email,
)
from ml_model import predict_careers

DB_PATH = BASE_DIR / "career_system.db"
sender_email = "edvpavankumar@gmail.com"
sender_password = "knbn mwaz kzbf kgfz"
otp_storage: dict[str, str] = {}

app = Flask(__name__)
app.secret_key = "career-recommendation-secret-key"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def send_otp(email: str) -> str:
    otp = f"{random.randint(100000, 999999)}"
    otp_storage[email] = otp

    message = MIMEText(f"Your OTP for Career Recommendation System is: {otp}")
    message["Subject"] = "Career Recommendation System OTP"
    message["From"] = sender_email
    message["To"] = email

    print(f"OTP for {email}: {otp}")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=8) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
    except Exception as error:
        print(f"Email send failed for {email}: {error}")

    return otp


def initialize_database() -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS system_overview (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            subtitle TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS highlight_metrics (
            id INTEGER PRIMARY KEY,
            label TEXT NOT NULL,
            value TEXT NOT NULL,
            detail TEXT NOT NULL,
            sort_order INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recommended_careers (
            id INTEGER PRIMARY KEY,
            role_name TEXT NOT NULL,
            match_score INTEGER NOT NULL,
            demand_level TEXT NOT NULL,
            description TEXT NOT NULL,
            skills TEXT NOT NULL,
            growth_path TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            level TEXT NOT NULL,
            company TEXT NOT NULL,
            duration TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS learning_paths (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            provider TEXT NOT NULL,
            duration TEXT NOT NULL,
            focus_area TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS student_profile (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            academic_score TEXT NOT NULL,
            interests TEXT NOT NULL,
            strengths TEXT NOT NULL,
            confidence_score INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            branch TEXT NOT NULL,
            interests TEXT NOT NULL,
            skills TEXT NOT NULL
        );
        """
    )

    history_columns = [
        row["name"]
        for row in cursor.execute("PRAGMA table_info(recommendation_history)").fetchall()
    ]
    if history_columns and history_columns != ["id", "student_id", "run_date"]:
        cursor.execute("ALTER TABLE recommendation_history RENAME TO recommendation_history_legacy")

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS recommendation_history (
            id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            run_date TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS recommendation_results (
            id INTEGER PRIMARY KEY,
            history_id INTEGER NOT NULL,
            career_name TEXT NOT NULL,
            confidence_score TEXT NOT NULL,
            FOREIGN KEY (history_id) REFERENCES recommendation_history(id)
        );
        """
    )

    legacy_exists = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'recommendation_history_legacy'
        """
    ).fetchone()
    if legacy_exists:
        legacy_rows = cursor.execute(
            """
            SELECT student_id, career_name, confidence_score, date
            FROM recommendation_history_legacy
            ORDER BY id
            """
        ).fetchall()
        for row in legacy_rows:
            cursor.execute(
                """
                INSERT INTO recommendation_history (student_id, run_date)
                VALUES (?, ?)
                """,
                (row["student_id"], row["date"]),
            )
            history_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO recommendation_results (history_id, career_name, confidence_score)
                VALUES (?, ?, ?)
                """,
                (history_id, row["career_name"], row["confidence_score"]),
            )
        cursor.execute("DROP TABLE recommendation_history_legacy")

    has_data = cursor.execute(
        "SELECT COUNT(*) AS total FROM system_overview"
    ).fetchone()["total"]

    if has_data == 0:
        cursor.execute(
            """
            INSERT INTO system_overview (title, subtitle, description)
            VALUES (?, ?, ?)
            """,
            (
                "Career Recommendation System for Students",
                "A professional guidance platform for careers, skills, and internships",
                (
                    "This platform helps students discover the right career path by "
                    "combining interests, technical strengths, and academic performance "
                    "into a clear recommendation flow."
                ),
            ),
        )

        cursor.executemany(
            """
            INSERT INTO highlight_metrics (label, value, detail, sort_order)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("Career Paths", "12+", "Personalized role suggestions from student inputs", 1),
                ("Skill Coverage", "24", "Mapped skills across software and data domains", 2),
                ("Internships", "18", "Recommended opportunities by readiness level", 3),
                ("Confidence", "91%", "Explainable recommendation confidence score", 4),
            ],
        )

        cursor.executemany(
            """
            INSERT INTO recommended_careers
                (role_name, match_score, demand_level, description, skills, growth_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "Full Stack Developer",
                    94,
                    "High",
                    "Ideal for students who enjoy problem-solving, application design, and practical product building.",
                    "Python, Flask, SQL, HTML, CSS, JavaScript",
                    "Junior Developer -> Software Engineer -> Technical Lead",
                ),
                (
                    "Data Analyst",
                    89,
                    "High",
                    "Well suited for students interested in data interpretation, reporting, and business insights.",
                    "Python, Pandas, SQL, Excel, Visualization",
                    "Analyst -> BI Specialist -> Analytics Consultant",
                ),
                (
                    "Machine Learning Engineer",
                    86,
                    "Growing",
                    "A strong path for students who like predictive systems, model training, and intelligent automation.",
                    "Python, Scikit-learn, NumPy, Statistics, Model Evaluation",
                    "ML Associate -> ML Engineer -> AI Specialist",
                ),
            ],
        )

        cursor.executemany(
            """
            INSERT INTO internships (title, level, company, duration, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    "Web Application Intern",
                    "Beginner",
                    "Campus Tech Labs",
                    "8 Weeks",
                    "Build responsive modules, improve UI polish, and support backend integration tasks.",
                ),
                (
                    "Data Insights Intern",
                    "Intermediate",
                    "Insight Forge",
                    "10 Weeks",
                    "Work on dashboards, data cleaning, and KPI reporting with mentor review cycles.",
                ),
                (
                    "AI Solutions Intern",
                    "Advanced",
                    "Future Stack AI",
                    "12 Weeks",
                    "Assist with recommendation pipelines, evaluation metrics, and intelligent feature prototypes.",
                ),
            ],
        )

        cursor.executemany(
            """
            INSERT INTO learning_paths (title, provider, duration, focus_area)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("Python for Career Systems", "Internal Academy", "6 Weeks", "Backend Logic"),
                ("Modern Web UI Foundations", "Design Sprint Lab", "4 Weeks", "Frontend UX"),
                ("SQL and Data Modeling", "Database Studio", "5 Weeks", "Database"),
                ("Scikit-learn Essentials", "AI Practice Hub", "6 Weeks", "Machine Learning"),
            ],
        )

        cursor.execute(
            """
            INSERT INTO student_profile
                (full_name, branch, academic_score, interests, strengths, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Student Demo Profile",
                "Information Technology",
                "8.7 CGPA",
                "Web development, data analysis, intelligent systems",
                "Problem-solving, Python, SQL, communication",
                91,
            ),
        )

    connection.commit()
    connection.close()


def fetch_dashboard_data() -> dict[str, object]:
    connection = get_connection()

    data = {
        "overview": connection.execute(
            "SELECT * FROM system_overview LIMIT 1"
        ).fetchone(),
        "metrics": connection.execute(
            "SELECT * FROM highlight_metrics ORDER BY sort_order"
        ).fetchall(),
        "careers": connection.execute(
            "SELECT * FROM recommended_careers ORDER BY match_score DESC"
        ).fetchall(),
        "internships": connection.execute(
            "SELECT * FROM internships ORDER BY id"
        ).fetchall(),
        "learning_paths": connection.execute(
            "SELECT * FROM learning_paths ORDER BY id"
        ).fetchall(),
        "student": connection.execute(
            "SELECT * FROM student_profile LIMIT 1"
        ).fetchone(),
    }

    connection.close()
    return data


def fetch_student_profile(student_id: int) -> sqlite3.Row | None:
    connection = get_connection()
    student = connection.execute(
        "SELECT id, name, email, branch, interests, skills FROM students WHERE id = ?",
        (student_id,),
    ).fetchone()
    connection.close()
    return student


def fetch_recommendation_history(student_id: int) -> list[dict[str, object]]:
    connection = get_connection()
    runs = connection.execute(
        """
        SELECT id, run_date
        FROM recommendation_history
        WHERE student_id = ?
        ORDER BY id DESC
        LIMIT 8
        """,
        (student_id,),
    ).fetchall()
    history: list[dict[str, object]] = []
    for run in runs:
        results = connection.execute(
            """
            SELECT career_name, confidence_score
            FROM recommendation_results
            WHERE history_id = ?
            ORDER BY id
            """,
            (run["id"],),
        ).fetchall()
        history.append(
            {
                "id": run["id"],
                "run_date": run["run_date"],
                "results": results,
            }
        )
    connection.close()
    return history


def get_profile_completion(student_profile: sqlite3.Row | None) -> int:
    if not student_profile:
        return 0

    fields = [
        student_profile["name"],
        student_profile["email"],
        student_profile["branch"],
        student_profile["interests"],
        student_profile["skills"],
    ]
    completed = sum(1 for field in fields if str(field).strip())
    return round((completed / len(fields)) * 100)


initialize_database()
init_user_database()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "student_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def home() -> str:
    return render_template(
        "index.html",
        current_student=session.get("student_name"),
        **fetch_dashboard_data(),
    )


@app.route("/register", methods=["GET", "POST"])
def register() -> str:
    success = False
    error = None
    form_data = {
        "name": "",
        "email": "",
        "password": "",
        "branch": "",
        "interests": "",
    }

    if request.method == "POST":
        form_data = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "password": request.form.get("password", "").strip(),
            "branch": request.form.get("branch", "").strip(),
            "interests": request.form.get("interests", "").strip(),
        }

        if len(form_data["password"]) < 6:
            error = "Password must be at least 6 characters"
        else:
            connection = get_connection()
            existing_user = connection.execute(
                """
                SELECT id FROM students
                WHERE LOWER(email) = LOWER(?) OR LOWER(name) = LOWER(?)
                LIMIT 1
                """,
                (form_data["email"], form_data["name"]),
            ).fetchone()

            if existing_user:
                connection.close()
                error = "User already exists. Please login."
            else:
                connection.execute(
                    """
                    INSERT INTO students (name, email, password, branch, interests, skills)
                    VALUES (:name, :email, :password, :branch, :interests, :skills)
                    """,
                    {**form_data, "skills": ""},
                )
                connection.commit()
                connection.close()
                save_user(form_data["name"], form_data["email"], form_data["password"])
                success = True
                session["auth_message"] = "Registration successful. Please login."
                return redirect(url_for("login"))

    return render_template("register.html", success=success, error=error, form_data=form_data)


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    error = None
    message = session.pop("auth_message", None)
    form_data = {"email": "", "password": ""}

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        form_data["email"] = email
        form_data["password"] = password

        if len(password) < 6:
            error = "Password must be at least 6 characters"
            return render_template("login.html", error=error, message=message, form_data=form_data)

        connection = get_connection()
        student = connection.execute(
            """
            SELECT * FROM students
            WHERE email = ? AND password = ?
            LIMIT 1
            """,
            (email, password),
        ).fetchone()
        connection.close()

        if student:
            save_user(student["name"], student["email"], password)
            send_otp(student["email"])
            session["pending_login_email"] = student["email"]
            return redirect(url_for("verify_login_otp", email=student["email"]))

        error = "Invalid email or password"

    return render_template("login.html", error=error, message=message, form_data=form_data)


@app.route("/logout")
def logout() -> str:
    session.clear()
    return redirect(url_for("login"))


@app.route("/verify-login-otp/<email>", methods=["GET", "POST"])
def verify_login_otp(email: str) -> str:
    error = None

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        if otp_storage.get(email) == entered_otp:
            connection = get_connection()
            student = connection.execute(
                "SELECT * FROM students WHERE email = ? LIMIT 1",
                (email,),
            ).fetchone()
            connection.close()

            if student:
                otp_storage.pop(email, None)
                session.pop("pending_login_email", None)
                session["student_id"] = student["id"]
                session["user_id"] = student["id"]
                session["student_name"] = student["name"]
                session["student_email"] = student["email"]
                return redirect(url_for("student_dashboard"))

            error = "User not found."
        else:
            error = "Invalid OTP"

    return render_template("verify_login_otp.html", email=email, error=error)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password() -> str:
    error = None
    message = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        connection = get_connection()
        student = connection.execute(
            "SELECT id FROM students WHERE email = ? LIMIT 1",
            (email,),
        ).fetchone()
        connection.close()

        if student:
            send_otp(email)
            return redirect(url_for("verify_reset_otp", email=email))
        error = "Email not found"

    return render_template("forgot_password.html", error=error, message=message)


@app.route("/verify-reset-otp/<email>", methods=["GET", "POST"])
def verify_reset_otp(email: str) -> str:
    error = None

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        if otp_storage.get(email) == entered_otp:
            otp_storage.pop(email, None)
            session["reset_verified_email"] = email
            return redirect(url_for("reset_password", email=email))
        error = "Invalid OTP"

    return render_template("verify_reset_otp.html", email=email, error=error)


@app.route("/reset-password/<email>", methods=["GET", "POST"])
def reset_password(email: str) -> str:
    error = None
    message = None

    if session.get("reset_verified_email") != email:
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if len(password) < 6:
            error = "Password must be at least 6 characters"
        elif password != confirm_password:
            error = "Password and confirm password must match"
        else:
            connection = get_connection()
            connection.execute(
                "UPDATE students SET password = ? WHERE email = ?",
                (password, email),
            )
            connection.commit()
            connection.close()
            update_user_password_by_email(email, password)
            session.pop("reset_verified_email", None)
            session["auth_message"] = "Password reset successful. Please login."
            return redirect(url_for("login"))

    return render_template("reset_password.html", email=email, error=error, message=message)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile() -> str:
    error = None
    current_user_id = session.get("user_id", session["student_id"])
    student_profile = fetch_student_profile(current_user_id)
    form_data = {
        "name": student_profile["name"] if student_profile else "",
        "email": student_profile["email"] if student_profile else "",
        "branch": student_profile["branch"] if student_profile else "",
        "interests": student_profile["interests"] if student_profile else "",
        "skills": student_profile["skills"] if student_profile else "",
    }

    if request.method == "POST":
        form_data = {
            "name": request.form.get("name", "").strip(),
            "email": student_profile["email"] if student_profile else session.get("student_email", ""),
            "branch": request.form.get("branch", "").strip(),
            "interests": request.form.get("interests", "").strip(),
            "skills": request.form.get("skills", "").strip(),
        }
        password = request.form.get("password", "").strip()

        connection = get_connection()
        if password and len(password) < 6:
            connection.close()
            error = "Password must be at least 6 characters"
        else:
            if password:
                connection.execute(
                    """
                    UPDATE students
                    SET name = ?, email = ?, password = ?, branch = ?, interests = ?, skills = ?
                    WHERE id = ?
                    """,
                    (
                        form_data["name"],
                        form_data["email"],
                        password,
                        form_data["branch"],
                        form_data["interests"],
                        form_data["skills"],
                        current_user_id,
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE students
                    SET name = ?, email = ?, branch = ?, interests = ?, skills = ?
                    WHERE id = ?
                    """,
                    (
                        form_data["name"],
                        form_data["email"],
                        form_data["branch"],
                        form_data["interests"],
                        form_data["skills"],
                        current_user_id,
                    ),
                )
            connection.commit()
            connection.close()
            update_user(current_user_id, form_data["name"], form_data["email"], password if password else None)
            session["student_name"] = form_data["name"]
            session["student_email"] = form_data["email"]
            return redirect(url_for("student_profile"))

    return render_template("edit_profile.html", error=error, form_data=form_data)


@app.route("/dashboard")
@login_required
def student_dashboard() -> str:
    student_profile = fetch_student_profile(session["student_id"])
    history = fetch_recommendation_history(session["student_id"])
    return render_template(
        "dashboard.html",
        student_name=session.get("student_name"),
        student_profile=student_profile,
        history=history,
        profile_completion=get_profile_completion(student_profile),
    )


@app.route("/profile")
@login_required
def student_profile() -> str:
    profile = fetch_student_profile(session["student_id"])
    return render_template(
        "profile.html",
        student_name=session.get("student_name"),
        student_profile=profile,
        profile_completion=get_profile_completion(profile),
    )


@app.route("/recommend", methods=["POST"])
@login_required
def recommend() -> str:
    form_data = {
        "skills": request.form.get("skills", "").strip(),
        "interests": request.form.get("interests", "").strip(),
        "preferred_field": request.form.get("preferred_field", "").strip(),
        "programming_languages": request.form.get("programming_languages", "").strip(),
        "gpa": request.form.get("gpa", "").strip(),
    }
    student_profile = fetch_student_profile(session["student_id"])
    branch_interested = form_data["preferred_field"] or (student_profile["branch"] if student_profile else "")

    recommendation_payload = predict_careers(
        form_data["skills"],
        form_data["interests"],
        form_data["programming_languages"],
        branch_interested,
    )
    recommendations = recommendation_payload["recommendations"]
    top_recommendation = recommendations[0] if recommendations else {"title": "", "confidence_score": ""}
    save_profile(
        session["student_id"],
        form_data["skills"],
        form_data["interests"],
        form_data["gpa"],
        top_recommendation["title"],
        top_recommendation["confidence_score"],
    )

    connection = get_connection()
    connection.execute(
        """
        INSERT INTO recommendation_history (student_id, run_date)
        VALUES (?, datetime('now', 'localtime'))
        """,
        (session["student_id"],),
    )
    history_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    for recommendation in recommendations:
        connection.execute(
            """
            INSERT INTO recommendation_results (history_id, career_name, confidence_score)
            VALUES (?, ?, ?)
            """,
            (history_id, recommendation["title"], recommendation["confidence_score"]),
        )
    connection.commit()
    connection.close()

    return render_template(
        "recommendation.html",
        student_name=session.get("student_name"),
        form_data=form_data,
        student_profile=student_profile,
        recommendations=recommendations,
        internship_groups=recommendation_payload["internship_groups"],
        roadmap=recommendation_payload["roadmap"],
        analytics=recommendation_payload["analytics"],
        history=fetch_recommendation_history(session["student_id"]),
    )


@app.route("/admin")
def admin() -> str:
    return render_template("admin.html", profiles=fetch_profiles())


if __name__ == "__main__":
    app.run(debug=True)
