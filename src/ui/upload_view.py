"""图片上传界面"""
import re
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from typing import List


class UploadView(QWidget):
    """图片上传界面"""

    # 信号：当用户点击"开始识别"按钮时发出
    start_ocr_signal = pyqtSignal(list)  # 发送图片路径列表

    def __init__(self):
        super().__init__()
        self.image_paths: List[str] = []
        self.init_ui()

    @staticmethod
    def natural_sort_key(path: str):
        """
        自然排序键函数，用于正确排序包含数字的文件名
        例如: 1.jpg, 2.jpg, 10.jpg 会按 1, 2, 10 排序（而不是 1, 10, 2）
        """
        filename = os.path.basename(path)
        # 将文件名分割为文本和数字部分
        parts = re.split(r'(\d+)', filename)
        # 将数字部分转换为整数，其他保持字符串
        return [int(part) if part.isdigit() else part.lower() for part in parts]

    def init_ui(self):
        """初始化UI"""
        # 启用拖拽
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout()

        # 标题
        title = QLabel("OCR工作流程 - 图片上传")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.upload_btn = QPushButton("选择图片")
        self.upload_btn.setMinimumHeight(40)
        self.upload_btn.clicked.connect(self.select_images)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_images)

        self.start_btn = QPushButton("开始OCR识别")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_ocr)
        self.start_btn.setEnabled(False)

        button_layout.addWidget(self.upload_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.start_btn)
        layout.addLayout(button_layout)

        # 图片预览区域
        self.preview_label = QLabel("已选择 0 张图片")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("font-size: 14px; margin: 10px;")
        layout.addWidget(self.preview_label)

        # 图片网格
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)

        self.image_container = QWidget()
        self.image_grid = QGridLayout()
        self.image_container.setLayout(self.image_grid)
        scroll_area.setWidget(self.image_container)

        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def select_images(self):
        """选择图片文件，并按文件名数字顺序排序"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*)"
        )

        if files:
            self.image_paths.extend(files)
            # 按文件名的自然数字顺序排序（1, 2, 3, 10, 11 而不是 1, 10, 11, 2, 3）
            self.image_paths.sort(key=self.natural_sort_key)
            self.update_preview()

    def clear_images(self):
        """清空已选择的图片"""
        self.image_paths.clear()
        self.update_preview()

    def update_preview(self):
        """更新图片预览"""
        # 清空现有网格
        for i in reversed(range(self.image_grid.count())):
            widget = self.image_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 更新状态
        count = len(self.image_paths)
        self.preview_label.setText(f"已选择 {count} 张图片 (支持拖拽上传)")
        self.start_btn.setEnabled(count > 0)

        # 显示缩略图（每行4张）
        for idx, path in enumerate(self.image_paths):
            row = idx // 4
            col = idx % 4

            # 创建容器widget
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(5)
            container_layout.setContentsMargins(5, 5, 5, 5)

            # 序号标签
            order_label = QLabel(f"#{idx + 1}")
            order_label.setAlignment(Qt.AlignCenter)
            order_label.setStyleSheet("font-weight: bold; color: #2196F3;")
            container_layout.addWidget(order_label)

            # 图片标签
            img_label = QLabel()
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled_pixmap)
            else:
                img_label.setText(f"无法加载\n{path}")

            img_label.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(img_label)

            # 文件名标签
            filename = os.path.basename(path)
            filename_label = QLabel(filename)
            filename_label.setAlignment(Qt.AlignCenter)
            filename_label.setWordWrap(True)
            filename_label.setStyleSheet("font-size: 10px; color: #666;")
            container_layout.addWidget(filename_label)

            container.setStyleSheet("border: 1px solid #ccc; background-color: white;")
            self.image_grid.addWidget(container, row, col)

    def start_ocr(self):
        """开始OCR识别"""
        if self.image_paths:
            self.start_ocr_signal.emit(self.image_paths.copy())

    def reset(self):
        """重置界面"""
        self.image_paths.clear()
        self.update_preview()

    # 拖拽事件处理
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查是否有图片文件
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self._is_image(file_path):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """拖拽释放事件"""
        new_files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self._is_image(file_path) and file_path not in self.image_paths:
                new_files.append(file_path)
        
        if new_files:
            self.image_paths.extend(new_files)
            # 重新排序
            self.image_paths.sort(key=self.natural_sort_key)
            self.update_preview()
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件（必须实现，否则dropEvent可能不触发）"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _is_image(self, file_path: str) -> bool:
        """检查是否为支持的图片格式"""
        if not os.path.isfile(file_path):
            return False
        
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        ext = os.path.splitext(file_path)[1].lower()
        return ext in valid_extensions
