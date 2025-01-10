import streamlit as st
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
from src.chat.context import ChatContext
from src.chat.bill_comparison import compare_bills
from src.chat.user_info import UserInfo
from src.chat.conversation import Conversation

def initialize_chat_model():
    if 'chat_model' not in st.session_state:
        model_name = "facebook/blenderbot-400M-distill"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        st.session_state.chat_model = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=100
        )

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

def process_query(query, user_info, chat_context):
    # Combine bill information with query for context
    bill_info = user_info.get_bills()
    context = f"Bill information: {bill_info}\nQuery: {query}"
    
    # Generate response using transformer model
    response = st.session_state.chat_model(context)[0]['generated_text']
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
        user_id = st.text_input("Enter your user ID:")
        if user_id and user_id != st.session_state.user_id:
            user_info.load_user_data(user_id)
            st.session_state.user_id = user_id
            st.session_state.messages = []

    # Chat container
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Query input
    if prompt := st.chat_input("Ask about your bills..."):
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

if __name__ == "__main__":
    main()