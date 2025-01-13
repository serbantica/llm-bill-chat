# Copyright (c) Alibaba Cloud.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import streamlit as st
import torch
from argparse import ArgumentParser
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

DEFAULT_CKPT_PATH = "Qwen/Qwen2.5-7B-Instruct"

def _get_args():
    parser = ArgumentParser(description="Qwen2.5-Instruct web chat demo.")
    parser.add_argument(
        "-c",
        "--checkpoint-path",
        type=str,
        default=DEFAULT_CKPT_PATH,
        help="Checkpoint name or path, default to %(default)r",
    )
    parser.add_argument("--cpu-only", action="store_true", help="Run demo with CPU only")
    parser.add_argument(
        "--share",
        action="store_true",
        default=False,
        help="Create a publicly shareable link for the interface.",
    )
    return parser.parse_args()

def load_model_and_tokenizer(ckpt_path, cpu_only):
    device = "cpu" if cpu_only else ("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(ckpt_path)
    model = AutoModelForCausalLM.from_pretrained(ckpt_path, torch_dtype="auto", device_map="auto")
    model.to(device)
    model.eval()
    return model, tokenizer, device

def generate_response(model, tokenizer, device, prompt):
    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
        decode_kwargs={"skip_special_tokens": True},
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        generated = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
            repetition_penalty=1.2,
            do_sample=True
        )
    output = tokenizer.decode(generated[0], skip_special_tokens=True)
    return output

def run_streamlit_app():
    args = _get_args()
    model, tokenizer, device = load_model_and_tokenizer(args.checkpoint_path, args.cpu_only)

    st.title("Qwen2.5-Instruct Streamlit Demo")

    # Text input for user query
    user_input = st.text_area("Enter your prompt here:", height=100)

    # Button to run inference
    if st.button("Run Inference"):
        with st.spinner("Generating response..."):
            response = generate_response(
                model, tokenizer, device, user_input.strip()
            )
        st.success("Response generated!")
        st.write(response)

def main():
    run_streamlit_app()

if __name__ == "__main__":
    main()