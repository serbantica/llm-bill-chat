from src.chat.context import ChatContext

class Conversation:
    def __init__(self, user_info, chat_context: ChatContext):
        self.user_info = user_info
        self.chat_context = chat_context

    def handle_query(self, query):
        self.chat_context.add_message("User", query)
        response = self.generate_response(query)
        self.chat_context.add_message("Assistant", response)
        return response

    def generate_response(self, query):
        if "factura" in query:
            return self.get_bill_info()
        return "Imi pare rau, te pot ajuta doar cu informatii despre factura ta."

    def get_bill_info(self):
        if "difer" in self.chat_context.context:
            return self.compare_bills()
        bills = self.user_info.get_bills()
        if len(bills) < 2:
            return "I need at least 2 bills to compare."
        comparison_result = self.compare_bills(bills[-4:])  # Assuming you want the last 4 bills
        return comparison_result

    def compare_bills(self, last_bills):
        # Placeholder for bill comparison logic
        return f"Comparing the last four bills: {last_bills}"