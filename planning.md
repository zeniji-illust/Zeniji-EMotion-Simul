

# 🚀 Zeniji Emotion Simul: 최종 통합 아키텍처 및 구현 계획

## 1. 프로젝트 개요 (The Zeniji Core)

Zeniji Emotion Simul은 **심리 시뮬레이션의 정밀성**과 **ComfyUI 기반의 VRAM 효율성**을 결합한 연구용 프로젝트입니다.

- **LLM 엔진:** Qwen 2.5 14B Q6-K GGUF 사용.
    
- **이미지 엔진:** 로컬 실행 ComfyUI API를 통한 이미지 생성 (Zhitu 워크플로우).
    
- **핵심 전략:** **Memory Dance**를 통한 16GB VRAM 극복 (LLM $\rightleftharpoons$ ComfyUI 교대 로드).
    

## 2. 시스템 아키텍처 (Module Map)

LLM의 연기와 Python의 로직이 분리된 **Director-Engine-Artist** 구조입니다.

|**모듈 이름 (파일)**|**페르소나**|**주요 기능**|
|---|---|---|
|**`app.py`**|🎮 Gradio UI|메인 실행. Gradio UI 구성, 비동기(Async) 루프 및 세션 상태 관리.|
|**`brain.py`**|🧠 The Director|**핵심 판단.** LLM 프롬프트 최종 조립, JSON 파싱, 이미지 생성 요청 판단, `memory_manager` 제어.|
|**`logic_engine.py`**|⚙️ The Engine|**게임 규칙 및 수치 관리.** PAD/ITD 6축 관리, 관성 적용, 가챠(Multiplier), 뱃지 조건 판정.|
|**`state_manager.py`**|📊 Data Model|`CharacterState` (6축 수치, 뱃지) 정의 및 데이터 업데이트 (관성/클램핑 적용).|
|**`comfy_client.py`**|🎨 The Artist|**ComfyUI 통신 전담.** 워크플로우 로드/수정, API 큐 전송, 이미지 수신.|
|**`memory_manager.py`**|💾 The Handler|**VRAM 교대 관리.** Qwen 모델의 `load`/`unload` 및 $torch.cuda.empty\_cache()$ 실행.|

## 3. 핵심 로직: 지능형 연출 및 델타 반영

### 3-1. LLM 출력 포맷 (Director's Instruction)

LLM은 **연기, 로직, 연출 지시**를 한 번의 호출로 모두 처리합니다.

JSON

```
{
  "thought": "캐릭터의 속마음",
  "speech": "캐릭터의 대사",
  "visual_change_detected": true, // 이미지 생성 요청 (true/false)
  "visual_prompt": "english tags based on expression/scene",
  "reason": "이미지 생성이 필요한 이유",
  "proposed_delta": {"P": 5, "I": 3, "T": -2} // Python Engine이 증폭할 기본 델타값 (Max 12 제한)
}
```

### 3-2. 이미지 생성 트리거 조건 (연출 판단)

`visual_change_detected: true`를 유발하는 조건:

- **장소/의상 변경** (팀플 $\rightarrow$ 카페).
    
- **감정의 격변** (수치 극한 돌파, $A \approx 100$ 또는 $P \approx 0$).
    
- **특수 뱃지 해금** (얀데레, Broken Doll 활성화 시).
    
- **강제 갱신** (N턴 이상 이미지 미갱신).
    

### 3-3. 심리 분석 보고서 (엔딩 시스템)

게임 종료 시, **LLM**은 **'분석가'** 역할로 전환되어 **최종 상태**와 **달성하지 못한 뱃지들의 요구 조건**을 비교하여 **실패 원인(Gap)**을 분석하고 **다음 전략**을 제시합니다.

## 4. VRAM 16GB 생존 전략 (Memory Dance)

LLM(Qwen 14B)과 ComfyUI가 VRAM을 교대하는 순차적 실행을 엄격히 준수합니다.

|**단계**|**주체 (Module)**|**상태 (VRAM Occupancy)**|**액션 및 설명**|
|---|---|---|---|
|**Fast Path (False)**|`app.py`|Qwen **로드 상태 유지**.|이미지 교체 없이 즉시 응답.|
|**Slow Path (True)**|`brain.py` $\rightarrow$ `comfy_client.py`|Qwen $\rightarrow$ **Unload**. ComfyUI **로드**|**VRAM 교대:** Qwen 언로드 후, $torch.cuda.empty\_cache()$ 실행, ComfyUI 호출.|

## 5. 최종 구현 단계 (Optimized for Efficiency)

디버깅 효율성을 극대화하기 위해, 복잡한 하드웨어 의존성 로직을 가장 나중에 구현합니다.

|**Phase**|**목표**|**구현 내용**|
|---|---|---|
|**Phase 1**|**Text-Only CLI MVP**|`logic_engine.py`와 `brain.py`로 6축 수치 변화, 가챠, 뱃지 판정 등 **핵심 게임 밸런스**를 CLI 환경에서 확정.|
|**Phase 2**|**Gradio UI 적용**|`app.py`로 Gradio UI 구성. 채팅 및 **수치(PAD/ITD) 출력 UI** 구현.|
|**Phase 3**|**Comfy API Client 검증**|`comfy_client.py`로 ComfyUI API 통신 성공 검증. 워크플로우 수정 후 이미지 수신 확인.|
|**Phase 4**|**Memory Manager 통합**|`memory_manager.py`로 Qwen 로드/언로드 및 VRAM 교대 로직 구현. 모든 모듈 통합하여 최종 앱 완성.|