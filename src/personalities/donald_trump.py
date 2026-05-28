"""特朗普人物模块 - Truth Social 动态抓取"""
import asyncio
import json
import random
import traceback
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

try:
    from curl_cffi.requests import AsyncSession
    USE_CURL_CFFI = True
except ImportError:
    USE_CURL_CFFI = False

try:
    from playwright.async_api import async_playwright
    USE_PLAYWRIGHT = True
except ImportError:
    USE_PLAYWRIGHT = False


class DonaldTrumpFetcher:
    """特朗普动态抓取器"""
    
    PERSONALITY_ID = "donald_trump"
    PERSONALITY_NAME = "特朗普"
    TARGET_USER = "realDonaldTrump"
    ACCOUNT_ID = "107780257626128497"
    
    def __init__(self, config):
        self.config = config
    
    def _log(self, message, level="INFO"):
        """统一日志打印"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level_color = {
            "INFO": "📋",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍"
        }
        print(f"[{timestamp}] {level_color.get(level, '📋')} [{self.PERSONALITY_NAME}] {message}")
    
    async def fetch_recent_items(self):
        """获取最新动态列表"""
        self._log(f"开始获取 @{self.TARGET_USER} 的最新动态", "INFO")
        valid_items = []
        
        # 优先尝试 curl_cffi 方案（更稳定）
        if USE_CURL_CFFI:
            self._log("尝试 curl_cffi 方案", "INFO")
            valid_items = await self._fetch_with_curl_cffi()
            if valid_items:
                self._log(f"curl_cffi 成功获取 {len(valid_items)} 条动态", "SUCCESS")
                return valid_items
            self._log("curl_cffi 方案失败，尝试 Playwright 方案", "WARNING")
        
        # 备用 Playwright 方案
        if USE_PLAYWRIGHT:
            self._log("尝试 Playwright 方案", "INFO")
            valid_items = await self._fetch_with_playwright()
            if valid_items:
                self._log(f"Playwright 成功获取 {len(valid_items)} 条动态", "SUCCESS")
                return valid_items
        
        self._log("所有方案均失败", "ERROR")
        self._log("解决方法：", "INFO")
        self._log("  1. 安装 Playwright: pip install playwright && playwright install", "INFO")
        self._log("  2. 确保代理服务器可以正常访问国外网站", "INFO")
        self._log("  3. 在 .env 中添加 TRUTH_SOCIAL_COOKIES 配置", "INFO")
        self._log("  4. 尝试更换代理 IP（推荐使用国外 VPS）", "INFO")
        return valid_items
    
    async def _fetch_with_playwright(self):
        """使用 Playwright 获取数据"""
        valid_items = []
        url = f"https://truthsocial.com/@realDonaldTrump"
        
        try:
            async with async_playwright() as p:
                browser_args = [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
                if self.config.proxy:
                    browser_args.append(f'--proxy-server={self.config.proxy}')
                
                browser = await p.chromium.launch(headless=True, args=browser_args)
                
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="America/New_York"
                )
                
                page = await context.new_page()
                await page.set_extra_http_headers({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://truthsocial.com/",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                })
                
                self._log("正在加载页面...", "DEBUG")
                response = await page.goto(url, wait_until="networkidle", timeout=60000)
                
                if response.status == 403:
                    self._log("页面被 Cloudflare 拦截", "ERROR")
                    await browser.close()
                    return valid_items
                
                await page.wait_for_selector('article', timeout=30000)
                
                # 滚动页面加载更多内容
                for i in range(3):
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await page.wait_for_timeout(2000)
                    self._log(f"滚动加载第 {i+1}/3 次", "DEBUG")
                
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                articles = soup.find_all('article')
                self._log(f"解析到 {len(articles)} 条动态", "DEBUG")
                
                for article in articles:
                    item = self._parse_html_item(article)
                    if item:
                        valid_items.append(item)
                
                await browser.close()
                valid_items.sort(key=lambda x: x['datetime'], reverse=True)
                return valid_items
                
        except Exception as e:
            self._log(f"Playwright 请求失败: {e}", "ERROR")
            traceback.print_exc()
            return valid_items
    
    async def _fetch_with_curl_cffi(self):
        """使用 curl_cffi 获取数据"""
        valid_items = []
        url = f"https://truthsocial.com/api/v1/accounts/{self.ACCOUNT_ID}/statuses"
        
        headers = self._generate_headers()
        params = {
            "limit": min(self.config.max_items_per_check, 40),
            "exclude_replies": "true",
            "with_muted": "true"
        }
        
        browsers = ["chrome120", "chrome110", "safari17", "firefox120", "edge120"]
        
        for browser in browsers:
            try:
                await asyncio.sleep(1 + random.uniform(0.5, 1.5))
                
                async with AsyncSession(proxy=self.config.proxy, impersonate=browser) as session:
                    if self.config.truth_social_cookies:
                        session.cookies.update(self._parse_cookies(self.config.truth_social_cookies))
                    response = await session.get(url, headers=headers, params=params)
                
                self._log(f"尝试浏览器指纹: {browser}, 状态码: {response.status_code}", "DEBUG")
                
                if response.status_code == 200:
                    posts = response.json()
                    for post in posts:
                        item = self._parse_api_item(post)
                        if item:
                            valid_items.append(item)
                    valid_items.sort(key=lambda x: x['datetime'], reverse=True)
                    return valid_items
                
                elif response.status_code == 403:
                    self._log(f"{browser} 指纹被 Cloudflare 拦截", "WARNING")
                    continue
                    
            except Exception as e:
                self._log(f"{browser} 请求失败: {e}", "ERROR")
                continue
        
        return valid_items
    
    def _generate_headers(self):
        """生成模拟浏览器的请求头"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ]
        
        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"https://truthsocial.com/@realDonaldTrump",
            "Origin": "https://truthsocial.com",
            "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest"
        }
    
    def _parse_cookies(self, cookie_string):
        """解析 Cookie 字符串"""
        cookies = {}
        for pair in cookie_string.split(';'):
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                cookies[key] = value
        return cookies
    
    def _parse_html_item(self, article):
        """解析 HTML 页面中的动态"""
        try:
            content_div = article.find('div', {'dir': 'auto'}) or article.find('p')
            if not content_div:
                return None
            
            text = content_div.get_text(strip=True)
            if not text:
                return None
            
            # 解析时间
            time_elem = article.find('time')
            if time_elem and time_elem.get('datetime'):
                try:
                    time_str = time_elem.get('datetime')
                    parsed_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ") if '.' in time_str else datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
                    beijing_dt = parsed_time + timedelta(hours=8)
                except ValueError:
                    beijing_dt = datetime.now()
            else:
                beijing_dt = datetime.now()
            
            # 解析互动数据
            likes = 0
            retweets = 0
            for span in article.find_all('span'):
                span_class = str(span.get('class', []))
                if 'like' in span_class or 'favourite' in span_class:
                    try:
                        likes = int(span.get_text().strip())
                    except:
                        pass
                elif 'reblog' in span_class or 'retweet' in span_class:
                    try:
                        retweets = int(span.get_text().strip())
                    except:
                        pass
            
            # 生成唯一 ID
            item_id = f"{beijing_dt.strftime('%Y%m%d%H%M%S')}_{hash(text) % 10000}"
            
            return {
                "id": item_id,
                "text": text,
                "quoted_text": "",
                "likes": likes,
                "retweets": retweets,
                "time": beijing_dt.strftime('%Y-%m-%d %H:%M:%S'),
                "datetime": beijing_dt
            }
        except Exception as e:
            self._log(f"HTML 解析失败: {e}", "ERROR")
            return None
    
    def _parse_api_item(self, post):
        """解析 API 返回的动态"""
        item_id = str(post.get('id', ''))
        if not item_id:
            return None
        
        raw_content = post.get('content', '')
        clean_content = BeautifulSoup(raw_content, "html.parser").get_text().strip()
        
        if not clean_content:
            return None
        
        quoted_text = ""
        
        # 处理转发
        reblog = post.get('reblog')
        if reblog:
            original_author = reblog.get('account', {}).get('username', 'Unknown')
            reblog_content = BeautifulSoup(reblog.get('content', ''), "html.parser").get_text().strip()
            clean_content = f"[🔁 转发了 @{original_author}]:\n{reblog_content}"
        
        # 处理引用回复
        quote = post.get('quote')
        if quote:
            quote_author = quote.get('account', {}).get('username', 'Unknown')
            quote_content = BeautifulSoup(quote.get('content', ''), "html.parser").get_text().strip()
            quoted_text = f"[📎 引用 @{quote_author}]:\n{quote_content}"
        
        # 解析时间
        raw_time = post.get('created_at', '')
        if raw_time:
            try:
                parsed_time = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S.%fZ") if '.' in raw_time else datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ")
                beijing_dt = parsed_time + timedelta(hours=8)
            except ValueError:
                beijing_dt = datetime.now()
        else:
            beijing_dt = datetime.now()
        
        return {
            "id": item_id,
            "text": clean_content,
            "quoted_text": "",
            "likes": post.get('favourites_count', 0),
            "retweets": post.get('reblogs_count', 0),
            "time": beijing_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "datetime": beijing_dt
        }