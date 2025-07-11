class UserInfo:
    def __init__(self):
        self.user_data = {}
    
    def save_user_info(self, user_id, info):
        self.user_data[user_id] = info
    
    def get_user_info(self, user_id):
        return self.user_data.get(user_id, None)