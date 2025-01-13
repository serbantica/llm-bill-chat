#!/usr/bin/env -S poetry run python

import os
import json
import pdfplumber
import streamlit as st
from openai import OpenAI

client = OpenAI()

def load_user_data(user_id):
    file_path = os.path.join("data", "user_data", f"user_data_{user_id}.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as file:
        return json.load(file)

def parse_pdf_to_json(pdf_path):
    user_id = {}
    serie_factura = {}
    data_factura = {}
    costuri = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')

                # Process each line and look for specific categories
                for line in lines:
                    # Check for 'Data emiterii facturii'
                    if 'Data facturii' in line:
                        date = line.split()[-1]
                        data_factura['Data factura'] = date

                    # Check for 'Valoare facturată fără TVA'
                    if 'Sold precedent' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Sold precedent'] = value
                    
                    # Check for 'Total bază de impozitare TVA'
                    elif 'Total platit din sold precedent' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Total platit din sold precedent'] = value
                    
                    # Check for 'TVA'
                    elif 'TVA' in line and '%' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['TVA'] = value
                    
                    # Check for 'Dobânzi penalizatoare'
                    elif 'Abonamente si extraopþiuni' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Dobanzi penalizatoare'] = value
                    
                    # Check for 'TOTAL DE PLATĂ FACTURĂ CURENTĂ'
                    elif 'Total factura curenta fara TVA' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Total factura curenta fara TVA'] = value
                    
                    # Check for 'Sold Cont Contract'
                    elif 'Servicii utilizate' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Servicii utilizate'] = value
                    
                    # Check for 'Compensatii'
                    elif 'Rate terminal' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Rate terminal'] = value

                    # Check for 'TVA 19,00%'
                    elif 'TVA 19,00%' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['TVA'] = value

                    # Check for 'Compensatii'
                    elif 'Total factura curenta' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Total factura curenta'] = value

    return costuri

def check_related_keys(question, user_id):
    user_data = load_user_data(user_id)
    bill_keys = set()
    for bill in user_data.get("bills", []):
        bill_keys.update(bill.keys())
    return [key for key in bill_keys if key.lower() in question.lower()]

def process_query(query, user_id):
    user_data = load_user_data(user_id)
    bill_info = user_data.get("bills", [])
    related_keys = check_related_keys(query, user_id)
    related_keys_str = ", ".join(related_keys) if related_keys else "N/A"

    if related_keys_str != "N/A":
        context = (
            f"Citeste informatiile despre costrurile in lei facturate din dictionar: {bill_info} "
            f"si raspunde la intrebarea: '{query}' dar numai cu info legate de: {related_keys_str}"
        )
    else:
        context = (
            f"Citeste informatiile despre costrurile in lei facturate din dictionar: {bill_info} "
            f"si raspunde la intrebarea: '{query}' dar numai cu info legate de factura"
        )

    max_input_length = 550
    st.write(f"Context:\n{context}")
    st.write(f"Context size: {len(context)} characters")

    if len(context) > max_input_length:
        st.warning("Prea multe caractere în context, solicitarea nu va fi trimisă.")
        return None

    return context

def main():

    st.title("Telecom Bill Chat with LLM Agent")

    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    user_id = st.sidebar.text_input("Introdu numărul de telefon:")
    if user_id and user_id != st.session_state.user_id:
        data = load_user_data(user_id)
        if data:
            st.session_state.user_id = user_id
            st.success("Utilizator găsit!")
        else:
            st.warning("Nu am găsit date pentru acest ID. Încărcați o factură PDF la nevoie.")
            st.session_state.user_id = user_id

    uploaded_file = st.file_uploader("Încarcă factura PDF", type="pdf")
    if uploaded_file and st.session_state.user_id:
        bill_data = parse_pdf_to_json(uploaded_file)
        existing_data = load_user_data(st.session_state.user_id)
        if "bills" not in existing_data:
            existing_data["bills"] = []
        existing_data["bills"].append(bill_data)
        file_path = os.path.join("data", "user_data", f"user_data_{st.session_state['user_id']}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(existing_data, file)
        st.success("Factura a fost încărcată și salvată cu succes!")

    if st.session_state.user_id:
        data = load_user_data(st.session_state.user_id)
        st.write(f"Phone Number: {st.session_state.user_id}")
        st.write("Facturi existente:")
        for bill in data.get("bills", []):
            st.write(bill)
    else:
        st.info("Introduceți un ID și/sau încărcați o factură PDF pentru a continua.")

    # Initialize conversation in the session state
    # "context_prompt_added" indicates whether we've added the specialized "bill info" context yet.
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Cu ce te pot ajuta?"}
        ]
    if "context_prompt_added" not in st.session_state:
        st.session_state.context_prompt_added = False

    st.write("---")
    st.subheader("Chat")

    for msg in st.session_state["messages"]:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Introduceți întrebarea aici:"):
        if not st.session_state.user_id:
            st.error("Trebuie să introduceți un număr de telefon valid sau să încărcați date.")
            return

        # If the context prompt hasn't been added yet, build & inject it once;
        # otherwise, just add the user's raw question.
        if not st.session_state.context_prompt_added:
            final_prompt = process_query(prompt, st.session_state["user_id"])
            if final_prompt is None:
                st.stop()
            st.session_state["messages"].append({"role": "user", "content": final_prompt})
            st.session_state.context_prompt_added = True
        else:
            st.session_state["messages"].append({"role": "user", "content": prompt})

        # Display the latest user message in the chat
        st.chat_message("user").write(st.session_state["messages"][-1]["content"])

        # Now call GPT-4 with the entire conversation
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state["messages"]
        )
        response_text = completion.choices[0].message.content.strip()

        st.session_state["messages"].append({"role": "assistant", "content": response_text})
        st.chat_message("assistant").write(response_text)

        if hasattr(completion, "usage"):
            st.write("Prompt tokens:", completion.usage.prompt_tokens)
            st.write("Completion tokens:", completion.usage.completion_tokens)
            st.write("Total tokens:", completion.usage.total_tokens)

if __name__ == "__main__":
    main()