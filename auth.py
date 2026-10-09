import hashlib
import hmac
import os
import secrets
import time

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

ITERATIONS = 200_000


def _derive(password, salt_hex):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), ITERATIONS
    ).hex()


def hash_password(password):
    salt_hex = secrets.token_hex(16)
    return f"{salt_hex}:{_derive(password, salt_hex)}"


def verify_password(password, stored_hash):
    try:
        salt_hex, expected = stored_hash.split(":")
        actual = _derive(password, salt_hex)
    except ValueError:
        return False
    return hmac.compare_digest(actual.encode(), expected.encode())


def is_configured():
    return bool(os.getenv("DASHBOARD_USER") and os.getenv("DASHBOARD_PASSWORD_HASH"))


def check_credentials(username, password):
    user_ok = hmac.compare_digest(username.encode(), os.getenv("DASHBOARD_USER").encode())
    password_ok = verify_password(password, os.getenv("DASHBOARD_PASSWORD_HASH"))
    return user_ok and password_ok


def require_login():
    if st.session_state.get("authenticated"):
        return

    _, middle, _ = st.columns([1, 1, 1])
    with middle:
        st.title("Sales Analytics")

        if not is_configured():
            st.error(
                "Login is not configured. Run make_password_hash.py "
                "and add the printed lines to the .env file."
            )
            st.stop()

        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

        if submitted:
            if check_credentials(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.rerun()
            time.sleep(1)
            st.error("Invalid username or password.")

    st.stop()


def logout():
    st.session_state["authenticated"] = False
    st.session_state.pop("username", None)


def render_logout():
    st.sidebar.divider()
    st.sidebar.caption(f"Logged in as {st.session_state.get('username', '')}")
    st.sidebar.button("Log out", on_click=logout)