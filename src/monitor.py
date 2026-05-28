"""统一监控调度器模块"""

import asyncio
from datetime import datetime

from src.common.config import Config
from src.common.ai_service import AIService
from src.common.data_store import DataStore
from src.common.report_generator import ReportGenerator
from src.common.wecom_service import WeComService
from src.personalities.elon_musk import ElonMuskFetcher
from src.personalities.donald_trump import DonaldTrumpFetcher


class PersonalityMonitor:
    """人物动态监控类"""
    
    # 支持的人物列表
    PERSONALITIES = {
        "elon_musk": {
            "name": "马斯克",
            "fetcher_class": ElonMuskFetcher
        },
        "donald_trump": {
            "name": "特朗普",
            "fetcher_class": DonaldTrumpFetcher
        }
    }
    
    def __init__(self, personality_id: str):
        self.personality_id = personality_id
        self.config = Config()
        
        # 获取人物配置
        if personality_id not in self.PERSONALITIES:
            raise ValueError(f"不支持的人物: {personality_id}")
        
        self.personality_info = self.PERSONALITIES[personality_id]
        self.fetcher = self.personality_info["fetcher_class"](self.config)
        self.ai_service = AIService(self.config)
        self.data_store = DataStore(personality_id)
        self.wecom_service = WeComService(self.config.wecom_webhook_url)
    
    async def run_once(self):
        """执行一次抓取和推送"""
        if not self.config.validate():
            return
        
        personality_name = self.personality_info["name"]
        
        print(f"🚀 开始执行 {personality_name} 动态抓取任务", flush=True)
        print(f"⏰ 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"🔤 目标人物：{personality_name}", flush=True)
        print(f"📊 最大抓取数量：{self.config.max_items_per_check}", flush=True)
        
        if self.config.wecom_webhook_url:
            print("📤 企业微信推送已启用", flush=True)
        else:
            print("📤 未配置企业微信 Webhook，推送功能已禁用", flush=True)
        
        print("="*60, flush=True)
        
        try:
            self.data_store.load_sent_items()
            
            items = await self.fetcher.fetch_recent_items()
            if not items:
                error_msg = f"❌ {personality_name} 动态抓取失败"
                print(f"📭 {error_msg}", flush=True)
                await self.wecom_service.send_markdown(error_msg, f"{personality_name}抓取失败")
                return
            
            print(f"📥 共抓取到 {len(items)} 条动态", flush=True)
            
            new_items = [item for item in items if not self.data_store.is_sent(item['id'])]
            
            if not new_items:
                print("✅ 暂无新动态", flush=True)
                return
            
            print(f"\n🔔 发现 {len(new_items)} 条新动态，正在生成报告...", flush=True)
            
            report = await self.ai_service.generate_report(new_items, personality_name)
            
            print("\n" + "="*60, flush=True)
            print(report, flush=True)
            print("="*60 + "\n", flush=True)
            
            if report.startswith("❌ AI 报告生成失败"):
                print("⚠️ AI 报告生成失败，不标记已发送，下次将重新抓取", flush=True)
                await self.wecom_service.send_markdown(report, f"{personality_name}报告生成失败")
            else:
                for item in new_items:
                    self.data_store.mark_sent(item['id'])
                self.data_store.save_sent_items()
                
                ReportGenerator.save_report(report, self.personality_id, personality_name)
                
                await self.wecom_service.send_markdown(report, f"{personality_name}动态报告")
            
            print(f"\n✅ 任务执行完成", flush=True)
            
        except Exception as e:
            print(f"❌ 任务执行失败: {e}", flush=True)
            raise


class BatchMonitor:
    """批量监控调度器"""
    
    def __init__(self, personality_ids: list = None):
        self.config = Config()
        self.monitors = []
        
        if personality_ids is None:
            personality_ids = list(PersonalityMonitor.PERSONALITIES.keys())
        
        for pid in personality_ids:
            if pid in PersonalityMonitor.PERSONALITIES:
                self.monitors.append(PersonalityMonitor(pid))
    
    async def run_all(self):
        """顺序执行所有人物的监控任务"""
        if not self.config.validate():
            return
        
        print(f"\n🚀 开始批量监控任务", flush=True)
        print(f"⏰ 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"📋 监控人物：{', '.join(m.personality_info['name'] for m in self.monitors)}", flush=True)
        print("="*60, flush=True)
        
        for i, monitor in enumerate(self.monitors, 1):
            print(f"\n{'='*60}", flush=True)
            print(f"[{i}/{len(self.monitors)}] ", end="", flush=True)
            
            try:
                await monitor.run_once()
            except Exception as e:
                print(f"❌ {monitor.personality_info['name']} 监控失败: {e}", flush=True)
        
        print(f"\n{'='*60}", flush=True)
        print(f"✅ 批量监控任务完成", flush=True)