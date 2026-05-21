"""报告生成模块"""
import os
from datetime import datetime


class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def save_report(report_text, personality_id, personality_name):
        """保存报告到文件"""
        now = datetime.now()
        file_name = f"output/{now.strftime('%Y-%m-%d_%H%M')}_{personality_id}_Report.md"
        
        try:
            os.makedirs("output", exist_ok=True)
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"\n💾 报告已保存：{file_name}")
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")