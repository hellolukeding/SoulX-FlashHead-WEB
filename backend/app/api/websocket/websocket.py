"""
WebSocket 路由端点

方案 A：全链路异步流式 WebRTC 架构
- 目标延迟: < 250ms
- LLM 流式 → CosyVoice 流式切片 → SoulX 时空缓存 → WebRTC UDP
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from app.api.websocket.handler import manager, handler
from app.api.webrtc import streaming_endpoint  # ✅ 全链路异步流式架构
from app.api.webrtc import video_stream_webrtc  # 基础 WebRTC (备用)


router = APIRouter()

# ========== 方案 A：全链路异步流式架构（主路线） ==========
router.include_router(
    streaming_endpoint.router,
    prefix="/webrtc",
    tags=["webrtc_streaming"]
)

# ========== 备用：基础 WebRTC ==========
router.include_router(video_stream_webrtc.router, tags=["webrtc_basic"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket 端点

    Args:
        websocket: WebSocket 连接
        token: JWT Token（用于认证）
    """
    # 生成会话 ID
    import uuid
    session_id = str(uuid.uuid4())

    # 接受连接
    if not await manager.connect(websocket, session_id):
        await websocket.close(code=1008, reason="连接失败")
        return

    logger.info(f"🔗 WebSocket 连接建立: {session_id}")

    try:
        # 发送欢迎消息
        await manager.send_message(session_id, {
            "type": "connected",
            "data": {
                "session_id": session_id,
                "server_time": handler._get_timestamp()
            }
        })

        # 消息循环
        while True:
            # 接收消息
            data = await websocket.receive_json()

            # 处理消息
            await handler.handle_message(session_id, data)

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket 断开连接: {session_id}")
        manager.disconnect(session_id)

    except Exception as e:
        logger.error(f"❌ WebSocket 错误: {e}")
        await manager.send_message(session_id, {
            "type": "error",
            "data": {
                "code": 500,
                "message": str(e)
            }
        })
        manager.disconnect(session_id)


@router.get("/ws/sessions")
async def list_sessions():
    """
    列出所有活跃会话

    Returns:
        会话列表
    """
    return {
        "code": 0,
        "message": "success",
        "data": {
            "sessions": manager.list_sessions(),
            "total": len(manager.sessions)
        }
    }
