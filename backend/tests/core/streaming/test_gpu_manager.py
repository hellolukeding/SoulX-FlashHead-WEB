import pytest
from app.core.streaming.gpu_manager import GPUMemoryManager


@pytest.fixture
def manager():
    return GPUMemoryManager(max_sessions=5)


def test_can_allocate_session(manager):
    """测试可以分配新会话"""
    assert manager.can_allocate_session() is True


def test_allocate_session(manager):
    """测试分配会话"""
    session_id = "test_session_1"
    manager.allocate_session(session_id)

    assert session_id in manager.allocated_sessions


def test_max_sessions_limit(manager):
    """测试最大会话数限制"""
    # 分配 5 个会话
    for i in range(5):
        manager.allocate_session(f"session_{i}")

    # 第 6 个应该被拒绝
    assert manager.can_allocate_session() is False


def test_free_session(manager):
    """测试释放会话"""
    session_id = "test_session_1"
    manager.allocate_session(session_id)
    manager.free_session(session_id)

    assert session_id not in manager.allocated_sessions
