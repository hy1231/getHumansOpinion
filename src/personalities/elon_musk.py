"""马斯克人物模块 - Twitter/X 动态抓取"""
import json
from datetime import datetime, timedelta

import httpx


class ElonMuskFetcher:
    """马斯克推文抓取器"""
    
    PERSONALITY_ID = "elon_musk"
    PERSONALITY_NAME = "马斯克"
    TARGET_USER = "elonmusk"
    USER_ID = "44196397"
    QUERY_ID = "O0epvwaQPUx-bT9YlqlL6w"
    
    def __init__(self, config):
        self.config = config
    
    async def fetch_recent_items(self):
        """获取最新动态列表"""
        print(f"\n📡 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在获取 @{self.TARGET_USER} 的最新动态...")
        valid_items = []
        cursor = None
        
        url = f"https://x.com/i/api/graphql/{self.QUERY_ID}/UserTweets"
        headers = self._build_headers()
        
        async with httpx.AsyncClient(proxy=self.config.proxy, timeout=20) as client:
            try:
                while len(valid_items) < self.config.max_items_per_check:
                    params = self._build_params(cursor)
                    resp = await client.get(url, headers=headers, params=params)
                    
                    if resp.status_code != 200:
                        print(f"❌ 请求失败，状态码: {resp.status_code}")
                        break
                    
                    data = resp.json()
                    items, cursor = self._parse_response(data)
                    
                    for item in items:
                        if len(valid_items) >= self.config.max_items_per_check:
                            break
                        valid_items.append(item)
                    
                    if not cursor or not items:
                        break
                
                valid_items.sort(key=lambda x: x['datetime'], reverse=True)
                print(f"✅ 共抓取到 {len(valid_items)} 条最新动态")
                return valid_items
                
            except Exception as e:
                print(f"💥 抓取解析失败: {e}")
                import traceback
                traceback.print_exc()
                return valid_items
    
    def _build_headers(self):
        """构建请求头"""
        return {
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'cookie': f'auth_token={self.config.auth_token}; ct0={self.config.ct0}',
            'x-csrf-token': self.config.ct0,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'content-type': 'application/json'
        }
    
    def _build_params(self, cursor=None):
        """构建请求参数"""
        variables = {
            "userId": self.USER_ID,
            "count": 10,
            "includePromotedContent": False,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True
        }
        if cursor:
            variables["cursor"] = cursor
        
        features = {
            "rweb_tipjar_consumption_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "units_2024_03_enabled": True
        }
        
        field_toggles = {"withArticleRichContentState": False}
        
        return {
            "variables": json.dumps(variables),
            "features": json.dumps(features),
            "fieldToggles": json.dumps(field_toggles)
        }
    
    def _parse_response(self, data):
        """解析API响应"""
        items = []
        cursor = None
        
        user_res = data.get('data', {}).get('user', {}).get('result', {})
        timeline = user_res.get('timeline_v2', {}).get('timeline', {})
        if not timeline:
            timeline = user_res.get('timeline', {}).get('timeline', {})
        
        instructions = timeline.get('instructions', [])
        add_entries = next((i for i in instructions if i['type'] == 'TimelineAddEntries'), None)
        
        if not add_entries:
            print("⚠️ 未能找到动态列表模块")
            return items, cursor
        
        entries = add_entries.get('entries', [])
        
        for entry in entries:
            if 'cursor-bottom' in entry.get('entryId', ''):
                cursor = entry.get('content', {}).get('value')
                continue
            
            item_res = entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
            legacy = item_res.get('legacy') or item_res.get('tweet', {}).get('legacy', {})
            
            if not legacy:
                continue
            
            item = self._parse_item(item_res, legacy)
            if item:
                items.append(item)
        
        return items, cursor
    
    def _parse_item(self, item_res, legacy):
        """解析单条动态"""
        item_id = legacy.get('id_str', '')
        text = legacy.get('full_text', '').strip()
        
        if text.startswith("RT @"):
            return None
        
        quoted_text = ""
        is_quote = legacy.get('is_quote_status', False)
        if is_quote:
            q_res = item_res.get('quoted_status_result', {}).get('result', {})
            q_legacy = q_res.get('legacy') or q_res.get('tweet', {}).get('legacy', {})
            if q_legacy:
                quoted_text = q_legacy.get('full_text', '').strip()
        
        utc_dt = datetime.strptime(legacy['created_at'], '%a %b %d %H:%M:%S %z %Y')
        beijing_dt = utc_dt + timedelta(hours=8)
        
        return {
            "id": item_id,
            "text": text,
            "quoted_text": quoted_text,
            "likes": legacy.get('favorite_count', 0),
            "retweets": legacy.get('retweet_count', 0),
            "time": beijing_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "datetime": beijing_dt
        }