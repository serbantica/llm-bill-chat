from streamlit import st
from chat.context import ChatContext
from chat.bill_comparison import compare_bills
from chat.user_info import UserInfo
from chat.conversation import Conversation

def main():
    st.title("Telecom Bill Chat Assistant")
    
    user_info = UserInfo()
    chat_context = ChatContext()
    conversation = Conversation(chat_context)

    user_id = st.text_input("Enter your user ID:")
    if user_id:
        user_info.load_user_data(user_id)
        st.session_state['user_id'] = user_id

    user_query = st.text_input("Ask about your bills:")
    if st.button("Submit"):
        if user_query:
            response = conversation.handle_query(user_query, user_info.get_bills())
            st.write(response)
            chat_context.add_message("User", user_query)
            chat_context.add_message("Assistant", response)

if __name__ == "__main__":
    main()