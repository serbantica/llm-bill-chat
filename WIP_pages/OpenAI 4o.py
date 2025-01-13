#!/usr/bin/env -S poetry run python

import os
import json
import streamlit as st
from openai import OpenAI

# The OpenAI object picks up OPENAI_API_KEY from the environment variable
client = OpenAI()

# Example function to load user data
def load_user_data(user_id):
    file_path = os.path.join("data", "user_data", f"user_data_{user_id}.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as file:
        return json.load(file)

# Example function to check for related bill keys in the user’s question
def check_related_keys(question, user_id):
    user_data = load_user_data(user_id)
    bill_keys = set()
    for bill in user_data.get("bills", []):
        bill_keys.update(bill.keys())

    related_keys = [key for key in bill_keys if key.lower() in question.lower()]
    return related_keys

# Example function to generate context from bill info + user query
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
    max_input_length = 350
    st.write(f"Context:\n{context}")
    st.write(f"Context size: {len(context)} characters")

    if len(context) > max_input_length:
        st.warning("Context too big, the request will not be sent.")
        return "Context too large to process."

    return context

# For demo, we use a placeholder user_id, e.g. "12345"
USER_ID = "12345"

# Initialize conversation in session_state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

st.title("Bill Info - OpenAI ChatCompletion (GPT-4) și Streamlit")

# Display existing conversation
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat input for the user
if prompt := st.chat_input("Introduceți întrebarea aici:"):
    # Build context from the question + bill info
    final_prompt = process_query(prompt, USER_ID)

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