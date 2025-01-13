import os
import streamlit as st
import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import pdfplumber
import json
from src.chat.context import ChatContext
from src.chat.bill_comparison import compare_bills
from src.chat.user_info import UserInfo
from src.chat.conversation import Conversation
from src.chat.llm import generate_response, initialize_chat_model  # Import the function from llm.py


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0

import pdfplumber

def parse_pdf_to_json(pdf_path):
    # Initialize the dictionary to store the extracted costs
    costuri = {}

    with pdfplumber.open(pdf_path) as pdf:
        # Iterate through each page of the PDF
        for page in pdf.pages:
            # Extract the text from the page
            text = page.extract_text()
            
            if text:  # Check if there is any text on the page
                # Split the text into lines
                lines = text.split('\n')
                
                # Process each line and look for specific categories
                for line in lines:
                    # Check for 'Data emiterii facturii'
                    if 'Data emiterii facturii' in line:
                        date = line.split()[-1]
                        costuri['Data emiterii facturii'] = date

                    # Check for 'Valoare facturată fără TVA'
                    if 'Valoare facturată fără TVA' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Valoare facturata'] = value
                    
                    # Check for 'Total bază de impozitare TVA'
                    elif 'Total bază de impozitare TVA' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Total baza de impozitare TVA'] = value
                    
                    # Check for 'TVA'
                    elif 'TVA' in line and '%' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['TVA'] = value
                    
                    # Check for 'Dobânzi penalizatoare'
                    elif 'Dobânzi penalizatoare' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Dobanzi penalizatoare'] = value
                    
                    # Check for 'TOTAL DE PLATĂ FACTURĂ CURENTĂ'
                    elif 'TOTAL DE PLATĂ FACTURĂ CURENTĂ' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Total de plata factura curenta'] = value
                    
                    # Check for 'Sold Cont Contract'
                    elif 'Sold Cont Contract' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Sold Cont Contract'] = value
                    
                    # Check for 'Compensatii'
                    elif 'Compensatii' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Compensatii'] = value
                    
                    # Check for 'TOTAL DE PLATĂ CONT CONTRACT'
                    elif 'TOTAL DE PLATĂ CONT CONTRACT' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Total de plata cont contract'] = value
                    
                    # Check for 'Consum Energie Activă'
                    elif 'Consum Energie Activă' in line:
                        value = float(line.split()[-2].replace(',', '.'))  # Extract and convert to float
                        costuri['Consum Energie Activa'] = value

    return costuri

def check_related_keys(question, user_id):
    # Load user data
    file_path = os.path.join('data', 'user_data', f"user_data_{user_id}.json")
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r') as file:
        user_data = json.load(file)

    # Extract bill keys
    bill_keys = set()
    for bill in user_data.get("bills", []):
        bill_keys.update(bill.keys())

    # Check if question is related to any bill keys
    related_keys = [key for key in bill_keys if key.lower() in question.lower()]
    return related_keys

def process_query(query, user_info, chat_context):
    # Combine bill information with query for context
    bill_info = user_info.get_bills()
    related_keys = check_related_keys(query, st.session_state.user_id)
    
    if related_keys:
        related_keys = ", ".join(related_keys)
    else:   
        related_keys = "N/A"
    if related_keys != "N/A":
        context = f"Informatii factura: {bill_info}\nQuery: {query}\nRaspunde Campuri: {related_keys}"
    else:
        context = f"Informatii factura: {bill_info}\nQuery: {query}"
    
    # Truncate context to fit within model's maximum input length
    max_input_length = 300  # Adjust based on model's max_length
    if len(context) > max_input_length:
        context = context[:max_input_length]
    
    # Generate response using transformer model from llm.py
    response = st.session_state.generate_response(context)

    return response

def main():
    st.title("Telecom Bill Chat Assistant")
    initialize_session_state()
    initialize_chat_model()

    # Initialize components
    user_info = UserInfo()
    chat_context = ChatContext()
    conversation = Conversation(user_info, chat_context)

    # Sidebar for user authentication
    with st.sidebar:
        user_id = st.text_input("Scrie-mi te rog numarul de telefon:")
        if user_id and user_id != st.session_state.user_id:
            try:
                user_info.load_user_data(user_id)
                st.session_state.user_id = user_id
                st.session_state.messages = []
                st.session_state.question_count = 0
                st.success("User valid   ✅️")
            except FileNotFoundError:
                st.error("User ID not found. Please enter a valid user ID.")
        


    # PDF Bill Upload
    uploaded_file = st.file_uploader("Incarca factura PDF", type="pdf")
    if uploaded_file:
        bill_data = parse_pdf_to_json(uploaded_file)
        user_info.save_bill_data(st.session_state.user_id, bill_data)
        st.success("Incarcata cu succes!")

    # verify the user data: id and bill info
    if st.session_state.user_id:
        st.write(f"phoneNumber: {st.session_state.user_id}")
        bills = user_info.get_bills()
        st.write("Informatii factura:")
        for bill in bills:
            st.write(bill)
    else:
        st.warning("Nu am gasit acest numar de telefon in sistem. Te rog sa introduci un numar de telefon valid.")


    # Chat container
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Query input
    if st.session_state.question_count < 3:
        if prompt := st.chat_input("Cu ce informatii te pot ajuta? Orice e legat de factura ta de telefonie mobila"):
            if not st.session_state.user_id:
                st.error("Please enter a user ID first")
                return

            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            # Generate response
            with st.chat_message("assistant"):
                response = process_query(prompt, user_info, chat_context)
                st.write(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                st.session_state.question_count += 1
    else:
        st.write("Assistant: Am cam obosit azi. Mai intreaba-ma si maine! 😴️")

if __name__ == "__main__":
    main()