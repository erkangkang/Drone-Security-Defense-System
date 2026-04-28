"""
加密工具
Crypto Utility
"""

import hashlib
import hmac
import secrets
from typing import Optional, Union


class CryptoUtils:
    """加密工具类"""

    @staticmethod
    def generate_random_bytes(length: int = 32) -> bytes:
        """生成随机字节"""
        return secrets.token_bytes(length)

    @staticmethod
    def generate_random_string(length: int = 16) -> str:
        """生成随机字符串"""
        return secrets.token_hex(length)

    @staticmethod
    def hash_data(
        data: Union[str, bytes],
        algorithm: str = "sha256"
    ) -> str:
        """计算数据哈希"""
        if isinstance(data, str):
            data = data.encode("utf-8")

        hash_func = hashlib.new(algorithm)
        hash_func.update(data)
        return hash_func.hexdigest()

    @staticmethod
    def hash_file(
        file_path: str,
        algorithm: str = "sha256",
        chunk_size: int = 8192
    ) -> str:
        """计算文件哈希"""
        hash_func = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    @staticmethod
    def hmac_sign(
        data: Union[str, bytes],
        key: Union[str, bytes],
        algorithm: str = "sha256"
    ) -> str:
        """HMAC签名"""
        if isinstance(data, str):
            data = data.encode("utf-8")
        if isinstance(key, str):
            key = key.encode("utf-8")

        signature = hmac.new(key, data, algorithm)
        return signature.hexdigest()

    @staticmethod
    def hmac_verify(
        data: Union[str, bytes],
        key: Union[str, bytes],
        signature: str,
        algorithm: str = "sha256"
    ) -> bool:
        """验证HMAC签名"""
        expected_signature = CryptoUtils.hmac_sign(data, key, algorithm)
        return hmac.compare_digest(expected_signature, signature)

    @staticmethod
    def generate_api_key(secret: Optional[str] = None) -> str:
        """生成API密钥"""
        if secret is None:
            secret = secrets.token_hex(16)
        return f"ds_{secret}"

    @staticmethod
    def derive_key(
        password: str,
        salt: Optional[bytes] = None,
        iterations: int = 100000
    ) -> tuple[str, bytes]:
        """派生密钥（PBKDF2）"""
        if salt is None:
            salt = secrets.token_bytes(16)

        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return key.hex(), salt

    @staticmethod
    def base64_encode(data: Union[str, bytes]) -> str:
        """Base64编码"""
        import base64
        if isinstance(data, str):
            data = data.encode("utf-8")
        return base64.b64encode(data).decode("utf-8")

    @staticmethod
    def base64_decode(data: str) -> bytes:
        """Base64解码"""
        import base64
        return base64.b64decode(data)
