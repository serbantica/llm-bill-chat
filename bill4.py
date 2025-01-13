#!/usr/bin/env -S poetry run python

import os
import json
import pdfplumber
import streamlit as st
from openai import OpenAI

######################################
# 1. OPENAI SETUP
######################################
# The OpenAI object picks up OPENAI_API_KEY from the environment variable
client = OpenAI()

######################################
# 2. DATA LOADING & PARSING
######################################
def load_user_data(user_id):
    file_path = os.path.join("data", "user_data", f"user_data_{user_id}.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as file:
        return json.load(file)

def parse_pdf_to_json(pdf_path):
    costuri = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    if 'Data emiterii facturii' in line:
                        date = line.split()[-1]
                        costuri['Data emiterii facturii'] = date
                    elif 'Valoare facturată fără TVA' in line:
                        value = float(line.split()[-2].replace(',', '.'))
                        costuri['Valoare facturata'] = value
    return costuri

def check_related_keys(question, user_id):
    user_data = load_user_data(user_id)
    bill_keys = set()
    for bill in user_data.get("bills", []):
        bill_keys.update(bill.keys())
    related_keys = [key for key in bill_keys if key.lower() in question.lower()]
    return related_keys

######################################
# 3. BUILD CONTEXT FROM USER QUERY + BILL DATA
######################################
def process_query(query, user_id):
    user_data = load_user_data(user_id)
    bill_info = user_data.get("bills", [])
    related_keys = check_related_keys(query, user_id)
    related_keys_str = ", ".join(related_keys) if related_keys else "N/A"

    if related_keys_str != "N/A":
        context = (
            f"Citeste informatiile despre costrurile facturate din dictionar: {bill_info} "
            f"si raspunde la intrebarea: '{query}' dar numai cu info legate de: {related_keys_str}"
        )
    else:
        context = (
            f"Citeste informatiile despre costrurile facturate din dictionar: {bill_info} "
            f"si raspunde la intrebarea: '{query}' dar numai cu info legate de factura"
        )

    # Optional: Check length
    max_input_length = 550
    st.write(f"Context:\n{context}")
    st.write(f"Context size: {len(context)} characters")

    if len(context) > max_input_length:
        st.warning("Context too big, the request will not be sent.")
        return "Context too large to process."

    return context

######################################
# 4. STREAMLIT MAIN APP
######################################
def main():
    st.title("Telecom Bill Chat Assistant (OpenAI ChatCompletion)")

    # Sidebar user ID input
    user_id = st.sidebar.text_input("Introdu numărul de telefon:")
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None

    # If user changed the ID, load their data
    if user_id and user_id != st.session_state["user_id"]:
        # Attempt loading user data
        data = load_user_data(user_id)
        if data:
            st.session_state["user_id"] = user_id
            st.success("Utilizator găsit!")
        else:
            st.warning("Nu am găsit date pentru acest id. Poate încărcați o factură PDF?")
            st.session_state["user_id"] = user_id

    # PDF uploader
    uploaded_file = st.file_uploader("Încarcă factura PDF", type="pdf")
    if uploaded_file and st.session_state["user_id"]:
        # Parse PDF
        bill_data = parse_pdf_to_json(uploaded_file)
        # Load existing data or create new
        existing_data = load_user_data(st.session_state["user_id"])
        if "bills" not in existing_data:
            existing_data["bills"] = []
        existing_data["bills"].append(bill_data)

        # Save updated data
        file_path = os.path.join("data", "user_data", f"user_data_{st.session_state['user_id']}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(existing_data, file)
        st.success("Factura a fost încărcată și salvată cu succes!")

    # Display existing bills if data is loaded
    if st.session_state["user_id"]:
        data = load_user_data(st.session_state["user_id"])
        st.write(f"Phone Number: {st.session_state['user_id']}")
        st.write("Facturi existente:")
        for bill in data.get("bills", []):
            st.write(bill)
    else:
        st.info("Introduceți în sidebar un ID și/sau încărcați o factură PDF.")

    # Initialize conversation in session_state
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "How can I help you?"}
        ]

    st.write("---")
    st.subheader("Chat-ul cu asistentul")

    # Display existing conversation
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Chat input for the user
    if prompt := st.chat_input("Introduceți întrebarea aici:"):
        if not st.session_state["user_id"]:
            st.error("Trebuie să introduceți un număr de telefon valid sau să încărcați date.")
            return

        final_prompt = process_query(prompt, st.session_state["user_id"])

        # Append a new "user" message with the enriched prompt/context
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        st.chat_message("user").write(final_prompt)

        # Send the entire conversation (including the new context) to GPT-4
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages
        )
        response_text = completion.choices[0].message.content.strip()

        # Append the assistant's response
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.chat_message("assistant").write(response_text)

        # If usage data is available, you can display it
        if hasattr(completion, "usage"):
            st.write("Numărul de tokeni în întrebare:", completion.usage.prompt_tokens)
            st.write("Numărul de tokeni în răspuns:", completion.usage.completion_tokens)
            st.write("Numărul total de tokeni folosiți:", completion.usage.total_tokens)

if __name__ == "__main__":
    main()