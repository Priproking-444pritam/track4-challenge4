"""
Auth + persistence backend, powered by MongoDB (e.g. a free MongoDB Atlas cluster).

- Passwords are hashed with bcrypt — never stored in plain text.
- Episodes (topic, script, audio bytes, settings) are saved per user so a
  logged-in listener's history survives across sessions/devices.

If MONGODB_URI isn't set, every function here degrades gracefully (auth is
simply unavailable and the app falls back to guest/free-trial mode) instead
of crashing the whole app.
"""

import os
import datetime as dt

import bcrypt
from pymongo import MongoClient
from pymongo.errors import PyMongoError

_client = None


class AuthError(Exception):
    """Raised for any user-facing auth/storage problem."""
    pass


def _get_client():
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            return None
        try:
            _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        except PyMongoError as exc:
            raise AuthError(f"Could not connect to the database: {exc}") from exc
    return _client


def is_configured() -> bool:
    """Whether a database connection is available at all."""
    return _get_client() is not None


def _db():
    client = _get_client()
    if client is None:
        raise AuthError("Accounts aren't configured on this deployment yet.")
    return client[os.getenv("MONGODB_DB_NAME", "spotify_for_learning")]


def signup(username: str, password: str) -> None:
    username = username.strip()
    if len(username) < 3:
        raise AuthError("Username must be at least 3 characters.")
    if len(password) < 6:
        raise AuthError("Password must be at least 6 characters.")

    users = _db()["users"]
    if users.find_one({"username": username}):
        raise AuthError("That username is already taken.")

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    users.insert_one({
        "username": username,
        "password": hashed,
        "created_at": dt.datetime.utcnow(),
    })


def login(username: str, password: str) -> str:
    """Returns the username on success, raises AuthError on failure."""
    username = username.strip()
    users = _db()["users"]
    user = users.find_one({"username": username})
    if not user:
        raise AuthError("No account found with that username.")
    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        raise AuthError("Incorrect password.")
    return username


def save_episode(username: str, entry: dict) -> None:
    """Persists a generated episode for a logged-in user. Fails silently
    (logs to console) rather than breaking the listening experience if the
    DB is briefly unavailable."""
    try:
        episodes = _db()["episodes"]
        doc = {
            "username": username,
            "topic": entry["topic"],
            "language": entry["language"],
            "tone": entry["tone"],
            "length": entry["length"],
            "two_host": entry["two_host"],
            "script": entry["script"],
            "audio": entry["audio"],
            "timestamp": entry["timestamp"],
            "created_at": dt.datetime.utcnow(),
        }
        episodes.insert_one(doc)
    except PyMongoError as exc:
        print(f"[warn] failed to save episode to MongoDB: {exc}")


def get_episodes(username: str, limit: int = 50) -> list[dict]:
    """Fetches a user's saved episodes, most recent first."""
    try:
        episodes = _db()["episodes"]
        cursor = episodes.find({"username": username}).sort("created_at", -1).limit(limit)
        return list(cursor)
    except PyMongoError as exc:
        print(f"[warn] failed to load episodes from MongoDB: {exc}")
        return []
