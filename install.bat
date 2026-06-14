@echo off
chcp 65001 >nul
title 采购助手 安装程序
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║       采购助手 V2.0.6 安装程序          ║
echo  ║                                        ║
echo  ║  默认安装到：%%USERPROFILE%%\采购助手   ║
echo  ╚══════════════════════════════════════════╝
echo.
set "INSTALL_DIR=%USERPROFILE%\采购助手"

echo [1/3] 正在创建安装目录...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\assets" mkdir "%INSTALL_DIR%\assets"

echo [2/3] 正在复制程序文件...
copy /Y "%~dp0采购助手.exe" "%INSTALL_DIR%\" >nul
xcopy /Y /E /I /Q "%~dp0assets\*" "%INSTALL_DIR%\assets\" >nul

echo [3/3] 正在创建快捷方式...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\采购助手.lnk'); $s.TargetPath='%INSTALL_DIR%\采购助手.exe'; $s.IconLocation='%INSTALL_DIR%\采购助手.exe'; $s.Save()" 2>nul
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Programs')+'\采购助手\采购助手.lnk'); $s.TargetPath='%INSTALL_DIR%\采购助手.exe'; $s.IconLocation='%INSTALL_DIR%\采购助手.exe'; $s.Save()" 2>nul

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║       安装完成！                        ║
echo  ║                                        ║
echo  ║  程序位置：%INSTALL_DIR%               ║
echo  ║  桌面已创建快捷方式                     ║
echo  ╚══════════════════════════════════════════╝
echo.
echo 按任意键退出...
pause >nul
