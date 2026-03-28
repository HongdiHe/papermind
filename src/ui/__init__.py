"""用户界面模块

使用PyQt5提供的可视化界面，包含主窗口和各个工作流程视图组件。
"""

from src.ui.main_window import MainWindow
from src.ui.upload_view import UploadView
from src.ui.ocr_view import OcrView
from src.ui.result_view import ResultView

__all__ = [
    "MainWindow",
    "UploadView",
    "OcrView",
    "ResultView",
]
