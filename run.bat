@echo off
chcp 65001 >nul
cd /d "%~dp0"

setlocal enabledelayedexpansion

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=!dt:~0,4!"
set "MM=!dt:~4,2!"
set "DD=!dt:~6,2!"
set "HH=!dt:~8,2!"
set "Min=!dt:~10,2!"
set "Sec=!dt:~12,2!"
set "logfile=task_log_!YYYY!!MM!!DD!_!HH!!Min!!Sec!.txt"

(
echo ==========================================
echo 启动时间: %date% %time%
echo 日志文件: !logfile!
echo ==========================================
echo 正在启动人物动态监控...

if exist ".venv\Scripts\activate.bat" (
    echo 发现虚拟环境，正在激活...
    call ".venv\Scripts\activate.bat"
) else (
    echo 警告：未找到虚拟环境，尝试直接运行
)

echo 开始执行主程序...
echo ------------------------------------------

python main.py

echo ------------------------------------------
echo 程序执行完毕
echo ==========================================
) >> logs\!logfile! 2>&1

if not exist "logs" mkdir logs