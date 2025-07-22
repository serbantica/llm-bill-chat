#!/usr/bin/env -S poetry run python

import os
import json
import streamlit as st
import glob
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("The OPENAI_API_KEY environment variable is not set.")

client = OpenAI()

def load_customer_database():
    """Load the mock customer database to validate phone numbers."""
    try:
        with open("data/customer_database.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"customers": {}}

def validate_customer(phone_number):
    """
    Validate if a phone number exists in the customer database.
    Accepts phone numbers with or without leading "0".
    Returns customer info if valid, None if invalid.
    """
    db = load_customer_database()
    customers = db.get("customers", {})
    
    # Remove any leading "0" to normalize the format
    normalized_number = phone_number.lstrip("0")
    
    # Try both the original number and normalized number
    return customers.get(phone_number) or customers.get(normalized_number)

def reset_chat_session():
    """Reset the entire chat session for a new customer."""
    # Clear all session state related to user and conversation
    keys_to_clear = ['user_id', 'customer_info', 'messages', 'context_prompt_added', 'customer_validated']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clean up user data files (optional - for demo purposes)
    user_data_pattern = os.path.join("data", "user_data", "user_data_*.json")
    user_data_files = glob.glob(user_data_pattern)
    for file_path in user_data_files:
        try:
            os.remove(file_path)
        except OSError:
            pass

def load_user_data(user_id):
    file_path = os.path.join("data", "user_data", f"user_data_{user_id}.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as file:
        return json.load(file)

def save_user_data(user_id, data):
    file_path = os.path.join("data", "user_data", f"user_data_{user_id}.json")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as file:
        json.dump(data, file)

def check_duplicate_bill(existing_bills, new_bill):
    """
    Check if a bill is a duplicate based on billNo and billDate.
    Returns True if duplicate found, False otherwise.
    """
    new_bill_no = new_bill.get("billNo")
    new_bill_date = new_bill.get("billDate")
    
    for existing_bill in existing_bills:
        if (existing_bill.get("billNo") == new_bill_no and 
            existing_bill.get("billDate") == new_bill_date):
            return True
    
    return False

def load_available_bills(customer_info):
    """Load available bills for a validated customer from the file system."""
    bills = []
    for bill_id in customer_info.get("availableBills", []):
        bill_file = f"data/bill_{bill_id}.json"
        try:
            with open(bill_file, "r") as f:
                bill_data = json.load(f)
                parsed_bill = parseBill(bill_data)
                parsed_bill["bill_id"] = bill_id  # Add bill ID for reference
                bills.append(parsed_bill)
        except FileNotFoundError:
            st.warning(f"Bill file {bill_file} not found for customer")
    return bills

def parseBill(data):
    billDate = data.get("billDate")
    billNo = data.get("billNo")
    amountDue = data.get("amountDue")
    extraCharge = data.get("extraCharge")
    taxItems = data.get("taxItem", [])
    subscribers = data.get("subscribers", [])

    totalBillCosts = [{"categorie": t.get("cat"), "amount": t.get("amt")} for t in taxItems]
    subscriberCosts = []
    for sub in subscribers:
        logicalResource = sub.get("logicalResource")
        billSummaryItems = sub.get("billSummaryItem", [])
        subscriberCosts.append({
            "logicalResource": logicalResource,
            "billSummaryItems": [
                {"categorie": bsi.get("cat"), "amount": bsi.get("amt"), "name": bsi.get("name")}
                for bsi in billSummaryItems
            ],
        })

    return {
        "billDate": billDate,
        "billNo": billNo,
        "amountDue": amountDue,
        "extraCharge": extraCharge,
        "totalBillCosts": totalBillCosts,
        "subscriberCosts": subscriberCosts
    }

def check_related_keys(question, user_id):
    user_data = load_user_data(user_id)
    bill_keys = set()
    for bill in user_data.get("bills", []):
        bill_keys.update(bill.keys())
    return [key for key in bill_keys if key.lower() in question.lower()]

def detect_user_intent(query):
    """
    Detect the user's intent from their query to customize LLM context.
    Returns intent type and confidence level.
    """
    query_lower = query.lower()
    
    # Define intent patterns
    intents = {
        "bill_comparison": [
            r"compar[ei]", r"difference", r"vs", r"versus", r"between", 
            r"last.*bill", r"previous.*bill", r"month.*month", r"trend"
        ],
        "cost_breakdown": [
            r"breakdown", r"detail", r"explain.*cost", r"what.*charge", 
            r"why.*pay", r"itemize", r"service.*cost"
        ],
        "payment_inquiry": [
            r"pay", r"due", r"amount", r"total", r"balance", r"owe", 
            r"payment", r"outstanding"
        ],
        "service_analysis": [
            r"service", r"subscription", r"plan", r"package", r"feature", 
            r"addon", r"extra", r"usage"
        ],
        "discount_inquiry": [
            r"discount", r"promotion", r"reduction", r"promo", r"offer", 
            r"save", r"cheaper"
        ],
        "device_charges": [
            r"device", r"phone", r"smartphone", r"terminal", r"installment", 
            r"rate.*terminal", r"equipment"
        ],
        "general_question": [
            r"help", r"explain", r"understand", r"what.*is", r"how.*work"
        ]
    }
    
    detected_intents = {}
    
    for intent, patterns in intents.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, query_lower):
                score += 1
        if score > 0:
            detected_intents[intent] = score
    
    # Return the intent with highest score, or general_question if none detected
    if detected_intents:
        primary_intent = max(detected_intents.keys(), key=lambda k: detected_intents[k])
        confidence = detected_intents[primary_intent] / len(intents[primary_intent])
        return primary_intent, confidence
    else:
        return "general_question", 0.5

def build_intent_context(intent, query, bill_info, related_keys_str):
    """
    Build specialized context prompts based on detected intent.
    """
    base_instruction = "You are a helpful telecom billing assistant. Always respond in English, even when the billing data contains Romanian text."
    
    intent_instructions = {
        "bill_comparison": (
            f"{base_instruction} The user wants to compare bills. "
            f"Focus on identifying trends, differences in amounts, new charges, or changes in services. "
            f"Compare multiple bills chronologically and highlight significant changes."
        ),
        "cost_breakdown": (
            f"{base_instruction} The user wants a detailed breakdown of costs. "
            f"Explain each charge category, what services they represent, and provide clear itemization. "
            f"Translate Romanian billing terms to English explanations."
        ),
        "payment_inquiry": (
            f"{base_instruction} The user is asking about payment amounts. "
            f"Focus on total amounts due, payment dates, outstanding balances, and payment history."
        ),
        "service_analysis": (
            f"{base_instruction} The user wants to understand their services. "
            f"Explain subscriptions, plans, features, and service usage. Focus on what services they have and how they're being charged."
        ),
        "discount_inquiry": (
            f"{base_instruction} The user is asking about discounts and promotions. "
            f"Identify all reductions, promotional offers, and savings. Explain what each discount applies to."
        ),
        "device_charges": (
            f"{base_instruction} The user is asking about device-related charges. "
            f"Focus on installment payments, device costs, terminal charges, and equipment fees."
        ),
        "general_question": (
            f"{base_instruction} Provide a comprehensive overview of the billing information to help answer the user's question."
        )
    }
    
    instruction = intent_instructions.get(intent, intent_instructions["general_question"])
    
    if related_keys_str != "N/A":
        context = (
            f"{instruction} "
            f"Read the billing cost information in RON from this JSON: {bill_info} "
            f"and answer the question: '{query}' but only with information related to: {related_keys_str}. "
            f"Please respond in English."
        )
    else:
        context = (
            f"{instruction} "
            f"Read the billing cost information in RON from this JSON: {bill_info} "
            f"and answer the question: '{query}' but only with information related to the bill. "
            f"Please respond in English."
        )
    
    return context

def process_query(query, user_id, model_name):
    user_data = load_user_data(user_id)
    bill_info = user_data.get("bills", [])
    related_keys = check_related_keys(query, user_id)
    related_keys_str = ", ".join(related_keys) if related_keys else "N/A"

    # ENHANCED INTENT DETECTION
    intent, confidence = detect_user_intent(query)
    st.write(f"Detected Intent: {intent} (confidence: {confidence:.2f})")
    
    # Build context based on detected intent
    context = build_intent_context(intent, query, bill_info, related_keys_str)

    max_input_length = 5550
    st.write(f"Context:\n{context}")
    st.write(f"Context size: {len(context)} characters")

    if len(context) > max_input_length:
        st.warning("Too many characters in context, the request will not be sent.")
        return None

    # Update this part to run the chosen model
    if model_name == "gpt-4o-mini":
        # Code to run model 4o mini
        st.write("Running model GPT-4o-mini")
    elif model_name == "gpt-4o":
        # Code to run model 4o
        st.write("Running model GPT-4o")

    return context

def process_quick_action(question, user_id, model_name="gpt-4"):
    """Process a quick action question and get AI response."""
    # Add the question to the conversation
    st.session_state["messages"].append({"role": "user", "content": question})
    
    # If context hasn't been added yet, process the query to add context
    if not st.session_state.context_prompt_added:
        final_prompt = process_query(question, user_id, model_name)
        if final_prompt is None:
            return
        # Replace the last message with the context-enhanced version
        st.session_state["messages"][-1] = {"role": "user", "content": final_prompt}
        st.session_state.context_prompt_added = True
    
    # Call OpenAI API
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=st.session_state["messages"]
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Add the response to the conversation
        st.session_state["messages"].append({"role": "assistant", "content": response_text})
        
        # Show model and token usage in sidebar
        if hasattr(completion, "usage"):
            st.sidebar.markdown("---")
            st.sidebar.subheader("🤖 Current Model")
            st.sidebar.write(f"**Model:** {model_name}")
            st.sidebar.subheader("🔢 Token Usage")
            st.sidebar.write(f"Prompt: {completion.usage.prompt_tokens}")
            st.sidebar.write(f"Completion: {completion.usage.completion_tokens}")
            st.sidebar.write(f"Total: {completion.usage.total_tokens}")
            
    except Exception as e:
        st.error(f"❌ Error calling OpenAI API: {str(e)}")

def main():
    st.title("🏢 Telecom Bill Chat with LLM Agent")
    st.markdown("---")

    # Initialize session state variables
    if "customer_validated" not in st.session_state:
        st.session_state.customer_validated = False
    if "customer_info" not in st.session_state:
        st.session_state.customer_info = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    # Sidebar configuration
    st.sidebar.title("⚙️ Settings")
    model_name = st.sidebar.selectbox("Choose OpenAI Model", ["gpt-4o-mini", "gpt-4o"])
    
    # Reset session button
    if st.sidebar.button("🔄 Reset Session (New Customer)", type="secondary"):
        reset_chat_session()
        st.session_state.customer_validated = False
        st.session_state.customer_info = None
        st.session_state.user_id = None
        st.sidebar.success("Session reset! Please validate a new customer.")
        st.rerun()

    # Step 1: Customer Validation
    if not st.session_state.customer_validated:
        st.header("📞 Customer Validation")
        st.info("Enter your phone number to access your billing information.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            phone_number = st.text_input("Phone Number:", placeholder="e.g., 727723137 or 0727723137", key="phone_input")
        with col2:
            st.write("")
            st.write("")  # Add spacing
            validate_btn = st.button("Validate", type="primary")

        if validate_btn and phone_number:
            customer_info = validate_customer(phone_number)
            if customer_info:
                st.session_state.customer_validated = True
                st.session_state.customer_info = customer_info
                # Store the normalized number (without leading 0)
                normalized_number = phone_number.lstrip("0")
                st.session_state.user_id = normalized_number
                st.success(f"✅ Welcome {customer_info['name']}! Customer validation successful.")
                st.info(f"Plan: {customer_info['plan']} | Status: {customer_info['status']}")
                st.rerun()
            else:
                st.error("❌ Invalid phone number. Customer not found in our database.")
                st.info("💡 Try one of these demo numbers: 727723137, 0727723137, 722339918, or 0724077190")
        
        elif validate_btn and not phone_number:
            st.error("Please enter a phone number.")
        
        # Stop here until customer is validated
        return

    # Main Application Flow - Bill Management and Chat
    customer_name = st.session_state.customer_info.get('name', 'Customer') if st.session_state.customer_info else 'Customer'
    st.header(f"👋 Welcome, {customer_name}!")
    
    # Display current session info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Current Session")
    st.sidebar.write(f"**Customer:** {customer_name}")
    st.sidebar.write(f"**Phone:** {st.session_state.user_id or 'N/A'}")
    if st.session_state.customer_info:
        st.sidebar.write(f"**Plan:** {st.session_state.customer_info.get('plan', 'N/A')}")

    # Bill Upload Section
    st.subheader("📤 Bill Management")
    
    # Show current bills
    current_data = load_user_data(st.session_state.user_id)
    current_bills = current_data.get("bills", [])
    
    if current_bills:
        st.success(f"✅ You have {len(current_bills)} bill(s) loaded and ready for analysis.")
        with st.expander(f"👁️ View Loaded Bills ({len(current_bills)} bills)", expanded=False):
            for i, bill in enumerate(current_bills):
                st.write(f"**Bill {i+1}:** #{bill.get('billNo', 'N/A')} - {bill.get('billDate', 'N/A')} - {bill.get('amountDue', 'N/A')} RON")
        
        # Option to clear all bills
        if st.button("🗑️ Clear All Bills"):
            empty_data = {"bills": []}
            save_user_data(st.session_state.user_id, empty_data)
            # Clear conversation context when bills are cleared
            if "context_prompt_added" in st.session_state:
                del st.session_state["context_prompt_added"]
            st.success("✅ All bills cleared!")
            st.rerun()
    else:
        st.info("📄 No bills uploaded yet. Upload your first bill to get started!")
    
    # Bill upload interface
    st.write("**Upload Additional Bills:**")
    uploaded_file = st.file_uploader("Upload JSON bill", type="json", key="bill_uploader")
    if uploaded_file:
        bill_data = json.load(uploaded_file)
        parsed_bill = parseBill(bill_data)
        existing_data = load_user_data(st.session_state.user_id)
        if "bills" not in existing_data:
            existing_data["bills"] = []
        
        # Debug: Show what we're uploading
        st.write(f"🔍 **Uploading:** Bill #{parsed_bill.get('billNo')} dated {parsed_bill.get('billDate')}")
        
        # Check for duplicate bills
        if check_duplicate_bill(existing_data["bills"], parsed_bill):
            st.error(f"❌ Duplicate bill detected! Bill #{parsed_bill['billNo']} dated {parsed_bill['billDate']} already exists.")
            
            # Offer to replace existing bills
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Replace Duplicate"):
                    # Remove the duplicate and add the new one
                    existing_data["bills"] = [bill for bill in existing_data["bills"] 
                                            if not (bill.get("billNo") == parsed_bill.get("billNo") and 
                                                   bill.get("billDate") == parsed_bill.get("billDate"))]
                    existing_data["bills"].append(parsed_bill)
                    save_user_data(st.session_state.user_id, existing_data)
                    # Reset context when bills change
                    if "context_prompt_added" in st.session_state:
                        del st.session_state["context_prompt_added"]
                    st.success("✅ Bill replaced successfully!")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel Upload"):
                    st.info("Upload cancelled.")
                    st.rerun()
        else:
            existing_data["bills"].append(parsed_bill)
            save_user_data(st.session_state.user_id, existing_data)
            # Reset context when new bills are added
            if "context_prompt_added" in st.session_state:
                del st.session_state["context_prompt_added"]
            st.success("✅ Bill uploaded successfully!")
            st.info(f"📊 You now have {len(existing_data['bills'])} bill(s) ready for analysis.")
            st.rerun()

    # Only show chat if there are bills loaded
    if not current_bills:
        st.info("💡 Upload at least one bill to start chatting with the AI assistant.")
        return

    # Initialize conversation in the session state
    # "context_prompt_added" indicates whether we've added the specialized "bill info" context yet.
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": "You are a helpful telecom billing assistant. Always respond in English, even when the billing data contains Romanian text. Explain telecom charges, compare bills, and help users understand their billing information."},
            {"role": "assistant", "content": "How can I help you with your telecom bill?"}
        ]
    if "context_prompt_added" not in st.session_state:
        st.session_state.context_prompt_added = False

    st.markdown("---")
    st.subheader("💬 Chat")

    # Display conversation
    for msg in st.session_state["messages"]:
        if msg["role"] != "system":  # Don't show system messages
            st.chat_message(msg["role"]).write(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask me about your bills..."):
        if not st.session_state.user_id:
            st.error("❌ You must enter a valid phone number.")
            return

        # If the context prompt hasn't been added yet, build & inject it once;
        # otherwise, just add the user's raw question.
        if not st.session_state.context_prompt_added:
            final_prompt = process_query(prompt, st.session_state["user_id"], model_name)
            if final_prompt is None:
                st.stop()
            st.session_state["messages"].append({"role": "user", "content": final_prompt})
            st.session_state.context_prompt_added = True
        else:
            st.session_state["messages"].append({"role": "user", "content": prompt})

        # Display the latest user message in the chat
        st.chat_message("user").write(prompt)

        # Call OpenAI API
        with st.spinner("🤖 Thinking..."):
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state["messages"]
                )
                response_text = completion.choices[0].message.content.strip()

                st.session_state["messages"].append({"role": "assistant", "content": response_text})
                st.chat_message("assistant").write(response_text)

                # Show model and token usage in sidebar
                if hasattr(completion, "usage"):
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("🤖 Current Model")
                    st.sidebar.write(f"**Model:** {model_name}")
                    st.sidebar.subheader("🔢 Token Usage")
                    st.sidebar.write(f"Prompt: {completion.usage.prompt_tokens}")
                    st.sidebar.write(f"Completion: {completion.usage.completion_tokens}")
                    st.sidebar.write(f"Total: {completion.usage.total_tokens}")

            except Exception as e:
                st.error(f"❌ Error calling OpenAI API: {str(e)}")

    # Quick action buttons for common queries
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    st.info("💡 Click these buttons to automatically ask common questions about your bills:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💰 Show Total Amount", use_container_width=True):
            # Process the question through LLM
            question = "What is the total amount due on my latest bill?"
            if not st.session_state.context_prompt_added:
                final_prompt = process_query(question, st.session_state["user_id"], model_name)
                if final_prompt:
                    st.session_state["messages"].append({"role": "user", "content": final_prompt})
                    st.session_state.context_prompt_added = True
            else:
                st.session_state["messages"].append({"role": "user", "content": question})
            
            # Get AI response
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state["messages"]
                )
                response_text = completion.choices[0].message.content.strip()
                st.session_state["messages"].append({"role": "assistant", "content": response_text})
                
                # Show model and token usage in sidebar
                if hasattr(completion, "usage"):
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("🤖 Current Model")
                    st.sidebar.write(f"**Model:** {model_name}")
                    st.sidebar.subheader("🔢 Token Usage")
                    st.sidebar.write(f"Prompt: {completion.usage.prompt_tokens}")
                    st.sidebar.write(f"Completion: {completion.usage.completion_tokens}")
                    st.sidebar.write(f"Total: {completion.usage.total_tokens}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("📊 Compare Bills", use_container_width=True):
            question = "Compare my bills and show me the differences between them."
            if not st.session_state.context_prompt_added:
                final_prompt = process_query(question, st.session_state["user_id"], model_name)
                if final_prompt:
                    st.session_state["messages"].append({"role": "user", "content": final_prompt})
                    st.session_state.context_prompt_added = True
            else:
                st.session_state["messages"].append({"role": "user", "content": question})
            
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state["messages"]
                )
                response_text = completion.choices[0].message.content.strip()
                st.session_state["messages"].append({"role": "assistant", "content": response_text})
                
                # Show model and token usage in sidebar
                if hasattr(completion, "usage"):
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("🤖 Current Model")
                    st.sidebar.write(f"**Model:** {model_name}")
                    st.sidebar.subheader("🔢 Token Usage")
                    st.sidebar.write(f"Prompt: {completion.usage.prompt_tokens}")
                    st.sidebar.write(f"Completion: {completion.usage.completion_tokens}")
                    st.sidebar.write(f"Total: {completion.usage.total_tokens}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col3:
        if st.button("🔍 Cost Breakdown", use_container_width=True):
            question = "Give me a detailed breakdown of all charges on my bill."
            if not st.session_state.context_prompt_added:
                final_prompt = process_query(question, st.session_state["user_id"], model_name)
                if final_prompt:
                    st.session_state["messages"].append({"role": "user", "content": final_prompt})
                    st.session_state.context_prompt_added = True
            else:
                st.session_state["messages"].append({"role": "user", "content": question})
            
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state["messages"]
                )
                response_text = completion.choices[0].message.content.strip()
                st.session_state["messages"].append({"role": "assistant", "content": response_text})
                
                # Show model and token usage in sidebar
                if hasattr(completion, "usage"):
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("🤖 Current Model")
                    st.sidebar.write(f"**Model:** {model_name}")
                    st.sidebar.subheader("🔢 Token Usage")
                    st.sidebar.write(f"Prompt: {completion.usage.prompt_tokens}")
                    st.sidebar.write(f"Completion: {completion.usage.completion_tokens}")
                    st.sidebar.write(f"Total: {completion.usage.total_tokens}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Additional quick actions
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("📱 Device Charges", use_container_width=True):
            question = "Show me all device-related charges and installments on my bills."
            if not st.session_state.context_prompt_added:
                final_prompt = process_query(question, st.session_state["user_id"], model_name)
                if final_prompt:
                    st.session_state["messages"].append({"role": "user", "content": final_prompt})
                    st.session_state.context_prompt_added = True
            else:
                st.session_state["messages"].append({"role": "user", "content": question})
            
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state["messages"]
                )
                response_text = completion.choices[0].message.content.strip()
                st.session_state["messages"].append({"role": "assistant", "content": response_text})
                
                # Show model and token usage in sidebar
                if hasattr(completion, "usage"):
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("🤖 Current Model")
                    st.sidebar.write(f"**Model:** {model_name}")
                    st.sidebar.subheader("🔢 Token Usage")
                    st.sidebar.write(f"Prompt: {completion.usage.prompt_tokens}")
                    st.sidebar.write(f"Completion: {completion.usage.completion_tokens}")
                    st.sidebar.write(f"Total: {completion.usage.total_tokens}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col5:
        if st.button("🎯 Discounts & Promotions", use_container_width=True):
            question = "What discounts and promotions are applied to my bills?"
            if not st.session_state.context_prompt_added:
                final_prompt = process_query(question, st.session_state["user_id"], model_name)
                if final_prompt:
                    st.session_state["messages"].append({"role": "user", "content": final_prompt})
                    st.session_state.context_prompt_added = True
            else:
                st.session_state["messages"].append({"role": "user", "content": question})
            
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state["messages"]
                )
                response_text = completion.choices[0].message.content.strip()
                st.session_state["messages"].append({"role": "assistant", "content": response_text})
                
                # Show model and token usage in sidebar
                if hasattr(completion, "usage"):
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("🤖 Current Model")
                    st.sidebar.write(f"**Model:** {model_name}")
                    st.sidebar.subheader("🔢 Token Usage")
                    st.sidebar.write(f"Prompt: {completion.usage.prompt_tokens}")
                    st.sidebar.write(f"Completion: {completion.usage.completion_tokens}")
                    st.sidebar.write(f"Total: {completion.usage.total_tokens}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col6:
        if st.button("📈 Usage Analysis", use_container_width=True):
            question = "Analyze my service usage and explain what I'm paying for."
            if not st.session_state.context_prompt_added:
                final_prompt = process_query(question, st.session_state["user_id"], model_name)
                if final_prompt:
                    st.session_state["messages"].append({"role": "user", "content": final_prompt})
                    st.session_state.context_prompt_added = True
            else:
                st.session_state["messages"].append({"role": "user", "content": question})
            
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state["messages"]
                )
                response_text = completion.choices[0].message.content.strip()
                st.session_state["messages"].append({"role": "assistant", "content": response_text})
                
                # Show model and token usage in sidebar
                if hasattr(completion, "usage"):
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("🤖 Current Model")
                    st.sidebar.write(f"**Model:** {model_name}")
                    st.sidebar.subheader("🔢 Token Usage")
                    st.sidebar.write(f"Prompt: {completion.usage.prompt_tokens}")
                    st.sidebar.write(f"Completion: {completion.usage.completion_tokens}")
                    st.sidebar.write(f"Total: {completion.usage.total_tokens}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()