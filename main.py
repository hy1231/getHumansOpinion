#!/usr/bin/env python3
"""人物动态监控 - 主入口"""
import sys
import io
import asyncio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.monitor import PersonalityMonitor, BatchMonitor


def main():
    """主入口函数"""
    config = PersonalityMonitor("elon_musk").config
    
    if config.monitor_personalities:
        monitor = BatchMonitor(config.monitor_personalities)
    else:
        monitor = BatchMonitor()
    
    asyncio.run(monitor.run_all())


if __name__ == "__main__":
    main()