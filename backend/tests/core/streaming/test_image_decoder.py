from pathlib import Path
import pytest
import base64
from app.core.streaming.image_decoder import ImageDecoder


@pytest.fixture
def decoder():
    return ImageDecoder()


@pytest.fixture
def sample_image_b64():
    """创建测试用的 base64 编码图像"""
    import io
    from PIL import Image
    import numpy as np

    # 创建 512x512 的测试图像
    img = Image.fromarray(np.zeros((512, 512, 3), dtype=np.uint8))

    # 转为 base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    return base64.b64encode(img_bytes).decode()


def test_decode_base64_image(decoder, sample_image_b64, tmp_path):
    """测试解码 base64 图像"""
    output_path = tmp_path / "test_output.png"

    result = decoder.decode_and_save(sample_image_b64, str(output_path))

    assert result == str(output_path)
    assert Path(result).exists()


def test_save_to_temp_dir(decoder, sample_image_b64):
    """测试保存到临时目录"""
    result = decoder.decode_and_save(sample_image_b64)

    assert Path(result).exists()
    assert result.endswith(".png")
