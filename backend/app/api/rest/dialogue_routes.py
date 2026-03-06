"""
对话流程 REST API
实现前端需要的对话接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import base64
import io
import soundfile as sf
from loguru import logger

from app.services.llm.client import get_llm_client
from app.services.tts.factory import get_tts
from app.services.asr.factory import get_asr
from app.core.streaming.audio_decoder import AudioDecoder
from app.core.session.state import SessionState


router = APIRouter()

# 全局会话管理
sessions: dict = {}
decoders: dict = {}


# ==================== Pydantic 模型 ====================

class OfferPayload(BaseModel):
    """WebRTC Offer payload"""
    sdp: Optional[str] = None
    type: Optional[str] = "offer"


class OfferResponse(BaseModel):
    """WebRTC Offer response"""
    sdp: str
    type: str
    sessionid: str


class HumanMessageRequest(BaseModel):
    """用户消息请求"""
    text: Optional[str] = None
    audio_data: Optional[str] = None
    audio_format: Optional[str] = "wav"
    type: Literal["echo", "chat"] = "chat"
    interrupt: bool = True
    sessionid: int


class SpeakingStatusRequest(BaseModel):
    """说话状态请求"""
    sessionid: int


class InterruptRequest(BaseModel):
    """中断请求"""
    sessionid: int


# ==================== 辅助函数 ====================

def get_session(session_id: int):
    """获取会话"""
    return sessions.get(str(session_id))


def create_session_if_not_exists(session_id: int):
    """创建会话（如果不存在）"""
    sid = str(session_id)
    if sid not in sessions:
        sessions[sid] = SessionState(
            session_id=sid,
            created_at=None,
            status="active"
        )
        decoders[sid] = AudioDecoder()
    return sessions[sid]


# ==================== API 端点 ====================

@router.post("/offer", response_model=OfferResponse)
async def negotiate_offer(payload: OfferPayload):
    """
    WebRTC SDP 协商
    
    创建新的对话会话并返回 SDP answer
    """
    import uuid
    session_id = str(uuid.uuid4())
    
    # 创建会话状态
    sessions[session_id] = SessionState(
        session_id=session_id,
        created_at=None,
        status="ready"
    )
    
    # 初始化解码器
    decoders[session_id] = AudioDecoder()
    
    logger.info(f"[{session_id}] WebRTC offer negotiated")
    
    # 返回 SDP answer（简化版本，实际应该生成真实的 SDP）
    return OfferResponse(
        sdp=payload.sdp or "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0",
        type="answer",
        sessionid=session_id
    )


@router.post("/human")
async def send_human_message(request: HumanMessageRequest):
    """
    发送用户消息，触发完整对话流程
    
    流程: ASR识别 → LLM生成 → TTS合成 → 返回结果
    """
    session_id = str(request.sessionid)
    
    try:
        # 确保会话存在
        session = create_session_if_not_exists(request.sessionid)
        decoder = decoders.get(session_id)
        
        if not decoder:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 获取服务
        llm = get_llm_client()
        tts = get_tts()
        asr = get_asr()
        
        # 处理文本或音频输入
        if request.audio_data:
            # 音频输入：使用 ASR 识别
            logger.info(f"[{session_id}] Processing audio message...")
            user_audio = decoder.decode_base64_audio(request.audio_data, request.audio_format or "wav")
            user_text = await asr.recognize(user_audio)
        else:
            # 文本输入：直接使用
            user_text = request.text or ""
        
        logger.info(f"[{session_id}] User: {user_text}")
        
        # LLM 生成（流式）
        logger.info(f"[{session_id}] LLM generating...")
        ai_text_chunks = []
        
        async for chunk in llm.chat_stream(user_text):
            ai_text_chunks.append(chunk)
        
        ai_text = "".join(ai_text_chunks)
        logger.info(f"[{session_id}] AI: {ai_text}")
        
        # TTS 合成
        logger.info(f"[{session_id}] TTS synthesizing...")
        ai_audio = await tts.synthesize(ai_text)
        
        # 编码音频为 Base64
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, ai_audio, 16000, format='WAV')
        audio_buffer.seek(0)
        audio_b64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        
        # 返回结果
        return {
            "code": 0,
            "message": "success",
            "data": {
                "user_text": user_text,
                "ai_text": ai_text,
                "audio_data": audio_b64,
                "audio_format": "wav",
                "sample_rate": 16000
            }
        }
        
    except Exception as e:
        logger.error(f"[{session_id}] Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/is_speaking")
async def check_speaking_status(request: SpeakingStatusRequest):
    """
    检查 AI 是否正在说话
    """
    session_id = str(request.sessionid)
    session = get_session(session_id)
    
    if not session:
        return {"code": 404, "data": False}
    
    is_speaking = session.status == "speaking"
    
    return {
        "code": 0,
        "data": is_speaking
    }


@router.post("/interrupt_talk")
async def interrupt_talk(request: InterruptRequest):
    """
    中断 AI 说话
    """
    session_id = str(request.sessionid)
    session = get_session(session_id)
    
    if not session:
        return {"code": 404, "message": "Session not found"}
    
    # 更新会话状态
    session.status = "interrupted"
    
    logger.info(f"[{session_id}] Talk interrupted")
    
    return {
        "code": 0,
        "message": "Talk interrupted"
    }


@router.get("/sessions")
async def list_sessions():
    """
    列出所有活跃会话
    """
    session_list = [
        {
            "session_id": sid,
            "status": session.status,
            "created_at": session.created_at
        }
        for sid, session in sessions.items()
    ]
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "sessions": session_list,
            "total": len(sessions)
        }
    }


@router.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    """
    关闭会话
    """
    if session_id in sessions:
        del sessions[session_id]
        
    if session_id in decoders:
        del decoders[session_id]
    
    logger.info(f"[{session_id}] Session closed")
    
    return {
        "code": 0,
        "message": "Session closed"
    }
