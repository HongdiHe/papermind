"""
打包脚本 - 将应用打包成可执行文件

使用方法:
    python scripts/build.py

功能:
1. 自动检测操作系统 (Windows/macOS/Linux)
2. 设置平台特定的参数 (图标、分隔符)
3. 自动收集必要的数据文件 (配置文件模板)
4. 处理隐式导入 (PyQt5, WebEngine)
"""
import sys
import os
import platform
import PyInstaller.__main__

def build():
    """执行打包流程"""
    # 1. 环境准备
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    system_name = platform.system()
    print(f"当前平台: {system_name}")
    print(f"项目根目录: {project_root}")

    # 2. 基础参数
    app_name = "OCRWorkflow"
    params = [
        'main.py',                          # 入口文件
        f'--name={app_name}',               # 应用名称
        '--onefile',                        # 单文件模式
        '--windowed',                       # GUI模式（无控制台）
        '--clean',                          # 清理缓存
        '--noconfirm',                      # 覆盖输出
    ]

    # 3. 平台差异化配置
    # 数据文件分隔符: Windows使用';', 类Unix使用':'
    sep = ';' if system_name == 'Windows' else ':'
    
    # 图标配置
    icon_path = ""
    if system_name == 'Windows':
        icon_path = os.path.join('assets', 'icon.ico')
    elif system_name == 'Darwin': # macOS
        icon_path = os.path.join('assets', 'icon.icns')
    # Linux通常不需要在打包时指定图标，或者是.png
    
    if icon_path and os.path.exists(icon_path):
        params.append(f'--icon={icon_path}')
        print(f"使用图标: {icon_path}")
    else:
        print("未找到图标文件或当前平台无需指定，使用默认图标")

    # 4. 数据文件 (add-data)
    # 格式: 源路径{sep}目标路径
    # 尝试包含 config.example.yaml 如果存在
    config_template = os.path.join('config', 'config.example.yaml')
    if os.path.exists(config_template):
        params.append(f'--add-data={config_template}{sep}config')
    
    # 包含 README.md (可选，作为说明)
    if os.path.exists('README.md'):
        params.append(f'--add-data=README.md{sep}.')

    # 5. 隐式导入 (Hidden Imports)
    # PyQt5 和 WebEngine 经常需要手动指定
    hidden_imports = [
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtNetwork',
        'PyQt5.QtPrintSupport',
        'jinja2',  # 如果使用了Markdown渲染可能依赖
        'yaml',
        'requests',
        'PIL',
    ]
    
    for lib in hidden_imports:
        params.append(f'--hidden-import={lib}')

    # 6. 执行打包
    print("\n[开始打包]...")
    print(f"参数: {' '.join(params)}")
    
    try:
        PyInstaller.__main__.run(params)
        print("\n[打包成功]")
        
        # 输出位置提示
        dist_dir = os.path.join(project_root, 'dist')
        executable = app_name
        if system_name == 'Windows':
            executable += '.exe'
        elif system_name == 'Darwin':
            executable += '.app'
            
        print(f"可执行文件位于: {os.path.join(dist_dir, executable)}")
        
    except Exception as e:
        print(f"\n[打包失败]: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    build()
