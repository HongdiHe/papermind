#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR工作流程应用 - 主入口
"""
import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main() -> None:
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("OCR工作流程")

    # 设置应用样式
    app.setStyle('Fusion')

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
