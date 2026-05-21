"""AI服务模块"""
import os
from datetime import datetime

from google import genai


class AIService:
    """AI服务类（翻译和解读）"""
    
    def __init__(self, config):
        self.config = config
        self.client = self._init_client()
        self.model_name = "gemini-2.5-flash"
    
    def _init_client(self):
        """初始化 Gemini 客户端"""
        if not self.config.google_api_key:
            return None
        
        os.environ["HTTPS_PROXY"] = self.config.proxy
        return genai.Client(api_key=self.config.google_api_key)
    
    async def generate_report(self, items, personality_name):
        """批量处理内容，生成统一格式的报告"""
        if not self.client:
            return self._generate_fallback_report(items, personality_name)
        
        try:
            items_text = ""
            for i, item in enumerate(items, 1):
                quoted_part = f"\n引用原文：{item['quoted_text']}" if item.get('quoted_text') else ""
                items_text += f"""
{item['time']} - 动态#{i}
原文：{item['text']}{quoted_part}
互动数据：{item['likes']} 点赞 | {item['retweets']} 转发
---
"""
            
            prompt = f"""请对以下{personality_name}的最新动态进行分析，并生成一份简洁易读的报告：

{items_text}

报告格式要求：
1. 采用 Markdown 格式输出
2. 每条动态包含：动态标题、发布时间、中文翻译、要点解读
3. 动态标题要简洁概括核心内容（不超过20字）
4. 解读要简洁明了，突出核心观点（50字以内）
5. 在报告末尾添加一个"综合分析"部分，总结整体趋势
6. 使用表情符号增加可读性

示例格式：
## 📢 {personality_name}最新动态报告
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 动态1：[动态标题]
**发布时间**：2024-01-15 10:30:00
**原文**：[英文原文]
**翻译**：[中文翻译]
**解读**：[简要分析]

### 动态2：[动态标题]
...

## 💡 综合分析
[对所有动态的整体总结]
"""
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"❌ AI 报告生成失败: {str(e)[:100]}\n\n{self._generate_fallback_report(items, personality_name)}"
    
    def _generate_fallback_report(self, items, personality_name):
        """当未配置 API Key 时生成降级报告"""
        lines = [f"## 📢 {personality_name}最新动态报告", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
        
        for i, item in enumerate(items, 1):
            lines.append(f"### 🔹 动态 #{i}")
            lines.append(f"**发布时间**：{item['time']}")
            lines.append(f"**原文**：{item['text']}")
            if item.get('quoted_text'):
                lines.append(f"**引用**：{item['quoted_text']}")
            lines.append(f"**互动**：{item['likes']} 点赞 | {item['retweets']} 转发")
            lines.append(f"**翻译**：⚠️ 未配置 Google API Key，无法翻译")
            lines.append(f"**解读**：⚠️ 未配置 Google API Key，无法解读")
            lines.append("")
        
        lines.append("## 💡 综合分析")
        lines.append("⚠️ 未配置 Google API Key，无法进行综合分析")
        
        return "\n".join(lines)