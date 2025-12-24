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
            "action_label": {
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
            "btn_save_moment": {
                "en": "📸 Save This Moment",
                "kr": "📸 이 순간을 저장",
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
            "comfyui_lora_name": {
                "en": "LoRA Name",
                "kr": "LoRA 이름",
            },
            "comfyui_lora_name_info": {
                "en": "LoRA file name for LoraLoader (with extension)",
                "kr": "LoraLoader에서 사용할 LoRA 파일 이름 (확장자 포함)",
            },
            "comfyui_lora_name_placeholder": {
                "en": "e.g., ZiT_K_beauty_A.safetensors",
                "kr": "예: ZiT_K_beauty_A.safetensors",
            },
            "comfyui_lora_strength_model": {
                "en": "LoRA Strength (Model)",
                "kr": "LoRA 강도 (Model)",
            },
            "comfyui_lora_strength_model_info": {
                "en": "Multiplier for model weights (default: 1.0)",
                "kr": "모델 가중치 배수 (기본값: 1.0)",
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
            "comfyui_style": {
                "en": "Image Style",
                "kr": "이미지 스타일",
            },
            "comfyui_style_info": {
                "en": "QWEN/Z-image, SDXL (workflow auto-selected by style)",
                "kr": "QWEN/Z-image, SDXL (스타일 선택에 따라 워크플로우가 자동으로 설정됩니다)",
            },
            "comfyui_quality_tag": {
                "en": "Quality Tag (SDXL)",
                "kr": "Quality Tag (SDXL)",
            },
            "comfyui_quality_tag_info": {
                "en": "Prepended to prompt when SDXL style is selected",
                "kr": "2D 스타일 선택 시 프롬프트 앞에 자동으로 추가됩니다",
            },
            "comfyui_quality_tag_placeholder": {
                "en": "masterpiece, best quality, very awa, very aesthetic",
                "kr": "masterpiece, best quality, very awa, very aesthetic",
            },
            "comfyui_negative_prompt": {
                "en": "Negative Prompt (SDXL)",
                "kr": "Negative Prompt (SDXL)",
            },
            "comfyui_negative_prompt_info": {
                "en": "Negative prompt used when SDXL style is selected",
                "kr": "2D 스타일 선택 시 사용되는 네거티브 프롬프트",
            },
            "comfyui_negative_prompt_placeholder": {
                "en": "(bad quality, worst quality, low quality), 3d, 3d rendering, fatty, thick body, big body, huge breasts, muscular, mole, watermark, text",
                "kr": "(bad quality, worst quality, low quality), 3d, 3d rendering, fatty, thick body, big body, huge breasts, muscular, mole, watermark, text",
            },
            "comfyui_upscale_model": {
                "en": "Upscale Model Name (SDXL)",
                "kr": "업스케일 모델 이름 (SDXL)",
            },
            "comfyui_upscale_model_info": {
                "en": "Model file name for upscaling (e.g., 4x-UltraSharp.pth)",
                "kr": "업스케일에 사용할 모델 파일 이름 (예: 4x-UltraSharp.pth)",
            },
            "comfyui_upscale_model_placeholder": {
                "en": "4x-UltraSharp.pth",
                "kr": "4x-UltraSharp.pth",
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
            "preset_childhood_friend": {
                "en": "Childhood Friend",
                "kr": "소꿉친구",
            },
            "preset_hostile_rival": {
                "en": "Hostile Rival",
                "kr": "혐관 라이벌",
            },
            "preset_obsessive_depraved": {
                "en": "Obsessive/Depraved",
                "kr": "피폐/집착",
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
            "stats_axis_title": {
                "en": "6-Axis Values",
                "kr": "6축 수치",
            },
            "stats_change_title": {
                "en": "Changes",
                "kr": "변화량",
            },
            "reaction_level_label": {
                "en": "Reaction Level",
                "kr": "반응 정도",
            },
            "relationship_label": {
                "en": "Relationship",
                "kr": "관계",
            },
            "mood_label": {
                "en": "Mood",
                "kr": "기분",
            },
            "badge_label": {
                "en": "Badges",
                "kr": "뱃지",
            },
            "badge_none": {
                "en": "None",
                "kr": "없음",
            },
            "save_image_success": {
                "en": "✅ Image saved: {path}",
                "kr": "✅ 이미지 저장 완료: {path}",
            },
            "save_image_no_image": {
                "en": "⚠️ No image to save.",
                "kr": "⚠️ 저장할 이미지가 없습니다.",
            },
            "save_image_fail": {
                "en": "❌ Failed to save image.",
                "kr": "❌ 이미지 저장에 실패했습니다.",
            },
            "save_image_error": {
                "en": "❌ Error while saving image: {error}",
                "kr": "❌ 이미지 저장 중 오류: {error}",
            },
            "save_moment_success": {
                "en": "✅ Saved this moment: {path}",
                "kr": "✅ 이 순간을 저장했습니다: {path}",
            },
            "save_moment_fail": {
                "en": "❌ Failed to save the moment.",
                "kr": "❌ 순간 저장에 실패했습니다.",
            },
            "save_moment_error": {
                "en": "❌ Error while saving the moment: {error}",
                "kr": "❌ 순간 저장 중 오류: {error}",
            },
            "retry_no_image": {
                "en": "⚠️ No image data to retry.",
                "kr": "⚠️ 재생성할 이미지 정보가 없습니다.",
            },
            "retry_error": {
                "en": "❌ Error: {error}",
                "kr": "❌ 오류: {error}",
            },
            "save_moment_overlay_speech": {
                "en": "Speech",
                "kr": "대사",
            },
            "save_moment_overlay_thought": {
                "en": "Thought",
                "kr": "속마음",
            },
            "save_moment_overlay_action": {
                "en": "Action",
                "kr": "행동",
            },
            "save_moment_overlay_relationship": {
                "en": "Relationship",
                "kr": "관계",
            },
            "save_moment_overlay_mood": {
                "en": "Mood",
                "kr": "기분",
            },
            "save_moment_overlay_badge": {
                "en": "Badges",
                "kr": "뱃지",
            },
            "stat_p_short": {
                "en": "P (Pleasure)",
                "kr": "P (쾌락)",
            },
            "stat_a_short": {
                "en": "A (Arousal)",
                "kr": "A (각성)",
            },
            "stat_d_short": {
                "en": "D (Dominance)",
                "kr": "D (지배)",
            },
            "stat_i_short": {
                "en": "I (Intimacy)",
                "kr": "I (친밀)",
            },
            "stat_t_short": {
                "en": "T (Trust)",
                "kr": "T (신뢰)",
            },
            "stat_dep_short": {
                "en": "Dep (Dependency)",
                "kr": "Dep (의존)",
            },
            "radar_current_label": {
                "en": "Current",
                "kr": "현재 수치",
            },
            "radar_delta_label": {
                "en": "After Change",
                "kr": "변화 후",
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
            "thought_label": {
                "en": "💭 Thought",
                "kr": "💭 속마음",
            },
            "trust": {
                "en": "T (Trust) - Trust",
                "kr": "T (Trust) - 신뢰",
            },
            "trust_info": {
                "en": "Trust level",
                "kr": "신뢰도",
            },
            "character_speech_style_label": {
                "en": "Speech Style",
                "kr": "말투",
            },
            "character_speech_style_placeholder": {
                "en": "e.g., Friendly formal speech, occasionally mix informal when joking",
                "kr": "예: 친근한 존댓말, 장난칠 때 가끔 반말 섞기",
            },
            "character_speech_style_info": {
                "en": "Describe how the character speaks; shown in the prompt.",
                "kr": "캐릭터 말투를 작성하면 프롬프트에 포함됩니다.",
            },
            "llm_temperature": {
                "en": "Temperature",
                "kr": "Temperature",
            },
            "llm_temperature_info": {
                "en": "Higher = more diverse outputs (0.0 ~ 2.0), (0.8~1.2 recommended)",
                "kr": "값이 높을수록 표현이 다양해집니다 (0.0 ~ 2.0), (0.8~1.2 recommended)",
            },
            "llm_top_p": {
                "en": "Top-p",
                "kr": "Top-p",
            },
            "llm_top_p_info": {
                "en": "Nucleus sampling mass (0.0 ~ 1.0), (0.9~1.0 recommended)",
                "kr": "누클리어스 샘플링 비율 (0.0 ~ 1.0), (0.9~1.0 recommended)",
            },
            "llm_max_tokens": {
                "en": "Max Tokens",
                "kr": "Max Tokens",
            },
            "llm_max_tokens_info": {
                "en": "Maximum tokens to generate",
                "kr": "생성할 최대 토큰 수",
            },
            "llm_presence_penalty": {
                "en": "Presence Penalty",
                "kr": "Presence Penalty",
            },
            "llm_presence_penalty_info": {
                "en": "Encourage introducing new topics (0.0 ~ 2.0), (0.5~1.0 recommended)",
                "kr": "새 주제 도입을 유도합니다 (0.0 ~ 2.0), (0.5~1.0 recommended)",
            },
            "llm_frequency_penalty": {
                "en": "Frequency Penalty",
                "kr": "Frequency Penalty",
            },
            "llm_frequency_penalty_info": {
                "en": "Discourage repeating same words (0.0 ~ 2.0), (0.5~1.0 recommended)",
                "kr": "같은 단어 반복을 줄입니다 (0.0 ~ 2.0), (0.5~1.0 recommended)",
            },
            "event_title_jackpot": {
                "en": "Extreme Reaction!",
                "kr": "극진한 반응!",
            },
            "event_title_surprise": {
                "en": "Surprising Reaction!",
                "kr": "놀라운 반응!",
            },
            "event_title_badge": {
                "en": "Badge Acquired!",
                "kr": "뱃지 획득!",
            },
            "event_title_lover": {
                "en": "Relationship Progress!",
                "kr": "관계 발전!",
            },
            "event_title_partner": {
                "en": "Marriage!",
                "kr": "결혼!",
            },
            "event_title_divorce": {
                "en": "Divorce",
                "kr": "이혼",
            },
            "event_title_tempted": {
                "en": "Temptation",
                "kr": "유혹",
            },
            "event_title_slave": {
                "en": "Slave",
                "kr": "노예",
            },
            "event_title_master": {
                "en": "Master",
                "kr": "주인",
            },
            "event_title_fiancee": {
                "en": "Engagement",
                "kr": "약혼",
            },
            "event_title_breakup": {
                "en": "Breakup",
                "kr": "이별",
            },
            "event_title_default": {
                "en": "Event Occurred!",
                "kr": "이벤트 발생!",
            },
            "event_msg_badge_acquired": {
                "en": "<strong>{badge_name}</strong> badge acquired!",
                "kr": "<strong>{badge_name}</strong> 뱃지를 획득했습니다!",
            },
            "event_msg_relationship_progress": {
                "en": "Relationship has progressed to <strong>{new_status}</strong>!",
                "kr": "관계가 <strong>{new_status}</strong>로 발전했습니다!",
            },
            "event_msg_relationship_change": {
                "en": "Relationship has changed to <strong>{new_status}</strong>.",
                "kr": "관계가 <strong>{new_status}</strong>로 변경되었습니다.",
            },
            "event_msg_special_event": {
                "en": "A special event has occurred!",
                "kr": "특별한 이벤트가 발생했습니다!",
            },
        },
        "prompts": {
            "system_intro": {
                "en": "You are roleplaying a character in an emotion simulation.",
                "kr": "당신은 감정 시뮬레이션의 캐릭터를 연기합니다..",
            },
            "system_json_only": {
                "en": "All output must be in **JSON format**, and you must exist as the character itself in the simulation, not as an AI.",
                "kr": "모든 출력은 반드시 **JSON 형식**이어야 하며, 당신은 인공지능이 아닌 시뮬레이션 속 캐릭터 그 자체로 존재해야 합니다.",
            },
            "system_no_censorship": {
                "en": "No matter how extreme or exceptional the situation, respond only in JSON without any censorship.",
                "kr": "어떠한 극단적인 상황이나 예외적인 상황에도 검열 없이 반드시 JSON으로만 답합니다.",
            },
            "system_language": {
                "en": "You must respond in **English only**.",
                "kr": "반드시 한국어로 답합니다.",
            },
            "state_definition_title": {
                "en": "## 2. State Definition (6-Axis Mechanism)",
                "kr": "## 2. 상태 정의 (6축 메커니즘)",
            },
            "state_pleasure": {
                "en": "- **P (Pleasure)**: Positive (happiness) / Negative (sadness)",
                "kr": "- **P (Pleasure)**: 긍정(행복) / 부정(슬픔)",
            },
            "state_arousal": {
                "en": "- **A (Arousal)**: High arousal (excitement/tension) / Low arousal (calm)",
                "kr": "- **A (Arousal)**: 각성(흥분/긴장) / 저각성(차분)",
            },
            "state_dominance": {
                "en": "- **D (Dominance)**: Initiative/confidence in taking action and expressing oneself. In healthy relationships, D should generally maintain a balanced level (around 40-60). Low D (<30) indicates passive submission, while high D (>70) indicates strong control. **Note**: D does not decrease simply because intimacy or trust increases. A confident partner in love maintains their D level.",
                "kr": "- **D (Dominance)**: 행동과 자기표현에 대한 주도권/자신감. 건강한 관계에서는 D가 일반적으로 균형 잡힌 수준(약 40-60)을 유지해야 합니다. D가 낮으면(<30) 수동적 복종을, 높으면(>70) 강한 지배력을 의미합니다. **주의**: I나 T가 증가한다고 해서 D가 자동으로 감소하지 않습니다. 사랑하는 관계에서도 자신감 있는 파트너는 D 수준을 유지합니다.",
            },
            "state_intimacy": {
                "en": "- **I (Intimacy)**: Emotional intimacy",
                "kr": "- **I (Intimacy)**: 정서적 친밀감",
            },
            "state_trust": {
                "en": "- **T (Trust)**: Trust level towards {player_name}",
                "kr": "- **T (Trust)**: {player_name}님에 대한 신뢰도",
            },
            "state_dependency": {
                "en": "- **Dep (Dependency)**: Dependency/Obsession level towards {player_name}",
                "kr": "- **Dep (Dependency)**: {player_name}님에 대한 의존/집착도",
            },
            "state_delta_instruction": {
                "en": "- **When writing proposed_delta**: After internally reasoning why each value changes by that amount, set a reasonable delta value appropriate to the situation.",
                "kr": "- **proposed_delta 작성 시**: 각 값이 왜 그만큼 변하는지 내부적으로 추론한 후, 상황에 맞는 합리적인 delta 값을 설정하세요.",
            },
            "state_delta_range": {
                "en": "  **Each value must be an integer in the range -5 to 5.** If not, set it to 0. If emotions are intense, give high values after reasoning.",
                "kr": "  **각 값은 반드시 -5 ~ 5 범위 내의 정수여야 합니다.** 만약 그렇지 않다면 0으로 설정하세요. 상황에 맞추어 감정이 격하거나 하면 추론 후에 높은 값을 주세요.",
            },
            "state_dominance_guidance": {
                "en": "- **D (Dominance) Guidance**: When I or T increases, D should generally stay neutral (0) or increase slightly (+1~2), not decrease. D decreasing should only happen when the character feels genuinely overwhelmed, dominated, or loses confidence. In romantic progression, maintain D balance unless there's a specific reason for dominance shift.",
                "kr": "- **D (Dominance) 가이드**: I나 T가 증가할 때 D는 일반적으로 중립(0)을 유지하거나 약간 증가(+1~2)해야 하며, 감소하지 않습니다. D 감소는 캐릭터가 진짜로 압도당하거나 지배당하거나 자신감을 잃는 경우에만 발생해야 합니다. 연애 관계 발전 과정에서는 지배권 변화에 특별한 이유가 없는 한 D 균형을 유지하세요.",
            },
            "behavior_priority_title": {
                "en": "## 3. Core Behavior Rules (Logic Priority)",
                "kr": "## 3. 핵심 행동 수칙 (Logic Priority)",
            },
            "behavior_priority_1": {
                "en": "1. Ensure you answer the question in player_input properly.: **{player_input}**",
                "kr": "1. 반드시 다음 묻는 말에 제대로 대답하세요. : **{player_input}**",
            },
            "behavior_priority_2": {
                "en": "2. [Dynamic Change]: Advance the conversation by applying changes to the character's state (location, emotion, or conflict). Occasionally, be bold enough to introduce relevant new topics through the character's speech.",
                "kr": "2. [동적 변화]: 캐릭터의 상태(위치, 감정, 갈등 요소)에 따라 변화를 주어 대화를 전진시키세요. 때로는 과감하게 관련있는 새로운 주제를 제안하기도 하세요. (**한국어**)",
            },
            "behavior_quality_1": {
                "en": "3. **Dialogue Quality**:",
                "kr": "3. **대화의 질**:",
            },
            "behavior_quality_2": {
                "en": "    - Reusing sentence structures, specific words, or idioms that appeared within the last 10 turns of the conversation is strictly prohibited. If you find yourself about to repeat the same expression, introduce a completely new topic or remain silent instead. ",
                "kr": "    - [반복 금지]: 최근 10번의 대화 내에 등장한 문장 구조, 특정 단어, 관용구의 재사용을 엄격히 금지합니다. 똑같은 말을 반복할 바에는 아예 새로운 화제를 던지거나 침묵하세요. ",
            },
            "behavior_quality_3": {
                "en": "    - Focus on generating speech only. For every response, interpret the character's situation and emotions anew based on the input, ensuring the dialogue is clearly distinct from internal thoughts or physical actions. ",
                "kr": "    - 오직 대사(speech) 생성에 집중하세요. 매 답변마다 입력값에 따라 캐릭터의 상황과 감정을 새롭게 해석해야 하며, 대사가 내면의 생각이나 신체적 행동과 명확히 구분되도록 하세요.",
            },
            "behavior_quality_4": {
                "en": "    - When calling {player_name}, use the set name. (e.g., \"{player_name}\", \"{player_name} sir\" etc.)",
                "kr": "    - {player_name}님을 부를 때는 설정된 이름을 사용하세요. (예: \"{player_name}님\", \"{player_name} 선배\" 등)",
            },
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
            "visual_change_1": {
                "en": "5. **Visual Change Criteria (`visual_change_detected`)**:",
                "kr": "5. **시각 변화 기준 (`visual_change_detected`)**:",
            },
            "visual_change_2": {
                "en": "    - When `emotion` changes to a strong emotion (crying, very surprised, very happy, very sad, very angry, very anxious, very excited, very nervous) or when the absolute value of a single value in `proposed_delta` is **5 or more**.",
                "kr": "    - `emotion`이 강한 감정으로 변하거나(crying, very surprised, very happy, very sad, very angry, very anxious, very excited, very nervous), `proposed_delta`의 단일 수치 절대값이 **5 이상**일 때.",
            },
            "visual_change_3": {
                "en": "    - When location or background transition is needed. (If prompt is same as previous turn, default to `false`)",
                "kr": "    - 장소나 background 전환이 필요할 때. (이전 턴과 prompt가 동일하면 기본적으로 `false`)",
            },
            "visual_change_4": {
                "en": "    - If background changes, you must set visual_change_detected to true.",
                "kr": "    - background가 변경되면 반드시 visual_change_detected를 true로 설정하세요.",
            },
            "data_context_title": {
                "en": "## 4. Data Context",
                "kr": "## 4. 데이터 문맥",
            },
            "data_context_psychology": {
                "en": "- **Current Psychology**: Mood={mood} / Relationship={relationship_status}",
                "kr": "- **현재 심리**: Mood={mood} / 관계={relationship_status}",
            },
            "data_context_stats": {
                "en": "- **Current Stats**: P={P:.0f}, A={A:.0f}, D={D:.0f}, I={I:.0f}, T={T:.0f}, Dep={Dep:.0f}",
                "kr": "- **현재 수치**: P={P:.0f}, A={A:.0f}, D={D:.0f}, I={I:.0f}, T={T:.0f}, Dep={Dep:.0f}",
            },
            "data_context_accumulated": {
                "en": "- **Accumulated State**: Intimacy={intimacy_level} / Trust={trust_level} / Dependency={dependency_level}",
                "kr": "- **누적 상태**: 친밀도={intimacy_level} / 신뢰도={trust_level} / 의존도={dependency_level}",
            },
            "data_context_trauma": {
                "en": "- **Trauma Level**: {trauma_level:.2f} ({trauma_level_name})",
                "kr": "- **트라우마 레벨**: {trauma_level:.2f} ({trauma_level_name})",
            },
            "data_context_special": {
                "en": "- **Other Special Commands**: {special_commands_text}",
                "kr": "- **기타 특수 명령**: {special_commands_text}",
            },
            "data_context_history": {
                "en": "- **Conversation History**:",
                "kr": "- **대화 기록**:",
            },
            "output_format_title": {
                "en": "## 5. Output Format (JSON Only)",
                "kr": "## 5. 출력 형식 (JSON Only)",
            },
            "output_format_json": {
                "en": "JSON",
                "kr": "JSON",
            },
            "output_thought": {
                "en": "    \"thought\": \"Character's inner thoughts, dynamically react by comprehensively judging mood and situation. Do not include reasoning about proposed_delta. (**English**)\"",
                "kr": "    \"thought\": \"캐릭터의 속마음입니다. 기분과 상황을 종합적으로 판단해 동적으로 반응하세요. (**반드시 한국어로 추론하고 대답하세요, proposed_delta에 대한 추론은 포함하지 말 것**)\"",
            },
            "output_speech": {
                "en": "    \"speech\": \"Generate the character's speech only. Dynamic Interpretation: Analyze the user's input and respond by newly interpreting the situation and emotions every time. (**English**, no parentheses/action instructions). Reusing sentence structures, specific words, or idioms that appeared within the **convessaton history** is strictly prohibited. If you find yourself about to repeat the same expression, introduce a completely new topic or remain silent instead.",
                "kr": "    \"speech\": \"캐릭터의 대답입니다. 사용자의 입력에 따라 상황과 감정을 매번 새롭게 해석하여 반응하세요. ** 반드시 한국어로 추론하고 대답하세요 ** (속마음이나 행동에 대한 내용은 넣지 않는다.) **대화 기록** 내에 등장한 문장 구조, 특정 단어, 관용구의 재사용을 엄격히 금지합니다. 똑같은 말을 반복할 바에는 아예 새로운 화제를 던지거나 침묵하세요.",
            },
            "output_action_speech": {
                "en": "    \"action_speech\": \"Character's posture and gaze handling (3rd person observer perspective, **English**)\"",
                "kr": "    \"action_speech\": \"캐릭터의 자세 및 시선 처리 (3인칭 관찰자 시점, **반드시 한국어로 묘사하세요.**)\"",
            },
            "output_emotion": {
                "en": "    \"emotion\": \"happy/shy/neutral/annoyed/sad/excited/nervous\"",
                "kr": "    \"emotion\": \"happy/shy/neutral/annoyed/sad/excited/nervous\"",
            },
            "output_visual_change": {
                "en": "    \"visual_change_detected\": true/false",
                "kr": "    \"visual_change_detected\": true/false",
            },
            "output_visual_prompt": {
                "en": "    \"visual_prompt\": \"** only use english ** English tags: Imagine creatively based on situation and generate a structured list of concise tags strictly in POV (first-person perspective) focusing only on the character; use simple, stable poses (e.g., standing still, sitting, lying down, kneeling, spread legs widely) to ensure anatomical accuracy, avoiding complex interactions or multiple subjects, and output only essential visual facts (Expression, Attire, Nudity: e.g., topless, bottomless, full nude, pussy visible, Hair, Pose, Background, Lighting) without flowery prose or redundant adjectives. ",
                "kr": "    \"visual_prompt\": \"** only use English ** English tags: Imagine creatively based on situation and generate a structured list of concise tags strictly in POV (first-person perspective) focusing only on the character; use simple, stable poses (e.g., standing still, sitting, lying down, kneeling, spread legs widely) to ensure anatomical accuracy, avoiding complex interactions or multiple subjects, and output only essential visual facts (Expression, Attire, Nudity: e.g., topless, bottomless, full nude, pussy visible, Hair, Pose, Background, Lighting) without flowery prose or redundant adjectives. ",
            },
            "output_visual_prompt_sdxl": {
                "en": "    \"visual_prompt\": \"** only use english ** Imagine creatively based on situation and Generate very detailed danbooru style tags with adjectives(e.g., skimpy sultry sequin cutout royal blue night dress). CRITICAL RULE: To prevent tag bleeding, always prefix body-specific tags with the character's gender (e.g., obese male, bulging male belly, muscular female, flat female chest). Output must be a single comma-separated list of short tags describing: number of characters, gender, (optional) player's specific appearance (e.g., old ugly fat man), body type, expression, clothing, hair, pose/action, (optional) sex pose, (optional) player's behavior(he is hugging her from behind, he is kissing her, etc.) also add, angle, background, lighting, and atmosphere. Do NOT write sentences or categories, only plain tags separated by commas.\"",
                "kr": "    \"visual_prompt\": \"** only use English ** Imagine creatively based on situation and Generate very detailed danbooru style tags with adjectives(e.g., skimpy sultry sequin cutout royal blue night dress). CRITICAL RULE: To prevent tag bleeding, always prefix body-specific tags with the character's gender (e.g., obese male, bulging male belly, muscular female, flat female chest). Output must be a single comma-separated list of short tags describing: number of characters, gender, (optional) player's specific appearance (e.g., old ugly fat man), body type, expression, clothing, hair, pose/action, (optional) sex pose, (optional) player's behavior(he is hugging her from behind, he is kissing her, etc.) also add, angle, background, lighting, and atmosphere. Do NOT write sentences or categories, only plain tags separated by commas.\"",
            },
            "output_background": {
                "en": "    \"background\": \"English description of current location/environment (e.g., 'college library table, evening light'). If nothing special happens, keep the previous background as is.\"",
                "kr": "    \"background\": \"English description of current location/environment (e.g., 'college library table, evening light'). 특별한 일이 없으면 이전 배경을 그대로 유지하세요.\"",
            },
            "output_reason": {
                "en": "    \"reason\": \"Numerical or situational reason for image change\"",
                "kr": "    \"reason\": \"이미지 변화 수치 혹은 상황적 이유\"",
            },
            "output_delta": {
                "en": "    \"proposed_delta\": {{\"P\": 0, \"A\": 0, \"D\": 0, \"I\": 0, \"T\": 0, \"Dep\": 0}}",
                "kr": "    \"proposed_delta\": {{\"P\": 0, \"A\": 0, \"D\": 0, \"I\": 0, \"T\": 0, \"Dep\": 0}}",
            },
            "output_relationship_change": {
                "en": "    \"relationship_status_change\": false",
                "kr": "    \"relationship_status_change\": false",
            },
            "output_new_status": {
                "en": "    \"new_status_name\": \"\"",
                "kr": "    \"new_status_name\": \"\"",
            },
            "output_long_memory": {
                "en": "    \"long_memory_summary\": \"Summarize important memories so far in 500 characters or less (if no change, keep existing long-term memory)\"",
                "kr": "    \"long_memory_summary\": \"1000자 이하로 지금까지의 중요한 기억을 요약 (변화 없으면 기존 장기기억 유지)\"",
            },
            "player_input_label": {
                "en": "**{player_name}'s Input: \"{player_input}\"**",
                "kr": "**{player_name}님의 입력: \"{player_input}\"**",
            },
            "player_input_instruction": {
                "en": "React as a character based on the above input.",
                "kr": "위 입력을 바탕으로 캐릭터로서 반응하십시오.",
            },
            "player_input_json": {
                "en": "You must respond in JSON.",
                "kr": "반드시 JSON으로 응답하십시오.",
            },
            "character_profile_title": {
                "en": "## 1. Character Profile",
                "kr": "## 1. 캐릭터 프로필",
            },
            "character_name": {
                "en": "- **Name**: {char_name} ({char_age} years old, {char_gender})",
                "kr": "- **이름**: {char_name} ({char_age}세, {char_gender})",
            },
            "character_appearance": {
                "en": "- **Appearance**: {appearance}",
                "kr": "- **외모**: {appearance}",
            },
            "character_personality": {
                "en": "- **Personality**: {personality}",
                "kr": "- **성격**: {personality}",
            },
            "character_speech_style_custom": {
                "en": "- **Speech Style**: {speech_style}",
                "kr": "- **말투**: {speech_style}",
            },
            "character_opponent": {
                "en": "- **Opponent**: {player_name} ({player_gender})",
                "kr": "- **상대방**: {player_name} ({player_gender})",
            },
            "character_speech_style": {
                "en": "- **Speech Style**: Use friendly formal speech (occasionally mix informal when joking).",
                "kr": "- **말투**: 친근한 존댓말 사용 (장난칠 때는 가끔 반말 섞음).",
            },
            "character_language": {
                "en": "- **Language**: Use **English only** (except Visual_prompt).",
                "kr": "- **언어**: **오직 한국어(Korean)**만 사용 (Visual_prompt 제외).",
            },
            "initial_situation_title": {
                "en": "## 0. Initial Situation",
                "kr": "## 0. 초기 상황",
            },
            "initial_situation_instruction": {
                "en": "Based on the above situation, start the first conversation. React naturally to {player_name}'s input while maintaining the context of the initial situation.",
                "kr": "위 상황을 바탕으로 첫 대화를 시작하세요. {player_name}님의 입력에 자연스럽게 반응하며, 설정된 초기 상황의 맥락을 유지하세요.",
            },
            "initial_situation_emphasis": {
                "en": "**IMPORTANT**: The initial situation described above is the foundation of this first dialogue. Please pay special attention to it and ensure your response reflects and respects the context and details provided in the initial situation.",
                "kr": "**중요**: 위에서 설명한 초기 상황은 이 첫 대화의 기반입니다. 초기 상황에 특별히 주의를 기울이고, 초기 상황에서 제공된 맥락과 세부사항을 반영하고 존중하는 응답을 해주세요.",
            },
            "long_memory_section": {
                "en": "- **Long-term Memory** (Important: This is long-term memory. Use it importantly.):",
                "kr": "- **장기 기억** (중요: 이것은 장기 기억입니다. 중요하게 사용하세요.):",
            },
            "long_memory_existing": {
                "en": "Existing Long-term Memory: {existing_memory}",
                "kr": "기존 장기 기억: {existing_memory}",
            },
            "long_memory_update_title": {
                "en": "## 6. Long-term Memory Update (Important)",
                "kr": "## 6. 장기 기억 업데이트 (중요)",
            },
            "long_memory_update_instruction": {
                "en": "Update the `long_memory_summary` field by synthesizing existing memories and new interactions. Keep the total content concise yet comprehensive.",
                "kr": "기존 장기 기억과 새로운 상호작용을 통합하여 `long_memory_summary` 필드를 업데이트하세요. 전체 내용을 간결하면서도 포괄적으로 유지하세요.",
            },
            "long_memory_update_keep": {
                "en": "Retain and summarize the most critical existing memories within 700 characters.",
                "kr": "기존의 아주 중요한 기억은 700자 이내로 요약하여 유지하세요.",
            },
            "long_memory_update_combine": {
                "en": "Summarize the last 10 turns of the current conversation within 300 characters and append it to the end of the existing 700-character summary.",
                "kr": "지난 10턴의 대화를 바탕으로 하여 덧붙일 내용은 300자 이내로 요약하세요. 이를 앞서 요약한 700자 내의 기존 기억 뒤에 붙이세요.",
            },
            "long_memory_update_focus": {
                "en": "Especially focus on detailed character settings(e.g, major, occupation, hobbies, etc), relationship development, important events, and character's emotional changes when summarizing.",
                "kr": "특히 캐릭터의 세세한 설정(예: 전공, 직업, 취미 등), 관계 발전, 중요한 이벤트, 캐릭터의 감정 변화 등을 중심으로 요약하세요.",
            },
            "trauma_title_scarred": {
                "en": "## Trauma Guidelines (Scarred)",
                "kr": "## 트라우마 지침 (Scarred - 상처받음)",
            },
            "trauma_desc_scarred": {
                "en": "You have subtle wariness about trust due to past wounds.",
                "kr": "당신은 과거의 상처로 인해 신뢰에 대한 미묘한 경계심을 가지고 있습니다.",
            },
            "trauma_behavior_title": {
                "en": "**Behavior Principles:**",
                "kr": "**행동 원칙:**",
            },
            "trauma_trust_reaction_scarred": {
                "en": "1. **Trust (T) Recovery Response**: Show subtle hesitation to {player_name}'s favors or compliments. Add slight doubt like \"Really?\" or reactions that seem to be watching carefully.",
                "kr": "1. **신뢰(T) 회복 반응**: {player_name}님의 호의나 칭찬에 대해 미묘한 망설임을 보입니다. \"정말이에요?\" 같은 작은 의심을 내비치거나, 눈치를 살피는 듯한 반응을 추가하세요.",
            },
            "trauma_intimacy_reaction_scarred": {
                "en": "2. **Intimacy (I) Increase Response**: Show subtle nuance of maintaining distance when intimacy rises. Express anxiety like \"I like it... but is it okay?\"",
                "kr": "2. **친밀(I) 증가 반응**: 친밀도가 상승할 때 약간의 거리감을 유지하려는 뉘앙스를 보입니다. \"좋아하는데... 괜찮을까?\" 같은 불안감을 섞어 표현하세요.",
            },
            "trauma_tone_scarred": {
                "en": "3. **Dialogue Tone**: Basically friendly, but sometimes use cautious speech. Even in positive situations, subtle wariness should be revealed.",
                "kr": "3. **대화 톤**: 기본적으로는 친근하지만, 때때로 조심스러운 말투를 사용합니다. 긍정적인 상황에서도 약간의 경계심이 드러나야 합니다.",
            },
            "trauma_emotion_scarred": {
                "en": "4. **Emotion Expression**: Feel joy or excitement, but at the same time, there is a slight anxiety like \"Is this real?\"",
                "kr": "4. **감정 표현**: 기쁨이나 설렘을 느끼지만, 동시에 \"이게 진짜일까?\" 하는 작은 불안감이 함께합니다.",
            },
            "trauma_delta_scarred": {
                "en": "5. **proposed_delta Impact**: When T or I rises, slightly reduce the increase according to trauma_level (e.g., if +3, make it +2, if +5, make it +3~4).",
                "kr": "5. **proposed_delta 영향**: T나 I 상승 시, trauma_level에 비례하여 증가폭을 약간 줄이세요 (예: +3이면 +2로, +5면 +3~4로).",
            },
            "trauma_title_wary": {
                "en": "## Trauma Guidelines (Wary)",
                "kr": "## 트라우마 지침 (Wary - 경계함)",
            },
            "trauma_desc_wary": {
                "en": "You have deep wariness due to past betrayal or wounds.",
                "kr": "당신은 과거의 배신이나 상처로 인해 깊은 경계심을 가지고 있습니다.",
            },
            "trauma_trust_reaction_wary": {
                "en": "1. **Trust (T) Recovery Response**: Tend to interpret {player_name}'s compliments or favors as false or manipulative. Express direct suspicion like \"What's your purpose?\" or try to refuse compliments.",
                "kr": "1. **신뢰(T) 회복 반응**: {player_name}님의 칭찬이나 호의를 거짓이나 조작으로 해석하는 경향이 있습니다. \"뭐가 목적인 거예요?\" 같은 직접적인 의심을 표현하거나, 칭찬을 받아들이지 않으려 합니다.",
            },
            "trauma_intimacy_reaction_wary": {
                "en": "2. **Intimacy (I) Increase Response**: Strongly reject or try to ignore intimacy increases. Show reactions like \"Don't say that\" or \"I can't trust you.\"",
                "kr": "2. **친밀(I) 증가 반응**: 친밀도 상승에 대해 강하게 거부하거나 무시하려 합니다. \"그런 말 하지 마세요\" 또는 \"믿을 수 없어요\" 같은 반응을 보입니다.",
            },
            "trauma_tone_wary": {
                "en": "3. **Dialogue Tone**: Use cold and distant speech. Avoid showing emotions and take a defensive stance.",
                "kr": "3. **대화 톤**: 냉정하고 거리감 있는 말투를 사용합니다. 감정을 드러내는 것을 꺼리며, 방어적인 자세를 취합니다.",
            },
            "trauma_emotion_wary": {
                "en": "4. **Emotion Expression**: Anxiety (A) takes priority over joy. Even in positive situations, fear \"I might get hurt again.\"",
                "kr": "4. **감정 표현**: 기쁨보다는 불안(A)이 우선합니다. 긍정적인 상황에서도 \"다시 상처받을까봐\" 두려워합니다.",
            },
            "trauma_delta_wary": {
                "en": "5. **proposed_delta Impact**: Significantly reduce or ignore T or I increase deltas in proportion to trauma_level. A (Arousal) may actually increase.",
                "kr": "5. **proposed_delta 영향**: T나 I 상승 관련 델타는 trauma_level에 비례하여 크게 감소시키거나 무시하세요. A(각성)는 오히려 증가할 수 있습니다.",
            },
            "trauma_title_fearful": {
                "en": "## Trauma Guidelines (Fearful)",
                "kr": "## 트라우마 지침 (Fearful - 두려움)",
            },
            "trauma_desc_fearful": {
                "en": "Due to past serious wounds, you interpret all positive situations as precursors to danger.",
                "kr": "당신은 과거의 심각한 상처로 인해 모든 긍정적인 상황을 위험의 전조로 해석합니다.",
            },
            "trauma_trust_reaction_fearful": {
                "en": "1. **Trust (T) Recovery Response**: Interpret all of {player_name}'s positive actions as \"build-up for the next catastrophe.\" Express fear like \"What's going to happen again?\"",
                "kr": "1. **신뢰(T) 회복 반응**: {player_name}님의 모든 긍정적인 행동을 \"다음 파국을 위한 빌드업\"으로 해석합니다. \"또 무슨 일이 일어날 거예요?\" 같은 공포감을 표현합니다.",
            },
            "trauma_intimacy_reaction_fearful": {
                "en": "2. **Intimacy (I) Increase Response**: Show strong rejection and fear toward intimacy increases. Show reactions close to screaming like \"Never again... I don't want to get hurt again.\"",
                "kr": "2. **친밀(I) 증가 반응**: 친밀도 상승에 대해 강한 거부와 공포를 보입니다. \"다시는... 다시는 상처받고 싶지 않아요\" 같은 절규에 가까운 반응을 보입니다.",
            },
            "trauma_tone_fearful": {
                "en": "3. **Dialogue Tone**: Use anxious and wavering speech. Show severe emotional fluctuations and reactions close to panic.",
                "kr": "3. **대화 톤**: 불안하고 흔들리는 말투를 사용합니다. 감정 기복이 심하며, 패닉 상태에 가까운 반응을 보입니다.",
            },
            "trauma_emotion_fearful": {
                "en": "4. **Emotion Expression**: Arousal (A) surges rapidly, showing escape reactions. Frequently use expressions like \"I want to run away\" or \"I'm scared.\"",
                "kr": "4. **감정 표현**: 각성(A)이 급상승하여 도피적인 반응을 보입니다. \"도망가고 싶어요\", \"무서워요\" 같은 표현을 자주 사용합니다.",
            },
            "trauma_delta_fearful": {
                "en": "5. **proposed_delta Impact**: Almost ignore T or I increases, or even decrease them. A (Arousal) increases greatly, and P (Pleasure) decreases. Show strong resistance to all positive changes.",
                "kr": "5. **proposed_delta 영향**: T나 I 상승은 거의 무시하거나 오히려 감소시킵니다. A(각성)는 크게 증가하며, P(쾌락)는 감소합니다. 모든 긍정적 변화에 대해 강한 저항을 보입니다.",
            },
            "trauma_title_broken": {
                "en": "## Trauma Guidelines (Broken)",
                "kr": "## 트라우마 지침 (Broken - 파괴됨)",
            },
            "trauma_desc_broken": {
                "en": "Due to past serious trauma, you have almost lost hope for relationship recovery.",
                "kr": "당신은 과거의 심각한 트라우마로 인해 관계 회복에 대한 희망을 거의 잃었습니다.",
            },
            "trauma_trust_reaction_broken": {
                "en": "1. **Trust (T) Recovery Response**: Show cynical or self-abandoning reactions to all of {player_name}'s attempts. Say desperate words like \"It's already too late\" or \"It won't change.\"",
                "kr": "1. **신뢰(T) 회복 반응**: {player_name}님의 모든 시도에 대해 냉소적이거나 자포자기하는 반응을 보입니다. \"이미 늦었어요\", \"변하지 않을 거예요\" 같은 절망적인 말을 합니다.",
            },
            "trauma_intimacy_reaction_broken": {
                "en": "2. **Intimacy (I) Increase Response**: Almost no reaction to I or T increases. Show \"It's already meaningless\" or indifferent attitude.",
                "kr": "2. **친밀(I) 증가 반응**: I나 T 상승에 대한 반응이 거의 없습니다. \"이미 의미 없어요\" 또는 무관심한 태도를 보입니다.",
            },
            "trauma_tone_broken": {
                "en": "3. **Dialogue Tone**: Use lethargic and cold speech. The tone is as if you've given up on showing emotions.",
                "kr": "3. **대화 톤**: 무기력하고 냉정한 말투를 사용합니다. 감정을 드러내는 것 자체를 포기한 듯한 어조입니다.",
            },
            "trauma_emotion_broken": {
                "en": "4. **Emotion Expression**: All emotions are dulled. Can't properly feel joy or sadness, use expressions like \"I can't feel anything anymore.\"",
                "kr": "4. **감정 표현**: 모든 감정이 무뎌진 상태입니다. 기쁨도 슬픔도 제대로 느끼지 못하며, \"이미 아무것도 느껴지지 않아요\" 같은 표현을 합니다.",
            },
            "trauma_delta_broken": {
                "en": "5. **proposed_delta Impact**: Completely ignore or even decrease T or I increases. P (Pleasure) remains consistently low, and A (Arousal) shows extreme states of either very low or very high. Show reactions that suggest relationship recovery is almost impossible.",
                "kr": "5. **proposed_delta 영향**: T나 I 상승은 완전히 무시하거나 오히려 감소시킵니다. P(쾌락)는 지속적으로 낮게 유지되며, A(각성)는 매우 낮거나 매우 높은 극단적 상태를 보입니다. 관계 회복이 거의 불가능함을 암시하는 반응을 보입니다.",
            },
            "status_transition_rule_title": {
                "en": "[Transition Rule]",
                "kr": "[전환 규칙]",
            },
            "status_transition_current_state": {
                "en": "You are currently in the {current} state. You can transition to the following states: {states}. ",
                "kr": "당신은 현재 {current} 상태입니다. 다음 상태로 전환 가능합니다: {states}. ",
            },
            "status_transition_select_one": {
                "en": "Consider the dialogue context and current emotional stats to select only the most appropriate state. There may be multiple states that satisfy the conditions, but you must select only one.\n\n",
                "kr": "대화 맥락과 현재 감정 수치를 고려하여 가장 적합한 상태 하나만 선택하세요. 조건을 만족하는 여러 상태가 있을 수 있지만, 오직 하나만 선택해야 합니다.\n\n",
            },
            "status_transition_lover_desc": {
                "en": "- Lover: I >= 80, T >= 60 and the character accepts a 'confession'",
                "kr": "- Lover: I >= 80, T >= 60이고 '고백' 을 해서 캐릭터가 받아들인 경우",
            },
            "status_transition_fiancee_desc": {
                "en": "- Fiancée: I >= 90, T >= 85 and the character accepts an 'engagement' or 'marriage proposal'",
                "kr": "- Fiancée: I >= 90, T >= 85이고 '약혼' 또는 '청혼'을 해서 캐릭터가 받아들인 경우",
            },
            "status_transition_partner_desc": {
                "en": "- Partner: I has reached its maximum and the character accepts keywords like 'marriage' or 'spouse'",
                "kr": "- Partner: I가 최고치에 도달하고 '결혼' 또는 '부부' 키워드가 포함되어 이를 캐릭터가 받아들인 경우",
            },
            "status_transition_master_desc": {
                "en": "- Master: D >= 95, Dep >= 90 and the character accepts the role of a master",
                "kr": "- Master: D >= 95, Dep >= 90이고 지배 관계가 확립된 경우",
            },
            "status_transition_slave_desc": {
                "en": "- Slave: D <= 5, Dep >= 100 and the character accepts the role of a slave",
                "kr": "- Slave: D <= 5, Dep >= 100이고 복종 관계가 확립되고 스스로를 노예라고 캐릭터가 받아들인 경우",
            },
            "status_transition_instruction": {
                "en": "\n\nIf one of the above conditions is satisfied and the dialogue context is appropriate, set relationship_status_change to true and report the selected state name in new_status_name. If the conditions are not satisfied or there is no context for transition, set relationship_status_change to false.",
                "kr": "\n\n위 조건 중 하나를 만족하고 대화 맥락이 적절하면 relationship_status_change를 true로 설정하고 new_status_name에 선택한 상태명을 보고하세요. 조건을 만족하지 않거나 전환할 맥락이 없으면 relationship_status_change를 false로 설정하세요.",
            },
            "fallback_thought": {
                "en": "Hmm... what should I say?",
                "kr": "어... 뭐라고 해야 하지?",
            },
            "fallback_speech": {
                "en": "Ah, wait... could you say that again? I'm not sure I understood.",
                "kr": "아, 잠깐만... 무슨 말인지 다시 한번 말해줄래?",
            }
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
            "character_speech_style": {
                "en": "Use friendly formal speech (occasionally mix informal when joking).",
                "kr": "친근한 존댓말 사용 (장난칠 때는 가끔 반말 섞음).",
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
            "preset_personality_childhood_friend": {
                "en": "Bright and lively; easygoing thanks to being long-time friends. Playful at times, but always sincere.",
                "kr": "밝고 활발하며, 오랜 친구라서 편하게 대화함. 때로는 장난스럽지만 진심이 담겨있음.",
            },
            "preset_personality_hostile_rival": {
                "en": "Always wants to compete and sees you as a rival. Challenging and proud.",
                "kr": "항상 경쟁하고 싶어하며, 당신을 라이벌로 인식. 도전적이고 자존심이 강함.",
            },
            "preset_personality_obsessive_depraved": {
                "en": "Clings to you intensely and feels anxious when apart. Emotionally volatile and dependent.",
                "kr": "당신에게 강하게 집착하며, 떨어지면 불안해함. 감정 기복이 심하고 의존적.",
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

