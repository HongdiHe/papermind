"""数据模型定义"""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class WorkflowData:
    """工作流数据模型"""
    # 图片路径列表
    image_paths: List[str] = field(default_factory=list)

    # OCR识别的Markdown结果
    ocr_markdown: str = ""

    # 用户编辑的题目和答案（OCR阶段）
    question_text: str = ""
    answer_text: str = ""

    # 大模型返回的Markdown结果
    llm_markdown: str = ""

    # 最终编辑的题目、答案和评价
    final_question: str = ""
    final_answer: str = ""
    final_evaluation: str = ""

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_json_format(self) -> dict:
        """
        转换为JSON格式
        处理：去除换行符，保留LaTeX格式
        输出格式：使用中文键名，包含时间戳
        """
        return {
            "题目": self._process_text(self.final_question),
            "标准答案": self._process_text(self.final_answer),
            "评价": self._process_text(self.final_evaluation),
            "创建时间": self.created_at
        }

    @staticmethod
    def _process_text(text: str) -> str:
        """
        处理文本：
        1. 保留LaTeX格式（$...$, $$...$$）
        2. 将其他换行符替换为空格
        3. 压缩成一行
        """
        import re

        # 暂时替换LaTeX块，避免被处理
        latex_blocks = []

        # 匹配 $$...$$ 和 $...$
        def save_latex(match):
            latex_blocks.append(match.group(0))
            return f"__LATEX_{len(latex_blocks)-1}__"

        # 保存LaTeX块
        text = re.sub(r'\$\$.*?\$\$|\$.*?\$', save_latex, text, flags=re.DOTALL)

        # 替换换行符为空格
        text = text.replace('\n', ' ').replace('\r', ' ')

        # 压缩多个空格为一个
        text = re.sub(r'\s+', ' ', text)

        # 恢复LaTeX块
        for i, latex_block in enumerate(latex_blocks):
            text = text.replace(f"__LATEX_{i}__", latex_block)

        return text.strip()
