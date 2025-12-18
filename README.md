v.1.3 업데이트(251219): 영어 지원, sdxl 지원, LoRA 지원(1개 가능), 이 순간 기억하기 저장 추가, system prompt 수정 및 보강, LLM 상세 세팅 추가(temperature 등)
v.1.3 (251219): Added English support, SDXL support, single LoRA support, "Save This Moment" feature, improved system prompts, and advanced LLM settings (temperature, etc.).

v.1.2 업데이트(251214): 시나리오 탭 추가, 이미지 저장 추가, 시나리오 로딩 시 컨텍스트 및 장기기억 복원 기능 추가, 장기 메모리 요약 길이 확대
v.1.2 (251214): Added Scenario tab, image saving, context/long-term memory restoration for scenario loading, and increased long-term memory summary length.

v.1.1 업데이트: 환경 설정 창에서 vae,  text encoders 선택 가능 / 시작 후 이동된 대화 탭에서 입력 창 사라지는 문제 해결 등
v.1.1: Added VAE and Text Encoder selection in settings; fixed the issue where the input box disappeared in the chat tab after navigation.


----


🚀 ZEMS(Zeniji EMotion Simul): 심리 조각 시뮬레이터 안내

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

- 심리적 격변: 감정이 급격하게 변하는 '잭팟' 순간 (표정 변화)

- 관계 전환: 연인, Master/Slave 등 관계의 정의가 바뀔 때 (관계 바뀔 때의 변화)

- 환경 변화: 배경이나 의상이 변경될 때 (배경과 의상의 변화)

- 주기적 생성: 대화 흐름 유지를 위해 매 5턴마다 생성 (비슷하지만 다른 이미지지)

Images are generated in real-time during emotional surges, relationship shifts, changes in background/outfit, or every 5 turns to maintain immersion. .

.

💎 핵심 시스템 (Core Systems)

- 6가지 감정 축: 쾌락, 각성, 지배, 친밀, 신뢰, 의존의 조합이 인물의 성격과 말투를 결정합니다.

- 트라우마 시스템: 파국 이후 재시작 시에도 과거의 상처가 남아 신뢰 회복을 방해합니다.

- 12가지 뱃지: 통제광, 맹목적 숭배자 등 당신의 선택이 만든 극단적 결말을 확인하세요.

Six emotional axes determine personality and tone. The Trauma system ensures past scars hinder trust even after a reset. Explore 12 extreme archetypes(badges) like The Warden or The Cultist. .

.

💻 요구 사양 (System Requirements)

OpenRouter API + ComfyUI 사용 시: 일반적인 수준의 PC에서도 원활하게 실행 가능합니다.

OpenRouter 크레딧 결제 및 유료 모델 사용을 권장합니다. (토큰 소모가 적어 적은 금액으로도 사용가능합니다.)

로컬 LLM(Ollama) 직접 구동 시: VRAM 16GB / RAM 32GB 이상 권장.

With OpenRouter API, ZEMS runs smoothly on most PCs. We highly recommend using paid models via OpenRouter credits; it's cost-effective due to low token consumption. For local LLM (Ollama), 16GB+ VRAM and 32GB+ RAM are recommended

. 

❤️ 홈페이지: zeniji.love

🌐 커뮤니티: 아카라이브 Zeniji 채널 

☕ 후원: buymeacoffee.com/zeniji


"그/녀의 마음을 조각하세요. 단, 모든 상처는 영원히 남습니다." 

"Sculpt his/her mind. But every scar lasts forever."

