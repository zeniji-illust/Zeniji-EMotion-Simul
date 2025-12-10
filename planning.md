# 📂 PROJECT_PLAN.md: Zeniji v3.0 (Open Source Edition)

## 1. 프로젝트 개요 (Project Overview)
**Zeniji**는 로컬 LLM과 이미지 생성 AI를 활용한 **"연구용 연애 시뮬레이터"**입니다.
v3.0의 핵심은 **"ComfyUI 의존적 아키텍처"**입니다. 복잡한 이미지 생성 파이프라인을 Python에서 직접 구현하지 않고, 로컬에 실행된 **ComfyUI API**를 호출하여 해결합니다.

### 🎯 핵심 변경 사항
1.  **이미지 엔진:** Python `diffusers` 라이브러리 제거 → **ComfyUI API 연동**으로 변경.
2.  **LLM 업그레이드:** Qwen 2.5 3B → **Qwen 2.5 14B (GGUF/Int4)** 사용.
3.  **효율적 렌더링:** 매 턴 이미지를 생성하지 않음. **LLM이 "장면 변화가 필요하다"고 판단할 때만** ComfyUI를 호출함.
4.  **16GB VRAM 전략:** **"순차적 실행(Sequential Execution)"**. LLM과 ComfyUI가 VRAM을 교대로 사용함.

---

## 2. 시스템 아키텍처 (System Architecture)

### 🏗️ The Director (Python App)
* **역할:** 게임 로직, 대화 생성, 장면 연출 판단, UI(Gradio).
* **LLM:** Qwen 2.5 14B (4-bit/8-bit GGUF).
* **VRAM 관리:** 대화 생성 후, ComfyUI 호출이 필요하면 **LLM을 RAM(CPU)으로 내리거나 Unload**하여 VRAM을 확보함.

### 🎨 The Artist (ComfyUI Server)
* **역할:** 이미지 생성 전담.
* **주소:** `http://127.0.0.1:8188` (기본값)
* **워크플로우:** `Flux.1` 또는 `Zhitu` 기반의 API 포맷 JSON (`.json`) 사용.

---

## 3. 핵심 로직: "Scene Change Detection"

LLM은 단순 대화뿐만 아니라 **연출 감독(Director)** 역할을 수행해야 합니다.
매 턴마다 아래 JSON 포맷으로 응답을 생성해야 합니다.

### 🧠 System Prompt 핵심 요구사항
```json
{
  "thought": "캐릭터의 속마음 (Internal Monologue)",
  "speech": "캐릭터의 대사",
  "visual_change_detected": true, // 또는 false
  "visual_prompt": "영어 프롬프트 (Ex: standing in the rain, crying, dark alley, cinematic lighting)",
  "reason": "이미지 생성이 필요한 이유 (Ex: 장소가 학교에서 집으로 변경됨)",
  "choices": ["선택지1", "선택지2", "선택지3"]
}
🎬 이미지 생성 트리거 조건 (visual_change_detected: true)
장소 이동: (카페 → 공원)

의상/자세 변경: (교복 → 사복, 앉음 → 일어섬)

감정의 격변: (무표정 → 활짝 웃음, 우는 얼굴)

강제 갱신: 플레이어가 요청하거나 N턴 이상 이미지가 바뀌지 않았을 때.

4. VRAM 16GB 생존 전략 (The Memory Dance)
Qwen 14B(~10GB)와 Flux(~12GB)는 동시에 VRAM에 올라갈 수 없습니다. 따라서 Python 코드는 아래 순서를 엄격히 지켜야 합니다.

[Python] Qwen 14B 로드 (VRAM 점유)

[Python] 대화 생성 및 JSON 파싱

[Decision] visual_change_detected 확인

False: 기존 이미지 유지 -> 즉시 응답 (Fast Path)

True: 이미지 생성 필요 -> Slow Path 진입

[Slow Path]

a. Qwen 모델 Unload (또는 CPU로 이동). torch.cuda.empty_cache() 필수.

b. ComfyUI API 호출 (웹소켓으로 대기).

c. ComfyUI가 이미지 생성 후 반환.

d. Qwen 모델 다시 VRAM 로드.

5. 구현 단계 (Implementation Steps)
Phase 1: ComfyUI Client 모듈 (comfy_client.py)
websocket-client를 사용하여 ComfyUI 서버와 통신.

워크플로우 JSON 파일을 읽어와서 positive_prompt 부분만 수정하여 큐에 전송.

생성 완료 시 이미지 데이터를 받아오는 클래스 구현.

Phase 2: Intelligent Brain (brain.py)
llama-cpp-python 또는 transformers를 사용하여 Qwen 14B 로드.

JSON Output Parsing 기능 구현 (재시도 로직 포함).

Memory Manager: unload_model() 및 load_model() 메서드 구현.

Phase 3: Game Loop & UI (app.py)
Gradio 기반 UI 구성 (좌측 이미지, 우측 채팅/로그).

비동기 처리를 통해 이미지 생성 중에는 "Rendering..." 상태 표시.

세션별 상태 관리 (PAD 수치, 대화 히스토리).

6. 폴더 구조 (Directory Structure)
Plaintext

Zeniji_v3/
├── workflows/
│   └── flux_api_workflow.json    # ComfyUI에서 'Save (API Format)'으로 저장한 파일
├── scenarios/
│   └── character_setup.yaml      # 캐릭터 설정 (프롬프트, 말투 등)
├── src/
│   ├── comfy_client.py           # ComfyUI 통신
│   ├── brain.py                  # LLM 및 로직
│   ├── utils.py                  # 기타 유틸
│   └── memory_manager.py         # VRAM 관리
├── app.py                        # 메인 실행 (Gradio)
├── requirements.txt
└── README.md
7. 개발자 노트 (Developer Notes)
ComfyUI 의존성: 사용자는 반드시 ComfyUI를 켜둬야 함. (에러 처리 필수: "ComfyUI 연결 실패. 8188 포트를 확인하세요.")

확장성: 나중에 워크플로우 파일만 교체하면 실사/애니/일러스트 등 화풍 변경 가능.

Qwen 14B: GGUF 포맷을 사용하여 로컬 구동 최적화. (GPU Offload 비율 조절 가능하게 설정)