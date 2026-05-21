"""企业微信推送服务模块"""
import httpx
import asyncio


class WeComService:
    """企业微信推送服务类"""
    
    MAX_LENGTH = 4096
    SEND_DELAY = 1.5
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_markdown(self, content: str, title: str = "动态报告"):
        """发送 Markdown 格式的消息到企业微信群"""
        if not self.webhook_url:
            print("⚠️ 未配置企业微信 Webhook URL，跳过推送")
            return
        
        chunks = self._split_by_headers(content)
        
        if not chunks:
            print("⚠️ 没有可推送的内容")
            return
        
        print(f"📤 将报告拆分为 {len(chunks)} 块进行推送...", flush=True)
        
        for i, chunk in enumerate(chunks, 1):
            await self._send_single_markdown(chunk, i, len(chunks), title)
            if i < len(chunks):
                await asyncio.sleep(self.SEND_DELAY)
    
    def _split_by_headers(self, content: str) -> list:
        """将内容按 Markdown 标题分割成独立的块"""
        chunks = []
        lines = content.split('\n')
        
        current_chunk_lines = []
        
        for line in lines:
            is_header = line.startswith('##')
            
            if is_header:
                if current_chunk_lines:
                    chunk_text = '\n'.join(current_chunk_lines).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                current_chunk_lines = [line]
            else:
                current_chunk_lines.append(line)
        
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines).strip()
            if chunk_text:
                chunks.append(chunk_text)
        
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.MAX_LENGTH:
                final_chunks.append(chunk)
            else:
                sub_chunks = self._split_long_chunk(chunk)
                final_chunks.extend(sub_chunks)
        
        return final_chunks
    
    def _split_long_chunk(self, chunk: str) -> list:
        """将超长块拆分成多个部分"""
        chunks = []
        lines = chunk.split('\n')
        
        current_lines = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1
            
            if current_length + line_length > self.MAX_LENGTH and current_lines:
                chunks.append('\n'.join(current_lines))
                current_lines = [line]
                current_length = line_length
            else:
                current_lines.append(line)
                current_length += line_length
        
        if current_lines:
            chunks.append('\n'.join(current_lines))
        
        return chunks
    
    async def _send_single_markdown(self, content: str, chunk_num: int, total_chunks: int, title: str):
        """发送单条 Markdown 消息"""
        if total_chunks > 1:
            header = f"📢 {title} ({chunk_num}/{total_chunks})\n\n"
            content = header + content
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=data)
                result = response.json()
                if result.get("errcode") == 0:
                    print(f"✅ 第 {chunk_num}/{total_chunks} 块推送成功", flush=True)
                else:
                    print(f"❌ 第 {chunk_num}/{total_chunks} 块推送失败: {result.get('errmsg')}", flush=True)
        except Exception as e:
            print(f"❌ 第 {chunk_num}/{total_chunks} 块推送异常: {e}", flush=True)