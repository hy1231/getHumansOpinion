"""配置管理模块"""
import os
from dotenv import load_dotenv


class Config:
    """配置管理类"""
    
    def __init__(self):
        load_dotenv()
        self.proxy = os.getenv("PROXY")
        self.auth_token = os.getenv("TWITTER_AUTH_TOKEN")
        self.ct0 = os.getenv("TWITTER_CT0")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.wecom_webhook_url = os.getenv("WECOM_WEBHOOK_URL")
        self.truth_social_cookies = os.getenv("TRUTH_SOCIAL_COOKIES", "")
        
        # 默认配置
        self.check_interval_minutes = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
        self.max_items_per_check = int(os.getenv("MAX_ITEMS_PER_CHECK", "30"))
        
        # 监控人物列表配置（逗号分隔，不配置则监控所有）
        personalities_str = os.getenv("MONITOR_PERSONALITIES", "")
        if personalities_str:
            self.monitor_personalities = [p.strip() for p in personalities_str.split(",") if p.strip()]
        else:
            self.monitor_personalities = None
    
    def validate(self):
        """验证配置完整性"""
        missing_configs = []
        
        if not self.proxy:
            missing_configs.append("PROXY")
        if not self.auth_token:
            missing_configs.append("TWITTER_AUTH_TOKEN")
        if not self.ct0:
            missing_configs.append("TWITTER_CT0")
        
        if missing_configs:
            print(f"缺少必要的配置项：{', '.join(missing_configs)}")
            print("请创建 .env 文件并配置相关参数，可参考 .env.example 文件")
            return False
        
        if not self.google_api_key:
            print("未配置 GOOGLE_API_KEY，将无法使用翻译和 AI 解读功能")
        
        print("配置检查通过")
        return True