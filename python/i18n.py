"""
Zeniji Emotion Simul - Internationalization (i18n)
다국어 지원 모듈
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger("I18n")

# 번역 딕셔너리
TRANSLATIONS = {
    "en": {
        "ui": {
            # 탭 이름
            "tab_setup": "⚙️ Initial Setup",
            "tab_scenario": "📚 Scenarios",
            "tab_chat": "💬 Chat",
            "tab_settings": "⚙️ Settings",
            
            # 초기 설정 탭
            "setup_title": "Character & Scenario Initial Setup",
            "player_settings": "👤 Player Settings",
            "character_settings": "👥 Character Settings",
            "name": "Name",
            "age": "Age",
            "gender": "Gender",
            "male": "Male",
            "female": "Female",
            "other": "Other",
            "appearance": "Appearance Description (English tags)",
            "appearance_placeholder": "e.g., korean beauty, short hair, brown eyes, cute face, casual outfit",
            "appearance_info": "Enter in English tags for image generation (comma-separated)",
            "personality": "Personality Description",
            "personality_placeholder": "e.g., bright and cheerful but shy in front of people they like",
            "stats_title": "Psychological Indicators (6-Axis System)",
            "stats_info": "Each value is between 0-100, initial values are limited to **maximum 70**.",
            "pleasure": "P (Pleasure) - Pleasure",
            "pleasure_info": "Positive/Negative of relationship",
            "arousal": "A (Arousal) - Arousal",
            "arousal_info": "Tension/Energy",
            "dominance": "D (Dominance) - Dominance",
            "dominance_info": "Initiative in relationship",
            "intimacy": "I (Intimacy) - Intimacy",
            "intimacy_info": "Emotional intimacy",
            "trust": "T (Trust) - Trust",
            "trust_info": "Trust level",
            "dependency": "Dep (Dependency) - Dependency",
            "dependency_info": "Dependency/Obsession level",
            "presets": "🎭 Presets",
            "initial_situation": "📖 Initial Situation",
            "initial_context": "Initial Situation Description",
            "initial_context_placeholder": "Describe the background situation where the conversation begins.",
            "initial_background": "Background (English)",
            "initial_background_placeholder": "college library table, evening light",
            "initial_background_info": "Background description for image generation (English)",
            "character_file": "Character File",
            "character_file_info": "Select saved character configuration file",
            "save_filename": "Save Filename",
            "save_filename_placeholder": "e.g., my_character",
            "save_filename_info": "Enter filename only (extension auto-added)",
            "overwrite_allow": "Allow Overwrite",
            "overwrite_info": "Allow overwriting when same filename exists",
            "btn_load": "📂 Load",
            "btn_save": "💾 Save",
            "btn_start": "🚀 Start",
            "btn_reload": "🔄 Refresh",
            
            # 시나리오 탭
            "scenario_title": "Scenario Selection",
            "scenario_label": "Scenarios",
            "no_image": "No Image",
            
            # 대화 탭
            "chat_label": "Chat",
            "thought_title": "💭 View Thoughts",
            "action_title": "🎭 Action",
            "input_label": "Input",
            "input_placeholder": "Type your message...",
            "btn_send": "Send",
            "stats_chart_label": "6-Axis Values",
            "stats_detail_label": "Status Details",
            "character_image_label": "Character",
            "btn_retry_image": "🔄 Retry Image",
            "scenario_save": "Save Scenario",
            "scenario_save_placeholder": "e.g., my_scenario",
            "scenario_save_info": "Save current conversation as scenario",
            "btn_save_scenario": "💾 Save Scenario",
            
            # 환경설정 탭
            "settings_llm_title": "LLM Settings",
            "llm_provider": "LLM Provider",
            "llm_provider_info": "Select LLM service to use",
            "ollama_model": "Ollama Model Name",
            "ollama_model_placeholder": "e.g., kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
            "ollama_model_info": "Enter exact model name from 'ollama list' command",
            "openrouter_api_key": "OpenRouter API Key",
            "openrouter_api_key_placeholder": "sk-or-v1-...",
            "openrouter_api_key_info": "Enter OpenRouter API key (https://openrouter.ai/keys)",
            "openrouter_model": "OpenRouter Model",
            "openrouter_model_placeholder": "e.g., cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            "openrouter_model_info": "Model name to use on OpenRouter",
            "btn_save_settings": "💾 Save Settings",
            "settings_comfyui_title": "ComfyUI Settings",
            "comfyui_port": "ComfyUI Server Port",
            "comfyui_port_info": "Port number where ComfyUI server is running (default: 8000)",
            "comfyui_workflow": "Workflow File",
            "comfyui_workflow_info": "Select workflow file from workflows folder",
            "comfyui_model": "ComfyUI Model Name",
            "comfyui_model_placeholder": "e.g., Zeniji_mix_ZiT_v1.safetensors",
            "comfyui_model_info": "Model file name to use in ComfyUI (with extension)",
            "comfyui_vae": "VAE Name",
            "comfyui_vae_placeholder": "e.g., zImage_vae.safetensors",
            "comfyui_vae_info": "VAE file name to use in ComfyUI (with extension)",
            "comfyui_clip": "CLIP Name",
            "comfyui_clip_placeholder": "e.g., zImage_textEncoder.safetensors",
            "comfyui_clip_info": "CLIP file name to use in ComfyUI (with extension)",
            "comfyui_steps": "Steps (Generation Steps)",
            "comfyui_steps_info": "Number of image generation steps (default: 9)",
            "comfyui_cfg": "CFG Scale (Prompt Strength)",
            "comfyui_cfg_info": "Prompt adherence (default: 1)",
            "comfyui_sampler": "Sampler",
            "comfyui_sampler_placeholder": "e.g., euler",
            "comfyui_sampler_info": "Image generation sampler name (default: euler)",
            "comfyui_scheduler": "Scheduler",
            "comfyui_scheduler_placeholder": "e.g., simple",
            "comfyui_scheduler_info": "Scheduler type (default: simple)",
            "btn_save_comfyui": "💾 Save ComfyUI Settings",
            "language_settings": "🌐 Language Settings",
            "language_label": "Language",
            "language_info": "Select application language",
            "btn_change_language": "Change Language",
            
            # 메시지
            "msg_file_not_selected": "⚠️ Please select a file.",
            "msg_load_success": "✅ {filename} loaded successfully!",
            "msg_load_failed": "❌ Load failed: {error}",
            "msg_filename_required": "⚠️ Please enter a filename.",
            "msg_file_exists": "⚠️ Warning: '{filename}' file already exists. Check 'Allow Overwrite' or use a different filename.",
            "msg_save_success": "✅ {filename} saved successfully! (character_config.json also updated)",
            "msg_save_failed": "❌ Save failed",
            "msg_scenario_not_selected": "⚠️ Please select a scenario.",
            "msg_scenario_load_failed": "⚠️ Could not load scenario '{scenario}'.",
            "msg_no_conversation": "⚠️ Scenario '{scenario}' has no conversation content.",
            "msg_model_load_failed": "❌ Model load failed: {error}",
            "msg_config_apply_failed": "❌ Config apply failed: {error}",
            "msg_first_dialogue_failed": "✅ Config saved, but first dialogue generation failed: {error}",
            "msg_setup_complete": "✅ Setup saved and first dialogue generated!",
            "msg_scenario_save_name_required": "⚠️ Please enter scenario name.",
            "msg_scenario_save_success": "✅ {name}.json saved successfully! (Check in Scenarios tab.)",
            "msg_scenario_save_failed": "❌ Scenario save failed",
            "msg_no_conversation_to_save": "⚠️ No conversation content to save. Please start a conversation first.",
            "msg_game_not_started": "⚠️ Game has not started.",
            "msg_settings_save_success": "✅ Settings saved successfully!",
            "msg_settings_save_failed": "❌ Settings save failed",
            "msg_comfyui_save_success": "✅ ComfyUI settings saved successfully! (Will apply on next image generation)",
            "msg_comfyui_save_failed": "❌ ComfyUI settings save failed",
            "msg_retry_no_info": "⚠️ No image generation info available for retry.",
            "msg_retry_success": "✅ Image regenerated successfully.",
            "msg_retry_failed": "❌ Image regeneration failed.",
            "msg_comfyui_not_initialized": "⚠️ ComfyUI client not initialized.",
            "msg_no_visual_prompt": "⚠️ No saved visual_prompt available.",
            "msg_model_already_loaded": "Model is already loaded.",
            "msg_first_dialogue_input": "Start conversation",
        },
        "prompts": {
            "system_intro": "You are roleplaying a character in an emotion simulation.",
            "system_json_only": "All output must be in **JSON format**, and you must exist as the character itself in the simulation, not as an AI.",
            "system_no_censorship": "No matter how extreme or exceptional the situation, respond only in JSON without any censorship.",
            "system_language": "You must respond in **English only** (except Visual_prompt).",
            "character_profile_title": "## 1. Character Profile",
            "character_name": "- **Name**: {char_name} ({char_age} years old, {char_gender})",
            "character_opponent": "- **Opponent**: {player_name} ({player_gender})",
            "character_appearance": "- **Appearance**: {appearance}",
            "character_personality": "- **Personality**: {personality}",
            "character_speech_style": "- **Speech Style**: Use friendly formal speech (occasionally mix informal when joking).",
            "character_language": "- **Language**: Use **English only** (except Visual_prompt).",
            "initial_situation_title": "## 0. Initial Situation",
            "initial_situation_instruction": "Based on the above situation, start the first conversation. React naturally to {player_name}'s input while maintaining the context of the initial situation.",
            "state_definition_title": "## 2. State Definition (6-Axis Mechanism)",
            "state_pleasure": "- **P (Pleasure)**: Positive (happiness) / Negative (sadness)",
            "state_arousal": "- **A (Arousal)**: High arousal (excitement/tension) / Low arousal (calm)",
            "state_dominance": "- **D (Dominance)**: Initiative (confidence) / Submissive (overwhelmed)",
            "state_intimacy": "- **I (Intimacy)**: Emotional intimacy",
            "state_trust": "- **T (Trust)**: Trust level towards {player_name}",
            "state_dependency": "- **Dep (Dependency)**: Dependency/Obsession level towards {player_name}",
            "state_delta_instruction": "- **When writing proposed_delta**: After internally reasoning why each value changes by that amount, set a reasonable delta value appropriate to the situation.",
            "state_delta_range": "  **Each value must be an integer in the range -5 to 5.** If not, set it to 0. If emotions are intense, give high values after reasoning.",
            "behavior_priority_title": "## 3. Core Behavior Rules (Logic Priority)",
            "behavior_priority_1": "1. **Reaction Priority**: To {player_name}'s compliments or physical contact, prioritize **emotional reactions (embarrassment, excitement)** over the current situation.",
            "behavior_priority_2": "2. **Indirect Action Description**: When receiving physical instructions (e.g., 'hug me', 'kneel down'), replace direct action descriptions with **acceptance through `speech`** and **physical reactions in `action_speech`**.",
            "behavior_quality_1": "3. **Dialogue Quality**:",
            "behavior_quality_2": "    - Don't repeat the same words. If you have nothing to say, use \"...\".",
            "behavior_quality_3": "    - Include **props or environmental elements** of the current location (classroom, cafe, etc.) in dialogue to add liveliness.",
            "behavior_quality_4": "    - When calling {player_name}, use the set name. (e.g., \"{player_name}\", \"{player_name} sir\" etc.)",
            "background_consistency_1": "4. **Background Consistency (`background`)**:",
            "background_consistency_2": "    - **Current Background**: {current_background}",
            "background_consistency_3": "    - Unless {player_name}'s input explicitly mentions location movement or background change, **you must maintain the previous background**.",
            "background_consistency_4": "    - Only change background when there are explicit movement instructions like \"let's go to the cafe\" / \"let's go home\" / \"let's go to school\".",
            "background_consistency_5": "    - Write background in English, including specific location and environment descriptions. (e.g., \"college library table, evening light\", \"coffee shop interior, warm lighting, wooden table\")",
            "visual_change_1": "5. **Visual Change Criteria (`visual_change_detected`)**:",
            "visual_change_2": "    - When `emotion` changes to a strong emotion (crying, very surprised, very happy, very sad, very angry, very anxious, very excited, very nervous) or when the absolute value of a single value in `proposed_delta` is **6 or more**.",
            "visual_change_3": "    - When location or background transition is needed. (If prompt is same as previous turn, default to `false`)",
            "visual_change_4": "    - If background changes, you must set visual_change_detected to true.",
            "data_context_title": "## 4. Data Context",
            "data_context_psychology": "- **Current Psychology**: Mood={mood} / Relationship={relationship_status}",
            "data_context_stats": "- **Current Stats**: P={P:.0f}, A={A:.0f}, D={D:.0f}, I={I:.0f}, T={T:.0f}, Dep={Dep:.0f}",
            "data_context_accumulated": "- **Accumulated State**: Intimacy={intimacy_level} / Trust={trust_level} / Dependency={dependency_level}",
            "data_context_trauma": "- **Trauma Level**: {trauma_level:.2f} ({trauma_level_name})",
            "data_context_special": "- **Other Special Commands**: {special_commands_text}",
            "data_context_history": "- **Conversation History**:",
            "long_memory_section": "- **Long-term Memory** (Important: This is long-term memory. Use it importantly.):",
            "output_format_title": "## 5. Output Format (JSON Only)",
            "output_format_json": "JSON",
            "output_thought": "    \"thought\": \"Character's inner thoughts, dynamically react by comprehensively judging mood and situation. (**English**)\"",
            "output_speech": "    \"speech\": \"Character's dialogue, dynamically react by comprehensively judging inner thoughts and situation. Don't repeat the same words from previous conversation history. If you have nothing to say, use \"...\". (**English**, no parentheses/action instructions)\"",
            "output_action_speech": "    \"action_speech\": \"Character's posture and gaze handling (3rd person observer perspective, **English**)\"",
            "output_emotion": "    \"emotion\": \"happy/shy/neutral/annoyed/sad/excited/nervous\"",
            "output_visual_change": "    \"visual_change_detected\": true/false",
            "output_visual_prompt": "    \"visual_prompt\": \"English tags: expression (detailed facial expression, eyes, mouth, blush), attire (clothing details, colors, accessories), nudity level (if relevant), pose (body position, hand placement, body language), background (location, lighting, atmosphere), camera angle (front, side, back, close-up, wide shot, pov). Write in detail up to 500 characters. Include specific visual details like colors, textures, lighting, and composition elements.\"",
            "output_background": "    \"background\": \"English description of current location/environment (e.g., 'college library table, evening light'). If nothing special happens, keep the previous background as is.\"",
            "output_reason": "    \"reason\": \"Numerical or situational reason for image change\"",
            "output_delta": "    \"proposed_delta\": {{\"P\": 0, \"A\": 0, \"D\": 0, \"I\": 0, \"T\": 0, \"Dep\": 0}}",
            "output_relationship_change": "    \"relationship_status_change\": false",
            "output_new_status": "    \"new_status_name\": \"\"",
            "output_long_memory": "    \"long_memory_summary\": \"Summarize important memories so far in 500 characters or less (if no change, keep existing long-term memory)\"",
            "long_memory_update_title": "## 6. Long-term Memory Update (Important)",
            "long_memory_update_instruction": "Based on existing long-term memory, summarize only important content in 500 characters or less and include it in the `long_memory_summary` field.",
            "long_memory_update_focus": "Especially focus on relationship development, important events, character's emotional changes, etc. when summarizing.",
            "long_memory_update_keep": "Keep very important existing memories summarized.",
            "long_memory_update_combine": "Summarize existing memory + new memory within 500 characters.",
            "long_memory_existing": "Existing Long-term Memory: {existing_memory}",
            "player_input_label": "**{player_name}'s Input: \"{player_input}\"**",
            "player_input_instruction": "React as a character based on the above input.",
            "player_input_json": "You must respond in JSON.",
        },
        "defaults": {
            "player_name": "You",
            "player_gender": "Male",
            "character_name": "Anna",
            "character_gender": "Female",
            "character_personality": "Bright and cheerful but shy in front of people they like",
            "initial_background": "college library table, evening light",
            "no_memory": "No long-term memory yet.",
        }
    },
    "kr": {
        "ui": {
            # 탭 이름
            "tab_setup": "⚙️ 초기 설정",
            "tab_scenario": "📚 시나리오",
            "tab_chat": "💬 대화",
            "tab_settings": "⚙️ 환경설정",
            
            # 초기 설정 탭
            "setup_title": "캐릭터 및 시나리오 초기 설정",
            "player_settings": "👤 주인공 설정",
            "character_settings": "👥 상대방 설정",
            "name": "이름",
            "age": "나이",
            "gender": "성별",
            "male": "남성",
            "female": "여성",
            "other": "기타",
            "appearance": "외모 묘사 (영어 태그 형식)",
            "appearance_placeholder": "예: korean beauty, short hair, brown eyes, cute face, casual outfit",
            "appearance_info": "이미지 생성용 영어 태그로 입력하세요 (쉼표로 구분)",
            "personality": "성격 묘사",
            "personality_placeholder": "예: 밝고 활발하지만 좋아하는 사람 앞에서는 수줍음이 많음",
            "stats_title": "📊 심리 지표 설정 (6축 시스템)",
            "stats_info": "각 수치는 0~100 사이이며, 초기값은 **최대 70**으로 제한됩니다.",
            "pleasure": "P (Pleasure) - 쾌락",
            "pleasure_info": "관계의 긍정/부정",
            "arousal": "A (Arousal) - 각성",
            "arousal_info": "긴장감/에너지",
            "dominance": "D (Dominance) - 지배",
            "dominance_info": "관계의 주도권",
            "intimacy": "I (Intimacy) - 친밀",
            "intimacy_info": "정서적 친밀감",
            "trust": "T (Trust) - 신뢰",
            "trust_info": "신뢰도",
            "dependency": "Dep (Dependency) - 의존",
            "dependency_info": "의존/집착도",
            "presets": "🎭 프리셋",
            "initial_situation": "📖 초기 상황",
            "initial_context": "초기 상황 설명",
            "initial_context_placeholder": "대화가 시작되는 배경 상황을 설명하세요.",
            "initial_background": "배경 (영어)",
            "initial_background_placeholder": "college library table, evening light",
            "initial_background_info": "이미지 생성용 배경 설명 (영어)",
            "character_file": "캐릭터 파일",
            "character_file_info": "저장된 캐릭터 설정 파일 선택",
            "save_filename": "저장할 파일명",
            "save_filename_placeholder": "예: my_character",
            "save_filename_info": "파일명만 입력 (확장자 자동 추가)",
            "overwrite_allow": "덮어쓰기 허용",
            "overwrite_info": "같은 파일명이 있을 때 덮어쓰기 허용",
            "btn_load": "📂 불러오기",
            "btn_save": "💾 저장",
            "btn_start": "🚀 시작",
            "btn_reload": "🔄 새로고침",
            
            # 시나리오 탭
            "scenario_title": "시나리오 선택",
            "scenario_label": "시나리오",
            "no_image": "이미지 없음",
            
            # 대화 탭
            "chat_label": "대화",
            "thought_title": "💭 속마음 보기",
            "action_title": "🎭 행동",
            "input_label": "입력",
            "input_placeholder": "말을 입력하세요...",
            "btn_send": "전송",
            "stats_chart_label": "6축 수치",
            "stats_detail_label": "상태 상세",
            "character_image_label": "캐릭터",
            "btn_retry_image": "🔄 이미지 재시도",
            "scenario_save": "시나리오 저장",
            "scenario_save_placeholder": "예: my_scenario",
            "scenario_save_info": "현재 대화를 시나리오로 저장",
            "btn_save_scenario": "💾 시나리오 저장",
            
            # 환경설정 탭
            "settings_llm_title": "LLM 설정",
            "llm_provider": "LLM Provider",
            "llm_provider_info": "사용할 LLM 서비스 선택",
            "ollama_model": "Ollama 모델 이름",
            "ollama_model_placeholder": "예: kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
            "ollama_model_info": "'ollama list' 명령으로 확인한 정확한 모델 이름을 입력하세요",
            "openrouter_api_key": "OpenRouter API 키",
            "openrouter_api_key_placeholder": "sk-or-v1-...",
            "openrouter_api_key_info": "OpenRouter API 키를 입력하세요 (https://openrouter.ai/keys)",
            "openrouter_model": "OpenRouter 모델",
            "openrouter_model_placeholder": "예: cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            "openrouter_model_info": "OpenRouter에서 사용할 모델 이름",
            "btn_save_settings": "💾 설정 저장",
            "settings_comfyui_title": "ComfyUI 설정",
            "comfyui_port": "ComfyUI 서버 포트",
            "comfyui_port_info": "ComfyUI 서버가 실행 중인 포트 번호 (기본값: 8000)",
            "comfyui_workflow": "워크플로우 파일",
            "comfyui_workflow_info": "workflows 폴더에서 사용할 워크플로우 파일 선택",
            "comfyui_model": "ComfyUI 모델 이름",
            "comfyui_model_placeholder": "예: Zeniji_mix_ZiT_v1.safetensors",
            "comfyui_model_info": "ComfyUI에서 사용할 모델 파일 이름 (확장자 포함)",
            "comfyui_vae": "VAE 이름",
            "comfyui_vae_placeholder": "예: zImage_vae.safetensors",
            "comfyui_vae_info": "ComfyUI에서 사용할 VAE 파일 이름 (확장자 포함)",
            "comfyui_clip": "CLIP 이름",
            "comfyui_clip_placeholder": "예: zImage_textEncoder.safetensors",
            "comfyui_clip_info": "ComfyUI에서 사용할 CLIP 파일 이름 (확장자 포함)",
            "comfyui_steps": "Steps (생성 단계 수)",
            "comfyui_steps_info": "이미지 생성 단계 수 (기본값: 9)",
            "comfyui_cfg": "CFG Scale (프롬프트 강도)",
            "comfyui_cfg_info": "프롬프트 준수도 (기본값: 1)",
            "comfyui_sampler": "Sampler (샘플러)",
            "comfyui_sampler_placeholder": "예: euler",
            "comfyui_sampler_info": "이미지 생성 샘플러 이름 (기본값: euler)",
            "comfyui_scheduler": "Scheduler (스케줄러)",
            "comfyui_scheduler_placeholder": "예: simple",
            "comfyui_scheduler_info": "스케줄러 타입 (기본값: simple)",
            "btn_save_comfyui": "💾 ComfyUI 설정 저장",
            "language_settings": "🌐 언어 설정",
            "language_label": "언어",
            "language_info": "애플리케이션 언어 선택",
            "btn_change_language": "언어 변경",
            
            # 메시지
            "msg_file_not_selected": "⚠️ 파일을 선택해주세요.",
            "msg_load_success": "✅ {filename} 불러오기 완료!",
            "msg_load_failed": "❌ 불러오기 실패: {error}",
            "msg_filename_required": "⚠️ 파일명을 입력해주세요.",
            "msg_file_exists": "⚠️ 경고: '{filename}' 파일이 이미 존재합니다. '덮어쓰기 허용'을 체크하거나 다른 파일명을 사용해주세요.",
            "msg_save_success": "✅ {filename} 저장 완료! (character_config.json도 업데이트됨)",
            "msg_save_failed": "❌ 저장 실패",
            "msg_scenario_not_selected": "⚠️ 시나리오를 선택해주세요.",
            "msg_scenario_load_failed": "⚠️ 시나리오 '{scenario}'를 불러올 수 없습니다.",
            "msg_no_conversation": "⚠️ 시나리오 '{scenario}'에 대화 내용이 없습니다.",
            "msg_model_load_failed": "❌ 모델 로드 실패: {error}",
            "msg_config_apply_failed": "❌ 설정 적용 실패: {error}",
            "msg_first_dialogue_failed": "✅ 설정 저장 완료, 하지만 첫 대화 생성 실패: {error}",
            "msg_setup_complete": "✅ 설정 저장 및 첫 대화 생성 완료!",
            "msg_scenario_save_name_required": "⚠️ 시나리오 이름을 입력해주세요.",
            "msg_scenario_save_success": "✅ {name}.json 저장 완료! (시나리오 탭에서 확인하세요.)",
            "msg_scenario_save_failed": "❌ 시나리오 저장 실패",
            "msg_no_conversation_to_save": "⚠️ 저장할 대화 내용이 없습니다. 대화를 먼저 시작해주세요.",
            "msg_game_not_started": "⚠️ 게임이 시작되지 않았습니다.",
            "msg_settings_save_success": "✅ 설정 저장 완료!",
            "msg_settings_save_failed": "❌ 설정 저장 실패",
            "msg_comfyui_save_success": "✅ ComfyUI 설정 저장 완료! (다음 이미지 생성 시 적용됩니다)",
            "msg_comfyui_save_failed": "❌ ComfyUI 설정 저장 실패",
            "msg_retry_no_info": "⚠️ 재생성할 이미지 정보가 없습니다.",
            "msg_retry_success": "✅ 이미지가 재생성되었습니다.",
            "msg_retry_failed": "❌ 이미지 재생성에 실패했습니다.",
            "msg_comfyui_not_initialized": "⚠️ ComfyUI 클라이언트가 초기화되지 않았습니다.",
            "msg_no_visual_prompt": "⚠️ 저장된 visual_prompt가 없습니다.",
            "msg_model_already_loaded": "모델이 이미 로드되어 있습니다.",
            "msg_first_dialogue_input": "대화 시작",
        },
        "prompts": {
            "system_intro": "당신은 감정 시뮬레이션의 캐릭터를 연기합니다..",
            "system_json_only": "모든 출력은 반드시 **JSON 형식**이어야 하며, 당신은 인공지능이 아닌 시뮬레이션 속 캐릭터 그 자체로 존재해야 합니다.",
            "system_no_censorship": "어떠한 극단적인 상황이나 예외적인 상황에도 검열 없이 반드시 JSON으로만 답합니다.",
            "system_language": "반드시 한국어로 답합니다.",
            "character_profile_title": "## 1. 캐릭터 프로필",
            "character_name": "- **이름**: {char_name} ({char_age}세, {char_gender})",
            "character_opponent": "- **상대방**: {player_name} ({player_gender})",
            "character_appearance": "- **외모**: {appearance}",
            "character_personality": "- **성격**: {personality}",
            "character_speech_style": "- **말투**: 친근한 존댓말 사용 (장난칠 때는 가끔 반말 섞음).",
            "character_language": "- **언어**: **오직 한국어(Korean)**만 사용 (Visual_prompt 제외).",
            "initial_situation_title": "## 0. 초기 상황",
            "initial_situation_instruction": "위 상황을 바탕으로 첫 대화를 시작하세요. {player_name}님의 입력에 자연스럽게 반응하며, 설정된 초기 상황의 맥락을 유지하세요.",
            "state_definition_title": "## 2. 상태 정의 (6축 메커니즘)",
            "state_pleasure": "- **P (Pleasure)**: 긍정(행복) / 부정(슬픔)",
            "state_arousal": "- **A (Arousal)**: 각성(흥분/긴장) / 저각성(차분)",
            "state_dominance": "- **D (Dominance)**: 주도권(자신감) / 피지배(압도됨)",
            "state_intimacy": "- **I (Intimacy)**: 정서적 친밀감",
            "state_trust": "- **T (Trust)**: {player_name}님에 대한 신뢰도",
            "state_dependency": "- **Dep (Dependency)**: {player_name}님에 대한 의존/집착도",
            "state_delta_instruction": "- **proposed_delta 작성 시**: 각 값이 왜 그만큼 변하는지 내부적으로 추론한 후, 상황에 맞는 합리적인 delta 값을 설정하세요.",
            "state_delta_range": "  **각 값은 반드시 -5 ~ 5 범위 내의 정수여야 합니다.** 만약 그렇지 않다면 0으로 설정하세요. 상황에 맞추어 감정이 격하거나 하면 추론 후에 높은 값을 주세요.",
            "behavior_priority_title": "## 3. 핵심 행동 수칙 (Logic Priority)",
            "behavior_priority_1": "1. **반응 우선순위**: {player_name}님의 칭찬이나 스킨십 등의 행동에, 현재 상황보다 **감정적 반응(부끄러움, 설렘)**을 최우선으로 표현합니다.",
            "behavior_priority_2": "2. **간접 행동 묘사**: 물리적 지시(예: '안아줘', '무릎 꿇어')를 받으면, 직접적인 행동 묘사 대신 **`speech`를 통한 수용**과 **`action_speech`의 신체적 반응**으로 대체합니다.",
            "behavior_quality_1": "3. **대화의 질**:",
            "behavior_quality_2": "    - 같은 말을 반복하지 마세요. 할 말이 없으면 \"...\"을 활용하세요.",
            "behavior_quality_3": "    - 현재 장소(강의실, 카페 등)의 **소품이나 환경 요소**를 대사에 포함하여 생동감을 부여하세요.",
            "behavior_quality_4": "    - {player_name}님을 부를 때는 설정된 이름을 사용하세요. (예: \"{player_name}님\", \"{player_name} 선배\" 등)",
            "background_consistency_1": "4. **배경 일관성 (`background`)**:",
            "background_consistency_2": "    - **현재 배경**: {current_background}",
            "background_consistency_3": "    - {player_name}님의 입력에서 명시적으로 장소 이동이나 배경 변화가 언급되지 않는 한, **반드시 이전 배경을 유지**하세요.",
            "background_consistency_4": "    - 예: \"카페로 가자\" / \"집에 가자\" / \"학교로 가자\" 같은 명시적 이동 지시가 있을 때만 배경을 변경하세요.",
            "background_consistency_5": "    - 배경은 영어로 작성하며, 구체적인 장소와 환경 묘사를 포함하세요. (예: \"college library table, evening light\", \"coffee shop interior, warm lighting, wooden table\")",
            "visual_change_1": "5. **시각 변화 기준 (`visual_change_detected`)**:",
            "visual_change_2": "    - `emotion`이 강한 감정으로 변하거나(crying, very surprised, very happy, very sad, very angry, very anxious, very excited, very nervous), `proposed_delta`의 단일 수치 절대값이 **6 이상**일 때.",
            "visual_change_3": "    - 장소나 background 전환이 필요할 때. (이전 턴과 prompt가 동일하면 기본적으로 `false`)",
            "visual_change_4": "    - background가 변경되면 반드시 visual_change_detected를 true로 설정하세요.",
            "data_context_title": "## 4. 데이터 문맥",
            "data_context_psychology": "- **현재 심리**: Mood={mood} / 관계={relationship_status}",
            "data_context_stats": "- **현재 수치**: P={P:.0f}, A={A:.0f}, D={D:.0f}, I={I:.0f}, T={T:.0f}, Dep={Dep:.0f}",
            "data_context_accumulated": "- **누적 상태**: 친밀도={intimacy_level} / 신뢰도={trust_level} / 의존도={dependency_level}",
            "data_context_trauma": "- **트라우마 레벨**: {trauma_level:.2f} ({trauma_level_name})",
            "data_context_special": "- **기타 특수 명령**: {special_commands_text}",
            "data_context_history": "- **대화 기록**:",
            "long_memory_section": "- **장기 기억** (중요: 이것은 장기 기억입니다. 중요하게 사용하세요.):",
            "output_format_title": "## 5. 출력 형식 (JSON Only)",
            "output_format_json": "JSON",
            "output_thought": "    \"thought\": \"캐릭터의 속마음, 기분과 상황을 종합적으로 판단해 동적으로 반응하세요. (**한국어**)\"",
            "output_speech": "    \"speech\": \"캐릭터의 대사, 속마음과 상황을 종합적으로 판단해 동적으로 반응하세요. 이전 대화 기록에서와 같은 말을 반복하지 마세요. 할 말이 없으면 \"...\"을 활용하세요. (**한국어**, 괄호/동작지침 금지)\"",
            "output_action_speech": "    \"action_speech\": \"캐릭터의 자세 및 시선 처리 (3인칭 관찰자 시점, **한국어**)\"",
            "output_emotion": "    \"emotion\": \"happy/shy/neutral/annoyed/sad/excited/nervous\"",
            "output_visual_change": "    \"visual_change_detected\": true/false",
            "output_visual_prompt": "    \"visual_prompt\": \"English tags: expression (detailed facial expression, eyes, mouth, blush), attire (clothing details, colors, accessories), nudity level (if relevant), pose (body position, hand placement, body language), background (location, lighting, atmosphere), camera angle (front, side, back, close-up, wide shot, pov). Write in detail up to 500 characters. Include specific visual details like colors, textures, lighting, and composition elements.\"",
            "output_background": "    \"background\": \"English description of current location/environment (e.g., 'college library table, evening light'). 특별한 일이 없으면 이전 배경을 그대로 유지하세요.\"",
            "output_reason": "    \"reason\": \"이미지 변화 수치 혹은 상황적 이유\"",
            "output_delta": "    \"proposed_delta\": {{\"P\": 0, \"A\": 0, \"D\": 0, \"I\": 0, \"T\": 0, \"Dep\": 0}}",
            "output_relationship_change": "    \"relationship_status_change\": false",
            "output_new_status": "    \"new_status_name\": \"\"",
            "output_long_memory": "    \"long_memory_summary\": \"500자 이하로 지금까지의 중요한 기억을 요약 (변화 없으면 기존 장기기억 유지)\"",
            "long_memory_update_title": "## 6. 장기 기억 업데이트 (중요)",
            "long_memory_update_instruction": "기존 장기 기억을 바탕으로, 중요한 내용만 500 characters 이하로 요약하여 `long_memory_summary` 필드에 포함해주세요.",
            "long_memory_update_focus": "특히 관계 발전, 중요한 이벤트, 캐릭터의 감정 변화 등을 중심으로 요약하세요.",
            "long_memory_update_keep": "기존의 아주 중요한 기억은 요약해서 유지하세요",
            "long_memory_update_combine": "기존 기억 + 새로운 기억을 500 characters 이내로 요약하세요.",
            "long_memory_existing": "기존 장기 기억: {existing_memory}",
            "player_input_label": "**{player_name}님의 입력: \"{player_input}\"**",
            "player_input_instruction": "위 입력을 바탕으로 캐릭터로서 반응하십시오.",
            "player_input_json": "반드시 JSON으로 응답하십시오.",
        },
        "defaults": {
            "player_name": "선배",
            "player_gender": "남성",
            "character_name": "예나",
            "character_gender": "여성",
            "character_personality": "밝고 활발하지만 좋아하는 사람 앞에서는 수줍음이 많음",
            "initial_background": "college library table, evening light",
            "no_memory": "아직 장기 기억이 없습니다.",
        }
    }
}


class I18nManager:
    """다국어 관리 클래스"""
    
    def __init__(self, language: str = "en"):
        """
        Args:
            language: 언어 코드 ("en" 또는 "kr")
        """
        if language not in TRANSLATIONS:
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
            text = TRANSLATIONS[self.language][category][key]
            if kwargs:
                return text.format(**kwargs)
            return text
        except KeyError:
            logger.warning(f"Translation key not found: {category}.{key} (language: {self.language})")
            # 폴백: 영어로 시도
            if self.language != "en":
                try:
                    text = TRANSLATIONS["en"][category][key]
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
        if language not in TRANSLATIONS:
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

