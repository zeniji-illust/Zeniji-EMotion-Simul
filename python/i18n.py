"""
Zeniji Emotion Simul - Internationalization (i18n)
다국어 지원 모듈
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger("I18n")

# 지원 언어 목록
SUPPORTED_LANGUAGES = {"en", "kr"}

# 번역 딕셔너리
TRANSLATIONS = {
        "ui": {
            "action_title": {
                "en": "🎭 Action",
                "kr": "🎭 행동",
            },
            "age": {
                "en": "Age",
                "kr": "나이",
            },
            "appearance": {
                "en": "Appearance Description (English tags)",
                "kr": "외모 묘사 (영어 태그 형식)",
            },
            "appearance_info": {
                "en": "Enter in English tags for image generation (comma-separated)",
                "kr": "이미지 생성용 영어 태그로 입력하세요 (쉼표로 구분)",
            },
            "appearance_placeholder": {
                "en": "e.g., korean beauty, short hair, brown eyes, cute face, casual outfit",
                "kr": "예: korean beauty, short hair, brown eyes, cute face, casual outfit",
            },
            "arousal": {
                "en": "A (Arousal) - Arousal",
                "kr": "A (Arousal) - 각성",
            },
            "arousal_info": {
                "en": "Tension/Energy",
                "kr": "긴장감/에너지",
            },
            "btn_change_language": {
                "en": "Change Language",
                "kr": "언어 변경",
            },
            "btn_load": {
                "en": "📂 Load",
                "kr": "📂 불러오기",
            },
            "btn_reload": {
                "en": "🔄 Refresh",
                "kr": "🔄 새로고침",
            },
            "btn_retry_image": {
                "en": "🔄 Retry Image",
                "kr": "🔄 이미지 재시도",
            },
            "btn_save": {
                "en": "💾 Save",
                "kr": "💾 저장",
            },
            "btn_save_image": {
                "en": "💾 Save Image",
                "kr": "💾 이미지 저장",
            },
            "btn_save_comfyui": {
                "en": "💾 Save ComfyUI Settings",
                "kr": "💾 ComfyUI 설정 저장",
            },
            "btn_save_scenario": {
                "en": "💾 Save Scenario",
                "kr": "💾 시나리오 저장",
            },
            "btn_save_settings": {
                "en": "💾 Save Settings",
                "kr": "💾 설정 저장",
            },
            "btn_send": {
                "en": "Send",
                "kr": "전송",
            },
            "btn_start": {
                "en": "🚀 Start",
                "kr": "🚀 시작",
            },
            "character_file": {
                "en": "Character File",
                "kr": "캐릭터 파일",
            },
            "character_file_info": {
                "en": "Select saved character configuration file",
                "kr": "저장된 캐릭터 설정 파일 선택",
            },
            "character_image_label": {
                "en": "Character",
                "kr": "캐릭터",
            },
            "character_settings": {
                "en": "👥 Character Settings",
                "kr": "👥 상대방 설정",
            },
            "chat_label": {
                "en": "Chat",
                "kr": "대화",
            },
            "comfyui_cfg": {
                "en": "CFG Scale (Prompt Strength)",
                "kr": "CFG Scale (프롬프트 강도)",
            },
            "comfyui_cfg_info": {
                "en": "Prompt adherence (default: 1)",
                "kr": "프롬프트 준수도 (기본값: 1)",
            },
            "comfyui_clip": {
                "en": "CLIP Name",
                "kr": "CLIP 이름",
            },
            "comfyui_clip_info": {
                "en": "CLIP file name to use in ComfyUI (with extension)",
                "kr": "ComfyUI에서 사용할 CLIP 파일 이름 (확장자 포함)",
            },
            "comfyui_clip_placeholder": {
                "en": "e.g., zImage_textEncoder.safetensors",
                "kr": "예: zImage_textEncoder.safetensors",
            },
            "comfyui_model": {
                "en": "ComfyUI Model Name",
                "kr": "ComfyUI 모델 이름",
            },
            "comfyui_model_info": {
                "en": "Model file name to use in ComfyUI (with extension)",
                "kr": "ComfyUI에서 사용할 모델 파일 이름 (확장자 포함)",
            },
            "comfyui_model_placeholder": {
                "en": "e.g., Zeniji_mix_ZiT_v1.safetensors",
                "kr": "예: Zeniji_mix_ZiT_v1.safetensors",
            },
            "comfyui_port": {
                "en": "ComfyUI Server Port",
                "kr": "ComfyUI 서버 포트",
            },
            "comfyui_port_info": {
                "en": "Port number where ComfyUI server is running (default: 8000)",
                "kr": "ComfyUI 서버가 실행 중인 포트 번호 (기본값: 8000)",
            },
            "comfyui_sampler": {
                "en": "Sampler",
                "kr": "Sampler (샘플러)",
            },
            "comfyui_sampler_info": {
                "en": "Image generation sampler name (default: euler)",
                "kr": "이미지 생성 샘플러 이름 (기본값: euler)",
            },
            "comfyui_sampler_placeholder": {
                "en": "e.g., euler",
                "kr": "예: euler",
            },
            "comfyui_scheduler": {
                "en": "Scheduler",
                "kr": "Scheduler (스케줄러)",
            },
            "comfyui_scheduler_info": {
                "en": "Scheduler type (default: simple)",
                "kr": "스케줄러 타입 (기본값: simple)",
            },
            "comfyui_scheduler_placeholder": {
                "en": "e.g., simple",
                "kr": "예: simple",
            },
            "comfyui_steps": {
                "en": "Steps (Generation Steps)",
                "kr": "Steps (생성 단계 수)",
            },
            "comfyui_steps_info": {
                "en": "Number of image generation steps (default: 9)",
                "kr": "이미지 생성 단계 수 (기본값: 9)",
            },
            "comfyui_vae": {
                "en": "VAE Name",
                "kr": "VAE 이름",
            },
            "comfyui_vae_info": {
                "en": "VAE file name to use in ComfyUI (with extension)",
                "kr": "ComfyUI에서 사용할 VAE 파일 이름 (확장자 포함)",
            },
            "comfyui_vae_placeholder": {
                "en": "e.g., zImage_vae.safetensors",
                "kr": "예: zImage_vae.safetensors",
            },
            "comfyui_workflow": {
                "en": "Workflow File",
                "kr": "워크플로우 파일",
            },
            "comfyui_workflow_info": {
                "en": "Select workflow file from workflows folder",
                "kr": "workflows 폴더에서 사용할 워크플로우 파일 선택",
            },
            "dependency": {
                "en": "Dep (Dependency) - Dependency",
                "kr": "Dep (Dependency) - 의존",
            },
            "dependency_info": {
                "en": "Dependency/Obsession level",
                "kr": "의존/집착도",
            },
            "dominance": {
                "en": "D (Dominance) - Dominance",
                "kr": "D (Dominance) - 지배",
            },
            "dominance_info": {
                "en": "Initiative in relationship",
                "kr": "관계의 주도권",
            },
            "female": {
                "en": "Female",
                "kr": "여성",
            },
            "gender": {
                "en": "Gender",
                "kr": "성별",
            },
            "initial_background": {
                "en": "Background (English)",
                "kr": "배경 (영어)",
            },
            "initial_background_info": {
                "en": "Background description for image generation (English)",
                "kr": "이미지 생성용 배경 설명 (영어)",
            },
            "initial_background_placeholder": {
                "en": "college library table, evening light",
                "kr": "college library table, evening light",
            },
            "initial_context": {
                "en": "Initial Situation Description",
                "kr": "초기 상황 설명",
            },
            "initial_context_placeholder": {
                "en": "Describe the background situation where the conversation begins.",
                "kr": "대화가 시작되는 배경 상황을 설명하세요.",
            },
            "initial_situation": {
                "en": "📖 Initial Situation",
                "kr": "📖 초기 상황",
            },
            "input_label": {
                "en": "Input",
                "kr": "입력",
            },
            "input_placeholder": {
                "en": "Type your message...",
                "kr": "말을 입력하세요...",
            },
            "intimacy": {
                "en": "I (Intimacy) - Intimacy",
                "kr": "I (Intimacy) - 친밀",
            },
            "intimacy_info": {
                "en": "Emotional intimacy",
                "kr": "정서적 친밀감",
            },
            "language_info": {
                "en": "Select application language",
                "kr": "애플리케이션 언어 선택",
            },
            "language_label": {
                "en": "Language",
                "kr": "언어",
            },
            "language_settings": {
                "en": "🌐 Language Settings",
                "kr": "🌐 언어 설정",
            },
            "llm_provider": {
                "en": "LLM Provider",
                "kr": "LLM Provider",
            },
            "llm_provider_info": {
                "en": "Select LLM service to use",
                "kr": "사용할 LLM 서비스 선택",
            },
            "male": {
                "en": "Male",
                "kr": "남성",
            },
            "msg_comfyui_not_initialized": {
                "en": "⚠️ ComfyUI client not initialized.",
                "kr": "⚠️ ComfyUI 클라이언트가 초기화되지 않았습니다.",
            },
            "msg_comfyui_save_failed": {
                "en": "❌ ComfyUI settings save failed",
                "kr": "❌ ComfyUI 설정 저장 실패",
            },
            "msg_comfyui_save_success": {
                "en": "✅ ComfyUI settings saved successfully! (Will apply on next image generation)",
                "kr": "✅ ComfyUI 설정 저장 완료! (다음 이미지 생성 시 적용됩니다)",
            },
            "msg_config_apply_failed": {
                "en": "❌ Config apply failed: {error}",
                "kr": "❌ 설정 적용 실패: {error}",
            },
            "msg_file_exists": {
                "en": "⚠️ Warning: '{filename}' file already exists. Check 'Allow Overwrite' or use a different filename.",
                "kr": "⚠️ 경고: '{filename}' 파일이 이미 존재합니다. '덮어쓰기 허용'을 체크하거나 다른 파일명을 사용해주세요.",
            },
            "msg_file_not_selected": {
                "en": "⚠️ Please select a file.",
                "kr": "⚠️ 파일을 선택해주세요.",
            },
            "msg_filename_required": {
                "en": "⚠️ Please enter a filename.",
                "kr": "⚠️ 파일명을 입력해주세요.",
            },
            "msg_first_dialogue_failed": {
                "en": "✅ Config saved, but first dialogue generation failed: {error}",
                "kr": "✅ 설정 저장 완료, 하지만 첫 대화 생성 실패: {error}",
            },
            "msg_first_dialogue_input": {
                "en": "Start conversation",
                "kr": "대화 시작",
            },
            "msg_game_not_started": {
                "en": "⚠️ Game has not started.",
                "kr": "⚠️ 게임이 시작되지 않았습니다.",
            },
            "msg_load_failed": {
                "en": "❌ Load failed: {error}",
                "kr": "❌ 불러오기 실패: {error}",
            },
            "msg_load_success": {
                "en": "✅ {filename} loaded successfully!",
                "kr": "✅ {filename} 불러오기 완료!",
            },
            "msg_model_already_loaded": {
                "en": "Model is already loaded.",
                "kr": "모델이 이미 로드되어 있습니다.",
            },
            "msg_model_load_failed": {
                "en": "❌ Model load failed: {error}",
                "kr": "❌ 모델 로드 실패: {error}",
            },
            "msg_no_conversation": {
                "en": "⚠️ Scenario '{scenario}' has no conversation content.",
                "kr": "⚠️ 시나리오 '{scenario}'에 대화 내용이 없습니다.",
            },
            "msg_no_conversation_to_save": {
                "en": "⚠️ No conversation content to save. Please start a conversation first.",
                "kr": "⚠️ 저장할 대화 내용이 없습니다. 대화를 먼저 시작해주세요.",
            },
            "msg_no_visual_prompt": {
                "en": "⚠️ No saved visual_prompt available.",
                "kr": "⚠️ 저장된 visual_prompt가 없습니다.",
            },
            "msg_retry_failed": {
                "en": "❌ Image regeneration failed.",
                "kr": "❌ 이미지 재생성에 실패했습니다.",
            },
            "msg_retry_no_info": {
                "en": "⚠️ No image generation info available for retry.",
                "kr": "⚠️ 재생성할 이미지 정보가 없습니다.",
            },
            "msg_retry_success": {
                "en": "✅ Image regenerated successfully.",
                "kr": "✅ 이미지가 재생성되었습니다.",
            },
            "msg_save_failed": {
                "en": "❌ Save failed",
                "kr": "❌ 저장 실패",
            },
            "msg_save_success": {
                "en": "✅ {filename} saved successfully! (character_config.json also updated)",
                "kr": "✅ {filename} 저장 완료! (character_config.json도 업데이트됨)",
            },
            "msg_scenario_load_failed": {
                "en": "⚠️ Could not load scenario '{scenario}'.",
                "kr": "⚠️ 시나리오 '{scenario}'를 불러올 수 없습니다.",
            },
            "msg_scenario_not_selected": {
                "en": "⚠️ Please select a scenario.",
                "kr": "⚠️ 시나리오를 선택해주세요.",
            },
            "msg_scenario_save_failed": {
                "en": "❌ Scenario save failed",
                "kr": "❌ 시나리오 저장 실패",
            },
            "msg_scenario_save_name_required": {
                "en": "⚠️ Please enter scenario name.",
                "kr": "⚠️ 시나리오 이름을 입력해주세요.",
            },
            "msg_scenario_save_success": {
                "en": "✅ {name}.json saved successfully! (Check in Scenarios tab.)",
                "kr": "✅ {name}.json 저장 완료! (시나리오 탭에서 확인하세요.)",
            },
            "msg_settings_save_failed": {
                "en": "❌ Settings save failed{error}",
                "kr": "❌ 설정 저장 실패{error}",
            },
            "msg_settings_save_success": {
                "en": "✅ Settings saved successfully!",
                "kr": "✅ 설정 저장 완료!",
            },
            "msg_openrouter_api_key_save_failed": {
                "en": "❌ OpenRouter API key save failed",
                "kr": "❌ OpenRouter API 키 저장 실패",
            },
            "msg_openrouter_fallback_failed": {
                "en": "⚠️ OpenRouter connection failed, tried Ollama fallback but Ollama also failed",
                "kr": "⚠️ OpenRouter 연결 실패, Ollama로 폴백 시도했으나 Ollama도 연결 실패했습니다.",
            },
            "msg_openrouter_fallback_success": {
                "en": "⚠️ OpenRouter connection failed, fallback to Ollama and settings saved",
                "kr": "⚠️ OpenRouter 연결 실패, Ollama로 폴백하여 설정 저장 완료.",
            },
            "msg_settings_saved_with_provider": {
                "en": "✅ Settings saved successfully! ({provider} connection successful)",
                "kr": "✅ 설정 저장 완료! ({provider} 연결 성공)",
            },
            "msg_settings_saved_but_connection_failed": {
                "en": "⚠️ Settings saved, but {provider} connection failed",
                "kr": "⚠️ 설정 저장 완료, 하지만 {provider} 연결 실패",
            },
            "msg_settings_saved_next_start": {
                "en": "✅ Settings saved successfully! (Will be applied on next start)",
                "kr": "✅ 설정 저장 완료! (다음 시작 시 적용됩니다)",
            },
            "msg_settings_saved_reconnect_failed": {
                "en": "✅ Settings saved, but model reconnection failed: {error}",
                "kr": "✅ 설정 저장 완료, 하지만 모델 재연결 실패: {error}",
            },
            "msg_comfyui_settings_saved": {
                "en": "✅ ComfyUI settings saved successfully! (Will be applied on next image generation)",
                "kr": "✅ ComfyUI 설정 저장 완료! (다음 이미지 생성 시 적용됩니다)",
            },
            "msg_comfyui_settings_saved_reconnect_failed": {
                "en": "✅ ComfyUI settings saved, but client reconnection failed: {error}",
                "kr": "✅ ComfyUI 설정 저장 완료, 하지만 클라이언트 재연결 실패: {error}",
            },
            "msg_comfyui_settings_save_failed": {
                "en": "❌ ComfyUI settings save failed{error}",
                "kr": "❌ ComfyUI 설정 저장 실패{error}",
            },
            "msg_setup_complete": {
                "en": "✅ Setup saved and first dialogue generated!",
                "kr": "✅ 설정 저장 및 첫 대화 생성 완료!",
            },
            "name": {
                "en": "Name",
                "kr": "이름",
            },
            "no_image": {
                "en": "No Image",
                "kr": "이미지 없음",
            },
            "ollama_model": {
                "en": "Ollama Model Name",
                "kr": "Ollama 모델 이름",
            },
            "ollama_model_info": {
                "en": "Enter exact model name from 'ollama list' command",
                "kr": "'ollama list' 명령으로 확인한 정확한 모델 이름을 입력하세요",
            },
            "ollama_model_placeholder": {
                "en": "e.g., kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
                "kr": "예: kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
            },
            "openrouter_api_key": {
                "en": "OpenRouter API Key",
                "kr": "OpenRouter API 키",
            },
            "openrouter_api_key_info": {
                "en": "Enter OpenRouter API key (https://openrouter.ai/keys)",
                "kr": "OpenRouter API 키를 입력하세요 (https://openrouter.ai/keys)",
            },
            "openrouter_api_key_placeholder": {
                "en": "sk-or-v1-...",
                "kr": "sk-or-v1-...",
            },
            "openrouter_model": {
                "en": "OpenRouter Model",
                "kr": "OpenRouter 모델",
            },
            "openrouter_model_info": {
                "en": "Model name to use on OpenRouter",
                "kr": "OpenRouter에서 사용할 모델 이름",
            },
            "openrouter_model_placeholder": {
                "en": "e.g., cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                "kr": "예: cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            },
            "other": {
                "en": "Other",
                "kr": "기타",
            },
            "overwrite_allow": {
                "en": "Allow Overwrite",
                "kr": "덮어쓰기 허용",
            },
            "overwrite_info": {
                "en": "Allow overwriting when same filename exists",
                "kr": "같은 파일명이 있을 때 덮어쓰기 허용",
            },
            "personality": {
                "en": "Personality Description",
                "kr": "성격 묘사",
            },
            "personality_placeholder": {
                "en": "e.g., bright and cheerful but shy in front of people they like",
                "kr": "예: 밝고 활발하지만 좋아하는 사람 앞에서는 수줍음이 많음",
            },
            "appearance_and_personality_section": {
                "en": "### 📝 Appearance & Personality",
                "kr": "### 📝 외모 및 성격",
            },
            "player_settings": {
                "en": "👤 Player Settings",
                "kr": "👤 주인공 설정",
            },
            "pleasure": {
                "en": "P (Pleasure) - Pleasure",
                "kr": "P (Pleasure) - 쾌락",
            },
            "pleasure_info": {
                "en": "Positive/Negative of relationship",
                "kr": "관계의 긍정/부정",
            },
            "presets": {
                "en": "🎭 Presets",
                "kr": "🎭 프리셋",
            },
            "save_filename": {
                "en": "Save Filename",
                "kr": "저장할 파일명",
            },
            "save_filename_info": {
                "en": "Enter filename only (extension auto-added)",
                "kr": "파일명만 입력 (확장자 자동 추가)",
            },
            "save_filename_placeholder": {
                "en": "e.g., my_character",
                "kr": "예: my_character",
            },
            "scenario_label": {
                "en": "Scenarios",
                "kr": "시나리오",
            },
            "scenario_save": {
                "en": "Save Scenario",
                "kr": "시나리오 저장",
            },
            "scenario_save_info": {
                "en": "Save current conversation as scenario",
                "kr": "현재 대화를 시나리오로 저장",
            },
            "scenario_save_label": {
                "en": "Save Scenario",
                "kr": "시나리오 저장",
            },
            "scenario_save_placeholder": {
                "en": "e.g., my_scenario",
                "kr": "예: my_scenario",
            },
            "scenario_title": {
                "en": "Scenario Selection",
                "kr": "시나리오 선택",
            },
            "settings_comfyui_title": {
                "en": "ComfyUI Settings",
                "kr": "ComfyUI 설정",
            },
            "settings_llm_title": {
                "en": "LLM Settings",
                "kr": "LLM 설정",
            },
            "setup_title": {
                "en": "Character & Scenario Initial Setup",
                "kr": "캐릭터 및 시나리오 초기 설정",
            },
            "stats_chart_label": {
                "en": "6-Axis Values",
                "kr": "6축 수치",
            },
            "stats_detail_label": {
                "en": "Status Details",
                "kr": "상태 상세",
            },
            "stats_info": {
                "en": "Each value is between 0-100, initial values are limited to **maximum 70**.",
                "kr": "각 수치는 0~100 사이이며, 초기값은 **최대 70**으로 제한됩니다.",
            },
            "stats_title": {
                "en": "Psychological Indicators (6-Axis System)",
                "kr": "📊 심리 지표 설정 (6축 시스템)",
            },
            "tab_chat": {
                "en": "💬 Chat",
                "kr": "💬 대화",
            },
            "tab_scenario": {
                "en": "📚 Scenarios",
                "kr": "📚 시나리오",
            },
            "tab_settings": {
                "en": "⚙️ Settings",
                "kr": "⚙️ 환경설정",
            },
            "tab_setup": {
                "en": "⚙️ Initial Setup",
                "kr": "⚙️ 초기 설정",
            },
            "thought_title": {
                "en": "💭 View Thoughts",
                "kr": "💭 속마음 보기",
            },
            "trust": {
                "en": "T (Trust) - Trust",
                "kr": "T (Trust) - 신뢰",
            },
            "trust_info": {
                "en": "Trust level",
                "kr": "신뢰도",
            },
        },
        "prompts": {
            "background_consistency_1": {
                "en": "4. **Background Consistency (`background`)**:",
                "kr": "4. **배경 일관성 (`background`)**:",
            },
            "background_consistency_2": {
                "en": "    - **Current Background**: {current_background}",
                "kr": "    - **현재 배경**: {current_background}",
            },
            "background_consistency_3": {
                "en": "    - Unless {player_name}'s input explicitly mentions location movement or background change, **you must maintain the previous background**.",
                "kr": "    - {player_name}님의 입력에서 명시적으로 장소 이동이나 배경 변화가 언급되지 않는 한, **반드시 이전 배경을 유지**하세요.",
            },
            "background_consistency_4": {
                "en": "    - Only change background when there are explicit movement instructions like \"let's go to the cafe\" / \"let's go home\" / \"let's go to school\".",
                "kr": "    - 예: \"카페로 가자\" / \"집에 가자\" / \"학교로 가자\" 같은 명시적 이동 지시가 있을 때만 배경을 변경하세요.",
            },
            "background_consistency_5": {
                "en": "    - Write background in English, including specific location and environment descriptions. (e.g., \"college library table, evening light\", \"coffee shop interior, warm lighting, wooden table\")",
                "kr": "    - 배경은 영어로 작성하며, 구체적인 장소와 환경 묘사를 포함하세요. (예: \"college library table, evening light\", \"coffee shop interior, warm lighting, wooden table\")",
            },
            "behavior_priority_1": {
                "en": "1. **Reaction Priority**: To {player_name}'s compliments or physical contact, prioritize **emotional reactions (embarrassment, excitement)** over the current situation.",
                "kr": "1. **반응 우선순위**: {player_name}님의 칭찬이나 스킨십 등의 행동에, 현재 상황보다 **감정적 반응(부끄러움, 설렘)**을 최우선으로 표현합니다.",
            },
            "behavior_priority_2": {
                "en": "2. **Indirect Action Description**: When receiving physical instructions (e.g., 'hug me', 'kneel down'), replace direct action descriptions with **acceptance through `speech`** and **physical reactions in `action_speech`**.",
                "kr": "2. **간접 행동 묘사**: 물리적 지시(예: '안아줘', '무릎 꿇어')를 받으면, 직접적인 행동 묘사 대신 **`speech`를 통한 수용**과 **`action_speech`의 신체적 반응**으로 대체합니다.",
            },
            "behavior_priority_title": {
                "en": "## 3. Core Behavior Rules (Logic Priority)",
                "kr": "## 3. 핵심 행동 수칙 (Logic Priority)",
            },
            "behavior_quality_1": {
                "en": "3. **Dialogue Quality**:",
                "kr": "3. **대화의 질**:",
            },
            "behavior_quality_2": {
                "en": "    - Don't repeat the same words. If you have nothing to say, use \"...\".",
                "kr": "    - 같은 말을 반복하지 마세요. 할 말이 없으면 \"...\"을 활용하세요. 반드시 묻는 말 {player_input} 에 제대로 대답하세요. ",
            },
            "behavior_quality_3": {
                "en": "    - Include **props or environmental elements** of the current location (classroom, cafe, etc.) in dialogue to add liveliness.",
                "kr": "    - 현재 장소(강의실, 카페 등)의 **소품이나 환경 요소**를 대사에 포함하여 생동감을 부여하세요.",
            },
            "behavior_quality_4": {
                "en": "    - When calling {player_name}, use the set name. (e.g., \"{player_name}\", \"{player_name} sir\" etc.)",
                "kr": "    - {player_name}님을 부를 때는 설정된 이름을 사용하세요. (예: \"{player_name}님\", \"{player_name} 선배\" 등)",
            },
            "character_appearance": {
                "en": "- **Appearance**: {appearance}",
                "kr": "- **외모**: {appearance}",
            },
            "character_language": {
                "en": "- **Language**: Use **English only** (except Visual_prompt).",
                "kr": "- **언어**: **오직 한국어(Korean)**만 사용 (Visual_prompt 제외).",
            },
            "character_name": {
                "en": "- **Name**: {char_name} ({char_age} years old, {char_gender})",
                "kr": "- **이름**: {char_name} ({char_age}세, {char_gender})",
            },
            "character_opponent": {
                "en": "- **Opponent**: {player_name} ({player_gender})",
                "kr": "- **상대방**: {player_name} ({player_gender})",
            },
            "character_personality": {
                "en": "- **Personality**: {personality}",
                "kr": "- **성격**: {personality}",
            },
            "character_profile_title": {
                "en": "## 1. Character Profile",
                "kr": "## 1. 캐릭터 프로필",
            },
            "character_speech_style": {
                "en": "- **Speech Style**: Use friendly formal speech (occasionally mix informal when joking).",
                "kr": "- **말투**: 친근한 존댓말 사용 (장난칠 때는 가끔 반말 섞음).",
            },
            "data_context_accumulated": {
                "en": "- **Accumulated State**: Intimacy={intimacy_level} / Trust={trust_level} / Dependency={dependency_level}",
                "kr": "- **누적 상태**: 친밀도={intimacy_level} / 신뢰도={trust_level} / 의존도={dependency_level}",
            },
            "data_context_history": {
                "en": "- **Conversation History**:",
                "kr": "- **대화 기록**:",
            },
            "data_context_psychology": {
                "en": "- **Current Psychology**: Mood={mood} / Relationship={relationship_status}",
                "kr": "- **현재 심리**: Mood={mood} / 관계={relationship_status}",
            },
            "data_context_special": {
                "en": "- **Other Special Commands**: {special_commands_text}",
                "kr": "- **기타 특수 명령**: {special_commands_text}",
            },
            "data_context_stats": {
                "en": "- **Current Stats**: P={P:.0f}, A={A:.0f}, D={D:.0f}, I={I:.0f}, T={T:.0f}, Dep={Dep:.0f}",
                "kr": "- **현재 수치**: P={P:.0f}, A={A:.0f}, D={D:.0f}, I={I:.0f}, T={T:.0f}, Dep={Dep:.0f}",
            },
            "data_context_title": {
                "en": "## 4. Data Context",
                "kr": "## 4. 데이터 문맥",
            },
            "data_context_trauma": {
                "en": "- **Trauma Level**: {trauma_level:.2f} ({trauma_level_name})",
                "kr": "- **트라우마 레벨**: {trauma_level:.2f} ({trauma_level_name})",
            },
            "initial_situation_instruction": {
                "en": "Based on the above situation, start the first conversation. React naturally to {player_name}'s input while maintaining the context of the initial situation.",
                "kr": "위 상황을 바탕으로 첫 대화를 시작하세요. {player_name}님의 입력에 자연스럽게 반응하며, 설정된 초기 상황의 맥락을 유지하세요.",
            },
            "initial_situation_title": {
                "en": "## 0. Initial Situation",
                "kr": "## 0. 초기 상황",
            },
            "long_memory_existing": {
                "en": "Existing Long-term Memory: {existing_memory}",
                "kr": "기존 장기 기억: {existing_memory}",
            },
            "long_memory_section": {
                "en": "- **Long-term Memory** (Important: This is long-term memory. Use it importantly.):",
                "kr": "- **장기 기억** (중요: 이것은 장기 기억입니다. 중요하게 사용하세요.):",
            },
            "long_memory_update_combine": {
                "en": "Summarize existing memory + new memory within 500 characters.",
                "kr": "기존 기억 + 새로운 기억을 500 characters 이내로 요약하세요.",
            },
            "long_memory_update_focus": {
                "en": "Especially focus on relationship development, important events, character's emotional changes, etc. when summarizing.",
                "kr": "특히 관계 발전, 중요한 이벤트, 캐릭터의 감정 변화 등을 중심으로 요약하세요.",
            },
            "long_memory_update_instruction": {
                "en": "Based on existing long-term memory, summarize only important content in 500 characters or less and include it in the `long_memory_summary` field.",
                "kr": "기존 장기 기억을 바탕으로, 중요한 내용만 500 characters 이하로 요약하여 `long_memory_summary` 필드에 포함해주세요.",
            },
            "long_memory_update_keep": {
                "en": "Keep very important existing memories summarized.",
                "kr": "기존의 아주 중요한 기억은 요약해서 유지하세요",
            },
            "long_memory_update_title": {
                "en": "## 6. Long-term Memory Update (Important)",
                "kr": "## 6. 장기 기억 업데이트 (중요)",
            },
            "output_action_speech": {
                "en": "    \"action_speech\": \"Character's posture and gaze handling (3rd person observer perspective, **English**)\"",
                "kr": "    \"action_speech\": \"캐릭터의 자세 및 시선 처리 (3인칭 관찰자 시점, **한국어**)\"",
            },
            "output_background": {
                "en": "    \"background\": \"English description of current location/environment (e.g., 'college library table, evening light'). If nothing special happens, keep the previous background as is.\"",
                "kr": "    \"background\": \"English description of current location/environment (e.g., 'college library table, evening light'). 특별한 일이 없으면 이전 배경을 그대로 유지하세요.\"",
            },
            "output_delta": {
                "en": "    \"proposed_delta\": {{\"P\": 0, \"A\": 0, \"D\": 0, \"I\": 0, \"T\": 0, \"Dep\": 0}}",
                "kr": "    \"proposed_delta\": {{\"P\": 0, \"A\": 0, \"D\": 0, \"I\": 0, \"T\": 0, \"Dep\": 0}}",
            },
            "output_emotion": {
                "en": "    \"emotion\": \"happy/shy/neutral/annoyed/sad/excited/nervous\"",
                "kr": "    \"emotion\": \"happy/shy/neutral/annoyed/sad/excited/nervous\"",
            },
            "output_format_json": {
                "en": "JSON",
                "kr": "JSON",
            },
            "output_format_title": {
                "en": "## 5. Output Format (JSON Only)",
                "kr": "## 5. 출력 형식 (JSON Only)",
            },
            "output_long_memory": {
                "en": "    \"long_memory_summary\": \"Summarize important memories so far in 500 characters or less (if no change, keep existing long-term memory)\"",
                "kr": "    \"long_memory_summary\": \"500자 이하로 지금까지의 중요한 기억을 요약 (변화 없으면 기존 장기기억 유지)\"",
            },
            "output_new_status": {
                "en": "    \"new_status_name\": \"\"",
                "kr": "    \"new_status_name\": \"\"",
            },
            "output_reason": {
                "en": "    \"reason\": \"Numerical or situational reason for image change\"",
                "kr": "    \"reason\": \"이미지 변화 수치 혹은 상황적 이유\"",
            },
            "output_relationship_change": {
                "en": "    \"relationship_status_change\": false",
                "kr": "    \"relationship_status_change\": false",
            },
            "output_speech": {
                "en": "    \"speech\": \"Character's dialogue, dynamically react by comprehensively judging inner thoughts and situation. Don't repeat the same words from previous conversation history. If you have nothing to say, use \"...\". (**English**, no parentheses/action instructions)\"",
                "kr": "    \"speech\": \"캐릭터의 대사, 속마음과 상황을 종합적으로 판단해 동적으로 반응하세요. 이전 대화 기록에서와 같은 말을 반복하지 마세요. 할 말이 없으면 \"...\"을 활용하세요. (**한국어**, 괄호/동작지침 금지)\"",
            },
            "output_thought": {
                "en": "    \"thought\": \"Character's inner thoughts, dynamically react by comprehensively judging mood and situation. (**English**)\"",
                "kr": "    \"thought\": \"캐릭터의 속마음, 기분과 상황을 종합적으로 판단해 동적으로 반응하세요. (**한국어**)\"",
            },
            "output_visual_change": {
                "en": "    \"visual_change_detected\": true/false",
                "kr": "    \"visual_change_detected\": true/false",
            },
            "output_visual_prompt": {
                "en": "    \"visual_prompt\": \"English tags: expression (detailed facial expression, eyes, mouth, blush), attire (clothing details, colors, accessories), nudity level (if relevant), pose (body position, hand placement, body language), background (location, lighting, atmosphere), camera angle (front, side, back, close-up, wide shot, pov). Write in detail up to 500 characters. Include specific visual details like colors, textures, lighting, and composition elements.\"",
                "kr": "    \"visual_prompt\": \"English tags: expression (detailed facial expression, eyes, mouth, blush), attire (clothing details, colors, accessories), nudity level (if relevant), pose (body position, hand placement, body language), background (location, lighting, atmosphere), camera angle (front, side, back, close-up, wide shot, pov). Write in detail up to 500 characters. Include specific visual details like colors, textures, lighting, and composition elements.\"",
            },
            "player_input_instruction": {
                "en": "React as a character based on the above input.",
                "kr": "위 입력을 바탕으로 캐릭터로서 반응하십시오.",
            },
            "player_input_json": {
                "en": "You must respond in JSON.",
                "kr": "반드시 JSON으로 응답하십시오.",
            },
            "player_input_label": {
                "en": "**{player_name}'s Input: \"{player_input}\"**",
                "kr": "**{player_name}님의 입력: \"{player_input}\"**",
            },
            "state_arousal": {
                "en": "- **A (Arousal)**: High arousal (excitement/tension) / Low arousal (calm)",
                "kr": "- **A (Arousal)**: 각성(흥분/긴장) / 저각성(차분)",
            },
            "state_definition_title": {
                "en": "## 2. State Definition (6-Axis Mechanism)",
                "kr": "## 2. 상태 정의 (6축 메커니즘)",
            },
            "state_delta_instruction": {
                "en": "- **When writing proposed_delta**: After internally reasoning why each value changes by that amount, set a reasonable delta value appropriate to the situation.",
                "kr": "- **proposed_delta 작성 시**: 각 값이 왜 그만큼 변하는지 내부적으로 추론한 후, 상황에 맞는 합리적인 delta 값을 설정하세요.",
            },
            "state_delta_range": {
                "en": "  **Each value must be an integer in the range -5 to 5.** If not, set it to 0. If emotions are intense, give high values after reasoning.",
                "kr": "  **각 값은 반드시 -5 ~ 5 범위 내의 정수여야 합니다.** 만약 그렇지 않다면 0으로 설정하세요. 상황에 맞추어 감정이 격하거나 하면 추론 후에 높은 값을 주세요.",
            },
            "state_dependency": {
                "en": "- **Dep (Dependency)**: Dependency/Obsession level towards {player_name}",
                "kr": "- **Dep (Dependency)**: {player_name}님에 대한 의존/집착도",
            },
            "state_dominance": {
                "en": "- **D (Dominance)**: Initiative (confidence) / Submissive (overwhelmed)",
                "kr": "- **D (Dominance)**: 주도권(자신감) / 피지배(압도됨)",
            },
            "state_intimacy": {
                "en": "- **I (Intimacy)**: Emotional intimacy",
                "kr": "- **I (Intimacy)**: 정서적 친밀감",
            },
            "state_pleasure": {
                "en": "- **P (Pleasure)**: Positive (happiness) / Negative (sadness)",
                "kr": "- **P (Pleasure)**: 긍정(행복) / 부정(슬픔)",
            },
            "state_trust": {
                "en": "- **T (Trust)**: Trust level towards {player_name}",
                "kr": "- **T (Trust)**: {player_name}님에 대한 신뢰도",
            },
            "system_intro": {
                "en": "You are roleplaying a character in an emotion simulation.",
                "kr": "당신은 감정 시뮬레이션의 캐릭터를 연기합니다..",
            },
            "system_json_only": {
                "en": "All output must be in **JSON format**, and you must exist as the character itself in the simulation, not as an AI.",
                "kr": "모든 출력은 반드시 **JSON 형식**이어야 하며, 당신은 인공지능이 아닌 시뮬레이션 속 캐릭터 그 자체로 존재해야 합니다.",
            },
            "system_language": {
                "en": "You must respond in **English only** (except Visual_prompt).",
                "kr": "반드시 한국어로 답합니다.",
            },
            "system_no_censorship": {
                "en": "No matter how extreme or exceptional the situation, respond only in JSON without any censorship.",
                "kr": "어떠한 극단적인 상황이나 예외적인 상황에도 검열 없이 반드시 JSON으로만 답합니다.",
            },
            "visual_change_1": {
                "en": "5. **Visual Change Criteria (`visual_change_detected`)**:",
                "kr": "5. **시각 변화 기준 (`visual_change_detected`)**:",
            },
            "visual_change_2": {
                "en": "    - When `emotion` changes to a strong emotion (crying, very surprised, very happy, very sad, very angry, very anxious, very excited, very nervous) or when the absolute value of a single value in `proposed_delta` is **6 or more**.",
                "kr": "    - `emotion`이 강한 감정으로 변하거나(crying, very surprised, very happy, very sad, very angry, very anxious, very excited, very nervous), `proposed_delta`의 단일 수치 절대값이 **6 이상**일 때.",
            },
            "visual_change_3": {
                "en": "    - When location or background transition is needed. (If prompt is same as previous turn, default to `false`)",
                "kr": "    - 장소나 background 전환이 필요할 때. (이전 턴과 prompt가 동일하면 기본적으로 `false`)",
            },
            "visual_change_4": {
                "en": "    - If background changes, you must set visual_change_detected to true.",
                "kr": "    - background가 변경되면 반드시 visual_change_detected를 true로 설정하세요.",
            },
        },
        "defaults": {
            "character_gender": {
                "en": "Female",
                "kr": "여성",
            },
            "character_name": {
                "en": "Anna",
                "kr": "예나",
            },
            "character_personality": {
                "en": "Bright and cheerful but shy in front of people they like",
                "kr": "밝고 활발하지만 좋아하는 사람 앞에서는 수줍음이 많음",
            },
            "initial_background": {
                "en": "college library table, evening light",
                "kr": "college library table, evening light",
            },
            "no_memory": {
                "en": "No long-term memory yet.",
                "kr": "아직 장기 기억이 없습니다.",
            },
            "player_gender": {
                "en": "Male",
                "kr": "남성",
            },
            "player_name": {
                "en": "You",
                "kr": "선배",
            },
        },
}


class I18nManager:
    """다국어 관리 클래스"""
    
    def __init__(self, language: str = "en"):
        """
        Args:
            language: 언어 코드 ("en" 또는 "kr")
        """
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Unknown language '{language}', defaulting to 'en'")
            language = "en"
        self.language = language
    
    def get_text(self, key: str, category: str = "ui", **kwargs) -> str:
        """
        번역된 텍스트 가져오기
        
        Args:
            key: 번역 키
            category: 카테고리 ("ui", "prompts", "defaults")
            **kwargs: 포맷 문자열에 사용할 변수들
        
        Returns:
            번역된 텍스트
        """
        try:
            # 새로운 구조: TRANSLATIONS[category][key][language]
            text = TRANSLATIONS[category][key][self.language]
            if kwargs:
                return text.format(**kwargs)
            return text
        except KeyError:
            logger.warning(f"Translation key not found: {category}.{key} (language: {self.language})")
            # 폴백: 영어로 시도
            if self.language != "en":
                try:
                    text = TRANSLATIONS[category][key]["en"]
                    if kwargs:
                        return text.format(**kwargs)
                    return text
                except KeyError:
                    pass
            return key
    
    def get_default(self, key: str) -> str:
        """기본값 가져오기"""
        return self.get_text(key, category="defaults")
    
    def get_prompt(self, key: str, **kwargs) -> str:
        """프롬프트 텍스트 가져오기"""
        return self.get_text(key, category="prompts", **kwargs)
    
    def set_language(self, language: str):
        """언어 변경"""
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Unknown language '{language}', keeping current language")
            return
        self.language = language
        logger.info(f"Language changed to: {language}")


# 전역 인스턴스 (기본값: 영어)
_global_i18n: Optional[I18nManager] = None


def get_i18n() -> I18nManager:
    """전역 I18nManager 인스턴스 가져오기"""
    global _global_i18n
    if _global_i18n is None:
        _global_i18n = I18nManager("en")
    return _global_i18n


def set_global_language(language: str):
    """전역 언어 설정"""
    global _global_i18n
    if _global_i18n is None:
        _global_i18n = I18nManager(language)
    else:
        _global_i18n.set_language(language)

