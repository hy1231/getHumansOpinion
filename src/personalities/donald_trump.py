"""特朗普人物模块 - Truth Social 动态抓取"""
import json
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

try:
    from curl_cffi.requests import AsyncSession
    USE_CURL_CFFI = True
except ImportError:
    import httpx
    USE_CURL_CFFI = False

 
class DonaldTrumpFetcher:
    """特朗普动态抓取器"""
    
    PERSONALITY_ID = "donald_trump"
    PERSONALITY_NAME = "特朗普"
    TARGET_USER = "realDonaldTrump"
    ACCOUNT_ID = "107780257626128497"
    
    def __init__(self, config):
        self.config = config
    
    async def fetch_recent_items(self):
        """获取最新动态列表"""
        print(f"\n📡 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在获取 @{self.TARGET_USER} 的最新动态...")
        valid_items = []
        
        url = f"https://truthsocial.com/api/v1/accounts/{self.ACCOUNT_ID}/statuses"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        params = {
            "limit": min(self.config.max_items_per_check, 40),
            "exclude_replies": "true",
            "with_muted": "true"
        }
        
        try:
            if USE_CURL_CFFI:
                async with AsyncSession(proxy=self.config.proxy, impersonate="chrome120") as session:
                    response = await session.get(url, headers=headers, params=params)
            else:
                async with httpx.AsyncClient(proxy=self.config.proxy, timeout=20) as client:
                    response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 403:
                print("❌ 获取失败：触发了 Cloudflare 或平台反爬机制")
                if not USE_CURL_CFFI:
                    print("💡 建议：运行 pip install curl_cffi 安装库以绕过 Cloudflare")
                return valid_items
            
            response.raise_for_status()
            posts = response.json()
            
            for post in posts:
                item = self._parse_item(post)
                if item:
                    valid_items.append(item)
            
            valid_items.sort(key=lambda x: x['datetime'], reverse=True)
            print(f"✅ 共抓取到 {len(valid_items)} 条最新动态")
            return valid_items
            
        except Exception as e:
            print(f"💥 请求错误: {e}")
            return valid_items
    
    def _parse_item(self, post):
        """解析单条动态"""
        item_id = str(post.get('id', ''))
        if not item_id:
            return None
        
        raw_content = post.get('content', '')
        clean_content = BeautifulSoup(raw_content, "html.parser").get_text().strip()
        
        if not clean_content:
            return None
        
        reblog = post.get('reblog')
        quoted_text = ""
        if reblog:
            original_author = reblog.get('account', {}).get('username', 'Unknown')
            reblog_content = BeautifulSoup(reblog.get('content', ''), "html.parser").get_text().strip()
            clean_content = f"[🔁 转发了 @{original_author} 的帖子]:\n{reblog_content}"
        
        raw_time = post.get('created_at', '')
        if raw_time:
            try:
                if '.' in raw_time:
                    parsed_time = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                else:
                    parsed_time = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ")
                beijing_dt = parsed_time + timedelta(hours=8)
            except ValueError:
                beijing_dt = datetime.now()
        else:
            beijing_dt = datetime.now()
        
        return {
            "id": item_id,
            "text": clean_content,
            "quoted_text": quoted_text,
            "likes": post.get('favourites_count', 0),
            "retweets": post.get('reblogs_count', 0),
            "time": beijing_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "datetime": beijing_dt
        }