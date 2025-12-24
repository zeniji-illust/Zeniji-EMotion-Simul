"""
UI Builder - Gradio UI 생성
"""

import gradio as gr
import logging
from pathlib import Path
import config
from comfy_client import ComfyClient
from memory_manager import MemoryManager
from i18n import get_i18n, set_global_language, TRANSLATIONS

logger = logging.getLogger("UIBuilder")

# 시나리오 이미지 캐시 (성능 최적화)
_scenario_image_cache = {}  # {scenario_name: (mtime, resized_image)}


class UIBuilder:
    """Gradio UI 빌더"""
    
    @staticmethod
    def create_ui(app_instance):
        """Gradio UI 생성"""
        # 설정 로드
        saved_config = app_instance.load_config()
        env_config = app_instance.load_env_config()
        
        # 언어 설정 로드 및 전역 설정
        language = env_config.get("language", "en")
        set_global_language(language)
        i18n = get_i18n()
        
        with gr.Blocks(title="Zeniji Emotion Simul") as demo:
            gr.Markdown("# 🎮 Zeniji Emotion Simul")
            
            with gr.Tabs() as tabs:
                # ========== 탭 1: 초기 설정 ==========
                with gr.Tab(i18n.get_text("tab_setup"), id="setup_tab") as setup_tab:
                    gr.Markdown(f"## {i18n.get_text('setup_title')}")
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown(f"### {i18n.get_text('player_settings')}")
                            player_name = gr.Textbox(
                                label=i18n.get_text("name"),
                                value=saved_config["player"].get("name", ""),
                                placeholder=i18n.get_text("name")
                            )
                            player_gender = gr.Radio(
                                label=i18n.get_text("gender"),
                                choices=[i18n.get_text("male"), i18n.get_text("female"), i18n.get_text("other")],
                                value=saved_config["player"].get("gender", i18n.get_default("player_gender"))
                            )
                        
                        with gr.Column(scale=1):
                            gr.Markdown(f"### {i18n.get_text('character_settings')}")
                            char_name = gr.Textbox(
                                label=i18n.get_text("name"),
                                value=saved_config["character"].get("name", i18n.get_default("character_name")),
                                placeholder=i18n.get_text("name")
                            )
                            # character 정보 안전하게 가져오기
                            character_info = saved_config.get("character") or {}
                            char_age_val = character_info.get("age")
                            char_age_val = int(char_age_val) if char_age_val is not None else 21
                            
                            char_age = gr.Slider(
                                label=i18n.get_text("age"),
                                minimum=18,
                                maximum=100,
                                value=char_age_val,
                                step=1
                            )
                            char_gender = gr.Radio(
                                label=i18n.get_text("gender"),
                                choices=[i18n.get_text("male"), i18n.get_text("female"), i18n.get_text("other")],
                                value=saved_config["character"].get("gender", i18n.get_default("character_gender"))
                            )
                    
                    gr.Markdown(i18n.get_text("appearance_and_personality_section"))
                    appearance = gr.Textbox(
                        label=i18n.get_text("appearance"),
                        value=saved_config["character"].get("appearance", ""),
                        placeholder=i18n.get_text("appearance_placeholder"),
                        info=i18n.get_text("appearance_info"),
                        lines=3,
                        max_lines=5
                    )
                    personality = gr.Textbox(
                        label=i18n.get_text("personality"),
                        value=saved_config["character"].get("personality", ""),
                        placeholder=i18n.get_text("personality_placeholder"),
                        lines=3,
                        max_lines=5
                    )
                    speech_style = gr.Textbox(
                        label=i18n.get_text("character_speech_style_label"),
                        value=saved_config["character"].get("speech_style", i18n.get_default("character_speech_style")),
                        placeholder=i18n.get_text("character_speech_style_placeholder"),
                        info=i18n.get_text("character_speech_style_info"),
                        lines=2,
                        max_lines=4
                    )
                    
                    gr.Markdown(f"### {i18n.get_text('stats_title')}")
                    gr.Markdown(i18n.get_text("stats_info"))
                    
                    # initial_stats가 없거나 None일 수 있으므로 안전하게 처리
                    initial_stats = saved_config.get("initial_stats") or {}
                    
                    def safe_get_stat(key: str, default: float) -> float:
                        """안전하게 통계 값 가져오기 (None 체크) - 명시적으로 한 번 더 or 처리"""
                        val = initial_stats.get(key)
                        if val is None:
                            return default
                        try:
                            result = float(val)
                            # NaN이나 inf 체크
                            if not (0 <= result <= 100):
                                return default
                            return result
                        except (ValueError, TypeError):
                            return default
                    
                    with gr.Row():
                        with gr.Column():
                            # 명시적으로 or 처리로 None 방지
                            p_val = gr.Slider(
                                label=i18n.get_text("pleasure"),
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("P", 50.0) or 50.0,
                                step=1.0,
                                info=i18n.get_text("pleasure_info")
                            )
                            a_val = gr.Slider(
                                label=i18n.get_text("arousal"),
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("A", 40.0) or 40.0,
                                step=1.0,
                                info=i18n.get_text("arousal_info")
                            )
                            d_val = gr.Slider(
                                label=i18n.get_text("dominance"),
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("D", 40.0) or 40.0,
                                step=1.0,
                                info=i18n.get_text("dominance_info")
                            )
                        with gr.Column():
                            i_val = gr.Slider(
                                label=i18n.get_text("intimacy"),
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("I", 20.0) or 20.0,
                                step=1.0,
                                info=i18n.get_text("intimacy_info")
                            )
                            t_val = gr.Slider(
                                label=i18n.get_text("trust"),
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("T", 50.0) or 50.0,
                                step=1.0,
                                info=i18n.get_text("trust_info")
                            )
                            dep_val = gr.Slider(
                                label=i18n.get_text("dependency"),
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("Dep", 0.0) or 0.0,
                                step=1.0,
                                info=i18n.get_text("dependency_info")
                            )
                    
                    gr.Markdown(f"### {i18n.get_text('presets')}")
                    with gr.Row():
                        # preset 이름과 i18n 키 매핑 (현재 언어만 표시)
                        preset_i18n_keys = {
                            "소꿉친구": "preset_childhood_friend",
                            "혐관 라이벌": "preset_hostile_rival",
                            "피폐/집착": "preset_obsessive_depraved",
                        }
                        for preset_name in config.PRESETS.keys():
                            if preset_name in preset_i18n_keys:
                                i18n_key = preset_i18n_keys[preset_name]
                                display_name = i18n.get_text(i18n_key)
                            else:
                                display_name = preset_name
                            preset_btn = gr.Button(display_name, variant="secondary")
                            # lambda 클로저 문제 해결 및 fn 명시
                            def make_preset_handler(name):
                                def handler():
                                    return app_instance.apply_preset(name)
                                return handler
                            preset_btn.click(
                                fn=make_preset_handler(preset_name),
                                inputs=[],
                                outputs=[p_val, a_val, d_val, i_val, t_val, dep_val, appearance, personality, speech_style]
                            )
                    
                    gr.Markdown(f"### {i18n.get_text('initial_situation')}")
                    initial_context = gr.Textbox(
                        label=i18n.get_text("initial_context"),
                        value=saved_config.get("initial_context", ""),
                        placeholder=i18n.get_text("initial_context_placeholder"),
                        lines=4,
                        max_lines=6
                    )
                    initial_background = gr.Textbox(
                        label=i18n.get_text("initial_background"),
                        value=saved_config.get("initial_background", i18n.get_text("initial_background_placeholder")),
                        placeholder=i18n.get_text("initial_background_placeholder"),
                        info=i18n.get_text("initial_background_info")
                    )
                    
                    # TODO: 랜덤 상황 생성 버튼
                    # random_context_btn = gr.Button("🎲 랜덤 상황 생성", variant="secondary")
                    
                    setup_status = gr.Markdown("")
                    
                    # Character 파일 관리
                    with gr.Row():
                        with gr.Column(scale=2):
                            character_file_dropdown = gr.Dropdown(
                                label=i18n.get_text("character_file"),
                                choices=app_instance.get_character_files(),
                                value=None,
                                info=i18n.get_text("character_file_info")
                            )
                        with gr.Column(scale=1):
                            character_filename_input = gr.Textbox(
                                label=i18n.get_text("save_filename"),
                                placeholder=i18n.get_text("save_filename_placeholder"),
                                info=i18n.get_text("save_filename_info")
                            )
                            overwrite_checkbox = gr.Checkbox(
                                label=i18n.get_text("overwrite_allow"),
                                value=False,
                                info=i18n.get_text("overwrite_info")
                            )
                    
                    with gr.Row():
                        load_btn = gr.Button(i18n.get_text("btn_load"), variant="secondary", size="lg")
                        save_btn = gr.Button(i18n.get_text("btn_save"), variant="secondary", size="lg")
                        start_btn = gr.Button(i18n.get_text("btn_start"), variant="primary", size="lg")
                        reload_character_btn = gr.Button(i18n.get_text("btn_reload"), variant="secondary", size="sm")
                    
                    def load_character(selected_file):
                        """캐릭터 파일 불러오기"""
                        if not selected_file:
                            return i18n.get_text("msg_file_not_selected"), *([gr.update()] * 16)
                        
                        try:
                            config = app_instance.load_character_config(selected_file)
                            
                            # UI 업데이트
                            return (
                                i18n.get_text("msg_load_success", filename=selected_file),
                                config["player"].get("name", ""),
                                config["player"].get("gender", i18n.get_text("male")),
                                config["character"].get("name", "예나"),
                                config["character"].get("age", 21),
                                config["character"].get("gender", i18n.get_text("female")),
                                config["character"].get("appearance", ""),
                                config["character"].get("personality", ""),
                                config["character"].get("speech_style", i18n.get_default("character_speech_style")),
                                config["initial_stats"].get("P", 50.0),
                                config["initial_stats"].get("A", 40.0),
                                config["initial_stats"].get("D", 40.0),
                                config["initial_stats"].get("I", 20.0),
                                config["initial_stats"].get("T", 50.0),
                                config["initial_stats"].get("Dep", 0.0),
                                config.get("initial_context", ""),
                                config.get("initial_background", i18n.get_text("initial_background_placeholder"))
                            )
                        except Exception as e:
                            logger.error(f"Failed to load character: {e}")
                            return i18n.get_text("msg_load_failed", error=str(e)), *([gr.update()] * 16)
                    
                    def save_character(filename, overwrite, player_name, player_gender, char_name, char_age, char_gender,
                                     appearance, personality, speech_style, p_val, a_val, d_val, i_val, t_val, dep_val,
                                     initial_context, initial_background):
                        """캐릭터 설정 저장"""
                        if not filename or not filename.strip():
                            return i18n.get_text("msg_filename_required"), gr.Dropdown()
                        
                        try:
                            # 파일명 정리
                            clean_filename = filename.strip()
                            if not clean_filename.endswith('.json'):
                                clean_filename = f"{clean_filename}.json"
                            
                            # 파일이 이미 존재하는지 확인
                            file_path = config.CHARACTER_DIR / clean_filename
                            if file_path.exists() and not overwrite:
                                return i18n.get_text("msg_file_exists", filename=clean_filename), gr.Dropdown()
                            
                            # 설정 데이터 구성
                            config_data = {
                                "player": {
                                    "name": player_name or "",
                                    "gender": player_gender or i18n.get_text("male")
                                },
                                "character": {
                                    "name": char_name or "예나",
                                    "age": int(char_age) if char_age else 21,
                                    "gender": char_gender or i18n.get_text("female"),
                                    "appearance": appearance or "",
                                "personality": personality or "",
                                "speech_style": speech_style or i18n.get_default("character_speech_style")
                                },
                                "initial_stats": {
                                    "P": float(p_val) if p_val is not None else 50.0,
                                    "A": float(a_val) if a_val is not None else 40.0,
                                    "D": float(d_val) if d_val is not None else 40.0,
                                    "I": float(i_val) if i_val is not None else 20.0,
                                    "T": float(t_val) if t_val is not None else 50.0,
                                    "Dep": float(dep_val) if dep_val is not None else 0.0
                                },
                                "initial_context": initial_context or "",
                                "initial_background": initial_background or i18n.get_text("initial_background_placeholder")
                            }
                            
                            if app_instance.save_character_config(config_data, clean_filename):
                                # character_config.json도 덮어쓰기 (다음 실행 시 기본값으로 사용)
                                app_instance.save_config(config_data)
                                
                                # 드롭다운 목록 새로고침
                                updated_files = app_instance.get_character_files()
                                return i18n.get_text("msg_save_success", filename=clean_filename), gr.Dropdown(choices=updated_files, value=clean_filename.replace('.json', ''))
                            else:
                                return i18n.get_text("msg_save_failed"), gr.Dropdown()
                        except Exception as e:
                            logger.error(f"Failed to save character: {e}")
                            return i18n.get_text("msg_save_failed"), gr.Dropdown()
                    
                    def reload_character_files():
                        """캐릭터 파일 목록 새로고침"""
                        updated_files = app_instance.get_character_files()
                        return gr.Dropdown(choices=updated_files)
                    
                    load_btn.click(
                        load_character,
                        inputs=[character_file_dropdown],
                        outputs=[
                            setup_status,
                            player_name, player_gender,
                            char_name, char_age, char_gender,
                            appearance, personality, speech_style,
                            p_val, a_val, d_val, i_val, t_val, dep_val,
                            initial_context, initial_background
                        ]
                    )
                    
                    save_btn.click(
                        save_character,
                        inputs=[
                            character_filename_input,
                            overwrite_checkbox,
                            player_name, player_gender,
                            char_name, char_age, char_gender,
                            appearance, personality, speech_style,
                            p_val, a_val, d_val, i_val, t_val, dep_val,
                            initial_context, initial_background
                        ],
                        outputs=[setup_status, character_file_dropdown]
                    )
                    
                    reload_character_btn.click(
                        reload_character_files,
                        outputs=[character_file_dropdown]
                    )
                    
                    def normalize_chatbot_history(history):
                        """Chatbot 히스토리를 Gradio 6.x 딕셔너리 형식으로 정규화"""
                        if history is None:
                            return []
                        
                        normalized = []
                        for item in history:
                            if isinstance(item, list) and len(item) == 2:
                                # 튜플 형식 [user_msg, assistant_msg]을 딕셔너리로 변환
                                user_msg = item[0] if item[0] else ""
                                assistant_msg = item[1] if item[1] else ""
                                
                                # 문자열로 변환 (리스트나 딕셔너리인 경우 처리)
                                if isinstance(user_msg, list):
                                    user_msg = ''.join([part.get('text', '') if isinstance(part, dict) else str(part) for part in user_msg])
                                elif isinstance(user_msg, dict):
                                    user_msg = user_msg.get('content', str(user_msg))
                                else:
                                    user_msg = str(user_msg) if user_msg else ""
                                
                                if isinstance(assistant_msg, list):
                                    assistant_msg = ''.join([part.get('text', '') if isinstance(part, dict) else str(part) for part in assistant_msg])
                                elif isinstance(assistant_msg, dict):
                                    assistant_msg = assistant_msg.get('content', str(assistant_msg))
                                else:
                                    assistant_msg = str(assistant_msg) if assistant_msg else ""
                                
                                # 딕셔너리 형식으로 변환
                                if user_msg:
                                    normalized.append({"role": "user", "content": user_msg})
                                if assistant_msg:
                                    normalized.append({"role": "assistant", "content": assistant_msg})
                            elif isinstance(item, dict):
                                # 이미 딕셔너리 형식인 경우
                                role = item.get("role", "")
                                content = item.get("content", "")
                                
                                # content가 리스트나 다른 형식인 경우 문자열로 변환
                                if isinstance(content, list):
                                    content = ''.join([part.get('text', '') if isinstance(part, dict) else str(part) for part in content])
                                else:
                                    content = str(content) if content else ""
                                
                                # role과 content가 모두 있어야 함
                                if role and content:
                                    normalized.append({"role": role, "content": content})
                            else:
                                # 알 수 없는 형식은 건너뛰기
                                logger.warning(f"Unknown history item format: {type(item)}, skipping")
                        
                        return normalized
                    
                    def continue_chat(selected_scenario):
                        """시나리오를 불러와서 대화 이어가기"""
                        if not selected_scenario:
                            return "⚠️ 시나리오를 선택해주세요.", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                        
                        try:
                            # 시나리오 불러오기
                            scenario_data = app_instance.load_scenario(selected_scenario)
                            
                            if not scenario_data:
                                return f"⚠️ 시나리오 '{selected_scenario}'를 불러올 수 없습니다.", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                            
                            # conversation 필드 확인 (전체 대화)
                            # 기존 시나리오 호환: conversation이 없으면 context.recent_turns에서 복원
                            if "conversation" in scenario_data:
                                history = scenario_data["conversation"]
                            elif "context" in scenario_data:
                                # context.recent_turns에서 conversation 형식으로 복원
                                context = scenario_data["context"]
                                recent_turns = context.get("recent_turns", [])
                                if not recent_turns:
                                    return f"⚠️ 시나리오 '{selected_scenario}'에 대화 내용이 없습니다.", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                                
                                # recent_turns에서 conversation 형식으로 변환
                                history = []
                                for turn_data in recent_turns:
                                    player_input = turn_data.get("player_input", "")
                                    character_speech = turn_data.get("character_speech", "")
                                    if player_input:
                                        history.append({"role": "user", "content": player_input})
                                    if character_speech:
                                        history.append({"role": "assistant", "content": character_speech})
                                
                                # 호환성을 위해 scenario_data에 conversation 필드 추가
                                scenario_data["conversation"] = history
                            else:
                                return f"⚠️ 시나리오 '{selected_scenario}'에 대화 내용이 없습니다. (conversation 또는 context 필드 없음)", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                            
                            if not history:
                                return f"⚠️ 시나리오 '{selected_scenario}'에 대화 내용이 없습니다.", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                            
                            # context 확인 (최근 10턴)
                            context = scenario_data.get("context", {})
                            recent_turns = context.get("recent_turns", [])
                            
                            # 시나리오와 같은 이름의 이미지 파일도 불러오기
                            scenario_image_path = config.SCENARIOS_DIR / f"{selected_scenario}.png"
                            if scenario_image_path.exists():
                                try:
                                    from PIL import Image
                                    app_instance.current_image = Image.open(scenario_image_path)
                                    logger.info(f"Scenario image loaded from: {scenario_image_path}")
                                except Exception as e:
                                    logger.warning(f"Failed to load scenario image: {e}")
                                    app_instance.current_image = None
                            else:
                                app_instance.current_image = None
                                logger.debug(f"Scenario image not found: {scenario_image_path} (optional)")
                            
                            # 모델이 로드되어 있는지 확인
                            if not app_instance.model_loaded:
                                status_msg, success = app_instance.load_model()
                                if not success:
                                    return f"❌ 모델 로드 실패: {status_msg}", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                            
                            # 초기 설정 정보 복원 (프롬프트에 필수)
                            if app_instance.brain is not None and "initial_config" in scenario_data:
                                app_instance.brain.set_initial_config(scenario_data["initial_config"])
                                logger.info("Initial config restored")
                            
                            # 상태 정보 복원
                            if app_instance.brain is not None and "state" in scenario_data:
                                state_data = scenario_data["state"]
                                state = app_instance.brain.state
                                
                                # Stats 복원
                                if "stats" in state_data:
                                    stats = state_data["stats"]
                                    state.P = stats.get("P", state.P)
                                    state.A = stats.get("A", state.A)
                                    state.D = stats.get("D", state.D)
                                    state.I = stats.get("I", state.I)
                                    state.T = stats.get("T", state.T)
                                    state.Dep = stats.get("Dep", state.Dep)
                                
                                # 관계 상태 복원
                                if "relationship" in state_data:
                                    state.relationship_status = state_data["relationship"]
                                    # previous_relationship도 초기화 (다음 턴에서 변경 감지용)
                                    app_instance.previous_relationship = state_data["relationship"]
                                    logger.info(f"Relationship status restored: {state.relationship_status}")
                                
                                # 기분은 interpret_mood로 계산되므로 복원 불필요 (stats 복원 후 자동 계산됨)
                                # mood는 저장만 하고 복원은 하지 않음 (계산된 값이므로)
                                
                                # 뱃지 복원
                                if "badges" in state_data:
                                    state.badges = set(state_data["badges"])
                                
                                # 트라우마 레벨 복원
                                if "trauma_level" in state_data:
                                    state.trauma_level = state_data["trauma_level"]
                                
                                # 현재 배경 복원
                                if "current_background" in state_data:
                                    state.current_background = state_data["current_background"]
                                
                                # 총 턴 수 복원
                                if "total_turns" in state_data:
                                    state.total_turns = state_data["total_turns"]
                                
                                # 장기 기억 복원
                                if "long_memory" in state_data:
                                    state.long_memory = state_data["long_memory"]
                                    logger.info(f"장기 기억 복원됨 (길이: {len(state.long_memory)}): {state.long_memory[:100]}...")
                                else:
                                    logger.warning("시나리오에 장기 기억 데이터가 없습니다")
                                
                                # mood는 interpret_mood로 계산되는 값
                                from logic_engine import interpret_mood
                                calculated_mood = interpret_mood(state)
                                
                                logger.info(f"State restored: relationship={state.relationship_status}, mood={calculated_mood}, badges={list(state.badges)}, background={state.current_background}, turns={state.total_turns}, long_memory exists: {bool(state.long_memory)}")
                                
                                # 이전 뱃지 목록도 복원 (알림용)
                                if isinstance(state.badges, list):
                                    app_instance.previous_badges = set(state.badges)
                                elif isinstance(state.badges, set):
                                    app_instance.previous_badges = state.badges.copy()
                                else:
                                    app_instance.previous_badges = set()
                            
                            # 문맥 정보 복원 (recent_turns가 있으면 사용, 없으면 conversation에서 추론)
                            if app_instance.brain is not None and hasattr(app_instance.brain, 'history'):
                                if recent_turns:
                                    # DialogueHistory에 턴 추가
                                    for turn_data in recent_turns:
                                        from state_manager import DialogueTurn
                                        character_speech = turn_data.get("character_speech", "")
                                        turn = DialogueTurn(
                                            turn_number=turn_data.get("turn_number", 0),
                                            player_input=turn_data.get("player_input", ""),
                                            character_speech=character_speech,
                                            character_thought=turn_data.get("character_thought", ""),
                                            emotion=turn_data.get("emotion", "neutral"),
                                            visual_prompt=turn_data.get("visual_prompt", ""),
                                            background=turn_data.get("background", "")
                                        )
                                        app_instance.brain.history.add(turn)
                                    logger.info(f"Context restored: {len(recent_turns)} turns")
                                else:
                                    # recent_turns가 없으면 conversation에서 추론 (하위 호환성)
                                    logger.warning("recent_turns가 없어 conversation에서 복원 시도")
                                
                                # 마지막 대화의 background를 current_background에 반영
                                if "last_background" in context and context["last_background"]:
                                    state.current_background = context["last_background"]
                                    logger.info(f"Last background restored to current_background: {context['last_background']}")
                                elif recent_turns and len(recent_turns) > 0:
                                    last_turn_bg = recent_turns[-1].get("background", "")
                                    if last_turn_bg:
                                        state.current_background = last_turn_bg
                                        logger.info(f"Last turn background restored to current_background: {last_turn_bg}")
                            
                            # conversation에서 chatbot 히스토리 생성 (정규화 함수 사용)
                            chatbot_history = normalize_chatbot_history(history)
                            
                            # 현재 상태로 차트 생성
                            if app_instance.brain is not None:
                                stats = app_instance.brain.state.get_stats_dict()
                                current_chart = app_instance.create_radar_chart(stats, {})
                                app_instance.current_chart = current_chart
                            else:
                                current_chart = app_instance.current_chart
                            
                            # 현재 이미지와 차트는 유지
                            current_image = app_instance.current_image
                            
                            # stats_text 생성
                            if app_instance.brain is not None:
                                state = app_instance.brain.state
                                stats = state.get_stats_dict()
                                
                                # mood는 interpret_mood로 계산되는 값
                                from logic_engine import interpret_mood
                                calculated_mood = interpret_mood(state)
                                
                                stats_axis_title = i18n.get_text("stats_axis_title", category="ui")
                                stats_change_title = i18n.get_text("stats_change_title", category="ui")
                                relationship_label = i18n.get_text("relationship_label", category="ui")
                                mood_label = i18n.get_text("mood_label", category="ui")
                                badge_label = i18n.get_text("badge_label", category="ui")
                                badge_none = i18n.get_text("badge_none", category="ui")
                                p_label = i18n.get_text("stat_p_short", category="ui")
                                a_label = i18n.get_text("stat_a_short", category="ui")
                                d_label = i18n.get_text("stat_d_short", category="ui")
                                i_label = i18n.get_text("stat_i_short", category="ui")
                                t_label = i18n.get_text("stat_t_short", category="ui")
                                dep_label = i18n.get_text("stat_dep_short", category="ui")

                                stats_text = f"""
<div style="font-size: 0.85em; color: #666;">
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
<div>
<strong>{stats_axis_title}:</strong><br>
{p_label}: {stats.get('P', 0):.0f}<br>
{a_label}: {stats.get('A', 0):.0f}<br>
{d_label}: {stats.get('D', 0):.0f}<br>
</div>
<div>
<strong>{stats_change_title}:</strong><br>
{i_label}: {stats.get('I', 0):.0f}<br>
{t_label}: {stats.get('T', 0):.0f}<br>
{dep_label}: {stats.get('Dep', 0):.0f}<br>
</div>
</div>
<br>
<strong>{relationship_label}:</strong> {state.relationship_status} | <strong>{mood_label}:</strong> {calculated_mood}<br>
<strong>{badge_label}:</strong> {', '.join(state.badges) or badge_none}
</div>
"""
                            else:
                                stats_text = ""
                            
                            return (
                                f"✅ 시나리오 '{selected_scenario}' 불러오기 완료!",
                                gr.Tabs(selected="chat_tab"),
                                chatbot_history,
                                "",
                                stats_text,
                                current_image,
                                "",
                                "",
                                "",
                                current_chart
                            )
                        except Exception as e:
                            logger.error(f"Failed to continue chat: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            return f"❌ 시나리오 불러오기 실패: {str(e)}", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                
                # ========== 탭 2: 시나리오 ==========
                with gr.Tab(i18n.get_text("tab_scenario"), id="scenario_tab") as scenario_tab:
                    gr.Markdown(f"## {i18n.get_text('scenario_title')}")
                    
                    # 플레이스홀더 이미지 생성 함수 (4:3 비율, 높이가 더 높게)
                    def create_placeholder_image():
                        """이미지가 없는 경우 사용할 플레이스홀더 생성 (4:3 비율)"""
                        from PIL import Image, ImageDraw, ImageFont
                        card_width = 200
                        card_height = int(card_width * 4 / 3)  # 4:3 비율 (267)
                        placeholder = Image.new('RGB', (card_width, card_height), color='#e0e0e0')
                        draw = ImageDraw.Draw(placeholder)
                        try:
                            font = ImageFont.truetype("malgun.ttf", 16)
                        except:
                            try:
                                font = ImageFont.truetype("gulim.ttc", 16)
                            except:
                                font = ImageFont.load_default()
                        text = i18n.get_text("no_image")
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        position = ((card_width - text_width) // 2, (card_height - text_height) // 2)
                        draw.text(position, text, fill='#999999', font=font)
                        return placeholder
                    
                    placeholder_img = create_placeholder_image()
                    
                    def get_scenario_gallery_items():
                        """시나리오 갤러리 아이템 생성 (동적 업데이트 가능, 캐싱 적용)"""
                        from PIL import Image
                        import os
                        global _scenario_image_cache
                        
                        scenarios = app_instance.get_scenario_files()
                        
                        # 파일 수정 시간 기준으로 최신순 정렬 (역순)
                        scenario_paths = []
                        for scenario_name in scenarios:
                            scenario_path = config.SCENARIOS_DIR / f"{scenario_name}.json"
                            if scenario_path.exists():
                                mtime = os.path.getmtime(scenario_path)
                                scenario_paths.append((mtime, scenario_name))
                        
                        # 수정 시간 역순 정렬 (최신이 먼저)
                        scenario_paths.sort(reverse=True)
                        scenarios = [name for _, name in scenario_paths]
                        
                        gallery_items = []
                        
                        # 4:3 비율로 리사이즈 (높이가 더 높게)
                        target_width = 200
                        target_height = int(target_width * 4 / 3)  # 267
                        
                        # 플레이스홀더는 이미 올바른 크기로 생성되어 있으므로 캐싱만 수행
                        if 'placeholder' not in _scenario_image_cache:
                            _scenario_image_cache['placeholder'] = (0, placeholder_img)
                        
                        for scenario_name in scenarios:  # 전체 시나리오 표시
                            image_path = config.SCENARIOS_DIR / f"{scenario_name}.png"
                            
                            # 캐시 확인
                            cache_key = scenario_name
                            use_cache = False
                            resized_img = None
                            
                            if image_path.exists():
                                try:
                                    # 이미지 파일의 수정 시간 확인
                                    img_mtime = os.path.getmtime(image_path)
                                    
                                    # 캐시에 있고 수정 시간이 같으면 캐시 사용
                                    if cache_key in _scenario_image_cache:
                                        cached_mtime, cached_img = _scenario_image_cache[cache_key]
                                        if cached_mtime == img_mtime:
                                            resized_img = cached_img
                                            use_cache = True
                                    
                                    # 캐시 미스 또는 파일이 변경된 경우 새로 로드 및 리사이즈
                                    if not use_cache:
                                        img = Image.open(image_path)
                                        resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                                        # 캐시에 저장
                                        _scenario_image_cache[cache_key] = (img_mtime, resized_img)
                                    
                                    gallery_items.append((resized_img, scenario_name))
                                except Exception as e:
                                    logger.warning(f"Failed to load/resize image for {scenario_name}: {e}")
                                    # 실패 시 플레이스홀더 사용
                                    placeholder_resized = _scenario_image_cache['placeholder'][1]
                                    gallery_items.append((placeholder_resized, scenario_name))
                            else:
                                # 이미지가 없으면 플레이스홀더 사용
                                placeholder_resized = _scenario_image_cache['placeholder'][1]
                                gallery_items.append((placeholder_resized, scenario_name))
                        
                        # 사용하지 않는 캐시 항목 정리 (현재 시나리오 목록에 없는 것들)
                        current_scenarios = set(scenarios)
                        keys_to_remove = [key for key in _scenario_image_cache.keys() 
                                        if key != 'placeholder' and key not in current_scenarios]
                        for key in keys_to_remove:
                            del _scenario_image_cache[key]
                        
                        return gallery_items
                    
                    # 시나리오 갤러리 (동적 업데이트 가능)
                    scenario_gallery = gr.Gallery(
                        label=i18n.get_text("scenario_title"),
                        value=get_scenario_gallery_items(),
                        show_label=False,
                        elem_id="scenario-gallery",
                        columns=4,
                        height="auto",
                        allow_preview=False
                    )
                    
                    # CSS로 이미지 크기(카드 폭)에 맞춰 동적으로 조절
                    gr.HTML(value="""
                    <style>
                    /* 시나리오 갤러리 이미지: 카드 폭에 맞춰 반응형으로 축소/확대 (3:4 비율 유지) */
                    #scenario-gallery img {
                        width: 100% !important;
                        height: auto !important;
                        max-width: 200px !important;  /* 카드가 1개일 때도 일정 크기 이상 커지지 않도록 제한 */
                        aspect-ratio: 3 / 4 !important;  /* 기존 200x267 비율 유지 (세로형) */
                        object-fit: contain !important;
                    }
                    /* 갤러리 아이템 컨테이너 - 중앙 정렬, 최대 너비 제한 (카드가 적을 때도 일정 크기 유지) */
                    #scenario-gallery .gallery-item {
                        display: flex !important;
                        flex-direction: column !important;
                        align-items: center !important;
                        justify-content: flex-start !important;
                        box-sizing: border-box !important;
                        max-width: 200px !important;  /* 카드가 1개일 때도 4개 있을 때와 같은 크기로 제한 */
                        width: 100% !important;  /* 그리드 내에서 반응형으로 조정되되, max-width로 제한 */
                    }
                    /* 제목/캡션 스타일 - 가운데 정렬 및 2줄까지 표시 */
                    #scenario-gallery .gallery-item .caption-label {
                        max-width: 180px !important;
                        width: 180px !important;
                        margin-left: auto !important;
                        margin-right: auto !important;
                        margin-top: 4px !important;
                        margin-bottom: 0 !important;
                        padding: 0 !important;
                        white-space: normal !important;
                        word-wrap: break-word !important;
                        overflow-wrap: break-word !important;
                        display: -webkit-box !important;
                        -webkit-line-clamp: 2 !important;
                        -webkit-box-orient: vertical !important;
                        overflow: hidden !important;
                        text-overflow: ellipsis !important;
                        line-height: 1.4em !important;
                        max-height: 2.8em !important;
                        text-align: center !important;
                        box-sizing: border-box !important;
                    }
                    </style>
                    """)
                    
                    # 새로고침 버튼
                    with gr.Row():
                        reload_scenario_cards_btn = gr.Button(i18n.get_text("btn_reload"), variant="secondary")
                    
                    def reload_scenario_gallery():
                        """시나리오 갤러리 새로고침"""
                        return gr.Gallery(value=get_scenario_gallery_items())
                    
                    reload_scenario_cards_btn.click(
                        fn=reload_scenario_gallery,
                        outputs=[scenario_gallery]
                    )
                    
                    # 카드 클릭 이벤트는 대화 탭 컴포넌트가 정의된 후에 연결됨 (아래에서 처리)
                
                # ========== 탭 3: 대화 ==========
                with gr.Tab(i18n.get_text("tab_chat"), id="chat_tab") as chat_tab:
                    # 이벤트 알림 (고정 위치, 필요시 표시)
                    event_notification = gr.HTML(value="", visible=False, elem_id="event-notification-container")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            chatbot = gr.Chatbot(label=i18n.get_text("chat_label"), height=500)
                            
                            # 속마음: Accordion으로 접기/펼치기 가능하게
                            with gr.Accordion(i18n.get_text("thought_title"), open=False, visible=True) as thought_accordion:
                                thought_display = gr.Markdown(label="", visible=True)
                            
                            action_display = gr.Markdown(label=i18n.get_text("action_title"), visible=True)
                            user_input = gr.Textbox(label=i18n.get_text("input_label"), placeholder=i18n.get_text("input_placeholder"), interactive=False)
                            submit_btn = gr.Button(i18n.get_text("btn_send"), variant="primary", interactive=False)
                        
                        with gr.Column(scale=1):
                            stats_chart = gr.Plot(label=i18n.get_text("stats_chart_label"), show_label=True)
                            stats_display = gr.Markdown(label=i18n.get_text("stats_detail_label"), show_label=True)
                            # 이미지와 재시도/저장 버튼을 함께 표시하기 위한 컨테이너
                            image_display = gr.Image(label=i18n.get_text("character_image_label"), height=400, show_label=False)
                            retry_image_btn = gr.Button(i18n.get_text("btn_retry_image"), variant="secondary", size="sm", visible=False)
                            save_image_btn = gr.Button(i18n.get_text("btn_save_image"), variant="secondary", size="sm", visible=True)
                            save_moment_btn = gr.Button(i18n.get_text("btn_save_moment"), variant="secondary", size="sm", visible=True)
                            # 버튼 상태/메시지 표시용
                            retry_image_status = gr.Markdown("", visible=False, elem_id="retry-status")
                            save_image_status = gr.Markdown("", visible=False, elem_id="save-image-status")
                            save_moment_status = gr.Markdown("", visible=False, elem_id="save-moment-status")
                    
                    # 시나리오 저장 (모든 컴포넌트 아래, 화면 너비 전체 사용)
                    with gr.Row():
                        scenario_save_name = gr.Textbox(
                            label=i18n.get_text("scenario_save_label"),
                            placeholder=i18n.get_text("scenario_save_placeholder"),
                            info=i18n.get_text("scenario_save_info"),
                            scale=3
                        )
                        save_scenario_btn = gr.Button(i18n.get_text("btn_save_scenario"), variant="secondary", scale=1)
                        scenario_save_status = gr.Markdown("")
                    
                    # 이미지 업데이트 트리거용 hidden state
                    image_update_trigger = gr.State(value=None)
                    
                    def on_submit(message, history):
                        """메인 대화 처리 핸들러 (로딩 이슈 디버깅용 로그/예외 방어 포함)"""
                        try:
                            logger.info(f"[on_submit] called. model_loaded={app_instance.model_loaded}, "
                                        f"message_preview={str(message)[:50]!r}, "
                                        f"history_type={type(history).__name__}")
                            
                            if not app_instance.model_loaded:
                                logger.info("[on_submit] model not loaded yet, returning history only.")
                                # history를 안전하게 리스트로 변환
                                if history is None:
                                    history = []
                                elif isinstance(history, set):
                                    history = list(history)
                                elif not isinstance(history, list):
                                    try:
                                        history = list(history)
                                    except (TypeError, ValueError):
                                        history = []
                                normalized_history = normalize_chatbot_history(history)
                                return normalized_history, "", "", "", "", None, None, gr.HTML(value="", visible=False)  # 마지막은 event_notification
                            
                            # 이전 차트를 먼저 반환 (로딩 중에도 차트가 보이도록)
                            # 초기 차트가 없으면 생성
                            if app_instance.current_chart is None and app_instance.brain is not None:
                                logger.debug("[on_submit] current_chart is None, creating initial chart.")
                                stats = app_instance.brain.state.get_stats_dict()
                                app_instance.current_chart = app_instance.create_radar_chart(stats, {})
                            previous_chart = app_instance.current_chart if app_instance.current_chart is not None else None
                            
                            # history를 안전하게 리스트로 변환 및 정규화
                            if history is None:
                                history = []
                            elif isinstance(history, set):
                                history = list(history)
                            elif not isinstance(history, list):
                                try:
                                    history = list(history)
                                except (TypeError, ValueError):
                                    history = []
                            
                            # 히스토리 정규화
                            normalized_history = normalize_chatbot_history(history)
                            logger.debug(f"[on_submit] normalized_history_len={len(normalized_history)}")
                            
                            new_history, output, stats, image, choices, thought, action, chart, event_notification = app_instance.process_turn(message, normalized_history)
                            
                            # 반환 전에 히스토리 다시 정규화 (안전장치)
                            normalized_new_history = normalize_chatbot_history(new_history)
                            
                            # image가 새로 생성됐으면 trigger에 넣고, 아니면 None
                            # 차트는 이전 차트를 먼저 반환하고, 새 차트는 나중에 업데이트
                            # 이벤트 알림이 있으면 표시, 없으면 숨김 (빈 문자열로 초기화)
                            event_visible = bool(event_notification and event_notification.strip())
                            event_html = event_notification if event_visible else ""
                            
                            logger.info(f"[on_submit] completed. "
                                        f"stats_keys={list(stats.keys()) if isinstance(stats, dict) else 'N/A'}, "
                                        f"image_generated={image is not None}, "
                                        f"event_visible={event_visible}")
                            
                            return (
                                normalized_new_history,
                                "",
                                stats,
                                thought,
                                action,
                                image,
                                previous_chart if previous_chart else chart,
                                gr.HTML(value=event_html, visible=event_visible),
                            )
                        except Exception as e:
                            import traceback
                            logger.error(f"[on_submit] ERROR: {e}")
                            logger.error(traceback.format_exc())
                            # 예외가 발생하더라도 Gradio 체인이 끝나도록 안전한 기본값 반환
                            safe_history = normalize_chatbot_history(history or [])
                            error_html = gr.HTML(
                                value=f"<div style='color:red;font-size:0.85em;'>⚠️ on_submit 오류: {str(e)}</div>",
                                visible=True,
                            )
                            return safe_history, "", "", "", "", None, None, error_html
                    
                    def update_chart_async(history):
                        """백그라운드에서 차트 업데이트 (로딩 이슈 디버깅용 로그 포함)"""
                        try:
                            logger.debug(f"[update_chart_async] called. model_loaded={app_instance.model_loaded}, "
                                         f"history_type={type(history).__name__}")
                            if not app_instance.model_loaded or not history:
                                logger.debug("[update_chart_async] skipped (model not loaded or empty history).")
                                return gr.skip()
                            
                            # 마지막 대화에서 stats 추출하여 차트 생성
                            # 실제로는 process_turn에서 이미 차트를 생성했으므로 current_chart 사용
                            if app_instance.current_chart is not None:
                                logger.debug("[update_chart_async] returning current_chart.")
                                return app_instance.current_chart
                        except Exception as e:
                            import traceback
                            logger.error(f"[update_chart_async] ERROR: {e}")
                            logger.error(traceback.format_exc())
                        logger.debug("[update_chart_async] no chart to update, skip.")
                        return gr.skip()
                    
                    def save_scenario_handler(scenario_name, history):
                        """시나리오 저장 핸들러 (Gradio history에서 전체 대화 저장, context.recent_turns는 최근 10턴만 저장)"""
                        if not scenario_name or not scenario_name.strip():
                            return i18n.get_text("msg_scenario_save_name_required")
                        
                        try:
                            logger.info(f"Saving scenario: {scenario_name}")
                            
                            # Brain에서 상태 정보 가져오기
                            scenario_data = {}
                            
                            if app_instance.brain is not None:
                                # 현재 상태 정보
                                state = app_instance.brain.state
                                
                                # mood는 interpret_mood 함수로 계산되는 값
                                from logic_engine import interpret_mood
                                calculated_mood = interpret_mood(state)
                                
                                scenario_data["state"] = {
                                    "stats": {
                                        "P": state.P,
                                        "A": state.A,
                                        "D": state.D,
                                        "I": state.I,
                                        "T": state.T,
                                        "Dep": state.Dep
                                    },
                                    "relationship": state.relationship_status,
                                    "mood": calculated_mood,  # 계산된 mood 값 저장
                                    "badges": list(state.badges) if hasattr(state, 'badges') else [],
                                    "trauma_level": state.trauma_level if hasattr(state, 'trauma_level') else 0.0,
                                    "current_background": state.current_background if hasattr(state, 'current_background') else "",
                                    "total_turns": state.total_turns if hasattr(state, 'total_turns') else 0,
                                    "long_memory": state.long_memory if hasattr(state, 'long_memory') else ""  # 장기 기억 저장
                                }
                                
                                # 초기 설정 정보 (프롬프트에 필수)
                                if hasattr(app_instance.brain, 'initial_config') and app_instance.brain.initial_config:
                                    scenario_data["initial_config"] = app_instance.brain.initial_config
                                
                                # 전체 대화를 Gradio history에서 가져와서 저장
                                # Chatbot 히스토리는 normalize_chatbot_history로 한 번 더 정규화해서 사용
                                conversation_list = []
                                try:
                                    normalized_history = normalize_chatbot_history(history)
                                    # 이미 {"role": ..., "content": ...} 형식이므로 그대로 사용
                                    for item in normalized_history:
                                        role = item.get("role")
                                        content = item.get("content", "")
                                        if role and isinstance(content, str) and content.strip():
                                            conversation_list.append({
                                                "role": role,
                                                "content": content.strip()
                                            })
                                except Exception as e:
                                    logger.warning(f"Failed to normalize chatbot history for scenario save: {e}")
                                
                                # 최근 대화 턴 (문맥 정보) - context에 저장 (최근 10턴)
                                if hasattr(app_instance.brain, 'history') and app_instance.brain.history:
                                    recent_turns = []
                                    last_background = None
                                    last_visual_prompt = None
                                    history_turns = app_instance.brain.history.turns  # 최근 10턴만 있음
                                    
                                    # 최근 10턴만 context에 저장
                                    recent_history_turns = history_turns[-10:] if len(history_turns) > 10 else history_turns
                                    
                                    for idx, turn in enumerate(history_turns):
                                        if hasattr(turn, 'player_input') and hasattr(turn, 'character_speech'):
                                            turn_bg = getattr(turn, 'background', '')
                                            turn_visual = getattr(turn, 'visual_prompt', '')
                                            
                                            # 최근 10턴만 recent_turns에 저장
                                            if turn in recent_history_turns:
                                                # 마지막 턴의 background와 visual_prompt 저장
                                                if idx == len(history_turns) - 1:
                                                    last_background = turn_bg
                                                    last_visual_prompt = turn_visual
                                                
                                                recent_turns.append({
                                                    "turn_number": getattr(turn, 'turn_number', 0),
                                                    "player_input": turn.player_input,
                                                    "character_speech": getattr(turn, 'character_speech', ''),
                                                    "character_thought": getattr(turn, 'character_thought', ''),
                                                    "emotion": getattr(turn, 'emotion', 'neutral'),
                                                    "visual_prompt": turn_visual,
                                                    "background": turn_bg,
                                                    "stats_delta": getattr(turn, 'stats_delta', {})
                                                })
                                    
                                    # context에 recent_turns 저장 (최근 10턴)
                                    context_data = {
                                        "recent_turns": recent_turns
                                    }
                                    if last_background:
                                        context_data["last_background"] = last_background
                                    elif state.current_background:
                                        context_data["last_background"] = state.current_background
                                    if last_visual_prompt:
                                        context_data["last_visual_prompt"] = last_visual_prompt
                                    
                                    scenario_data["context"] = context_data
                                
                                # conversation 저장 (전체 대화, Gradio history 기반)
                                if not conversation_list:
                                    return i18n.get_text("msg_no_conversation_to_save")
                                
                                scenario_data["conversation"] = conversation_list
                            else:
                                return i18n.get_text("msg_game_not_started")
                            
                            # 시나리오 저장
                            scenario_name_clean = scenario_name.strip()
                            # .json 확장자 제거 (save_scenario에서 자동 추가)
                            if scenario_name_clean.endswith('.json'):
                                scenario_name_clean = scenario_name_clean[:-5]
                            
                            if app_instance.save_scenario(scenario_data, scenario_name_clean):
                                # 마지막 이미지도 함께 저장 (같은 이름으로 PNG 파일)
                                if app_instance.current_image is not None:
                                    try:
                                        from PIL import Image
                                        scenario_image_path = config.SCENARIOS_DIR / f"{scenario_name_clean}.png"
                                        
                                        # 이미지 1.5배 리사이즈 (LANCZOS)
                                        width, height = app_instance.current_image.size
                                        resized_image = app_instance.current_image.resize((int(width * 1.5), int(height * 1.5)), Image.LANCZOS)
                                        
                                        resized_image.save(scenario_image_path, "PNG")
                                        logger.info(f"Scenario image saved to: {scenario_image_path}")
                                    except Exception as e:
                                        logger.warning(f"Failed to save scenario image: {e}")
                                
                                return i18n.get_text("msg_scenario_save_success", category="ui", name=scenario_name_clean)
                            else:
                                return i18n.get_text("msg_scenario_save_failed", category="ui")
                        except Exception as e:
                            logger.error(f"Failed to save scenario: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            return i18n.get_text("msg_scenario_save_failed", category="ui")
                    
                    save_scenario_btn.click(
                        save_scenario_handler,
                        inputs=[scenario_save_name, chatbot],
                        outputs=[scenario_save_status]
                    )
                    
                    def update_chart_if_needed(new_chart):
                        """차트가 있으면 업데이트, 없으면 건너뛰기"""
                        if new_chart is not None:
                            return new_chart
                        return gr.skip()
                    
                    def update_image_if_needed(trigger_image):
                        """트리거에 이미지가 있을 때만 반환, 없으면 업데이트 안 함 (로딩 이슈 디버깅용 로그 포함)"""
                        try:
                            logger.debug(f"[update_image_if_needed] called. trigger_image_is_none={trigger_image is None}, "
                                         f"has_current_image={app_instance.current_image is not None}")
                            if trigger_image is not None:
                                logger.debug("[update_image_if_needed] new image provided, showing retry button.")
                                # 이미지가 있으면 재시도 버튼도 표시
                                return trigger_image, gr.Button(visible=True)
                            # 이미지가 없어도 이전 이미지가 있으면 재시도 버튼 표시
                            if app_instance.current_image is not None:
                                logger.debug("[update_image_if_needed] no new image, but current_image exists -> show retry.")
                                return gr.skip(), gr.Button(visible=True)
                            logger.debug("[update_image_if_needed] no image at all -> hide retry.")
                            return gr.skip(), gr.Button(visible=False)  # Gradio 6.x: 업데이트 건너뛰기
                        except Exception as e:
                            import traceback
                            logger.error(f"[update_image_if_needed] ERROR: {e}")
                            logger.error(traceback.format_exc())
                            # 실패 시에도 체인을 끊지 않도록 기본 동작 반환
                            return gr.skip(), gr.Button(visible=bool(app_instance.current_image is not None))
                    
                    def retry_image_handler():
                        """이미지 재생성 핸들러"""
                        if not app_instance.last_image_generation_info:
                            msg = i18n.get_text("retry_no_image", category="ui")
                            return gr.skip(), gr.Markdown(value=msg, visible=True), gr.Button(visible=True)
                        
                        try:
                            image, status_msg = app_instance.retry_image_generation()
                            if image:
                                return image, gr.Markdown(value=status_msg, visible=True), gr.Button(visible=True)
                            else:
                                return gr.skip(), gr.Markdown(value=status_msg, visible=True), gr.Button(visible=True)
                        except Exception as e:
                            logger.error(f"Failed to retry image generation: {e}")
                            err = i18n.get_text("retry_error", category="ui", error=str(e))
                            return gr.skip(), gr.Markdown(value=err, visible=True), gr.Button(visible=True)
                    
                    def save_current_image_handler():
                        """현재 표시된 이미지를 그대로 image 폴더에 저장 (텍스트 오버레이 없음)"""
                        if app_instance.current_image is None:
                            msg = i18n.get_text("save_image_no_image", category="ui")
                            return gr.Markdown(value=msg, visible=True)
                        
                        try:
                            # 상태와 상관없이 현재 이미지를 그대로 저장 (오버레이 없음)
                            if app_instance.brain is not None and app_instance.brain.state is not None:
                                state = app_instance.brain.state
                                turn_number = getattr(state, "total_turns", None)
                            else:
                                turn_number = None

                            saved_path = app_instance._save_generated_image(app_instance.current_image, turn_number)
                            if saved_path:
                                msg = i18n.get_text("save_image_success", category="ui", path=saved_path)
                                return gr.Markdown(value=msg, visible=True)
                            else:
                                msg = i18n.get_text("save_image_fail", category="ui")
                                return gr.Markdown(value=msg, visible=True)
                        except Exception as e:
                            logger.error(f"Failed to save current image with overlay: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            msg = i18n.get_text("save_image_error", category="ui", error=str(e))
                            return gr.Markdown(value=msg, visible=True)

                    def save_moment_image_handler():
                        """현재 이미지를 2배 확대 + 대사/속마음/행동/상태 오버레이로 저장"""
                        if app_instance.current_image is None:
                            msg = i18n.get_text("save_image_no_image", category="ui")
                            return gr.Markdown(value=msg, visible=True)
                        try:
                            saved_path = app_instance.save_moment_image()
                            if saved_path:
                                msg = i18n.get_text("save_moment_success", category="ui", path=saved_path)
                                return gr.Markdown(value=msg, visible=True)
                            msg = i18n.get_text("save_moment_fail", category="ui")
                            return gr.Markdown(value=msg, visible=True)
                        except Exception as e:
                            logger.error(f"Failed to save moment image: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            msg = i18n.get_text("save_moment_error", category="ui", error=str(e))
                            return gr.Markdown(value=msg, visible=True)

                    # 메인 submit - 이미지와 차트는 비동기로 업데이트
                    submit_btn.click(
                        on_submit,
                        inputs=[user_input, chatbot],
                        outputs=[chatbot, user_input, stats_display, thought_display, action_display, image_update_trigger, stats_chart, event_notification]
                    ).then(
                        update_image_if_needed,
                        inputs=[image_update_trigger],
                        outputs=[image_display, retry_image_btn]
                    ).then(
                        update_chart_async,
                        inputs=[chatbot],
                        outputs=[stats_chart]
                    )
                    
                    user_input.submit(
                        on_submit,
                        inputs=[user_input, chatbot],
                        outputs=[chatbot, user_input, stats_display, thought_display, action_display, image_update_trigger, stats_chart, event_notification]
                    ).then(
                        update_image_if_needed,
                        inputs=[image_update_trigger],
                        outputs=[image_display, retry_image_btn]
                    ).then(
                        update_chart_async,
                        inputs=[chatbot],
                        outputs=[stats_chart]
                    )

                    # 재시도 버튼 클릭 핸들러
                    retry_image_btn.click(
                        retry_image_handler,
                        inputs=[],
                        outputs=[image_display, retry_image_status, retry_image_btn]
                    )

                    # 이미지 저장 버튼 클릭 핸들러
                    save_image_btn.click(
                        save_current_image_handler,
                        inputs=[],
                        outputs=[save_image_status]
                    )
                    
                    # 순간 저장 버튼 클릭 핸들러
                    save_moment_btn.click(
                        save_moment_image_handler,
                        inputs=[],
                        outputs=[save_moment_status]
                    )
                    
                    # 시나리오 갤러리 선택 이벤트 연결 (대화 탭 컴포넌트 정의 이후)
                    def on_scenario_gallery_select(evt: gr.SelectData):
                        """갤러리에서 시나리오 선택 시"""
                        if evt.index is None:
                            return gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip()
                        
                        import os
                        scenarios = app_instance.get_scenario_files()
                        # 파일 수정 시간 기준으로 최신순 정렬 (역순)
                        scenario_paths = []
                        for scenario_name in scenarios:
                            scenario_path = config.SCENARIOS_DIR / f"{scenario_name}.json"
                            if scenario_path.exists():
                                mtime = os.path.getmtime(scenario_path)
                                scenario_paths.append((mtime, scenario_name))
                        scenario_paths.sort(reverse=True)
                        scenarios = [name for _, name in scenario_paths]
                        
                        if evt.index >= len(scenarios):
                            return gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip()
                        
                        selected_scenario = scenarios[evt.index]
                        # continue_chat 함수 호출
                        return continue_chat(selected_scenario)
                    
                    scenario_gallery.select(
                        fn=on_scenario_gallery_select,
                        outputs=[
                            setup_status, tabs,
                            chatbot, gr.Textbox(visible=False), stats_display, image_display,
                            gr.Textbox(visible=False), thought_display, action_display, stats_chart
                        ]
                    )
                    
                    # 모델 로드 완료 시 UI 활성화
                    def enable_chat_ui():
                        if app_instance.model_loaded:
                            return (
                                gr.Button(interactive=True),  # submit_btn
                                gr.Textbox(interactive=True)  # user_input
                            )
                        return (
                            gr.Button(interactive=False),
                            gr.Textbox(interactive=False)
                        )
                    
                    # 탭 전환 시 UI 상태 확인
                    chat_tab.select(
                        enable_chat_ui,
                        inputs=[],
                        outputs=[submit_btn, user_input]
                    )
                    
                
                # ========== 탭 4: 환경설정 ==========
                with gr.Tab(i18n.get_text("tab_settings"), id="settings_tab"):
                    # 언어 설정 섹션 (최상단)
                    gr.Markdown(f"## {i18n.get_text('language_settings')}")
                    language_radio = gr.Radio(
                        label=i18n.get_text("language_label"),
                        choices=["en", "kr"],
                        value=language,
                        info=i18n.get_text("language_info")
                    )
                    language_status = gr.Markdown("")
                    
                    def change_language(selected_language):
                        """언어 변경 핸들러"""
                        try:
                            env_config = app_instance.load_env_config()
                            env_config["language"] = selected_language
                            if app_instance.save_env_config(env_config):
                                set_global_language(selected_language)
                                # Brain 언어 업데이트
                                if app_instance.brain is not None:
                                    app_instance.brain.language = selected_language
                                return i18n.get_text("msg_settings_save_success", category="ui")
                            else:
                                return i18n.get_text("msg_settings_save_failed", category="ui")
                        except Exception as e:
                            logger.error(f"Failed to change language: {e}")
                            return f"❌ Language change failed: {str(e)}"
                    
                    language_radio.change(
                        change_language,
                        inputs=[language_radio],
                        outputs=[language_status]
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown(f"## {i18n.get_text('settings_llm_title')}")
                    
                    # LLM 설정 로드
                    llm_settings = env_config.get("llm_settings", {})
                    provider = llm_settings.get("provider", "ollama")
                    ollama_model = llm_settings.get("ollama_model", "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest")
                    openrouter_model = llm_settings.get("openrouter_model", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
                    llm_temperature = float(llm_settings.get("temperature", config.LLM_CONFIG["temperature"]))
                    llm_top_p = float(llm_settings.get("top_p", config.LLM_CONFIG["top_p"]))
                    llm_max_tokens = int(llm_settings.get("max_tokens", config.LLM_CONFIG["max_tokens"]))
                    llm_presence_penalty = float(llm_settings.get("presence_penalty", config.LLM_CONFIG["presence_penalty"]))
                    llm_frequency_penalty = float(llm_settings.get("frequency_penalty", config.LLM_CONFIG["frequency_penalty"]))
                    # API 키는 파일에서 불러오기
                    openrouter_api_key = app_instance._load_openrouter_api_key()
                    
                    llm_provider = gr.Radio(
                        label=i18n.get_text("llm_provider"),
                        choices=["ollama", "openrouter"],
                        value=provider,
                        info=i18n.get_text("llm_provider_info")
                    )
                    
                    with gr.Group(visible=(provider == "ollama")) as ollama_group:
                        ollama_model_input = gr.Textbox(
                            label=i18n.get_text("ollama_model"),
                            value=ollama_model,
                            placeholder=i18n.get_text("ollama_model_placeholder"),
                            info=i18n.get_text("ollama_model_info")
                        )
                    
                    with gr.Group(visible=(provider == "openrouter")) as openrouter_group:
                        openrouter_api_key_input = gr.Textbox(
                            label=i18n.get_text("openrouter_api_key"),
                            value=openrouter_api_key,
                            placeholder=i18n.get_text("openrouter_api_key_placeholder"),
                            type="password",
                            info=i18n.get_text("openrouter_api_key_info")
                        )
                        openrouter_model_input = gr.Textbox(
                            label=i18n.get_text("openrouter_model"),
                            value=openrouter_model,
                            placeholder=i18n.get_text("openrouter_model_placeholder"),
                            info=i18n.get_text("openrouter_model_info")
                        )
                    
                    # 공통 LLM 파라미터 (ollama/openrouter 공통)
                    with gr.Row():
                        temperature_input = gr.Number(
                            label=i18n.get_text("llm_temperature"),
                            value=llm_temperature,
                            minimum=0.0,
                            maximum=2.0,
                            step=0.05,
                            info=i18n.get_text("llm_temperature_info")
                        )
                        top_p_input = gr.Number(
                            label=i18n.get_text("llm_top_p"),
                            value=llm_top_p,
                            minimum=0.0,
                            maximum=1.0,
                            step=0.01,
                            info=i18n.get_text("llm_top_p_info")
                        )
                    with gr.Row():
                        max_tokens_input = gr.Number(
                            label=i18n.get_text("llm_max_tokens"),
                            value=llm_max_tokens,
                            minimum=1,
                            maximum=4000,
                            step=50,
                            info=i18n.get_text("llm_max_tokens_info")
                        )
                        presence_penalty_input = gr.Number(
                            label=i18n.get_text("llm_presence_penalty"),
                            value=llm_presence_penalty,
                            minimum=-2.0,
                            maximum=2.0,
                            step=0.05,
                            info=i18n.get_text("llm_presence_penalty_info")
                        )
                        frequency_penalty_input = gr.Number(
                            label=i18n.get_text("llm_frequency_penalty"),
                            value=llm_frequency_penalty,
                            minimum=-2.0,
                            maximum=2.0,
                            step=0.05,
                            info=i18n.get_text("llm_frequency_penalty_info")
                        )

                    # Provider 변경 시 UI 표시/숨김
                    def update_provider_ui(selected_provider):
                        return (
                            gr.Group(visible=(selected_provider == "ollama")),
                            gr.Group(visible=(selected_provider == "openrouter"))
                        )
                    
                    llm_provider.change(
                        update_provider_ui,
                        inputs=[llm_provider],
                        outputs=[ollama_group, openrouter_group]
                    )
                    
                    settings_status = gr.Markdown("")
                    save_settings_btn = gr.Button(i18n.get_text("btn_save_settings"), variant="primary")
                    
                    def save_llm_settings(provider_val, ollama_model_val, openrouter_key_val, openrouter_model_val, temperature_val, top_p_val, max_tokens_val, presence_penalty_val, frequency_penalty_val):
                        """LLM 설정 저장"""
                        try:
                            env_config = app_instance.load_env_config()
                            
                            # OpenRouter API 키는 별도 파일에 저장
                            if provider_val == "openrouter" and openrouter_key_val:
                                if not app_instance._save_openrouter_api_key(openrouter_key_val):
                                    return i18n.get_text("msg_openrouter_api_key_save_failed")
                            
                            # LLM 설정 업데이트 (API 키는 제외)
                            # 수치형 파라미터 정규화
                            def to_float(val, default):
                                try:
                                    return float(val)
                                except (TypeError, ValueError):
                                    return default
                            def to_int(val, default):
                                try:
                                    return int(val)
                                except (TypeError, ValueError):
                                    return default
                            
                            env_config["llm_settings"] = {
                                "provider": provider_val,
                                "ollama_model": ollama_model_val or "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
                                "openrouter_model": openrouter_model_val or "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                                "temperature": to_float(temperature_val, config.LLM_CONFIG["temperature"]),
                                "top_p": to_float(top_p_val, config.LLM_CONFIG["top_p"]),
                                "max_tokens": to_int(max_tokens_val, config.LLM_CONFIG["max_tokens"]),
                                "presence_penalty": to_float(presence_penalty_val, config.LLM_CONFIG["presence_penalty"]),
                                "frequency_penalty": to_float(frequency_penalty_val, config.LLM_CONFIG["frequency_penalty"]),
                            }
                            
                            # 환경설정 저장
                            if app_instance.save_env_config(env_config):
                                # Brain 재초기화 (새 설정 적용)
                                try:
                                    if app_instance.brain is not None:
                                        # 기존 Brain의 memory_manager를 새 설정으로 재초기화
                                        llm_settings = env_config["llm_settings"]
                                        # API 키는 파일에서 불러오기
                                        api_key = app_instance._load_openrouter_api_key() if llm_settings["provider"] == "openrouter" else None
                                        app_instance.brain.memory_manager = MemoryManager(
                                            dev_mode=app_instance.dev_mode,
                                            provider=llm_settings["provider"],
                                            model_name=llm_settings["ollama_model"] if llm_settings["provider"] == "ollama" else llm_settings["openrouter_model"],
                                            api_key=api_key
                                        )
                                        
                                        # 모델 로드 시도 (OpenRouter 실패 시 Ollama로 폴백)
                                        result = app_instance.brain.memory_manager.load_model()
                                        if result is None and llm_settings["provider"] == "openrouter":
                                            logger.warning("OpenRouter 연결 실패, Ollama로 폴백 시도...")
                                            # Ollama로 폴백
                                            env_config["llm_settings"]["provider"] = "ollama"
                                            app_instance.brain.memory_manager = MemoryManager(
                                                dev_mode=app_instance.dev_mode,
                                                provider="ollama",
                                                model_name=llm_settings["ollama_model"]
                                            )
                                            result = app_instance.brain.memory_manager.load_model()
                                            if result is None:
                                                return i18n.get_text("msg_openrouter_fallback_failed")
                                            # 폴백 설정 저장
                                            app_instance.save_env_config(env_config)
                                            return i18n.get_text("msg_openrouter_fallback_success")
                                        
                                        app_instance.model_loaded = (result is not None)
                                        if app_instance.model_loaded:
                                            return i18n.get_text("msg_settings_saved_with_provider", provider=llm_settings['provider'].upper())
                                        else:
                                            return i18n.get_text("msg_settings_saved_but_connection_failed", provider=llm_settings['provider'].upper())
                                    else:
                                        return i18n.get_text("msg_settings_saved_next_start")
                                except Exception as e:
                                    logger.error(f"Failed to reinitialize Brain: {e}")
                                    return i18n.get_text("msg_settings_saved_reconnect_failed", error=str(e))
                            else:
                                return i18n.get_text("msg_settings_save_failed", error="")
                        except Exception as e:
                            logger.error(f"Failed to save LLM settings: {e}")
                            return i18n.get_text("msg_settings_save_failed", error=f": {str(e)}")
                    
                    save_settings_btn.click(
                        save_llm_settings,
                        inputs=[llm_provider, ollama_model_input, openrouter_api_key_input, openrouter_model_input, temperature_input, top_p_input, max_tokens_input, presence_penalty_input, frequency_penalty_input],
                        outputs=[settings_status]
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown("## ComfyUI 설정")
                    
                    # 스타일별 기본 설정값 정의
                    STYLE_CONFIGS = {
                        "SDXL": {
                            "workflow": "comfyui_2d.json",
                            "workflow_lora": "comfyui_2d_lora.json",
                            "model_name": "Zeniji_Mix K-Webtoon.safetensors",
                            "vae_name": "sdxl_vae.safetensors",
                            "clip_name": "",
                            "lora_name": "",
                            "lora_strength_model": 1.0,
                            "steps": 30,
                            "cfg": 5,
                            "sampler_name": "euler",
                            "scheduler": "simple"
                        },
                        "QWEN/Z-image": {
                            "workflow": "comfyui_real.json",
                            "workflow_lora": "comfyui_real_lora.json",
                            "model_name": "Zeniji_mix_ZiT_v1.safetensors",
                            "vae_name": "zImage_vae.safetensors",
                            "clip_name": "zImage_textEncoder.safetensors",
                            "lora_name": "ZiT_K_beauty_A.safetensors",
                            "lora_strength_model": 1.0,
                            "steps": 9,
                            "cfg": 1,
                            "sampler_name": "euler",
                            "scheduler": "simple"
                        }
                    }
                    
                    # ComfyUI 설정 로드
                    comfyui_settings = env_config.get("comfyui_settings", {})
                    comfyui_port = comfyui_settings.get("server_port", 8000)
                    comfyui_style = comfyui_settings.get("style", "QWEN/Z-image")
                    comfyui_use_lora = comfyui_settings.get("use_lora", False)
                    style_defaults = STYLE_CONFIGS.get(comfyui_style, STYLE_CONFIGS["QWEN/Z-image"])
                    # 스타일별 설정 로드 (개별 -> 공통 -> 기본값 순)
                    if comfyui_style == "SDXL":
                        default_workflow = style_defaults["workflow_lora"] if comfyui_use_lora else style_defaults["workflow"]
                        workflow_path = comfyui_settings.get("workflow_path_sdxl") or f"workflows/{default_workflow}"
                        comfyui_model = comfyui_settings.get("model_name_sdxl") or style_defaults["model_name"]
                        comfyui_vae = comfyui_settings.get("vae_name_sdxl") or style_defaults["vae_name"]
                        comfyui_clip = comfyui_settings.get("clip_name_sdxl") or style_defaults["clip_name"]
                        comfyui_lora_name = comfyui_settings.get("lora_name_sdxl") or style_defaults["lora_name"]
                        comfyui_lora_strength_model = comfyui_settings.get("lora_strength_model_sdxl")
                        if comfyui_lora_strength_model in (None, ""):
                            comfyui_lora_strength_model = style_defaults["lora_strength_model"]
                        comfyui_steps = comfyui_settings.get("steps_sdxl") or style_defaults["steps"]
                        comfyui_cfg = comfyui_settings.get("cfg_sdxl") or style_defaults["cfg"]
                        comfyui_sampler = comfyui_settings.get("sampler_name_sdxl") or style_defaults["sampler_name"]
                        comfyui_scheduler = comfyui_settings.get("scheduler_sdxl") or style_defaults["scheduler"]
                    else:
                        default_workflow = style_defaults["workflow_lora"] if comfyui_use_lora else style_defaults["workflow"]
                        workflow_path = comfyui_settings.get("workflow_path_qwen") or f"workflows/{default_workflow}"
                        comfyui_model = comfyui_settings.get("model_name_qwen") or style_defaults["model_name"]
                        comfyui_vae = comfyui_settings.get("vae_name_qwen") or style_defaults["vae_name"]
                        comfyui_clip = comfyui_settings.get("clip_name_qwen") or style_defaults["clip_name"]
                        comfyui_lora_name = comfyui_settings.get("lora_name_qwen") or style_defaults["lora_name"]
                        comfyui_lora_strength_model = comfyui_settings.get("lora_strength_model_qwen")
                        if comfyui_lora_strength_model in (None, ""):
                            comfyui_lora_strength_model = style_defaults["lora_strength_model"]
                        comfyui_steps = comfyui_settings.get("steps_qwen") or style_defaults["steps"]
                        comfyui_cfg = comfyui_settings.get("cfg_qwen") or style_defaults["cfg"]
                        comfyui_sampler = comfyui_settings.get("sampler_name_qwen") or style_defaults["sampler_name"]
                        comfyui_scheduler = comfyui_settings.get("scheduler_qwen") or style_defaults["scheduler"]
                    comfyui_quality_tag = comfyui_settings.get("quality_tag", "masterpiece, best quality, very awa")
                    comfyui_negative_prompt = comfyui_settings.get("negative_prompt", "(bad quality, worst quality, low quality), 3d, 3d rendering, manga, cartoon, 2d, fatty, thick body, big body, huge breasts, muscular, mole, watermark, text")
                    comfyui_upscale_model = comfyui_settings.get("upscale_model_name", "4x-UltraSharp.pth")
                    
                    with gr.Row():
                        with gr.Column():
                            comfyui_port_input = gr.Number(
                                label=i18n.get_text("comfyui_port"),
                                value=comfyui_port,
                                minimum=1,
                                maximum=65535,
                                step=1,
                                info=i18n.get_text("comfyui_port_info")
                            )
                            comfyui_style_input = gr.Radio(
                                label=i18n.get_text("comfyui_style"),
                                choices=["QWEN/Z-image", "SDXL"],
                                value=comfyui_style,
                                info=i18n.get_text("comfyui_style_info")
                            )
                            comfyui_use_lora_input = gr.Checkbox(
                                label=i18n.get_text("comfyui_use_lora") if hasattr(i18n, "get_text") else "Use LoRA",
                                value=comfyui_use_lora
                            )
                            with gr.Group(visible=(comfyui_style == "SDXL")) as comfyui_2d_group:
                                comfyui_quality_tag_input = gr.Textbox(
                                    label=i18n.get_text("comfyui_quality_tag"),
                                    value=comfyui_quality_tag,
                                    placeholder=i18n.get_text("comfyui_quality_tag_placeholder"),
                                    info=i18n.get_text("comfyui_quality_tag_info")
                                )
                                comfyui_negative_prompt_input = gr.Textbox(
                                    label=i18n.get_text("comfyui_negative_prompt"),
                                    value=comfyui_negative_prompt,
                                    placeholder=i18n.get_text("comfyui_negative_prompt_placeholder"),
                                    info=i18n.get_text("comfyui_negative_prompt_info"),
                                    lines=3
                                )
                                comfyui_upscale_model_input = gr.Textbox(
                                    label=i18n.get_text("comfyui_upscale_model"),
                                    value=comfyui_upscale_model,
                                    placeholder=i18n.get_text("comfyui_upscale_model_placeholder"),
                                    info=i18n.get_text("comfyui_upscale_model_info")
                                )
                            comfyui_model_input = gr.Textbox(
                                label=i18n.get_text("comfyui_model"),
                                value=comfyui_model,
                                placeholder=i18n.get_text("comfyui_model_placeholder"),
                                info=i18n.get_text("comfyui_model_info")
                            )
                            comfyui_vae_input = gr.Textbox(
                                label=i18n.get_text("comfyui_vae"),
                                value=comfyui_vae,
                                placeholder=i18n.get_text("comfyui_vae_placeholder"),
                                info=i18n.get_text("comfyui_vae_info")
                            )
                            comfyui_clip_input = gr.Textbox(
                                label=i18n.get_text("comfyui_clip"),
                                value=comfyui_clip,
                                placeholder=i18n.get_text("comfyui_clip_placeholder"),
                                info=i18n.get_text("comfyui_clip_info"),
                                visible=(comfyui_style != "SDXL")
                            )
                            with gr.Group(visible=comfyui_use_lora) as comfyui_lora_group:
                                comfyui_lora_name_input = gr.Textbox(
                                    label=i18n.get_text("comfyui_lora_name"),
                                    value=comfyui_lora_name,
                                    placeholder=i18n.get_text("comfyui_lora_name_placeholder"),
                                    info=i18n.get_text("comfyui_lora_name_info")
                                )
                        with gr.Column():
                            comfyui_steps_input = gr.Number(
                                label=i18n.get_text("comfyui_steps"),
                                value=comfyui_steps,
                                minimum=1,
                                maximum=100,
                                step=1,
                                info=i18n.get_text("comfyui_steps_info")
                            )
                            comfyui_cfg_input = gr.Number(
                                label=i18n.get_text("comfyui_cfg"),
                                value=comfyui_cfg,
                                minimum=0.1,
                                maximum=20.0,
                                step=0.1,
                                info=i18n.get_text("comfyui_cfg_info")
                            )
                            comfyui_sampler_input = gr.Textbox(
                                label=i18n.get_text("comfyui_sampler"),
                                value=comfyui_sampler,
                                placeholder=i18n.get_text("comfyui_sampler_placeholder"),
                                info=i18n.get_text("comfyui_sampler_info")
                            )
                            comfyui_scheduler_input = gr.Textbox(
                                label=i18n.get_text("comfyui_scheduler"),
                                value=comfyui_scheduler,
                                placeholder=i18n.get_text("comfyui_scheduler_placeholder"),
                                info=i18n.get_text("comfyui_scheduler_info")
                            )
                            with comfyui_lora_group:
                                comfyui_lora_strength_model_input = gr.Number(
                                    label=i18n.get_text("comfyui_lora_strength_model"),
                                    value=comfyui_lora_strength_model,
                                    minimum=-10.0,
                                    maximum=10.0,
                                    step=0.01,
                                    info=i18n.get_text("comfyui_lora_strength_model_info")
                                )
                    
                    # 스타일 변경 시 UI 업데이트
                    def update_style_ui(selected_style):
                        """스타일 변경 시 관련 설정 자동 변경"""
                        style_defaults = STYLE_CONFIGS.get(selected_style, STYLE_CONFIGS["QWEN/Z-image"])
                        style_key = "sdxl" if selected_style == "SDXL" else "qwen"
                        # 현재 설정에서 스타일별 sampler/scheduler 가져오기
                        env_config = app_instance.load_env_config()
                        comfyui_settings = env_config.get("comfyui_settings", {})
                        if selected_style == "SDXL":
                            sampler_val = comfyui_settings.get("sampler_name_sdxl") or comfyui_settings.get("sampler_name") or style_defaults["sampler_name"]
                            scheduler_val = comfyui_settings.get("scheduler_sdxl") or comfyui_settings.get("scheduler") or style_defaults["scheduler"]
                        else:
                            sampler_val = comfyui_settings.get("sampler_name_qwen") or comfyui_settings.get("sampler_name") or style_defaults["sampler_name"]
                            scheduler_val = comfyui_settings.get("scheduler_qwen") or comfyui_settings.get("scheduler") or style_defaults["scheduler"]
                        model_val = comfyui_settings.get(f"model_name_{style_key}") or style_defaults["model_name"]
                        vae_val = comfyui_settings.get(f"vae_name_{style_key}") or style_defaults["vae_name"]
                        clip_val = comfyui_settings.get(f"clip_name_{style_key}") or style_defaults["clip_name"]
                        lora_val = comfyui_settings.get(f"lora_name_{style_key}") or style_defaults.get("lora_name", "")
                        lora_strength_val = comfyui_settings.get(f"lora_strength_model_{style_key}")
                        if lora_strength_val in (None, ""):
                            lora_strength_val = style_defaults.get("lora_strength_model", 1.0)
                        steps_val = comfyui_settings.get(f"steps_{style_key}") or style_defaults["steps"]
                        cfg_val = comfyui_settings.get(f"cfg_{style_key}") or style_defaults["cfg"]
                        
                        return (
                            gr.Textbox(value=model_val),  # 모델
                            gr.Textbox(value=vae_val),  # VAE
                            gr.Textbox(value=clip_val, visible=(selected_style != "SDXL")),  # CLIP (SDXL일 때 숨김)
                            gr.Textbox(value=lora_val),  # LoRA 이름
                            gr.Number(value=steps_val),  # Steps
                            gr.Number(value=cfg_val),  # CFG
                            gr.Textbox(value=sampler_val),  # Sampler
                            gr.Textbox(value=scheduler_val),  # Scheduler
                            gr.Number(value=lora_strength_val),  # LoRA 강도
                            gr.Group(visible=(selected_style == "SDXL")),  # 2D 설정 그룹
                        )
                    
                    comfyui_style_input.change(
                        update_style_ui,
                        inputs=[comfyui_style_input],
                        outputs=[comfyui_model_input, comfyui_vae_input, comfyui_clip_input, comfyui_lora_name_input, comfyui_steps_input, comfyui_cfg_input, comfyui_sampler_input, comfyui_scheduler_input, comfyui_lora_strength_model_input, comfyui_2d_group]
                    )
                    
                    # LoRA 토글 변경 시 UI 업데이트 (LoRA 그룹만)
                    def update_lora_toggle(use_lora):
                        return gr.Group(visible=use_lora)
                    
                    comfyui_use_lora_input.change(
                        update_lora_toggle,
                        inputs=[comfyui_use_lora_input],
                        outputs=[comfyui_lora_group]
                    )
                    
                    comfyui_status = gr.Markdown("")
                    save_comfyui_btn = gr.Button(i18n.get_text("btn_save_comfyui"), variant="primary")
                    
                    def save_comfyui_settings(port_val, style_val, use_lora_val, model_val, vae_val, clip_val, lora_name_val, lora_strength_val, steps_val, cfg_val, sampler_val, scheduler_val, quality_tag_val, negative_prompt_val, upscale_model_val):
                        """ComfyUI 설정 저장"""
                        try:
                            env_config = app_instance.load_env_config()
                            
                            # ComfyUI 설정 업데이트
                            if "comfyui_settings" not in env_config:
                                env_config["comfyui_settings"] = {}
                            
                            # 스타일별 기본값 로드
                            style_val = style_val or "QWEN/Z-image"
                            style_key = "sdxl" if style_val == "SDXL" else "qwen"
                            style_defaults = STYLE_CONFIGS.get(style_val, STYLE_CONFIGS["QWEN/Z-image"])
                            # LoRA 토글에 따라 기본 워크플로우 선택
                            use_lora = bool(use_lora_val)
                            base_workflow = style_defaults["workflow_lora"] if use_lora else style_defaults["workflow"]
                            workflow_path = f"workflows/{base_workflow}"
                            model_default = style_defaults["model_name"]
                            vae_default = style_defaults["vae_name"]
                            clip_default = style_defaults["clip_name"]
                            lora_default = style_defaults.get("lora_name", "")
                            lora_strength_default = style_defaults.get("lora_strength_model", 1.0)
                            steps_default = style_defaults["steps"]
                            cfg_default = style_defaults["cfg"]
                            
                            model_value = model_val or model_default
                            vae_value = vae_val or vae_default
                            clip_value = clip_val or clip_default
                            lora_value = lora_name_val or lora_default
                            try:
                                lora_strength_value = float(lora_strength_val) if lora_strength_val not in (None, "") else lora_strength_default
                            except (TypeError, ValueError):
                                lora_strength_value = lora_strength_default
                            steps_value = int(steps_val) if steps_val not in (None, "") else steps_default
                            cfg_value = float(cfg_val) if cfg_val not in (None, "") else cfg_default
                            
                            env_config["comfyui_settings"]["server_port"] = int(port_val) if port_val else 8000
                            env_config["comfyui_settings"]["style"] = style_val
                            
                            # 전역 LoRA 사용 여부 저장
                            env_config["comfyui_settings"]["use_lora"] = use_lora
                            
                            env_config["comfyui_settings"][f"workflow_path_{style_key}"] = workflow_path
                            env_config["comfyui_settings"][f"model_name_{style_key}"] = model_value
                            env_config["comfyui_settings"][f"vae_name_{style_key}"] = vae_value
                            env_config["comfyui_settings"][f"clip_name_{style_key}"] = clip_value
                            env_config["comfyui_settings"][f"lora_name_{style_key}"] = lora_value
                            env_config["comfyui_settings"][f"lora_strength_model_{style_key}"] = lora_strength_value
                            env_config["comfyui_settings"][f"steps_{style_key}"] = steps_value
                            env_config["comfyui_settings"][f"cfg_{style_key}"] = cfg_value
                            # 스타일별로 sampler/scheduler 저장
                            if style_val == "SDXL":
                                env_config["comfyui_settings"]["sampler_name_sdxl"] = sampler_val or "euler"
                                env_config["comfyui_settings"]["scheduler_sdxl"] = scheduler_val or "simple"
                            else:
                                env_config["comfyui_settings"]["sampler_name_qwen"] = sampler_val or "euler"
                                env_config["comfyui_settings"]["scheduler_qwen"] = scheduler_val or "simple"
                            env_config["comfyui_settings"]["quality_tag"] = quality_tag_val or ""
                            env_config["comfyui_settings"]["negative_prompt"] = negative_prompt_val or ""
                            env_config["comfyui_settings"]["upscale_model_name"] = upscale_model_val or "4x-UltraSharp.pth"
                            
                            # 환경설정 저장
                            if app_instance.save_env_config(env_config):
                                # ComfyClient 재초기화 (새 설정 적용)
                                try:
                                    if app_instance.comfy_client is not None:
                                        server_address = f"127.0.0.1:{env_config['comfyui_settings']['server_port']}"
                                        style = env_config['comfyui_settings'].get('style', 'QWEN/Z-image')
                                        style_defaults = STYLE_CONFIGS.get(style, STYLE_CONFIGS["QWEN/Z-image"])
                                        # 스타일별 sampler/scheduler 가져오기 (하위 호환성 포함)
                                        if style == "SDXL":
                                            # 저장된 경로가 있으면 그대로 사용, 없으면 LoRA 토글에 따라 선택
                                            use_lora = env_config['comfyui_settings'].get('use_lora', False)
                                            default_workflow = style_defaults["workflow_lora"] if use_lora else style_defaults["workflow"]
                                            workflow_path = env_config['comfyui_settings'].get('workflow_path_sdxl') or f"workflows/{default_workflow}"
                                            model_name = env_config['comfyui_settings'].get('model_name_sdxl') or style_defaults['model_name']
                                            vae_name = env_config['comfyui_settings'].get('vae_name_sdxl') or style_defaults['vae_name']
                                            clip_name = env_config['comfyui_settings'].get('clip_name_sdxl') or style_defaults['clip_name']
                                            # LoRA 토글에 따라 로라 적용/비적용
                                            if env_config['comfyui_settings'].get('use_lora', False):
                                                lora_name = env_config['comfyui_settings'].get('lora_name_sdxl') or style_defaults.get('lora_name', '')
                                                lora_strength_model = env_config['comfyui_settings'].get('lora_strength_model_sdxl')
                                                if lora_strength_model in (None, ""):
                                                    lora_strength_model = style_defaults.get('lora_strength_model', 1.0)
                                            else:
                                                lora_name = None
                                                lora_strength_model = None
                                            steps = env_config['comfyui_settings'].get('steps_sdxl') or style_defaults['steps']
                                            cfg = env_config['comfyui_settings'].get('cfg_sdxl') or style_defaults['cfg']
                                            sampler_name = env_config['comfyui_settings'].get('sampler_name_sdxl') or style_defaults['sampler_name']
                                            scheduler = env_config['comfyui_settings'].get('scheduler_sdxl') or style_defaults['scheduler']
                                        else:
                                            # 저장된 경로가 있으면 그대로 사용, 없으면 LoRA 토글에 따라 선택
                                            use_lora = env_config['comfyui_settings'].get('use_lora', False)
                                            default_workflow = style_defaults["workflow_lora"] if use_lora else style_defaults["workflow"]
                                            workflow_path = env_config['comfyui_settings'].get('workflow_path_qwen') or f"workflows/{default_workflow}"
                                            model_name = env_config['comfyui_settings'].get('model_name_qwen') or style_defaults['model_name']
                                            vae_name = env_config['comfyui_settings'].get('vae_name_qwen') or style_defaults['vae_name']
                                            clip_name = env_config['comfyui_settings'].get('clip_name_qwen') or style_defaults['clip_name']
                                            # LoRA 토글에 따라 로라 적용/비적용
                                            if env_config['comfyui_settings'].get('use_lora', False):
                                                lora_name = env_config['comfyui_settings'].get('lora_name_qwen') or style_defaults.get('lora_name', '')
                                                lora_strength_model = env_config['comfyui_settings'].get('lora_strength_model_qwen')
                                                if lora_strength_model in (None, ""):
                                                    lora_strength_model = style_defaults.get('lora_strength_model', 1.0)
                                            else:
                                                lora_name = None
                                                lora_strength_model = None
                                            steps = env_config['comfyui_settings'].get('steps_qwen') or style_defaults['steps']
                                            cfg = env_config['comfyui_settings'].get('cfg_qwen') or style_defaults['cfg']
                                            sampler_name = env_config['comfyui_settings'].get('sampler_name_qwen') or style_defaults['sampler_name']
                                            scheduler = env_config['comfyui_settings'].get('scheduler_qwen') or style_defaults['scheduler']
                                        quality_tag = env_config['comfyui_settings'].get('quality_tag', '')
                                        negative_prompt = env_config['comfyui_settings'].get('negative_prompt', '')
                                        upscale_model_name = env_config['comfyui_settings'].get('upscale_model_name', '4x-UltraSharp.pth')
                                        app_instance.comfy_client = ComfyClient(
                                            server_address=server_address,
                                            workflow_path=workflow_path,
                                            model_name=model_name,
                                            steps=steps,
                                            cfg=cfg,
                                            sampler_name=sampler_name,
                                            scheduler=scheduler,
                                            vae_name=vae_name,
                                            clip_name=clip_name,
                                            style=style,
                                            quality_tag=quality_tag,
                                            negative_prompt=negative_prompt,
                                            upscale_model_name=upscale_model_name,
                                            lora_name=lora_name,
                                            lora_strength_model=lora_strength_model
                                        )
                                        # LoRA 사용 여부에 따라 로그 메시지 분리
                                        if lora_name is not None:
                                            logger.info(
                                                f"ComfyClient 재초기화 완료: {server_address}, "
                                                f"workflow: {workflow_path}, model: {model_name}, vae: {vae_name}, clip: {clip_name}, "
                                                f"LoRA enabled: name={lora_name}, strength_model={lora_strength_model}, "
                                                f"steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}"
                                            )
                                        else:
                                            logger.info(
                                                f"ComfyClient 재초기화 완료: {server_address}, "
                                                f"workflow: {workflow_path}, model: {model_name}, vae: {vae_name}, clip: {clip_name}, "
                                                f"LoRA disabled, steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}"
                                            )
                                    return i18n.get_text("msg_comfyui_settings_saved")
                                except Exception as e:
                                    logger.error(f"Failed to reinitialize ComfyClient: {e}")
                                    return i18n.get_text("msg_comfyui_settings_saved_reconnect_failed", error=str(e))
                            else:
                                return i18n.get_text("msg_comfyui_settings_save_failed", error="")
                        except Exception as e:
                            logger.error(f"Failed to save ComfyUI settings: {e}")
                            return i18n.get_text("msg_comfyui_settings_save_failed", error=f": {str(e)}")
                    
                    save_comfyui_btn.click(
                        save_comfyui_settings,
                        inputs=[comfyui_port_input, comfyui_style_input, comfyui_use_lora_input, comfyui_model_input, comfyui_vae_input, comfyui_clip_input, comfyui_lora_name_input, comfyui_lora_strength_model_input, comfyui_steps_input, comfyui_cfg_input, comfyui_sampler_input, comfyui_scheduler_input, comfyui_quality_tag_input, comfyui_negative_prompt_input, comfyui_upscale_model_input],
                        outputs=[comfyui_status]
                    )
            
            # 첫 탭의 버튼 클릭 시 대화 탭 컴포넌트 업데이트 (탭 밖에서 정의)
            start_btn.click(
                app_instance.validate_and_start,
                inputs=[
                    player_name, player_gender,
                    char_name, char_age, char_gender,
                    appearance, personality, speech_style,
                    p_val, a_val, d_val, i_val, t_val, dep_val,
                    initial_context, initial_background
                ],
                outputs=[
                    setup_status, tabs,
                    chatbot, gr.Textbox(visible=False), stats_display, image_display,
                    gr.Textbox(visible=False), thought_display, action_display, stats_chart,
                    submit_btn, user_input
                ]
            )
            
            # tabs 컴포넌트의 change 이벤트 연결 (탭 전환 시 UI 활성화)
            # 탭이 변경될 때마다 UI 상태 확인
            tabs.change(
                enable_chat_ui,
                inputs=[],
                outputs=[submit_btn, user_input]
            )
            
            # 설정 로드 시 UI 업데이트
            demo.load(
                enable_chat_ui,
                inputs=[],
                outputs=[submit_btn, user_input]
            )
            
            # Footer 추가
            gr.Markdown(
                f"""
                <div style="text-align: center; margin-top: 20px; padding: 10px; color: #666;">
                    ❤️ <a href="https://zeniji.love" target="_blank" style="color: #666; text-decoration: none;">zeniji.love</a><br>
                    💬 <a href="https://arca.live/b/zeniji" target="_blank" style="color: #666; text-decoration: none;">Zeniji Channel on Arcalive(KR)</a><br>
                    ☕ <a href="https://buymeacoffee.com/zeniji" target="_blank" style="color: #666; text-decoration: none;">Buy Me a Coffee</a><br>
                    <span style="font-size: 0.85em; opacity: 0.7;">Version {config.VERSION}</span>
                </div>
                """
            )
        
        return demo

