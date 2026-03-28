"""主窗口 - 整合工作流程"""
import json
import os
import sys
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QStackedWidget, QMessageBox,
                             QProgressDialog, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from src.ui.upload_view import UploadView
from src.ui.ocr_view import OcrView
from src.ui.result_view import ResultView
from src.models.data_models import WorkflowData
from src.services.mineru_api import MinerUService
from src.services.llm_api import LLMService
from src.utils.config_loader import get_config


class ApiWorker(QThread):
    """API调用工作线程"""
    finished = pyqtSignal(str)  # 完成信号，返回结果
    error = pyqtSignal(str)     # 错误信号

    def __init__(self, api_func: callable, *args: object) -> None:
        super().__init__()
        self.api_func = api_func
        self.args = args

    def run(self) -> None:
        try:
            result = self.api_func(*self.args)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self) -> None:
        super().__init__()
        self.workflow_data = WorkflowData()
        self.mineru_service = None
        self.llm_service = None
        self.init_services()
        self.init_ui()

    def init_services(self) -> None:
        """初始化服务，失败时退出应用"""
        try:
            self.mineru_service = MinerUService()
            self.llm_service = LLMService()
        except Exception as e:
            QMessageBox.critical(
                self,
                "初始化失败",
                f"服务初始化失败: {str(e)}\n\n请检查配置文件 config/config.yaml\n\n应用将退出。"
            )
            # 退出应用
            sys.exit(1)

    def init_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle("OCR工作流程应用")

        # 设置窗口大小
        config = get_config()
        width = config.get('ui.window_width', 1400)
        height = config.get('ui.window_height', 900)
        self.resize(width, height)

        # 创建堆叠窗口部件
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 创建各个界面
        self.upload_view = UploadView()
        self.ocr_view = OcrView()
        self.result_view = ResultView()

        # 添加到堆叠窗口
        self.stacked_widget.addWidget(self.upload_view)    # 索引0
        self.stacked_widget.addWidget(self.ocr_view)       # 索引1
        self.stacked_widget.addWidget(self.result_view)    # 索引2

        # 连接信号
        self.connect_signals()

        # 显示上传界面
        self.show_upload_view()

    def connect_signals(self) -> None:
        """连接信号和槽"""
        # 上传界面 -> 开始OCR
        self.upload_view.start_ocr_signal.connect(self.handle_start_ocr)

        # OCR界面 -> 提交给大模型
        self.ocr_view.submit_to_llm_signal.connect(self.handle_submit_to_llm)
        self.ocr_view.back_btn.clicked.connect(self.show_upload_view)

        # 结果界面 -> 提交/废弃
        self.result_view.submit_signal.connect(self.handle_final_submit)
        self.result_view.discard_signal.connect(self.handle_discard)

    def show_upload_view(self) -> None:
        """显示上传界面"""
        self.upload_view.reset()
        self.stacked_widget.setCurrentIndex(0)

    def show_ocr_view(self) -> None:
        """显示OCR结果界面"""
        self.stacked_widget.setCurrentIndex(1)

    def show_result_view(self) -> None:
        """显示最终结果界面"""
        self.stacked_widget.setCurrentIndex(2)

    def handle_start_ocr(self, image_paths: list) -> None:
        """处理开始OCR"""
        self.workflow_data.image_paths = image_paths

        # 创建进度对话框
        progress = QProgressDialog("正在进行OCR识别...", "取消", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # 创建工作线程
        self.ocr_worker = ApiWorker(
            self.mineru_service.ocr_images,
            image_paths
        )

        # 连接信号
        self.ocr_worker.finished.connect(lambda result: self.on_ocr_finished(result, progress))
        self.ocr_worker.error.connect(lambda error: self.on_api_error(error, progress, "OCR识别"))

        # 启动线程
        self.ocr_worker.start()

    def on_ocr_finished(self, markdown_result: str, progress: object) -> None:
        """OCR完成"""
        progress.close()

        self.workflow_data.ocr_markdown = markdown_result

        # 显示OCR结果界面
        self.ocr_view.set_data(self.workflow_data.image_paths, markdown_result)
        self.show_ocr_view()

    def handle_submit_to_llm(self, question: str, answer: str) -> None:
        """处理提交给大模型"""
        self.workflow_data.question_text = question
        self.workflow_data.answer_text = answer

        # 创建进度对话框
        progress = QProgressDialog("正在调用大模型处理...", "取消", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # 创建工作线程
        self.llm_worker = ApiWorker(
            self.llm_service.process_question_answer,
            question,
            answer
        )

        # 连接信号
        self.llm_worker.finished.connect(lambda result: self.on_llm_finished(result, progress))
        self.llm_worker.error.connect(lambda error: self.on_api_error(error, progress, "大模型调用"))

        # 启动线程
        self.llm_worker.start()

    def on_llm_finished(self, markdown_result: str, progress: object) -> None:
        """大模型调用完成"""
        progress.close()

        self.workflow_data.llm_markdown = markdown_result

        # 显示最终结果界面，填充大模型返回的结果
        self.result_view.set_data(
            self.workflow_data.image_paths,
            markdown_result
        )
        self.show_result_view()

    def handle_final_submit(self, data: dict) -> None:
        """处理最终提交"""
        # 更新工作流数据
        self.workflow_data.final_question = data['question']
        self.workflow_data.final_answer = data['answer']
        self.workflow_data.final_evaluation = data['evaluation']

        # 保存到JSON
        self.save_to_json()

        # 提示成功
        QMessageBox.information(self, "成功", "数据已保存！")

        # 返回上传界面，开始新的循环
        self.workflow_data = WorkflowData()  # 重置数据
        self.show_upload_view()

    def handle_discard(self) -> None:
        """处理废弃"""
        # 重置数据
        self.workflow_data = WorkflowData()

        # 返回上传界面
        self.show_upload_view()

    def save_to_json(self) -> None:
        """保存数据到JSON文件，追加到同一个数组中"""
        config = get_config()
        output_dir = config.get('data.output_dir', './data')
        output_file = config.get('data.output_file', 'output.json')

        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, output_file)

        # 读取现有数据
        existing_data = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # 确保是列表格式
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except json.JSONDecodeError as e:
                print(f"警告: JSON文件格式错误，将创建新文件。错误: {e}")
                # 备份损坏的文件
                backup_path = file_path + '.backup'
                shutil.copy(file_path, backup_path)
                print(f"已备份原文件到: {backup_path}")
                existing_data = []
            except Exception as e:
                print(f"警告: 读取文件失败: {e}")
                existing_data = []

        # 添加新数据到数组末尾
        new_entry = self.workflow_data.to_json_format()
        existing_data.append(new_entry)

        # 保存回文件（覆盖写入完整数组）
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        print(f"数据已保存到: {file_path}")
        print(f"当前共有 {len(existing_data)} 条记录")

    def on_api_error(self, error_msg: str, progress: object, api_name: str) -> None:
        """API调用错误处理"""
        progress.close()
        QMessageBox.critical(
            self,
            f"{api_name}失败",
            f"调用失败: {error_msg}"
        )
