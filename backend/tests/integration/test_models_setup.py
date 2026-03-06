"""
模型配置验证脚本
"""
import os
import sys

def check_model_path(path: str, name: str) -> bool:
    """检查模型路径"""
    exists = os.path.exists(path)
    size = ""
    if exists and os.path.isdir(path):
        # 计算目录大小
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        # 转换为 GB
        size_gb = total_size / (1024**3)
        size = f"({size_gb:.1f} GB)"
    
    status = "✅" if exists else "❌"
    print(f"{status} {name}: {path} {size}")
    return exists

def main():
    print("=" * 60)
    print("模型路径验证")
    print("=" * 60)
    print()
    
    # 检查模型目录
    models_base = "/opt/digital-human-platform/models"
    print(f"模型基础目录: {models_base}")
    print(f"目录存在: {os.path.exists(models_base)}")
    print()
    
    # 检查各个模型
    results = {}
    
    results["soulx"] = check_model_path(
        "/opt/digital-human-platform/models/SoulX-FlashHead-1_3B",
        "SoulX-FlashHead-1_3B"
    )
    
    results["wav2vec"] = check_model_path(
        "/opt/digital-human-platform/models/wav2vec2-base-960h",
        "wav2vec2-base-960h"
    )
    
    results["cosyvoice"] = check_model_path(
        "/opt/digital-human-platform/models/CosyVoice",
        "CosyVoice"
    )
    
    print()
    print("=" * 60)
    print("验证总结")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(results.values())
    print()
    if all_passed:
        print("🎉 所有模型配置正确！")
        return 0
    else:
        print("❌ 部分模型配置有问题")
        return 1

if __name__ == "__main__":
    exit(main())
