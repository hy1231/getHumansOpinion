"""数据存储模块"""
import json
import os
from datetime import datetime


class DataStore:
    """数据存储类"""
    
    def __init__(self, personality_id: str):
        self.personality_id = personality_id
        self.sent_ids = set()
    
    def load_sent_items(self):
        """加载已推送的记录ID"""
        file_path = f"data/sent_{self.personality_id}.json"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.sent_ids = set(data.get("sent_ids", []))
        except FileNotFoundError:
            self.sent_ids = set()
    
    def save_sent_items(self):
        """保存已推送的记录ID"""
        os.makedirs("data", exist_ok=True)
        file_path = f"data/sent_{self.personality_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({
                "sent_ids": list(self.sent_ids),
                "updated_at": datetime.now().isoformat()
            }, f)
    
    def is_sent(self, item_id):
        """检查记录是否已推送"""
        return item_id in self.sent_ids
    
    def mark_sent(self, item_id):
        """标记记录为已推送"""
        self.sent_ids.add(item_id)