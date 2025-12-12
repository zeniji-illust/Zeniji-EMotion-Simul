"""
설정 및 모델 로드 테스트 스크립트
"""

import sys
from pathlib import Path

print("=" * 60)
print("Zeniji Emotion Simul - Setup Test")
print("=" * 60)

# 1. Python 버전 확인
print(f"\n1. Python 버전: {sys.version}")

# 2. 필수 패키지 확인
print("\n2. 필수 패키지 확인:")
packages = {
    "gradio": "Gradio UI",
    "llama_cpp": "llama-cpp-python",
    "websocket": "websocket-client"
}

for package, desc in packages.items():
    try:
        if package == "llama_cpp":
            import llama_cpp
            print(f"  ✓ {desc}: 설치됨")
        elif package == "websocket":
            import websocket
            print(f"  ✓ {desc}: 설치됨")
        else:
            __import__(package)
            print(f"  ✓ {desc}: 설치됨")
    except ImportError:
        print(f"  ✗ {desc}: 설치되지 않음")

# 3. 모델 파일 확인
print("\n3. 모델 파일 확인:")
model_path = Path("models/qwen2.5-14b-instruct-q6_k.gguf")
if model_path.exists():
    size_gb = model_path.stat().st_size / (1024 ** 3)
    print(f"  ✓ 모델 파일 존재: {model_path}")
    print(f"    크기: {size_gb:.2f} GB")
else:
    print(f"  ✗ 모델 파일 없음: {model_path}")
    print(f"    경로 확인: {model_path.absolute()}")

# 4. 설정 파일 확인
print("\n4. 설정 파일 확인:")
try:
    import config
    print(f"  ✓ config.py 로드 성공")
    print(f"    모델 경로: {config.LLM_CONFIG['model_path']}")
except Exception as e:
    print(f"  ✗ config.py 로드 실패: {e}")

# 5. 모듈 import 테스트
print("\n5. 모듈 import 테스트:")
modules = ["state_manager", "logic_engine", "memory_manager", "brain"]
for module in modules:
    try:
        __import__(module)
        print(f"  ✓ {module}.py")
    except Exception as e:
        print(f"  ✗ {module}.py: {e}")

# 6. 모델 로드 테스트 (선택적)
print("\n6. 모델 로드 테스트:")
try:
    from memory_manager import MemoryManager
    mm = MemoryManager()
    model = mm.load_model()
    if model:
        print("  ✓ 모델 로드 성공")
    else:
        print("  ✗ 모델 로드 실패 (위의 에러 로그 확인)")
except Exception as e:
    print(f"  ✗ 모델 로드 테스트 실패: {e}")

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)

