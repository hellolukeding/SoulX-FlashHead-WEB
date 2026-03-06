"""
腾讯云 ASR 实现
基于 /opt/lt 项目的实现
"""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import numpy as np
from loguru import logger

from app.services.asr.base import BaseASR


class TencentASR(BaseASR):
    """
    腾讯云语音识别 (ASR)

    使用腾讯云一句话识别 API
    文档: https://cloud.tencent.com/document/product/1093/48982
    """

    def __init__(self):
        super().__init__()
        self._url = "https://asr.tencentcloudapi.com"
        self._secret_id = None
        self._secret_key = None
        self._engine_model_type = "16k_zh"

        # 加载凭证
        self._load_credentials()

    def _load_credentials(self):
        """从环境变量加载腾讯云凭证"""
        # 支持多种环境变量名称
        self._secret_id = (
            os.environ.get("TENCENT_ASR_SECRET_ID") or
            os.environ.get("TENCENT_ASR_SECERET_ID") or
            os.environ.get("TENCENT_SECRET_ID")
        )
        self._secret_key = (
            os.environ.get("TENCENT_ASR_SECRET_KEY") or
            os.environ.get("TENCENT_ASR_SECERET_KEY") or
            os.environ.get("TENCENT_SECRET_KEY")
        )

        if not self._secret_id or not self._secret_key:
            logger.warning("[ASR] 腾讯 ASR 凭证未配置，将回退到 MockASR")
            logger.warning("[ASR] 请设置环境变量 TENCENT_ASR_SECRET_ID 和 TENCENT_ASR_SECRET_KEY")
            return

        # 去除空格
        self._secret_id = self._secret_id.strip()
        self._secret_key = self._secret_key.strip()

        logger.info(f"[ASR] 腾讯 ASR 初始化成功: {self._secret_id[:8]}...")

    def _sign(self, key, msg: str):
        """生成 HMAC-SHA256 签名"""
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _build_request(self, audio_data: str):
        """构建腾讯 ASR API 请求"""
        service = "asr"
        host = "asr.tencentcloudapi.com"
        version = "2019-06-14"
        action = "SentenceRecognition"
        algorithm = "TC3-HMAC-SHA256"
        timestamp = int(time.time())
        date = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d")

        # 构建请求参数
        params = {
            "ProjectId": 0,
            "SubServiceType": 2,
            "EngSerViceType": self._engine_model_type,
            "SourceType": 1,
            "VoiceFormat": "wav",
            "UsrAudioKey": str(uuid.uuid4()),
            "Data": audio_data,
            "DataLen": len(base64.b64decode(audio_data)),
        }

        # TC3 签名
        canonical_querystring = ""
        payload = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
        canonical_headers = f"content-type:application/json\nhost:{host}\n"
        signed_headers = "content-type;host"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = f"POST\n/\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{hashed_request_payload}"
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"

        # 生成签名
        secret_date = self._sign(("TC3" + self._secret_key).encode("utf-8"), date)
        secret_service = self._sign(secret_date, service)
        secret_signing = self._sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # 构建授权头
        authorization = f"{algorithm} Credential={self._secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": version,
            "X-TC-Region": "ap-beijing"
        }

        return headers, payload

    def _pcm_to_wav_bytes(self, audio_array, sample_rate: int = 16000) -> bytes:
        """
        将 numpy 数组转换为 WAV 字节
        快速转换，避免使用 pydub/soundfile
        """
        try:
            import io
            import wave

            # 确保是 numpy 数组
            if not hasattr(audio_array, 'dtype'):
                return audio_array

            arr = audio_array

            # 如果是浮点数，转换为 int16
            if np.issubdtype(arr.dtype, np.floating):
                int16 = np.clip(arr * 32767, -32768, 32767).astype(np.int16)
            else:
                int16 = arr.astype(np.int16)

            # 写入 WAV
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(int16.tobytes())

            return buf.getvalue()
        except Exception as e:
            logger.warning(f"[ASR] PCM 转 WAV 失败: {e}")
            return audio_array

    async def recognize(self, audio: np.ndarray, metadata: Dict[str, Any] = None) -> str:
        """
        识别语音

        Args:
            audio: 音频数据 (16kHz, float32)
            metadata: 可选的元数据

        Returns:
            str: 识别的文本

        Raises:
            RuntimeError: 如果识别失败
        """
        # 检查凭证
        if not self._secret_id or not self._secret_key:
            logger.warning("[ASR] 腾讯 ASR 未配置，返回模拟文本")
            return "腾讯 ASR 未配置，请检查环境变量"

        try:
            # 转换音频为 WAV 字节并 Base64 编码
            wav_bytes = self._pcm_to_wav_bytes(audio, 16000)
            audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

            # 构建请求
            headers, payload = self._build_request(audio_base64)

            # 发送请求
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._url,
                    headers=headers,
                    data=payload,
                    timeout=10.0
                )

                logger.debug(f"[ASR] 腾讯 API 响应状态: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"[ASR] 腾讯 API 错误: {response.status_code}, {response.text}")
                    raise RuntimeError(f"腾讯 ASR API 错误: {response.status_code}")

                result = response.json()

                # 获取响应体
                if "Response" in result and isinstance(result["Response"], dict):
                    response_body = result["Response"]
                else:
                    response_body = result

                # 检查错误
                if "Error" in response_body:
                    error_msg = response_body['Error']['Message']
                    error_code = response_body['Error']['Code']
                    logger.error(f"[ASR] 腾讯 ASR 错误 - Code: {error_code}, Message: {error_msg}")

                    if error_code == "AuthFailure.SecretIdNotFound":
                        raise RuntimeError(f"腾讯 ASR 认证失败: SecretId 不存在")
                    elif error_code == "AuthFailure.SignatureFailure":
                        raise RuntimeError(f"腾讯 ASR 认证失败: 签名验证失败")
                    else:
                        raise RuntimeError(f"腾讯 ASR 错误: {error_msg}")

                # 提取识别结果
                transcript = None
                for key in ("Result", "Text", "Transcript", "TextResult"):
                    if isinstance(response_body.get(key), str) and response_body.get(key):
                        transcript = response_body.get(key)
                        break

                # 如果没有直接结果，尝试从 WordList 拼接
                if not transcript and isinstance(response_body.get("WordList"), list):
                    words = []
                    for w in response_body.get("WordList", []):
                        if isinstance(w, dict):
                            word_text = w.get("Word") or w.get("Text") or w.get("WordStr")
                            if word_text:
                                words.append(word_text)
                        elif isinstance(w, str):
                            words.append(w)
                    if words:
                        transcript = "".join(words)

                if not transcript:
                    if "TaskId" in response_body:
                        logger.warning(f"[ASR] 腾讯返回异步任务 ID: {response_body.get('TaskId')}")
                        return "语音识别处理中，请稍后重试"

                    logger.error(f"[ASR] 腾讯 API 响应缺少文本字段")
                    raise RuntimeError("腾讯 API 响应格式错误")

                logger.debug(f"[ASR] 识别结果: {transcript}")
                return transcript

        except Exception as e:
            logger.error(f"[ASR] 语音识别失败: {e}")
            raise RuntimeError(f"语音识别失败: {str(e)}")

    def is_available(self) -> bool:
        """检查 ASR 是否可用"""
        return bool(self._secret_id and self._secret_key)
