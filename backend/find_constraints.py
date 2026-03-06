#!/usr/bin/env python3
"""Find video_length values that satisfy SoulX-FlashHead constraints"""

print("=" * 60)
print("SoulX-FlashHead 约束搜索")
print("=" * 60)

# Test all possible video_length values to find which satisfy constraints
print("\n搜索满足以下约束的 video_length:")
print("1. (video_length - 1) % 4 == 0  (rearrange)")
print("2. video_length % 36 == 0  (model internal)")

solutions = []
for L in range(1, 1000):
    cond1 = (L - 1) % 4 == 0
    cond2 = L % 36 == 0
    if cond1 and cond2:
        solutions.append(L)

if solutions:
    print(f"\n找到 {len(solutions)} 个解:")
    for L in solutions[:10]:  # Show first 10
        audio_samples = L * 16000 // 25
        audio_seconds = audio_samples / 16000
        print(f"  L={L:4d} → audio={audio_samples:7d} samples ({audio_seconds:5.2f}s)")
else:
    print("\n❌ 没有找到同时满足两个约束的解！")
    print("\n这意味着这两个约束是矛盾的！")

    # Analyze why
    print("\n分析:")
    print("- 如果 L % 36 == 0，则 L 是 36 的倍数")
    print("- 36 是 4 的倍数，所以 L % 4 == 0")
    print("- 但我们需要 (L - 1) % 4 == 0，即 L % 4 == 1")
    print("- 0 ≠ 1 (mod 4)，所以没有解！")

    print("\n可能的解释:")
    print("1. 约束理解有误")
    print("2. 模型在不同阶段使用不同的约束")
    print("3. 需要查看实际源码来理解真正的约束")

# Let me also search for values that satisfy just one constraint
print("\n" + "=" * 60)
print("只满足 rearrange 约束的值 (L-1) % 4 == 0:")
rearrange_solutions = []
for L in range(200, 800, 4):
    if (L - 1) % 4 == 0:
        audio_samples = L * 16000 // 25
        audio_seconds = audio_samples / 16000
        rearrange_solutions.append((L, audio_samples, audio_seconds))

print(f"找到 {len(rearrange_solutions)} 个解，前5个:")
for L, audio_samples, audio_seconds in rearrange_solutions[:5]:
    print(f"  L={L} → audio={audio_samples} samples ({audio_seconds:.2f}s), L%36={L%36}")

print("\n" + "=" * 60)
print("只满足模型约束的值 L % 36 == 0:")
model_solutions = []
for L in range(200, 800, 36):
    if L % 36 == 0:
        audio_samples = L * 16000 // 25
        audio_seconds = audio_samples / 16000
        model_solutions.append((L, audio_samples, audio_seconds))

print(f"找到 {len(model_solutions)} 个解，前5个:")
for L, audio_samples, audio_seconds in model_solutions[:5]:
    print(f"  L={L} → audio={audio_samples} samples ({audio_seconds:.2f}s), (L-1)%4={(L-1)%4}")

print("\n" + "=" * 60)
