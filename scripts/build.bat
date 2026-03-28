@echo off
cd /d "%~dp0\.."
echo ========================================
echo OCR工作流程应用 - 打包脚本
echo ========================================
echo.
echo 当前目录: %CD%
echo.

echo [1/3] 检查PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller未安装，正在安装...
    pip install pyinstaller
)

echo.
echo [2/3] 开始打包...
python scripts\build.py

echo.
echo [3/3] 打包完成！
echo 可执行文件位置: dist\OCRWorkflow.exe
echo.
pause
