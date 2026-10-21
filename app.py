from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("PREACHSELAH_SECRET_KEY") or secrets.token_hex(32),
    DATABASE=os.environ.get(
        "PREACHSELAH_DATABASE",
        os.path.join(app.instance_path, "accounts.sqlite3"),
    ),
    PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("PREACHSELAH_COOKIE_SECURE") == "1",
)
os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)


def get_database() -> sqlite3.Connection:
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with closing(get_database()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def display_name_from_email(email: str) -> str:
    local_part = email.rsplit("@", 1)[0].split("+", 1)[0]
    local_part = re.sub(r"([a-z])([A-Z])", r"\1 \2", local_part)
    words = re.findall(r"[^\W_]+", local_part, flags=re.UNICODE)
    name = " ".join(word.capitalize() for word in words if not word.isdecimal())
    return name or "Friend"


def csrf_token() -> str: 
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.context_processor
def inject_csrf_token() -> dict[str, str]:
    return {"csrf_token": csrf_token()}


def csrf_is_valid() -> bool:
    token = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    return bool(token and expected and secrets.compare_digest(token, expected))


def valid_email(email: str) -> bool:
    if len(email) > 254 or email.count("@") != 1:
        return False
    local_part, domain = email.rsplit("@", 1)
    return (
        len(local_part) <= 64
        and bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+", local_part))
        and "." in domain
        and all(
            label
            and len(label) <= 63
            and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", label)
            for label in domain.split(".")
        )
    )


initialize_database()

BOOKS = [
    ("Genesis", 50), ("Exodus", 40), ("Leviticus", 27), ("Numbers", 36),
    ("Deuteronomy", 34), ("Joshua", 24), ("Judges", 21), ("Ruth", 4),
    ("1 Samuel", 31), ("2 Samuel", 24), ("1 Kings", 22), ("2 Kings", 25),
    ("1 Chronicles", 29), ("2 Chronicles", 36), ("Ezra", 10), ("Nehemiah", 13),
    ("Esther", 10), ("Job", 42), ("Psalms", 150), ("Proverbs", 31),
    ("Ecclesiastes", 12), ("Song of Solomon", 8), ("Isaiah", 66), ("Jeremiah", 52),
    ("Lamentations", 5), ("Ezekiel", 48), ("Daniel", 12), ("Hosea", 14),
    ("Joel", 3), ("Amos", 9), ("Obadiah", 1), ("Jonah", 4), ("Micah", 7),
    ("Nahum", 3), ("Habakkuk", 3), ("Zephaniah", 3), ("Haggai", 2),
    ("Zechariah", 14), ("Malachi", 4), ("Matthew", 28), ("Mark", 16),
    ("Luke", 24), ("John", 21), ("Acts", 28), ("Romans", 16),
    ("1 Corinthians", 16), ("2 Corinthians", 13), ("Galatians", 6),
    ("Ephesians", 6), ("Philippians", 4), ("Colossians", 4),
    ("1 Thessalonians", 5), ("2 Thessalonians", 3), ("1 Timothy", 6),
    ("2 Timothy", 4), ("Titus", 3), ("Philemon", 1), ("Hebrews", 13),
    ("James", 5), ("1 Peter", 5), ("2 Peter", 3), ("1 John", 5),
    ("2 John", 1), ("3 John", 1), ("Jude", 1), ("Revelation", 22),
]

TOPICS = [
    {
        "title": "Faith in the waiting",
        "category": "Faith",
        "reference": "Isaiah 40:31",
        "verse": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles.",
        "hint": "Encourage your church to see waiting not as wasted time, but as a place where God renews strength and deepens trust.",
        "points": ["Waiting can reshape our dependence on God", "God meets us with strength for today", "Hope gives us courage to keep moving"],
    },
    {
        "title": "Grace for a new beginning",
        "category": "Grace",
        "reference": "Lamentations 3:22–23",
        "verse": "It is of the LORD'S mercies that we are not consumed, because his compassions fail not. They are new every morning.",
        "hint": "Show how God's steadfast mercy meets people in the middle of their mess and gives them room to begin again.",
        "points": ["God's mercy is rooted in his character", "A hard season does not have the final word", "Receive today's grace and extend it to others"],
    },
    {
        "title": "Peace in the storm",
        "category": "Hope",
        "reference": "Mark 4:39",
        "verse": "And he arose, and rebuked the wind, and said unto the sea, Peace, be still.",
        "hint": "Use the storm on the lake to explore the difference between the presence of trouble and the presence of Jesus.",
        "points": ["Following Jesus does not mean avoiding every storm", "Bring honest fear to Christ", "His presence speaks peace in uncertainty"],
    },
    {
        "title": "A love that serves",
        "category": "Love",
        "reference": "John 13:14–15",
        "verse": "If I then, your Lord and Master, have washed your feet; ye also ought to wash one another's feet.",
        "hint": "Invite listeners to rethink greatness through Jesus' humble act of service and identify one practical way to serve.",
        "points": ["Jesus leads by serving", "Humility makes love visible", "Small acts of care can change a community"],
    },
    {
        "title": "Courage to take the next step",
        "category": "Courage",
        "reference": "Joshua 1:9",
        "verse": "Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee.",
        "hint": "Speak to the fear of the unknown and ground courage in God's companionship rather than in our own confidence.",
        "points": ["Courage can coexist with uncertainty", "Remember what God has already spoken", "Take the next faithful step together"],
    },
    {
        "title": "The gift of forgiveness",
        "category": "Forgiveness",
        "reference": "Ephesians 4:32",
        "verse": "And be ye kind one to another, tenderhearted, forgiving one another, even as God for Christ's sake hath forgiven you.",
        "hint": "Connect the forgiveness we receive in Christ with the difficult, freeing work of extending mercy to one another.",
        "points": ["Forgiveness begins with the grace we have received", "Kindness and tenderness create room for repair", "Forgiveness is a faithful process, not denial of harm"],
    },
    {
        "title": "Purpose in every season",
        "category": "Purpose",
        "reference": "Ecclesiastes 3:1",
        "verse": "To every thing there is a season, and a time to every purpose under the heaven.",
        "hint": "Help people discern what faithfulness looks like in the season they are actually living, not the one they wish they had.",
        "points": ["Every season has its own work", "God is present in change and transition", "Practice faithfulness with what is in your hands"],
    },
    {
        "title": "A generous life",
        "category": "Generosity",
        "reference": "2 Corinthians 9:7",
        "verse": "God loveth a cheerful giver.",
        "hint": "Frame generosity as a joyful response to God's generosity, reaching beyond money into time, attention, and welcome.",
        "points": ["Give freely, not from pressure", "Notice the needs right in front of you", "A generous community reflects God's abundant care"],
    },
]

CUSTOM_TOPIC_GUIDES = [
    (("faith", "trust", "waiting", "wait", "doubt"), 0),
    (("grace", "mercy", "beginning", "renewal", "compassion"), 1),
    (("peace", "hope", "storm", "anxiety", "worry"), 2),
    (("love", "serve", "service", "humility", "compassion"), 3),
    (("courage", "fear", "strength", "bravery"), 4),
    (("forgive", "forgiveness", "reconcile", "reconciliation"), 5),
    (("purpose", "season", "calling", "direction"), 6),
    (("generosity", "giving", "generous", "stewardship"), 7),
]


@app.get("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("auth.html")


@app.get("/healthz")
def health_check():
    return "ok"


@app.post("/register")
def register():
    if not csrf_is_valid():
        flash("Your session expired. Please try again.", "error")
        return redirect(url_for("home"))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not valid_email(email):
        flash("Enter a valid email address.", "error")
        return redirect(url_for("home", mode="register"))
    if len(password) < 8:
        flash("Choose a password with at least 8 characters.", "error")
        return redirect(url_for("home", mode="register"))

    name = display_name_from_email(email)
    with closing(get_database()) as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO users (email, display_name, password_hash) VALUES (?, ?, ?)",
                (email, name, generate_password_hash(password)),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            flash("An account with that email already exists. Sign in instead.", "error")
            return redirect(url_for("home"))

    session.clear()
    session["user_id"] = cursor.lastrowid
    session["display_name"] = name
    session["welcome_pending"] = True
    session.permanent = True
    csrf_token()
    return redirect(url_for("dashboard"))


@app.post("/login")
def login():
    if not csrf_is_valid():
        flash("Your session expired. Please try again.", "error")
        return redirect(url_for("home"))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    with closing(get_database()) as connection:
        user = connection.execute(
            "SELECT id, email, display_name, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Email or password was not recognized.", "error")
        return redirect(url_for("home"))

    session.clear()
    session["user_id"] = user["id"]
    session["display_name"] = user["display_name"]
    session["welcome_pending"] = True
    session.permanent = True
    csrf_token()
    return redirect(url_for("dashboard"))


@app.post("/logout")
def logout():
    if not csrf_is_valid():
        flash("Your session expired. Please try again.", "error")
        return redirect(url_for("home"))
    session.clear()
    return redirect(url_for("home"))


@app.get("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("home"))
    welcome_name = session.get("display_name") if session.pop("welcome_pending", False) else None
    return render_template(
        "dashboard.html",
        books=BOOKS,
        topics=TOPICS,
        display_name=session.get("display_name", "Friend"),
        welcome_name=welcome_name,
    )


@app.post("/api/topic")
def create_topic():
    if not session.get("user_id"):
        return jsonify(error="Sign in to create a topic."), 401
    payload = request.get_json(silent=True)
    title = payload.get("title", "").strip() if isinstance(payload, dict) else ""
    if not title:
        return jsonify(error="Enter a topic to get started."), 400
    if len(title) > 120:
        return jsonify(error="Keep your topic to 120 characters or fewer."), 400

    normalized_title = title.casefold()
    guide = next(
        (
            TOPICS[index]
            for keywords, index in CUSTOM_TOPIC_GUIDES
            if any(keyword in normalized_title for keyword in keywords)
        ),
        None,
    )
    if guide is None:
        guide = {
            "category": "Your topic",
            "reference": "2 Timothy 3:16",
            "verse": "All scripture is given by inspiration of God, and is profitable for doctrine, for reproof, for correction, for instruction in righteousness:",
            "hint": "Begin with the passage in its full context. Ask what it reveals about God and people, then connect that truth to “"
            + title
            + "” and a practical response for your listeners.",
            "points": [
                "What does Scripture say about this topic?",
                "What does the passage reveal about God?",
                "How can listeners respond this week?",
            ],
        }

    return jsonify(
        title=title,
        category=guide["category"],
        reference=guide["reference"],
        verse=guide["verse"],
        hint=guide["hint"],
        points=guide["points"],
        custom=True,
    )


@app.get("/api/chapter")
def chapter():
    if not session.get("user_id"):
        return jsonify(error="Sign in to read the Bible."), 401
    book_name = request.args.get("book", "")
    chapter_value = request.args.get("chapter", "")
    book = next((item for item in BOOKS if item[0].casefold() == book_name.casefold()), None)
    if book is None:
        return jsonify(error="Choose a valid book of the Bible."), 400
    try:
        chapter_number = int(chapter_value)
    except (TypeError, ValueError):
        return jsonify(error="Chapter must be a number."), 400
    if not 1 <= chapter_number <= book[1]:
        return jsonify(error=f"{book[0]} has chapters 1–{book[1]}."), 400

    url = f"https://bible-api.com/{quote(book[0])}%20{chapter_number}?translation=kjv"
    try:
        api_request = Request(url, headers={"User-Agent": "PreachSelah/1.0"})
        with urlopen(api_request, timeout=25) as response:
            passage = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        app.logger.warning("Bible API request failed for %s %s: %s", book[0], chapter_number, exc)
        return jsonify(error="The Bible chapter could not be loaded. Please try again shortly."), 502

    return jsonify(
        reference=passage.get("reference", f"{book[0]} {chapter_number}"),
        verses=[{"number": verse["verse"], "text": verse["text"].strip()} for verse in passage.get("verses", [])],
    )


if __name__ == "__main__":
    app.run()
