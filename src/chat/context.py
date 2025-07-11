class ChatContext:
    def __init__(self):
        self.messages = []
        self.user_info = {}

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get_context(self):
        return self.messages

    def set_user_info(self, user_info):
        self.user_info = user_info

    def get_user_info(self):
        return self.user_info

    def clear_context(self):
        self.messages = []