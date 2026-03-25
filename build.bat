@echo off
chcp 65001 >nul
title 物料管理系统 · 一键打包
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   物料管理系统 · 一键打包
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 运行 PowerShell 打包脚本
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"

echo.
echo 打包结束。按任意键关闭窗口…
pause >nul
