"""MinerU OCR API调用服务"""
import os
import time
import requests
import zipfile
import tempfile
from typing import List
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
                except (requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError,
                        requests.exceptions.RequestException) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # 指数退避
                        print(f"API请求失败 (尝试 {attempt + 1}/{max_retries})，{delay}秒后重试: {str(e)}")
                        time.sleep(delay)
                    else:
                        print(f"API请求在{max_retries}次尝试后仍失败")
            raise last_exception
        return wrapper
    return decorator


class MinerUService:
    """MinerU OCR服务类"""

    def __init__(self) -> None:
        config = get_config()
        self.api_key = config.get('mineru.api_key')
        self.model_version = config.get('mineru.model_version', 'vlm')
        self.timeout = config.get('mineru.timeout', 300)
        self.poll_interval = config.get('mineru.poll_interval', 5)  # 轮询间隔（秒）

        # MinerU API端点
        self.base_url = "https://mineru.net/api/v4"
        self.upload_url = f"{self.base_url}/file-urls/batch"
        self.batch_result_url = f"{self.base_url}/extract-results/batch"

    def ocr_images(self, image_paths: List[str]) -> str:
        """
        调用MinerU API识别多张图片

        流程：
        1. 申请上传链接
        2. 上传文件
        3. 轮询获取结果
        4. 下载并解压结果
        5. 提取Markdown内容

        Args:
            image_paths: 图片路径列表

        Returns:
            拼接后的Markdown结果

        Raises:
            Exception: OCR识别过程中的任何错误
        """
        # 步骤1: 申请上传链接
        batch_id, upload_urls = self._get_upload_urls(image_paths)
        print(f"申请上传链接成功，batch_id: {batch_id}")

        # 步骤2: 上传文件
        self._upload_files(image_paths, upload_urls)
        print("文件上传完成")

        # 步骤3: 等待并获取结果
        print("等待MinerU处理...")
        results = self._poll_results(batch_id)
        print("MinerU处理完成")

        # 步骤4: 下载并提取Markdown
        markdown_contents = self._extract_markdown_from_results(results)

        # 步骤5: 拼接所有Markdown结果
        if not markdown_contents:
            raise Exception("未能提取到任何Markdown内容")

        return "\n\n---\n\n".join(markdown_contents)

    @retry_with_backoff(max_retries=3, base_delay=1)
    def _get_upload_urls(self, image_paths: List[str]) -> tuple:
        """申请文件上传链接"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # 构建文件列表
        files_data = []
        for image_path in image_paths:
            filename = os.path.basename(image_path)
            files_data.append({
                "name": filename
            })

        data = {
            "files": files_data,
            "model_version": self.model_version
        }

        response = requests.post(
            self.upload_url,
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()

        result = response.json()
        if result["code"] != 0:
            raise Exception(f"申请上传链接失败: {result.get('msg', 'Unknown error')}")

        batch_id = result["data"]["batch_id"]
        upload_urls = result["data"]["file_urls"]

        return batch_id, upload_urls

    @retry_with_backoff(max_retries=3, base_delay=1)
    def _upload_files(self, image_paths: List[str], upload_urls: List[str]) -> None:
        """上传文件到MinerU"""
        for image_path, upload_url in zip(image_paths, upload_urls):
            with open(image_path, 'rb') as f:
                response = requests.put(
                    upload_url,
                    data=f,
                    timeout=self.timeout
                )
                response.raise_for_status()
                print(f"已上传: {os.path.basename(image_path)}")

    @retry_with_backoff(max_retries=3, base_delay=2)
    def _poll_results(self, batch_id: str, max_wait_time: int = 600) -> List[dict]:
        """轮询获取处理结果"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
        }

        start_time = time.time()

        while True:
            # 检查超时
            if time.time() - start_time > max_wait_time:
                raise Exception("处理超时，请稍后重试")

            # 获取结果
            url = f"{self.batch_result_url}/{batch_id}"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            if result["code"] != 0:
                raise Exception(f"获取结果失败: {result.get('msg', 'Unknown error')}")

            extract_results = result["data"]["extract_result"]

            # 检查所有文件的状态
            all_done = True
            failed_files = []

            for file_result in extract_results:
                state = file_result["state"]
                if state == "failed":
                    failed_files.append({
                        "name": file_result["file_name"],
                        "error": file_result.get("err_msg", "Unknown error")
                    })
                elif state in ["waiting-file", "pending", "running", "converting"]:
                    all_done = False
                    print(f"  {file_result['file_name']}: {state}")

            # 如果有失败的文件，抛出异常
            if failed_files:
                error_msg = "\n".join([f"{f['name']}: {f['error']}" for f in failed_files])
                raise Exception(f"部分文件处理失败:\n{error_msg}")

            # 如果全部完成，返回结果
            if all_done:
                return extract_results

            # 等待后重试
            time.sleep(self.poll_interval)

    @retry_with_backoff(max_retries=3, base_delay=1)
    def _extract_markdown_from_results(self, results: List[dict]) -> List[str]:
        """从结果中提取Markdown内容"""
        markdown_contents = []
        failed_files = []

        for result in results:
            zip_url = result.get("full_zip_url")
            file_name = result.get('file_name', 'Unknown')

            if not zip_url:
                failed_files.append(f"{file_name}: 未找到下载链接")
                continue

            try:
                # 下载zip文件
                response = requests.get(zip_url, timeout=self.timeout)
                response.raise_for_status()

                # 创建临时目录
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = os.path.join(temp_dir, "result.zip")

                    # 保存zip文件
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)

                    # 解压（安全检查）
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # 检查路径安全性
                        for member in zip_ref.namelist():
                            # 防止路径穿越攻击
                            member_path = os.path.join(temp_dir, member)
                            if not member_path.startswith(temp_dir):
                                raise Exception(f"不安全的ZIP路径: {member}")
                        zip_ref.extractall(temp_dir)

                    # 查找Markdown文件
                    markdown_content = self._find_markdown_in_dir(temp_dir)
                    if not markdown_content:
                        failed_files.append(f"{file_name}: 未找到Markdown内容")
                    else:
                        markdown_contents.append(markdown_content)

            except Exception as e:
                error_msg = f"{file_name}: {str(e)}"
                print(f"处理结果文件失败: {error_msg}")
                failed_files.append(error_msg)

        # 如果有任何文件失败，抛出异常
        if failed_files:
            error_detail = "\n".join(failed_files)
            raise Exception(f"部分文件处理失败:\n{error_detail}")

        return markdown_contents

    def _find_markdown_in_dir(self, directory: str) -> str:
        """在目录中查找并读取Markdown文件"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
        return ""
