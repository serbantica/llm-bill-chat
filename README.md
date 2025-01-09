# LLM Bill Chat App

This project is a proof of concept for a chat application utilizing a Large Language Model (LLM) to assist users with their telecom billing inquiries. The application is built using Python and Streamlit, providing an interactive web interface for users to engage with.

## Features

- Maintain chat conversation context
- Allow users to query their billing information
- Compare the last four bills and provide insights
- Respond exclusively with the user's own billing information
- Save user information and conversation history

## Project Structure

```
llm-bill-chat-app
├── src
│   ├── app.py                # Main entry point for the Streamlit app
│   ├── chat
│   │   ├── __init__.py       # Package initialization for chat module
│   │   ├── context.py         # Manages conversation context
│   │   ├── bill_comparison.py  # Compares user bills
│   │   ├── user_info.py       # Handles user-specific information
│   │   └── conversation.py     # Manages conversation flow
│   └── utils
│       └── __init__.py       # Package initialization for utils module
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/llm-chat-app.git
   cd llm-chat-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
streamlit run src/app.py
```

Open your web browser and navigate to `http://localhost:8501` to interact with the chat application.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.