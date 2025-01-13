import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

available_models = [
    "Qwen/Qwen1.5-7B-Chat",  # Example: This is our Qwen model
]

def initialize_chat_model(model_name):
    # Only load model if we haven't loaded it before, or if model_name changed
    if "chat_model" not in st.session_state or st.session_state.model_name != model_name:
        # Load the Qwen model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )

        # Pick device; if you have CUDA, this will be "cuda", else it defaults to "cpu"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)

        # Save in session state
        st.session_state.chat_tokenizer = tokenizer
        st.session_state.chat_model = model
        st.session_state.device = device
        st.session_state.model_name = model_name

def generate_response(
    user_input: str,
    model_name: str,
    temperature: float = 0.7,
    top_k: int = 50,
    top_p: float = 0.9,
    repetition_penalty: float = 1.2
) -> str:
    # Make sure model is initialized
    initialize_chat_model(model_name)

    tokenizer = st.session_state.chat_tokenizer
    model = st.session_state.chat_model
    device = st.session_state.device

    # Construct chat messages for Qwen
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ]

    # Use Qwen's chat template
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Tokenize and move to chosen device
    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    # Generate the output
    with torch.no_grad():
        generated_ids = model.generate(
            model_inputs.input_ids,
            max_new_tokens=512,  # Adjust as needed
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            do_sample=True
        )

    # Exclude the original input tokens from the output to get only newly generated text
    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    # Decode
    output_text = tokenizer.batch_decode(
        generated_ids, skip_special_tokens=True
    )[0]
    return output_text