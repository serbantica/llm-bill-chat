import os
import streamlit as st
import torch
import pdfplumber
import json
from src.chat.context import ChatContext
from src.chat.bill_comparison import compare_bills
from src.chat.user_info import UserInfo
from src.chat.conversation import Conversation
from src.chat.llm import generate_Qwen_response, initialize_Qwen_chat_model, initialize_chat_model, generate_response  # Import the functions from llm.py
from src.chat.llm import available_models  # Import the available models from llm.py

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0

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

def process_query(query, user_info, chat_context, model_name):
    bill_info = user_info.get_bills()
    related_keys = check_related_keys(query, st.session_state.user_id)
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

    # Check context size
    max_input_length = 350
    st.write(f"Context:\n{context}")
    st.write(f"Context size: {len(context)} characters")

    # If context is too big, skip
    if len(context) > max_input_length:
        st.warning("Context too big, the request will not be sent.")
        return "Context too large to process."

    # Generate the response with Qwen
    response = generate_response(context, model_name)
    return response

def main():
    st.title("Telecom Bill Chat Assistant")

    # Sidebar for model selection
    model_name = st.sidebar.radio("Selectează modelul 👇", available_models)
    initialize_session_state()
    initialize_chat_model(model_name=model_name)

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
        
        elif not user_id:
            pass

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

            # Add user message to the chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            # Generate response from the assistant
            with st.chat_message("assistant"):
                try:
                    response = process_query(prompt, user_info, chat_context, model_name)
                    st.write(response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                    st.session_state.question_count += 1
                except Exception as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.write("Assistant: Am cam obosit azi. Mai intreaba-ma si maine! 😴️")
        st.session_state.question_count = 0

if __name__ == "__main__":
    main()