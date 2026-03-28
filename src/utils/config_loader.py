"""配置文件加载器"""
import os
import yaml
from typing import Dict, Any, List


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigLoader:
    """配置加载类"""

    # 必需的配置项
    REQUIRED_KEYS = [
        'mineru.api_key',
        'mineru.model_version',
    ]

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}\n"
                f"请复制 config/config.example.yaml 为 config/config.yaml 并填入你的API信息"
            )

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if not isinstance(config, dict):
                    raise ConfigValidationError("配置文件格式错误：根节点必须是字典")
                return config
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"配置文件YAML格式错误: {str(e)}")

    def _validate_config(self):
        """验证配置文件"""
        missing_keys = []
        invalid_keys = []

        for key_path in self.REQUIRED_KEYS:
            value = self.get(key_path)
            if value is None:
                missing_keys.append(key_path)
            elif isinstance(value, str) and (not value.strip() or
                                            'your-' in value or
                                            'placeholder' in value):
                invalid_keys.append(key_path)

        errors = []
        if missing_keys:
            errors.append(f"缺少必需配置项: {', '.join(missing_keys)}")
        if invalid_keys:
            errors.append(f"配置项未填写或使用占位符: {', '.join(invalid_keys)}")

        if errors:
            raise ConfigValidationError('\n'.join(errors))

    def get(self, key_path: str, default=None):
        """
        获取配置值
        例如: get('mineru.api_key')
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default

        return value if value is not None else default


# 全局配置实例
_config = None


def get_config() -> ConfigLoader:
    """获取配置实例（单例模式）"""
    global _config
    if _config is None:
        _config = ConfigLoader()
    return _config
