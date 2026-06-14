@echo off
chcp 65001 >nul
cd /d "I:\采购管理系统\采购管理系统V2.3.2"
echo 正在打包采购助手 V2.3.4...
pyinstaller --noconfirm "采购助手V2.3.4.spec"
echo.
echo 打包完成！
echo 输出目录: dist\
pause
