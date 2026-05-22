"""
AI Email Agent — Streamlit Dashboard
Monitors Gmail inbox, classifies emails and generates professional replies.
"""
import streamlit as st
from config.settings import settings
from agent.gmail_client import (
    get_gmail_service,
    fetch_unread_emails,
    send_reply,
    apply_label,
)
from agent.classifier import build_classifier
from agent.responder import build_responder


st.set_page_config(
    page_title="AI Email Agent",
    page_icon="✉️",
    layout="wide",
)

st.title("✉️ AI Email Agent")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password",
                             value=settings.openai_api_key)
    max_emails = st.slider("Max emails to fetch", 1, 20, 5)
    st.divider()
    run_btn = st.button("▶ Run Agent", use_container_width=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = []
if "service" not in st.session_state:
    st.session_state.service = None

# ── Agent execution ────────────────────────────────────────────────────────────
if run_btn:
    if not api_key:
        st.error("OpenAI API key is required.")
        st.stop()

    classify = build_classifier(api_key)
    respond = build_responder(api_key)

    with st.spinner("Connecting to Gmail..."):
        st.session_state.service = get_gmail_service(
            settings.gmail_credentials_path,
            settings.gmail_token_path,
        )

    emails = fetch_unread_emails(
        st.session_state.service,
        max_results=max_emails,
    )

    if not emails:
        st.info("No unread emails found.")
        st.stop()

    st.info(f"Found **{len(emails)}** unread email(s). Processing...")
    st.session_state.results = []

    for email in emails:
        with st.status(f"Processing: {email['subject'][:60]}...", expanded=True):
            st.write("🔍 Classifying...")
            classification = classify(email)

            st.write(f"📂 Category: **{classification['category']}** "
                     f"({classification['confidence']:.0%} confidence)")

            st.write("✍️ Generating reply...")
            reply = respond(email, classification["category"])

            st.session_state.results.append({
                "email": email,
                "classification": classification,
                "reply": reply,
                "sent": False,
            })

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.results:
    st.divider()
    st.subheader("📋 Processed Emails")

    for idx, result in enumerate(st.session_state.results):
        email = result["email"]
        cls = result["classification"]

        col1, col2 = st.columns([1, 1])

        with col1:
            with st.expander(f"📧 {email['subject'][:70]}", expanded=False):
                st.caption(f"**From:** {email['from']}")
                st.caption(f"**Category:** `{cls['category']}` | "
                           f"**Confidence:** {cls['confidence']:.0%}")
                st.caption(f"**Reasoning:** {cls['reasoning']}")
                st.text_area(
                    "Original Email",
                    email["body"][:500],
                    height=150,
                    disabled=True,
                    key=f"orig_{idx}",
                )

        with col2:
            with st.expander("✉️ Generated Reply", expanded=True):
                reply_text = st.text_area(
                    "Edit before sending",
                    result["reply"],
                    height=200,
                    key=f"reply_{idx}",
                )
                if not result["sent"]:
                    if st.button("📤 Send Reply", key=f"send_{idx}"):
                        send_reply(
                            st.session_state.service,
                            email,
                            reply_text,
                        )
                        apply_label(
                            st.session_state.service,
                            email["id"],
                            cls["category"],
                        )
                        st.session_state.results[idx]["sent"] = True
                        st.success("✅ Reply sent and label applied.")
                        st.rerun()
                else:
                    st.success("✅ Already sent")