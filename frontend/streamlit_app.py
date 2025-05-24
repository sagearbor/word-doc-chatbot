import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Word Doc Chatbot")
st.title("📄 Word Document Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_file = st.sidebar.file_uploader("Upload a .docx file", type=["docx"])
author = st.sidebar.text_input("Author for tracked changes", "AI Reviewer")
case_sensitive = st.sidebar.checkbox("Case sensitive search", True)
add_comments = st.sidebar.checkbox("Add comments", True)

# Display chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Enter instructions and press Enter")
if prompt:
    if uploaded_file is None:
        st.warning("Please upload a document before sending instructions.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {
            "instructions": prompt,
            "author_name": author,
            "case_sensitive": str(case_sensitive).lower(),
            "add_comments": str(add_comments).lower(),
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/process-document/", files=files, data=data)
            resp.raise_for_status()
            result = resp.json()
            download_url = result.get("download_url")
            reply = "Document processed."
            if download_url:
                reply += f" [Download here]({download_url})"
            if result.get("log_content"):
                reply += "\n\n" + result["log_content"]
        except Exception as e:
            reply = f"Failed to process document: {e}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

