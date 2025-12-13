🚀 ZEMS(Zeniji EMotion Simul): 심리 조각 시뮬레이터 안내

.

** 현재는 한국어(Korean)만 지원합니다.**

Currently, only Korean is supported.

.

ZEMS는 단순한 챗봇이 아닌, 6가지 감정 축을 통해 인물의 내면을 조각하는 **심리 조각 시뮬레이터(Psychological Sculpting Simulator)**입니다. 당신의 선택은 실시간 감정 변화를 일으키며, 인물은 당신이 남긴 모든 상처와 흔적을 기억합니다.

ZEMS is a Psychological Sculpting Simulator where you shape characters through six emotional axes. Your choices cause real-time emotional shifts, and characters remember every scar and trace you leave behind. .

.

📥 설치 및 실행 단계 (Installation & Setup)

- 프로젝트 다운로드: git clone https://github.com/zeniji-illust/Zeniji-EMotion-Simul

- 의존성 설치: 폴더 내 install.bat 실행 (Python 3.11.0 최적화)

- 두뇌(LLM) 설정: OpenRouter API 연동 권장 (Ollama 로컬 구동보다 가볍고 빠릅니다.)

- 로컬 Ollama 사용 시: start_ollama_serve.bat 실행 후 전용 모델 다운로드 필요

- 이미지 생성: ComfyUI 실행 (기본 포트 8000 설정 확인)

- 실행: start.bat 실행

Clone the repo and run install.bat. We recommend using the OpenRouter API for a lighter experience. If using local Ollama, run start_ollama_serve.bat first. Ensure ComfyUI is running on port 8000 before launching start.bat. .

.

🛠️ 실행 모드 및 관리 (Maintenance & Dev Mode)

update.bat: git pull 후 새로운 의존성까지 자동으로 체크하여 업데이트합니다.

dev_mode.bat: 개발자용 모드로, 시스템 로그를 상세히 확인하며 실행할 수 있습니다.

Use update.bat to pull the latest changes and check dependencies. Run dev_mode.bat to access detailed system logs for debugging. .

.

🎨 비주얼 생성 (Visual Triggers)

ZEMS는 텍스트를 넘어 실시간 이미지 생성을 통해 몰입감을 제공합니다. 다음 상황에서 이미지가 자동 생성됩니다:

- 심리적 격변: 감정이 급격하게 변하는 '잭팟' 순간

- 관계 전환: 연인, Master/Slave 등 관계의 정의가 바뀔 때

- 환경 변화: 배경이나 의상이 변경될 때

- 주기적 생성: 대화 흐름 유지를 위해 매 5턴마다 생성

Images are generated in real-time during emotional surges, relationship shifts, changes in background/outfit, or every 5 turns to maintain immersion. .

.

💎 핵심 시스템 (Core Systems)

- 6가지 감정 축: 쾌락, 각성, 지배, 친밀, 신뢰, 의존의 조합이 인물의 성격과 말투를 결정합니다.

- 트라우마 시스템: 파국 이후 재시작 시에도 과거의 상처가 남아 신뢰 회복을 방해합니다.

- 12가지 아키타입: 통제광, 맹목적 숭배자 등 당신의 선택이 만든 극단적 결말을 확인하세요.

Six emotional axes determine personality and tone. The Trauma system ensures past scars hinder trust even after a reset. Explore 12 extreme archetypes like The Warden or The Cultist. .

.

💻 요구 사양 (System Requirements)

OpenRouter API + ComfyUI 사용 시: 일반적인 수준의 PC에서도 원활하게 실행 가능합니다.

OpenRouter 크레딧 결제 및 유료 모델 사용을 권장합니다. (토큰 소모가 적어 적은 금액으로도 사용가능합니다.)

로컬 LLM(Ollama) 직접 구동 시: VRAM 16GB / RAM 32GB 이상 권장.

With OpenRouter API, ZEMS runs smoothly on most PCs. We highly recommend using paid models via OpenRouter credits; it's cost-effective due to low token consumption. For local LLM (Ollama), 16GB+ VRAM and 32GB+ RAM are recommended

. 

🌐 커뮤니티: 아카라이브 Zeniji 채널 

"그녀의 마음을 조각하세요. 단, 모든 상처는 영원히 남습니다." 

"Sculpt her mind. But every scar lasts forever."
