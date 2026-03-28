"""大模型API调用服务"""
import time
import requests
from functools import wraps
from src.utils.config_loader import get_config


def retry_with_backoff(max_retries: int = 3, base_delay: int = 1):
    """
    装饰器：实现指数退避重试逻辑

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.Timeout as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"API请求超时 (尝试 {attempt + 1}/{max_retries})，{delay}秒后重试: {str(e)}")
                        time.sleep(delay)
                    else:
                        print(f"API请求在{max_retries}次尝试后仍超时")
                except requests.exceptions.ConnectionError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"API连接失败 (尝试 {attempt + 1}/{max_retries})，{delay}秒后重试: {str(e)}")
                        time.sleep(delay)
                    else:
                        print(f"API连接在{max_retries}次尝试后仍失败")
                except requests.exceptions.HTTPError as e:
                    last_exception = e
                    print(f"API返回HTTP错误: {str(e)}")
                    break  # HTTP错误通常不应重试（如401、403）
                except requests.exceptions.RequestException as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"API请求失败 (尝试 {attempt + 1}/{max_retries})，{delay}秒后重试: {str(e)}")
                        time.sleep(delay)
                    else:
                        print(f"API请求在{max_retries}次尝试后仍失败")
            raise last_exception
        return wrapper
    return decorator


class LLMService:
    """大模型API服务类"""

    # 默认prompt模板
    DEFAULT_PROMPT_TEMPLATE = """请分析以下题目和答案，并提供详细的解答过程和评价。

题目：
{question}

参考答案：
{answer}

请提供：
1. 完整的解题过程
2. 对答案的评价和改进建议"""

    def __init__(self) -> None:
        config = get_config()
        self.api_url: str = config.get('llm.api_url')
        self.api_key: str = config.get('llm.api_key')
        self.model: str = config.get('llm.model', 'gpt-4')
        self.timeout: int = config.get('llm.timeout', 60)
        # 如果配置中没有prompt_template，使用默认模板
        self.prompt_template: str = config.get('llm.prompt_template', self.DEFAULT_PROMPT_TEMPLATE)

        # API key 验证
        if not self.api_key or not self.api_key.strip():
            raise ValueError("LLM API key 未配置，请在 config.yaml 中设置 llm.api_key")
        if not self.api_url or not self.api_url.strip():
            raise ValueError("LLM API URL 未配置，请在 config.yaml 中设置 llm.api_url")

    @retry_with_backoff(max_retries=3, base_delay=2)
    def process_question_answer(self, question: str, answer: str) -> str:
        """
        调用大模型处理题目和答案

        Args:
            question: 题目内容
            answer: 答案内容

        Returns:
            大模型返回的Markdown结果

        Raises:
            Exception: 大模型调用过程中的任何错误
        """
        # 构建prompt
        prompt = self.prompt_template.format(
            question=question,
            answer=answer
        )

        # 调用API（OpenAI格式）
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.7
        }

        response = requests.post(
            self.api_url,
            json=data,
            headers=headers,
            timeout=self.timeout
        )

        response.raise_for_status()
        result = response.json()

        # 提取结果（OpenAI格式）
        if 'choices' not in result or len(result['choices']) == 0:
            raise Exception("大模型返回格式错误：未找到有效的响应内容")

        content = result['choices'][0]['message']['content']
        if not content or not content.strip():
            raise Exception("大模型返回内容为空")

        return content
