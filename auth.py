"""
Streamlit password gate — multi-user, SHA-256, session-state persistence.

Usage:
    from auth import require_login
    require_login()   # call once, immediately after st.set_page_config()

Secrets format (Streamlit Cloud → Settings → Secrets, or local
`.streamlit/secrets.toml`):

    [auth.users]
    alice = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
    bob   = "ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f"

Each value is the SHA-256 hex digest of the user's password. Generate with:

    python tools/hash_password.py

A successful login prints to stdout (captured by Streamlit Cloud logs):

    [AUTH] 2026-05-16T14:32:11Z user=alice login OK

Failed attempts log:

    [AUTH] 2026-05-16T14:33:02Z user=alice login FAIL
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import sys

import streamlit as st


def _log(event: str, user: str) -> None:
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[AUTH] {ts} user={user} {event}", flush=True, file=sys.stdout)


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_user_table() -> dict[str, str]:
    # Streamlit raises different exception types across versions when secrets
    # are missing (FileNotFoundError on old, StreamlitSecretNotFoundError on
    # newer, KeyError when the key is absent from an existing file). Catch
    # broadly — this is config-load, not a hot path.
    try:
        users = st.secrets["auth"]["users"]
    except Exception:
        st.error(
            "Authentication is not configured. Add an `[auth.users]` table to "
            "Streamlit Cloud Secrets (or local `.streamlit/secrets.toml`)."
        )
        st.stop()
    return {str(k): str(v) for k, v in users.items()}


def _verify(username: str, password: str, users: dict[str, str]) -> bool:
    expected = users.get(username)
    if expected is None:
        # Hash anyway to keep timing roughly constant.
        hmac.compare_digest(_hash(password), _hash(password))
        return False
    return hmac.compare_digest(_hash(password), expected.lower())


def require_login() -> str:
    """Gate the app behind a login form. Returns the logged-in username.

    Call once at the top of the script (after st.set_page_config). If the
    user is not authenticated, renders a login form and calls st.stop().
    """
    if st.session_state.get("auth_user"):
        _render_sidebar_status(st.session_state["auth_user"])
        return st.session_state["auth_user"]

    users = _load_user_table()

    st.markdown("### 🔒 Sign in")
    st.caption("Enter your username and password to access the normalizer.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="auth_username_input").strip()
        password = st.text_input(
            "Password", type="password", key="auth_password_input"
        )
        submitted = st.form_submit_button("Sign in")

    if submitted:
        if _verify(username, password, users):
            st.session_state["auth_user"] = username
            _log("login OK", username)
            st.rerun()
        else:
            _log("login FAIL", username or "<empty>")
            st.error("Invalid username or password.")

    st.stop()
    return ""  # unreachable


def _render_sidebar_status(username: str) -> None:
    with st.sidebar:
        st.markdown(f"**Signed in:** `{username}`")
        if st.button("Sign out", key="auth_logout_btn"):
            _log("logout", username)
            for k in ("auth_user", "auth_username_input", "auth_password_input"):
                st.session_state.pop(k, None)
            st.rerun()
        st.divider()
