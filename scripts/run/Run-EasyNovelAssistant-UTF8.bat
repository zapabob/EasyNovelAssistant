@echo off
chcp 65001 > NUL
echo EasyNovelAssistant を UTF-8 モードで起動しています...
py -3 easy_novel_assistant.py
if %errorlevel% neq 0 ( pause ) 