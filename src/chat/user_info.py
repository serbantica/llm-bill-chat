import json
import os

class UserInfo:
    def __init__(self):
        self.user_data = {}

    def load_user_data(self, user_id):
        # Placeholder for loading user data logic
        # For example, load data from a database or file
        file_path = f"user_data_{user_id}.json"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                self.user_data = json.load(file)
        else:
            self.user_data = {"user_id": user_id, "bills": []}
            # Save the initial user data to a file into the user_data folder under data directory
            os.makedirs('data\\user_data', exist_ok=True)
            file_path = os.path.join('data\\user_data', f"user_data_{user_id}.json")
            with open(file_path, 'w') as file:
                json.dump(self.user_data, file)
        
        # Ensure 'bills' key is always initialized
        if "bills" not in self.user_data:
            self.user_data["bills"] = []

    def save_bill_data(self, user_id, bill_data):
        if "bills" not in self.user_data:
            self.user_data["bills"] = []
        self.user_data["bills"].append(bill_data)
        file_path = f"user_data_{user_id}.json"

        # Vrify the path exists '\llm-bill-chat-app\data' windows path directory
        os.makedirs('data/user_data', exist_ok=True)
        
        # Save the updated user data to a file into C:\Users\ZZ029K826\Documents\GitHub\llm-bill-chat-app\data directory
        file_path = os.path.join('data\\user_data', f"user_data_{user_id}.json")

        with open(file_path, 'w') as file:
            json.dump(self.user_data, file)

    def get_bills(self):
        return self.user_data.get("bills", [])