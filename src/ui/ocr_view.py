"""OCR结果展示和编辑界面"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTextEdit, QSplitter, QScrollArea, QGridLayout,
                             QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from typing import List
from src.utils.markdown_renderer import markdown_to_html


class OcrView(QWidget):
    """OCR结果展示界面"""

    # 信号：提交题目和答案给大模型
    submit_to_llm_signal = pyqtSignal(str, str)  # (question, answer)

    def __init__(self):
        super().__init__()
        self.image_paths: List[str] = []
        self.ocr_markdown: str = ""
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()

        # 标题
        title = QLabel("OCR识别结果 - 编辑题目和答案")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title)

        # 创建分割器（上下分割）
        main_splitter = QSplitter(Qt.Vertical)

        # 上半部分：图片和OCR结果（左右分割）
        upper_splitter = QSplitter(Qt.Horizontal)

        # 左侧：图片展示
        image_widget = QWidget()
        image_layout = QVBoxLayout()
        image_layout.addWidget(QLabel("原始图片:"))

        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_container = QWidget()
        self.image_grid = QGridLayout()
        self.image_container.setLayout(self.image_grid)
        self.image_scroll.setWidget(self.image_container)

        image_layout.addWidget(self.image_scroll)
        image_widget.setLayout(image_layout)

        # 右侧：OCR Markdown渲染结果
        ocr_widget = QWidget()
        ocr_layout = QVBoxLayout()
        ocr_layout.addWidget(QLabel("OCR识别结果（Markdown渲染）:"))

        self.ocr_web_view = QWebEngineView()
        ocr_layout.addWidget(self.ocr_web_view)

        ocr_widget.setLayout(ocr_layout)

        upper_splitter.addWidget(image_widget)
        upper_splitter.addWidget(ocr_widget)
        upper_splitter.setStretchFactor(0, 1)
        upper_splitter.setStretchFactor(1, 1)

        # 下半部分：题目和答案编辑框（左右分割）
        lower_splitter = QSplitter(Qt.Horizontal)

        # 题目编辑区
        question_widget = QWidget()
        question_layout = QVBoxLayout()

        question_label = QLabel("题目:")
        question_label.setToolTip("OCR结果已自动填入，请编辑提取出题目内容")
        question_layout.addWidget(question_label)

        self.question_edit = QTextEdit()
        self.question_edit.setAcceptRichText(False)  # 纯文本模式
        self.question_edit.setPlaceholderText("OCR结果将自动填充到这里，请编辑提取题目部分...")
        question_layout.addWidget(self.question_edit)

        question_widget.setLayout(question_layout)

        # 标准答案编辑区
        answer_widget = QWidget()
        answer_layout = QVBoxLayout()

        answer_label = QLabel("标准答案:")
        answer_label.setToolTip("请从OCR结果中复制或手动输入答案内容")
        answer_layout.addWidget(answer_label)

        self.answer_edit = QTextEdit()
        self.answer_edit.setAcceptRichText(False)  # 纯文本模式
        self.answer_edit.setPlaceholderText("请从上方OCR结果中提取或输入答案...")
        answer_layout.addWidget(self.answer_edit)

        answer_widget.setLayout(answer_layout)

        lower_splitter.addWidget(question_widget)
        lower_splitter.addWidget(answer_widget)
        lower_splitter.setStretchFactor(0, 1)
        lower_splitter.setStretchFactor(1, 1)

        # 添加到主分割器
        main_splitter.addWidget(upper_splitter)
        main_splitter.addWidget(lower_splitter)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)

        main_layout.addWidget(main_splitter)

        # 底部按钮
        button_layout = QHBoxLayout()

        self.back_btn = QPushButton("返回")
        self.back_btn.setMinimumHeight(40)

        self.submit_btn = QPushButton("提交给大模型")
        self.submit_btn.setMinimumHeight(40)
        self.submit_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.submit_btn.clicked.connect(self.submit_to_llm)

        button_layout.addWidget(self.back_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.submit_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def set_data(self, image_paths: List[str], ocr_markdown: str):
        """设置数据"""
        self.image_paths = image_paths
        self.ocr_markdown = ocr_markdown

        # 显示图片
        self.display_images()

        # 渲染并显示OCR结果
        html_content = markdown_to_html(ocr_markdown)
        self.ocr_web_view.setHtml(html_content)

        # 自动填充OCR结果到题目和答案编辑框
        # 用户可以直接在这里编辑和删除不需要的部分
        self.question_edit.setPlainText(ocr_markdown)
        self.answer_edit.setPlainText(ocr_markdown)

    def display_images(self):
        """显示图片"""
        # 清空现有网格
        for i in reversed(range(self.image_grid.count())):
            widget = self.image_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 显示缩略图（每行2张）
        for idx, path in enumerate(self.image_paths):
            row = idx // 2
            col = idx % 2

            img_label = QLabel()
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled_pixmap)
            else:
                img_label.setText(f"无法加载\n{path}")

            img_label.setAlignment(Qt.AlignCenter)
            img_label.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
            self.image_grid.addWidget(img_label, row, col)

    def submit_to_llm(self):
        """提交给大模型"""
        question = self.question_edit.toPlainText().strip()
        answer = self.answer_edit.toPlainText().strip()

        if not question or not answer:
            missing_fields = []
            if not question:
                missing_fields.append("题目")
            if not answer:
                missing_fields.append("标准答案")

            QMessageBox.warning(
                self,
                "缺少必填信息",
                f"请填写以下必填字段：\n\n{', '.join(missing_fields)}"
            )
            return

        self.submit_to_llm_signal.emit(question, answer)
