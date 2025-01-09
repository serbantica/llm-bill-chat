from chat.context import ChatContext

class Conversation:
    def __init__(self, user_info, chat_context: ChatContext):
        self.user_info = user_info
        self.chat_context = chat_context

    def handle_query(self, query):
        self.chat_context.add_message(query)
        response = self.generate_response(query)
        self.chat_context.add_message(response)
        return response

    def generate_response(self, query):
        if "bill" in query:
            return self.get_bill_info()
        return "I'm sorry, I can only assist with bill-related queries."

    def get_bill_info(self):
        bills = self.user_info.get_bills()
        if len(bills) < 4:
            return "I need at least 4 bills to compare."
        comparison_result = self.compare_bills(bills[-4:])
        return comparison_result

    def compare_bills(self, last_four_bills):
        # Placeholder for bill comparison logic
        return f"Comparing the last four bills: {last_four_bills}"