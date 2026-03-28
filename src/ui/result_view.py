"""最终结果展示和编辑界面"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTextEdit, QSplitter, QScrollArea, QGridLayout,
                             QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from typing import List
from src.utils.markdown_renderer import markdown_to_html


class ResultView(QWidget):
    """最终结果编辑界面"""

    # 信号
    submit_signal = pyqtSignal(dict)  # 提交最终数据
    discard_signal = pyqtSignal()     # 废弃

    def __init__(self):
        super().__init__()
        self.image_paths: List[str] = []
        self.llm_markdown: str = ""
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()

        # 标题
        title = QLabel("大模型处理结果 - 最终编辑")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title)

        # 创建分割器（上下分割）
        main_splitter = QSplitter(Qt.Vertical)

        # 上部分：图片和大模型结果（左右分割）
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

        # 右侧：大模型返回的Markdown渲染结果
        llm_widget = QWidget()
        llm_layout = QVBoxLayout()
        llm_layout.addWidget(QLabel("大模型返回结果（Markdown渲染）:"))

        self.llm_web_view = QWebEngineView()
        llm_layout.addWidget(self.llm_web_view)

        llm_widget.setLayout(llm_layout)

        upper_splitter.addWidget(image_widget)
        upper_splitter.addWidget(llm_widget)
        upper_splitter.setStretchFactor(0, 1)
        upper_splitter.setStretchFactor(1, 1)

        # 下部分：三个编辑框（题目、答案、评价）
        lower_widget = QWidget()
        lower_layout = QHBoxLayout()

        # 题目编辑区
        question_widget = QWidget()
        question_layout = QVBoxLayout()

        question_label = QLabel("题目:")
        question_label.setToolTip("大模型结果已自动填入，请编辑提取题目部分")
        question_layout.addWidget(question_label)

        self.question_edit = QTextEdit()
        self.question_edit.setAcceptRichText(False)  # 纯文本模式
        self.question_edit.setPlaceholderText("大模型结果将自动填充，请编辑提取题目...")
        question_layout.addWidget(self.question_edit)

        question_widget.setLayout(question_layout)

        # 标准答案编辑区
        answer_widget = QWidget()
        answer_layout = QVBoxLayout()

        answer_label = QLabel("标准答案:")
        answer_label.setToolTip("大模型结果已自动填入，请编辑提取答案部分")
        answer_layout.addWidget(answer_label)

        self.answer_edit = QTextEdit()
        self.answer_edit.setAcceptRichText(False)  # 纯文本模式
        self.answer_edit.setPlaceholderText("大模型结果将自动填充，请编辑提取答案...")
        answer_layout.addWidget(self.answer_edit)

        answer_widget.setLayout(answer_layout)

        # 评价编辑区
        evaluation_widget = QWidget()
        evaluation_layout = QVBoxLayout()

        evaluation_label = QLabel("评价:")
        evaluation_label.setToolTip("请输入对题目和答案的评价")
        evaluation_layout.addWidget(evaluation_label)

        self.evaluation_edit = QTextEdit()
        self.evaluation_edit.setAcceptRichText(False)  # 纯文本模式
        self.evaluation_edit.setPlaceholderText("请输入评价（可选）...")
        evaluation_layout.addWidget(self.evaluation_edit)

        evaluation_widget.setLayout(evaluation_layout)

        lower_layout.addWidget(question_widget)
        lower_layout.addWidget(answer_widget)
        lower_layout.addWidget(evaluation_widget)

        lower_widget.setLayout(lower_layout)

        # 添加到主分割器
        main_splitter.addWidget(upper_splitter)
        main_splitter.addWidget(lower_widget)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 3)

        main_layout.addWidget(main_splitter)

        # 底部按钮
        button_layout = QHBoxLayout()

        self.discard_btn = QPushButton("废弃")
        self.discard_btn.setMinimumHeight(40)
        self.discard_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.discard_btn.clicked.connect(self.discard)

        self.submit_btn = QPushButton("提交")
        self.submit_btn.setMinimumHeight(40)
        self.submit_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.submit_btn.clicked.connect(self.submit)

        button_layout.addWidget(self.discard_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.submit_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def set_data(self, image_paths: List[str], llm_markdown: str):
        """设置数据

        Args:
            image_paths: 图片路径列表
            llm_markdown: 大模型返回的Markdown结果
        """
        self.image_paths = image_paths
        self.llm_markdown = llm_markdown

        # 显示图片
        self.display_images()

        # 渲染并显示大模型结果
        html_content = markdown_to_html(llm_markdown)
        self.llm_web_view.setHtml(html_content)

        # 自动填充大模型返回的结果到题目和答案框
        # 用户可以直接编辑提取需要的部分
        self.question_edit.setPlainText(llm_markdown)
        self.answer_edit.setPlainText(llm_markdown)
        # 评价框留空，由用户手动填写
        self.evaluation_edit.clear()

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

    def submit(self):
        """提交数据"""
        question = self.question_edit.toPlainText().strip()
        answer = self.answer_edit.toPlainText().strip()
        evaluation = self.evaluation_edit.toPlainText().strip()

        if not question or not answer:
            QMessageBox.warning(self, "提示", "请填写题目和标准答案")
            return

        # 发送数据
        data = {
            'question': question,
            'answer': answer,
            'evaluation': evaluation
        }
        self.submit_signal.emit(data)

    def discard(self):
        """废弃当前数据"""
        reply = QMessageBox.question(
            self,
            '确认',
            '确定要废弃当前数据吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.discard_signal.emit()
