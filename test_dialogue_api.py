#!/usr/bin/env python3
"""
测试对话API接口
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """测试健康检查"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/../health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_offer():
    """测试WebRTC offer协商"""
    print("🔍 Testing /offer endpoint...")
    payload = {
        "sdp": "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0",
        "type": "offer"
    }
    response = requests.post(f"{BASE_URL}/offer", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    return response.json().get("sessionid")

def test_human_text(session_id):
    """测试文本消息"""
    print("🔍 Testing /human endpoint (text)...")
    payload = {
        "text": "你好，请介绍一下自己",
        "type": "chat",
        "sessionid": session_id or 1
    }
    response = requests.post(f"{BASE_URL}/human", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"User text: {data['data'].get('user_text')}")
        print(f"AI text: {data['data'].get('ai_text')[:100]}...")
        print(f"Audio data length: {len(data['data'].get('audio_data', ''))}")
    else:
        print(f"Response: {response.text}")
    print()

def test_is_speaking(session_id):
    """测试查询说话状态"""
    print("🔍 Testing /is_speaking endpoint...")
    payload = {
        "sessionid": session_id or 1
    }
    response = requests.post(f"{BASE_URL}/is_speaking", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_list_sessions():
    """测试列出会话"""
    print("🔍 Testing /sessions endpoint...")
    response = requests.get(f"{BASE_URL}/sessions")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("测试对话API接口")
    print("=" * 60)
    print()
    
    try:
        # 测试健康检查
        test_health()
        
        # 测试offer协商
        session_id = test_offer()
        
        # 测试文本消息
        test_human_text(session_id)
        
        # 测试说话状态
        test_is_speaking(session_id)
        
        # 测试列出会话
        test_list_sessions()
        
        print("=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
        print("请确保后端服务已启动: bash start.sh")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
