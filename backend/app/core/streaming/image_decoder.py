import base64
import io
import tempfile
from pathlib import Path
from typing import Optional
from PIL import Image
from loguru import logger


class ImageDecoder:
    """
    图像解码器

    解码 base64 编码的图像并保存到文件
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """
        初始化图像解码器

        Args:
            temp_dir: 临时文件目录，None 则使用系统临时目录
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def decode_and_save(
        self,
        image_b64: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        解码 base64 图像并保存到文件

        Args:
            image_b64: base64 编码的图像数据
            output_path: 输出文件路径，None 则自动生成

        Returns:
            保存的图像文件路径
        """
        try:
            # 解码 base64
            image_bytes = base64.b64decode(image_b64)

            # 从字节加载图像
            image = Image.open(io.BytesIO(image_bytes))

            # 生成输出路径
            if output_path is None:
                output_path = self._generate_temp_path()

            # 确保目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存图像
            image.save(output_path)

            logger.info(f"Image decoded and saved: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Image decoding failed: {e}")
            raise

    def _generate_temp_path(self) -> str:
        """生成临时文件路径"""
        import uuid
        filename = f"ref_image_{uuid.uuid4().hex[:8]}.png"
        return str(Path(self.temp_dir) / filename)

    def cleanup_temp_files(self, older_than_seconds: int = 3600):
        """
        清理旧的临时文件

        Args:
            older_than_seconds: 清理超过此秒数的文件
        """
        import time

        temp_path = Path(self.temp_dir)
        current_time = time.time()

        for file_path in temp_path.glob("ref_image_*.png"):
            if current_time - file_path.stat().st_mtime > older_than_seconds:
                file_path.unlink()
                logger.debug(f"Cleaned up temp file: {file_path}")
