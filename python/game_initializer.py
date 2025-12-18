"""
Game Initializer - 게임 시작 및 초기화 로직
"""

import gradio as gr
import logging
from typing import Tuple, Optional, Any
from PIL import Image
import io
import config
from comfy_client import ComfyClient
from brain import Brain
from i18n import get_i18n

logger = logging.getLogger("GameInitializer")


class GameInitializer:
    """게임 초기화 및 시작 처리"""
    
    @staticmethod
    def validate_and_start(
        app_instance,
        player_name, player_gender,
        char_name, char_age, char_gender,
        appearance, personality, speech_style,
        p_val, a_val, d_val, i_val, t_val, dep_val,
        initial_context, initial_background
    ) -> Tuple[str, str, list, str, str, str, str, str, str, Any, Any, Any]:
        """설정 검증 및 시작 (첫 대화 자동 생성)"""
        # Slider 값들이 None이면 기본값 사용
        p_val = p_val if p_val is not None else 50.0
        a_val = a_val if a_val is not None else 40.0
        d_val = d_val if d_val is not None else 40.0
        i_val = i_val if i_val is not None else 20.0
        t_val = t_val if t_val is not None else 50.0
        dep_val = dep_val if dep_val is not None else 0.0
        char_age = char_age if char_age is not None else 21
        
        # 최대값 검증 (70 제한)
        max_val = 70.0
        stats = {"P": p_val, "A": a_val, "D": d_val, "I": i_val, "T": t_val, "Dep": dep_val}
        exceeded = [k for k, v in stats.items() if v > max_val]
        
        # 에러 시 기본값 반환 (입력창 상태 포함)
        empty_result = (
            "⚠️ 경고: 다음 수치가 70을 초과합니다: " + ", ".join(exceeded) if exceeded else "❌ 오류 발생",
            gr.Tabs(selected=None),
            [], "", "", None, "", "", "", None,
            gr.Button(interactive=False), gr.Textbox(interactive=False)
        )
        
        if exceeded:
            return empty_result
        
        # 언어 설정 가져오기
        env_config = app_instance.load_env_config()
        language = env_config.get("language", "en")
        i18n = get_i18n()
        i18n.set_language(language)
        
        # 설정 데이터 구성
        config_data = {
            "player": {
                "name": player_name or "",
                "gender": player_gender or i18n.get_default("player_gender")
            },
            "character": {
                "name": char_name or i18n.get_default("character_name"),
                "age": int(char_age) if char_age else 21,
                "gender": char_gender or i18n.get_default("character_gender"),
                "appearance": appearance or "",
                "personality": personality or "",
                "speech_style": speech_style or i18n.get_default("character_speech_style")
            },
            "initial_stats": {
                "P": float(p_val),
                "A": float(a_val),
                "D": float(d_val),
                "I": float(i_val),
                "T": float(t_val),
                "Dep": float(dep_val)
            },
            "initial_context": initial_context or "",
            "initial_background": initial_background or i18n.get_default("initial_background")
        }
        
        # 저장하지 않고 바로 시작 (파일 저장은 save 버튼으로 별도 처리)
        
        # 모델 로드
        status_msg, success = app_instance.load_model()
        if not success:
            return (f"❌ 모델 로드 실패: {status_msg}", gr.Tabs(selected=None), [], "", "", None, "", "", "", None, gr.Button(interactive=False), gr.Textbox(interactive=False))
        
        # Brain 초기화 및 설정 적용
        try:
            # LLM 설정 읽기 (환경설정에서)
            env_config = app_instance.load_env_config()
            llm_settings = env_config.get("llm_settings", {})
            
            # 환경설정에서 provider 가져오기 (기본값: ollama)
            provider = llm_settings.get("provider", "ollama")
            
            # OpenRouter API 키는 파일에서 불러오기
            openrouter_api_key = app_instance._load_openrouter_api_key()
            
            # 설정된 provider에 따라 검증 및 폴백 처리
            if provider == "openrouter":
                if not openrouter_api_key or not openrouter_api_key.strip():
                    logger.warning("환경설정에서 OpenRouter가 선택되었지만 API 키가 없습니다. Ollama로 폴백합니다.")
                    provider = "ollama"
                    llm_settings["provider"] = "ollama"
                else:
                    logger.info("환경설정에 따라 OpenRouter를 사용합니다.")
            else:
                logger.info("환경설정에 따라 Ollama를 사용합니다.")
            ollama_model = llm_settings.get("ollama_model", "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest")
            openrouter_model = llm_settings.get("openrouter_model", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
            
            if app_instance.brain is None:
                model_name = ollama_model if provider == "ollama" else openrouter_model
                api_key = openrouter_api_key if provider == "openrouter" else None
                app_instance.brain = Brain(
                    dev_mode=app_instance.dev_mode,
                    provider=provider,
                    model_name=model_name,
                    api_key=api_key,
                    language=language
                )
            else:
                # Brain이 이미 존재하면 새 게임을 위해 상태 초기화
                logger.info("Resetting Brain state and history for new game")
                from state_manager import CharacterState, DialogueHistory
                app_instance.brain.state = CharacterState()
                app_instance.brain.history = DialogueHistory(max_turns=10)
                app_instance.brain.turns_since_image = 0
            
            # 기타 앱 인스턴스 상태 초기화
            app_instance.current_image = None
            app_instance.current_chart = None
            app_instance.previous_relationship = None
            app_instance.previous_badges = set()
            app_instance.last_image_generation_info = None
            
            # 초기 설정 정보 전달
            app_instance.brain.set_initial_config(config_data)
            
            # 초기 상태 적용
            app_instance.brain.state.P = config_data["initial_stats"]["P"]
            app_instance.brain.state.A = config_data["initial_stats"]["A"]
            app_instance.brain.state.D = config_data["initial_stats"]["D"]
            app_instance.brain.state.I = config_data["initial_stats"]["I"]
            app_instance.brain.state.T = config_data["initial_stats"]["T"]
            app_instance.brain.state.Dep = config_data["initial_stats"]["Dep"]
            app_instance.brain.state.current_background = config_data["initial_background"]
            app_instance.brain.state.clamp()
            
            logger.info("Initial configuration applied to Brain")
        except Exception as e:
            logger.error(f"Failed to apply config: {e}")
            return (f"❌ 설정 적용 실패: {str(e)}", gr.Tabs(selected=None), [], "", "", None, "", "", "", None, gr.Button(interactive=False), gr.Textbox(interactive=False))
        
        # 첫 대화 자동 생성
        try:
            logger.info("Generating first dialogue automatically...")
            # 초기 관계 상태 설정 (첫 턴 전에)
            if app_instance.brain and app_instance.brain.state:
                app_instance.previous_relationship = app_instance.brain.state.relationship_status
                logger.info(f"Initial relationship status set: {app_instance.previous_relationship}")
            
            # 첫 대화 입력 텍스트 (언어별)
            first_input = i18n.get_text("msg_first_dialogue_input", category="ui") if i18n.get_text("msg_first_dialogue_input", category="ui") != "msg_first_dialogue_input" else ("Start conversation" if language == "en" else "대화 시작")
            history, output_text, stats_text, image, choices_text, thought_text, action_text, radar_chart, _ = app_instance.process_turn(first_input, [])
            
            # 초기 이미지는 첫 턴에서 생성된 이미지를 그대로 사용
            initial_image = image
            
            # 초기 차트 생성 (첫 대화 후 상태로)
            if app_instance.brain is not None:
                stats = app_instance.brain.state.get_stats_dict()
                initial_chart = app_instance.create_radar_chart(stats, {})
                app_instance.current_chart = initial_chart
            else:
                initial_chart = radar_chart if radar_chart is not None else None
            
            status_msg = "✅ 설정 저장 및 첫 대화 생성 완료!"
            # 탭 전환: chat_tab의 id를 사용
            # 입력창과 전송 버튼 활성화 상태도 함께 반환
            return (status_msg, gr.Tabs(selected="chat_tab"), history, output_text, stats_text, initial_image, choices_text, thought_text, action_text, initial_chart, gr.Button(interactive=True), gr.Textbox(interactive=True))
        except Exception as e:
            logger.error(f"Failed to generate first dialogue: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return (f"✅ 설정 저장 완료, 하지만 첫 대화 생성 실패: {str(e)}", gr.Tabs(selected="chat_tab"), [], "", "", None, "", "", "", None, gr.Button(interactive=True), gr.Textbox(interactive=True))

