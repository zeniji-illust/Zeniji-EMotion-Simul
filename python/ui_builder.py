"""
UI Builder - Gradio UI 생성
"""

import gradio as gr
import logging
from pathlib import Path
import config
from comfy_client import ComfyClient
from memory_manager import MemoryManager

logger = logging.getLogger("UIBuilder")


class UIBuilder:
    """Gradio UI 빌더"""
    
    @staticmethod
    def create_ui(app_instance):
        """Gradio UI 생성"""
        # 설정 로드
        saved_config = app_instance.load_config()
        env_config = app_instance.load_env_config()
        
        with gr.Blocks(title="Zeniji Emotion Simul", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🎮 Zeniji Emotion Simul")
            
            with gr.Tabs() as tabs:
                # ========== 탭 1: 초기 설정 ==========
                with gr.Tab("⚙️ 초기 설정", id="setup_tab") as setup_tab:
                    gr.Markdown("## 캐릭터 및 시나리오 초기 설정")
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 👤 주인공 설정")
                            player_name = gr.Textbox(
                                label="이름",
                                value=saved_config["player"].get("name", ""),
                                placeholder="플레이어 이름"
                            )
                            player_gender = gr.Radio(
                                label="성별",
                                choices=["남성", "여성", "기타"],
                                value=saved_config["player"].get("gender", "남성")
                            )
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### 👥 상대방 설정")
                            char_name = gr.Textbox(
                                label="이름",
                                value=saved_config["character"].get("name", "예나"),
                                placeholder="캐릭터 이름"
                            )
                            # character 정보 안전하게 가져오기
                            character_info = saved_config.get("character") or {}
                            char_age_val = character_info.get("age")
                            char_age_val = int(char_age_val) if char_age_val is not None else 21
                            
                            char_age = gr.Slider(
                                label="나이",
                                minimum=18,
                                maximum=100,
                                value=char_age_val,
                                step=1
                            )
                            char_gender = gr.Radio(
                                label="성별",
                                choices=["남성", "여성", "기타"],
                                value=saved_config["character"].get("gender", "여성")
                            )
                    
                    gr.Markdown("### 📝 외모 및 성격")
                    appearance = gr.Textbox(
                        label="외모 묘사 (영어 태그 형식)",
                        value=saved_config["character"].get("appearance", ""),
                        placeholder="예: korean beauty, short hair, brown eyes, cute face, casual outfit",
                        info="이미지 생성용 영어 태그로 입력하세요 (쉼표로 구분)",
                        lines=3,
                        max_lines=5
                    )
                    personality = gr.Textbox(
                        label="성격 묘사",
                        value=saved_config["character"].get("personality", ""),
                        placeholder="예: 밝고 활발하지만 좋아하는 사람 앞에서는 수줍음이 많음",
                        lines=3,
                        max_lines=5
                    )
                    
                    gr.Markdown("### 📊 심리 지표 설정 (6축 시스템)")
                    gr.Markdown("각 수치는 0~100 사이이며, 초기값은 **최대 70**으로 제한됩니다.")
                    
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
                                label="P (Pleasure) - 쾌락",
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("P", 50.0) or 50.0,
                                step=1.0,
                                info="관계의 긍정/부정"
                            )
                            a_val = gr.Slider(
                                label="A (Arousal) - 각성",
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("A", 40.0) or 40.0,
                                step=1.0,
                                info="긴장감/에너지"
                            )
                            d_val = gr.Slider(
                                label="D (Dominance) - 지배",
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("D", 40.0) or 40.0,
                                step=1.0,
                                info="관계의 주도권"
                            )
                        with gr.Column():
                            i_val = gr.Slider(
                                label="I (Intimacy) - 친밀",
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("I", 20.0) or 20.0,
                                step=1.0,
                                info="정서적 친밀감"
                            )
                            t_val = gr.Slider(
                                label="T (Trust) - 신뢰",
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("T", 50.0) or 50.0,
                                step=1.0,
                                info="신뢰도"
                            )
                            dep_val = gr.Slider(
                                label="Dep (Dependency) - 의존",
                                minimum=0,
                                maximum=100,
                                value=safe_get_stat("Dep", 0.0) or 0.0,
                                step=1.0,
                                info="의존/집착도"
                            )
                    
                    gr.Markdown("### 🎭 프리셋")
                    with gr.Row():
                        for preset_name in config.PRESETS.keys():
                            preset_btn = gr.Button(preset_name, variant="secondary")
                            # lambda 클로저 문제 해결 및 fn 명시
                            def make_preset_handler(name):
                                def handler():
                                    return app_instance.apply_preset(name)
                                return handler
                            preset_btn.click(
                                fn=make_preset_handler(preset_name),
                                inputs=[],
                                outputs=[p_val, a_val, d_val, i_val, t_val, dep_val, appearance, personality]
                            )
                    
                    gr.Markdown("### 📖 초기 상황")
                    initial_context = gr.Textbox(
                        label="초기 상황 설명",
                        value=saved_config.get("initial_context", ""),
                        placeholder="대화가 시작되는 배경 상황을 설명하세요.",
                        lines=4,
                        max_lines=6
                    )
                    initial_background = gr.Textbox(
                        label="배경 (영어)",
                        value=saved_config.get("initial_background", "college library table, evening light"),
                        placeholder="college library table, evening light",
                        info="이미지 생성용 배경 설명 (영어)"
                    )
                    
                    # TODO: 랜덤 상황 생성 버튼
                    # random_context_btn = gr.Button("🎲 랜덤 상황 생성", variant="secondary")
                    
                    setup_status = gr.Markdown("")
                    
                    # 시나리오 불러오기
                    gr.Markdown("### 📚 대화 이어가기")
                    with gr.Row():
                        with gr.Column(scale=2):
                            scenario_dropdown = gr.Dropdown(
                                label="시나리오 파일",
                                choices=app_instance.get_scenario_files(),
                                value=None,
                                info="저장된 대화 시나리오 선택"
                            )
                        with gr.Column(scale=1):
                            continue_chat_btn = gr.Button("📖 대화 이어가기", variant="secondary", size="lg")
                            reload_scenario_btn = gr.Button("🔄 새로고침", variant="secondary", size="sm")
                    
                    # Character 파일 관리
                    with gr.Row():
                        with gr.Column(scale=2):
                            character_file_dropdown = gr.Dropdown(
                                label="캐릭터 파일",
                                choices=app_instance.get_character_files(),
                                value=None,
                                info="저장된 캐릭터 설정 파일 선택"
                            )
                        with gr.Column(scale=1):
                            character_filename_input = gr.Textbox(
                                label="저장할 파일명",
                                placeholder="예: my_character",
                                info="파일명만 입력 (확장자 자동 추가)"
                            )
                            overwrite_checkbox = gr.Checkbox(
                                label="덮어쓰기 허용",
                                value=False,
                                info="같은 파일명이 있을 때 덮어쓰기 허용"
                            )
                    
                    with gr.Row():
                        load_btn = gr.Button("📂 불러오기", variant="secondary", size="lg")
                        save_btn = gr.Button("💾 저장", variant="secondary", size="lg")
                        start_btn = gr.Button("🚀 시작", variant="primary", size="lg")
                        reload_character_btn = gr.Button("🔄 새로고침", variant="secondary", size="sm")
                    
                    def load_character(selected_file):
                        """캐릭터 파일 불러오기"""
                        if not selected_file:
                            return "⚠️ 파일을 선택해주세요.", *([gr.update()] * 12)
                        
                        try:
                            config = app_instance.load_character_config(selected_file)
                            
                            # UI 업데이트
                            return (
                                f"✅ {selected_file} 불러오기 완료!",
                                config["player"].get("name", ""),
                                config["player"].get("gender", "남성"),
                                config["character"].get("name", "예나"),
                                config["character"].get("age", 21),
                                config["character"].get("gender", "여성"),
                                config["character"].get("appearance", ""),
                                config["character"].get("personality", ""),
                                config["initial_stats"].get("P", 50.0),
                                config["initial_stats"].get("A", 40.0),
                                config["initial_stats"].get("D", 40.0),
                                config["initial_stats"].get("I", 20.0),
                                config["initial_stats"].get("T", 50.0),
                                config["initial_stats"].get("Dep", 0.0),
                                config.get("initial_context", ""),
                                config.get("initial_background", "college library table, evening light")
                            )
                        except Exception as e:
                            logger.error(f"Failed to load character: {e}")
                            return f"❌ 불러오기 실패: {str(e)}", *([gr.update()] * 12)
                    
                    def save_character(filename, overwrite, player_name, player_gender, char_name, char_age, char_gender,
                                     appearance, personality, p_val, a_val, d_val, i_val, t_val, dep_val,
                                     initial_context, initial_background):
                        """캐릭터 설정 저장"""
                        if not filename or not filename.strip():
                            return "⚠️ 파일명을 입력해주세요.", gr.Dropdown()
                        
                        try:
                            # 파일명 정리
                            clean_filename = filename.strip()
                            if not clean_filename.endswith('.json'):
                                clean_filename = f"{clean_filename}.json"
                            
                            # 파일이 이미 존재하는지 확인
                            file_path = config.CHARACTER_DIR / clean_filename
                            if file_path.exists() and not overwrite:
                                return f"⚠️ 경고: '{clean_filename}' 파일이 이미 존재합니다. '덮어쓰기 허용'을 체크하거나 다른 파일명을 사용해주세요.", gr.Dropdown()
                            
                            # 설정 데이터 구성
                            config_data = {
                                "player": {
                                    "name": player_name or "",
                                    "gender": player_gender or "남성"
                                },
                                "character": {
                                    "name": char_name or "예나",
                                    "age": int(char_age) if char_age else 21,
                                    "gender": char_gender or "여성",
                                    "appearance": appearance or "",
                                    "personality": personality or ""
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
                                "initial_background": initial_background or "college library table, evening light"
                            }
                            
                            if app_instance.save_character_config(config_data, clean_filename):
                                # character_config.json도 덮어쓰기 (다음 실행 시 기본값으로 사용)
                                app_instance.save_config(config_data)
                                
                                # 드롭다운 목록 새로고침
                                updated_files = app_instance.get_character_files()
                                return f"✅ {clean_filename} 저장 완료! (character_config.json도 업데이트됨)", gr.Dropdown(choices=updated_files, value=clean_filename.replace('.json', ''))
                            else:
                                return "❌ 저장 실패", gr.Dropdown()
                        except Exception as e:
                            logger.error(f"Failed to save character: {e}")
                            return f"❌ 저장 실패: {str(e)}", gr.Dropdown()
                    
                    def reload_character_files():
                        """캐릭터 파일 목록 새로고침"""
                        updated_files = app_instance.get_character_files()
                        return gr.Dropdown(choices=updated_files)
                    
                    def reload_scenario_files():
                        """시나리오 파일 목록 새로고침"""
                        updated_files = app_instance.get_scenario_files()
                        return gr.Dropdown(choices=updated_files)
                    
                    def reload_workflow_files(current_value):
                        """워크플로우 파일 목록 새로고침"""
                        workflows_dir = config.PROJECT_ROOT / "workflows"
                        workflow_files = []
                        if workflows_dir.exists():
                            workflow_files = sorted([f.name for f in workflows_dir.glob("*.json")])
                        if not workflow_files:
                            workflow_files = ["comfyui.json"]  # 기본값
                        
                        # 현재 선택된 값이 새 목록에 있으면 유지, 없으면 첫 번째 파일 선택
                        if current_value and current_value in workflow_files:
                            return gr.Dropdown(choices=workflow_files, value=current_value)
                        else:
                            return gr.Dropdown(choices=workflow_files, value=workflow_files[0] if workflow_files else None)
                    
                    load_btn.click(
                        load_character,
                        inputs=[character_file_dropdown],
                        outputs=[
                            setup_status,
                            player_name, player_gender,
                            char_name, char_age, char_gender,
                            appearance, personality,
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
                            appearance, personality,
                            p_val, a_val, d_val, i_val, t_val, dep_val,
                            initial_context, initial_background
                        ],
                        outputs=[setup_status, character_file_dropdown]
                    )
                    
                    reload_character_btn.click(
                        reload_character_files,
                        outputs=[character_file_dropdown]
                    )
                    
                    reload_scenario_btn.click(
                        reload_scenario_files,
                        outputs=[scenario_dropdown]
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
                            
                            if not scenario_data or "conversation" not in scenario_data:
                                return f"⚠️ 시나리오 '{selected_scenario}'를 불러올 수 없습니다.", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                            
                            history = scenario_data.get("conversation", [])
                            if not history:
                                return f"⚠️ 시나리오 '{selected_scenario}'에 대화 내용이 없습니다.", gr.Tabs(selected=None), [], "", "", None, "", "", "", None
                            
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
                            
                            # 문맥 정보 복원 (최근 턴)
                            if app_instance.brain is not None and "context" in scenario_data:
                                context = scenario_data["context"]
                                if "recent_turns" in context and hasattr(app_instance.brain, 'history'):
                                    # DialogueHistory에 턴 추가
                                    for turn_data in context["recent_turns"]:
                                        from state_manager import DialogueTurn
                                        turn = DialogueTurn(
                                            player_input=turn_data.get("player_input", ""),
                                            character_response=turn_data.get("character_response", ""),
                                            emotion=turn_data.get("emotion", "neutral"),
                                            stats_delta=turn_data.get("stats_delta", {})
                                        )
                                        app_instance.brain.history.add(turn)
                                    logger.info(f"Context restored: {len(context.get('recent_turns', []))} recent turns")
                            
                            # 히스토리를 chatbot 형식으로 변환 (정규화 함수 사용)
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
                                
                                stats_text = f"""
<div style="font-size: 0.85em; color: #666;">
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
<div>
<strong>6축 수치:</strong><br>
P (쾌락): {stats.get('P', 0):.0f}<br>
A (각성): {stats.get('A', 0):.0f}<br>
D (지배): {stats.get('D', 0):.0f}<br>
</div>
<div>
<strong>변화량:</strong><br>
I (친밀): {stats.get('I', 0):.0f}<br>
T (신뢰): {stats.get('T', 0):.0f}<br>
Dep (의존): {stats.get('Dep', 0):.0f}<br>
</div>
</div>
<br>
<strong>관계:</strong> {state.relationship_status} | <strong>기분:</strong> {calculated_mood}<br>
<strong>뱃지:</strong> {', '.join(state.badges) or 'None'}
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
                
                # ========== 탭 2: 대화 ==========
                with gr.Tab("💬 대화", id="chat_tab") as chat_tab:
                    # 이벤트 알림 (고정 위치, 필요시 표시)
                    event_notification = gr.HTML(value="", visible=False, elem_id="event-notification-container")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            chatbot = gr.Chatbot(label="대화", height=500)
                            
                            # 속마음: Accordion으로 접기/펼치기 가능하게
                            with gr.Accordion("💭 속마음 보기", open=False, visible=True) as thought_accordion:
                                thought_display = gr.Markdown(label="", visible=True)
                            
                            action_display = gr.Markdown(label="🎭 행동", visible=True)
                            user_input = gr.Textbox(label="입력", placeholder="말을 입력하세요...", interactive=False)
                            submit_btn = gr.Button("전송", variant="primary", interactive=False)
                        
                        with gr.Column(scale=1):
                            stats_chart = gr.Plot(label="6축 수치", show_label=True)
                            stats_display = gr.Markdown(label="상태 상세", show_label=True)
                            # 이미지와 재시도 버튼을 함께 표시하기 위한 컨테이너
                            image_display = gr.Image(label="캐릭터", height=400, show_label=False)
                            retry_image_btn = gr.Button("🔄 이미지 재시도", variant="secondary", size="sm", visible=False)
                            # 재시도 버튼 상태 표시용 (간단한 메시지용)
                            retry_image_status = gr.Markdown("", visible=False, elem_id="retry-status")
                    
                    # 시나리오 저장 (모든 컴포넌트 아래, 화면 너비 전체 사용)
                    with gr.Row():
                        scenario_save_name = gr.Textbox(
                            label="시나리오 저장",
                            placeholder="예: my_scenario",
                            info="현재 대화를 시나리오로 저장",
                            scale=3
                        )
                        save_scenario_btn = gr.Button("💾 시나리오 저장", variant="secondary", scale=1)
                        scenario_save_status = gr.Markdown("")
                    
                    # 이미지 업데이트 트리거용 hidden state
                    image_update_trigger = gr.State(value=None)
                    
                    def on_submit(message, history):
                        if not app_instance.model_loaded:
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
                        
                        new_history, output, stats, image, choices, thought, action, chart, event_notification = app_instance.process_turn(message, normalized_history)
                        
                        # 반환 전에 히스토리 다시 정규화 (안전장치)
                        normalized_new_history = normalize_chatbot_history(new_history)
                        
                        # image가 새로 생성됐으면 trigger에 넣고, 아니면 None
                        # 차트는 이전 차트를 먼저 반환하고, 새 차트는 나중에 업데이트
                        # 이벤트 알림이 있으면 표시, 없으면 숨김 (빈 문자열로 초기화)
                        event_visible = bool(event_notification and event_notification.strip())
                        event_html = event_notification if event_visible else ""
                        return normalized_new_history, "", stats, thought, action, image, previous_chart if previous_chart else chart, gr.HTML(value=event_html, visible=event_visible)
                    
                    def update_chart_async(history):
                        """백그라운드에서 차트 업데이트"""
                        if not app_instance.model_loaded or not history:
                            return gr.skip()
                        
                        # 마지막 대화에서 stats 추출하여 차트 생성
                        try:
                            # history에서 마지막 응답의 stats 가져오기
                            # 실제로는 process_turn에서 이미 차트를 생성했으므로 current_chart 사용
                            if app_instance.current_chart is not None:
                                return app_instance.current_chart
                        except:
                            pass
                        return gr.skip()
                    
                    def save_scenario_handler(scenario_name, history):
                        """시나리오 저장 핸들러 (대화 + 상태 정보 포함)"""
                        if not scenario_name or not scenario_name.strip():
                            return "⚠️ 시나리오 이름을 입력해주세요.", gr.Dropdown()
                        
                        if not history:
                            return "⚠️ 저장할 대화가 없습니다.", gr.Dropdown()
                        
                        try:
                            logger.info(f"Saving scenario: {scenario_name}, history length: {len(history) if history else 0}")
                            
                            # chatbot history를 process_turn 형식으로 변환
                            converted_history = []
                            for item in history:
                                if isinstance(item, list) and len(item) == 2:
                                    # Gradio chatbot 형식: [user_msg, assistant_msg]
                                    user_msg, assistant_msg = item
                                    if user_msg:
                                        # content가 리스트인 경우 처리
                                        if isinstance(user_msg, list):
                                            # [{'text': '...', 'type': 'text'}] 형식
                                            text_parts = [part.get('text', '') if isinstance(part, dict) else str(part) for part in user_msg]
                                            user_msg = ''.join(text_parts)
                                        converted_history.append({"role": "user", "content": str(user_msg)})
                                    if assistant_msg:
                                        # content가 리스트인 경우 처리
                                        if isinstance(assistant_msg, list):
                                            text_parts = [part.get('text', '') if isinstance(part, dict) else str(part) for part in assistant_msg]
                                            assistant_msg = ''.join(text_parts)
                                        converted_history.append({"role": "assistant", "content": str(assistant_msg)})
                                elif isinstance(item, dict):
                                    # 이미 dict 형식인 경우
                                    content = item.get("content", "")
                                    # content가 리스트인 경우 처리
                                    if isinstance(content, list):
                                        text_parts = [part.get('text', '') if isinstance(part, dict) else str(part) for part in content]
                                        content = ''.join(text_parts)
                                        item["content"] = content
                                    converted_history.append(item)
                            
                            logger.info(f"Converted history length: {len(converted_history)}")
                            
                            if not converted_history:
                                return "⚠️ 변환된 대화 내용이 없습니다. 대화를 먼저 시작해주세요.", gr.Dropdown()
                            
                            # Brain에서 상태 정보 가져오기
                            scenario_data = {
                                "conversation": converted_history
                            }
                            
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
                                
                                # 최근 대화 턴 (문맥 정보)
                                if hasattr(app_instance.brain, 'history') and app_instance.brain.history:
                                    recent_turns = []
                                    for turn in app_instance.brain.history.turns[-5:]:  # 최근 5턴
                                        if hasattr(turn, 'player_input') and hasattr(turn, 'character_response'):
                                            recent_turns.append({
                                                "player_input": turn.player_input,
                                                "character_response": turn.character_response,
                                                "emotion": getattr(turn, 'emotion', 'neutral'),
                                                "stats_delta": getattr(turn, 'stats_delta', {})
                                            })
                                    scenario_data["context"] = {
                                        "recent_turns": recent_turns
                                    }
                            
                            if app_instance.save_scenario(scenario_data, scenario_name.strip()):
                                # 드롭다운 목록 새로고침
                                updated_files = app_instance.get_scenario_files()
                                return f"✅ {scenario_name.strip()}.json 저장 완료!", gr.Dropdown(choices=updated_files, value=scenario_name.strip())
                            else:
                                return "❌ 시나리오 저장 실패", gr.Dropdown()
                        except Exception as e:
                            logger.error(f"Failed to save scenario: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            return f"❌ 시나리오 저장 실패: {str(e)}", gr.Dropdown()
                    
                    save_scenario_btn.click(
                        save_scenario_handler,
                        inputs=[scenario_save_name, chatbot],
                        outputs=[scenario_save_status, scenario_dropdown]
                    )
                    
                    # 시나리오 불러오기 버튼 (대화 탭 컴포넌트가 정의된 후에 연결)
                    continue_chat_btn.click(
                        continue_chat,
                        inputs=[scenario_dropdown],
                        outputs=[
                            setup_status, tabs,
                            chatbot, gr.Textbox(visible=False), stats_display, image_display,
                            gr.Textbox(visible=False), thought_display, action_display, stats_chart
                        ]
                    )
                    
                    def update_chart_if_needed(new_chart):
                        """차트가 있으면 업데이트, 없으면 건너뛰기"""
                        if new_chart is not None:
                            return new_chart
                        return gr.skip()
                    
                    def update_image_if_needed(trigger_image):
                        """트리거에 이미지가 있을 때만 반환, 없으면 업데이트 안 함"""
                        if trigger_image is not None:
                            # 이미지가 있으면 재시도 버튼도 표시
                            return trigger_image, gr.Button(visible=True)
                        # 이미지가 없어도 이전 이미지가 있으면 재시도 버튼 표시
                        if app_instance.current_image is not None:
                            return gr.skip(), gr.Button(visible=True)
                        return gr.skip(), gr.Button(visible=False)  # Gradio 6.x: 업데이트 건너뛰기
                    
                    def retry_image_handler():
                        """이미지 재생성 핸들러"""
                        if not app_instance.last_image_generation_info:
                            return gr.skip(), gr.Markdown(value="⚠️ 재생성할 이미지 정보가 없습니다.", visible=True), gr.Button(visible=True)
                        
                        try:
                            image, status_msg = app_instance.retry_image_generation()
                            if image:
                                return image, gr.Markdown(value=status_msg, visible=True), gr.Button(visible=True)
                            else:
                                return gr.skip(), gr.Markdown(value=status_msg, visible=True), gr.Button(visible=True)
                        except Exception as e:
                            logger.error(f"Failed to retry image generation: {e}")
                            return gr.skip(), gr.Markdown(value=f"❌ 오류: {str(e)}", visible=True), gr.Button(visible=True)
                    
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
                    
                
                # ========== 탭 3: 환경설정 ==========
                with gr.Tab("⚙️ 환경설정", id="settings_tab"):
                    gr.Markdown("## LLM 설정")
                    
                    # LLM 설정 로드
                    llm_settings = env_config.get("llm_settings", {})
                    provider = llm_settings.get("provider", "ollama")
                    ollama_model = llm_settings.get("ollama_model", "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest")
                    openrouter_model = llm_settings.get("openrouter_model", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
                    # API 키는 파일에서 불러오기
                    openrouter_api_key = app_instance._load_openrouter_api_key()
                    
                    llm_provider = gr.Radio(
                        label="LLM Provider",
                        choices=["ollama", "openrouter"],
                        value=provider,
                        info="사용할 LLM 서비스 선택"
                    )
                    
                    with gr.Group(visible=(provider == "ollama")) as ollama_group:
                        ollama_model_input = gr.Textbox(
                            label="Ollama 모델 이름",
                            value=ollama_model,
                            placeholder="예: kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
                            info="'ollama list' 명령으로 확인한 정확한 모델 이름을 입력하세요"
                        )
                    
                    with gr.Group(visible=(provider == "openrouter")) as openrouter_group:
                        openrouter_api_key_input = gr.Textbox(
                            label="OpenRouter API 키",
                            value=openrouter_api_key,
                            placeholder="sk-or-v1-...",
                            type="password",
                            info="OpenRouter API 키를 입력하세요 (https://openrouter.ai/keys)"
                        )
                        openrouter_model_input = gr.Textbox(
                            label="OpenRouter 모델",
                            value=openrouter_model,
                            placeholder="예: cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                            info="OpenRouter에서 사용할 모델 이름"
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
                    save_settings_btn = gr.Button("💾 설정 저장", variant="primary")
                    
                    def save_llm_settings(provider_val, ollama_model_val, openrouter_key_val, openrouter_model_val):
                        """LLM 설정 저장"""
                        try:
                            env_config = app_instance.load_env_config()
                            
                            # OpenRouter API 키는 별도 파일에 저장
                            if provider_val == "openrouter" and openrouter_key_val:
                                if not app_instance._save_openrouter_api_key(openrouter_key_val):
                                    return "❌ OpenRouter API 키 저장 실패"
                            
                            # LLM 설정 업데이트 (API 키는 제외)
                            env_config["llm_settings"] = {
                                "provider": provider_val,
                                "ollama_model": ollama_model_val or "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
                                "openrouter_model": openrouter_model_val or "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
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
                                                return "⚠️ OpenRouter 연결 실패, Ollama로 폴백 시도했으나 Ollama도 연결 실패했습니다."
                                            # 폴백 설정 저장
                                            app_instance.save_env_config(env_config)
                                            return "⚠️ OpenRouter 연결 실패, Ollama로 폴백하여 설정 저장 완료."
                                        
                                        app_instance.model_loaded = (result is not None)
                                        if app_instance.model_loaded:
                                            return f"✅ 설정 저장 완료! ({llm_settings['provider'].upper()} 연결 성공)"
                                        else:
                                            return f"⚠️ 설정 저장 완료, 하지만 {llm_settings['provider'].upper()} 연결 실패"
                                    else:
                                        return "✅ 설정 저장 완료! (다음 시작 시 적용됩니다)"
                                except Exception as e:
                                    logger.error(f"Failed to reinitialize Brain: {e}")
                                    return f"✅ 설정 저장 완료, 하지만 모델 재연결 실패: {str(e)}"
                            else:
                                return "❌ 설정 저장 실패"
                        except Exception as e:
                            logger.error(f"Failed to save LLM settings: {e}")
                            return f"❌ 설정 저장 실패: {str(e)}"
                    
                    save_settings_btn.click(
                        save_llm_settings,
                        inputs=[llm_provider, ollama_model_input, openrouter_api_key_input, openrouter_model_input],
                        outputs=[settings_status]
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown("## ComfyUI 설정")
                    
                    # ComfyUI 설정 로드
                    comfyui_settings = env_config.get("comfyui_settings", {})
                    comfyui_port = comfyui_settings.get("server_port", 8000)
                    workflow_path = comfyui_settings.get("workflow_path", config.COMFYUI_CONFIG["workflow_path"])
                    comfyui_model = comfyui_settings.get("model_name", "Zeniji_mix_ZiT_v1.safetensors")
                    comfyui_vae = comfyui_settings.get("vae_name", "zImage_vae.safetensors")
                    comfyui_clip = comfyui_settings.get("clip_name", "zImage_textEncoder.safetensors")
                    comfyui_steps = comfyui_settings.get("steps", 9)
                    comfyui_cfg = comfyui_settings.get("cfg", 1)
                    comfyui_sampler = comfyui_settings.get("sampler_name", "euler")
                    comfyui_scheduler = comfyui_settings.get("scheduler", "simple")
                    
                    # workflows 폴더의 .json 파일 목록 가져오기
                    workflows_dir = config.PROJECT_ROOT / "workflows"
                    workflow_files = []
                    if workflows_dir.exists():
                        workflow_files = sorted([f.name for f in workflows_dir.glob("*.json")])
                    
                    if not workflow_files:
                        workflow_files = ["comfyui.json"]  # 기본값
                    
                    # 현재 선택된 워크플로우 파일명 추출
                    current_workflow = Path(workflow_path).name if workflow_path else workflow_files[0]
                    if current_workflow not in workflow_files:
                        current_workflow = workflow_files[0]
                    
                    with gr.Row():
                        with gr.Column():
                            comfyui_port_input = gr.Number(
                                label="ComfyUI 서버 포트",
                                value=comfyui_port,
                                minimum=1,
                                maximum=65535,
                                step=1,
                                info="ComfyUI 서버가 실행 중인 포트 번호 (기본값: 8000)"
                            )
                            with gr.Row():
                                comfyui_workflow_input = gr.Dropdown(
                                    label="워크플로우 파일",
                                    value=current_workflow,
                                    choices=workflow_files,
                                    info="workflows 폴더에서 사용할 워크플로우 파일 선택",
                                    scale=4
                                )
                                reload_workflow_btn = gr.Button("🔄 새로고침", variant="secondary", size="sm", scale=1)
                            comfyui_model_input = gr.Textbox(
                                label="ComfyUI 모델 이름",
                                value=comfyui_model,
                                placeholder="예: Zeniji_mix_ZiT_v1.safetensors",
                                info="ComfyUI에서 사용할 모델 파일 이름 (확장자 포함)"
                            )
                            comfyui_vae_input = gr.Textbox(
                                label="VAE 이름",
                                value=comfyui_vae,
                                placeholder="예: zImage_vae.safetensors",
                                info="ComfyUI에서 사용할 VAE 파일 이름 (확장자 포함)"
                            )
                            comfyui_clip_input = gr.Textbox(
                                label="CLIP 이름",
                                value=comfyui_clip,
                                placeholder="예: zImage_textEncoder.safetensors",
                                info="ComfyUI에서 사용할 CLIP 파일 이름 (확장자 포함)"
                            )
                        with gr.Column():
                            comfyui_steps_input = gr.Number(
                                label="Steps (생성 단계 수)",
                                value=comfyui_steps,
                                minimum=1,
                                maximum=100,
                                step=1,
                                info="이미지 생성 단계 수 (기본값: 9)"
                            )
                            comfyui_cfg_input = gr.Number(
                                label="CFG Scale (프롬프트 강도)",
                                value=comfyui_cfg,
                                minimum=0.1,
                                maximum=20.0,
                                step=0.1,
                                info="프롬프트 준수도 (기본값: 1)"
                            )
                            comfyui_sampler_input = gr.Textbox(
                                label="Sampler (샘플러)",
                                value=comfyui_sampler,
                                placeholder="예: euler",
                                info="이미지 생성 샘플러 이름 (기본값: euler)"
                            )
                            comfyui_scheduler_input = gr.Textbox(
                                label="Scheduler (스케줄러)",
                                value=comfyui_scheduler,
                                placeholder="예: simple",
                                info="스케줄러 타입 (기본값: simple)"
                            )
                    
                    comfyui_status = gr.Markdown("")
                    save_comfyui_btn = gr.Button("💾 ComfyUI 설정 저장", variant="primary")
                    
                    def save_comfyui_settings(port_val, workflow_val, model_val, vae_val, clip_val, steps_val, cfg_val, sampler_val, scheduler_val):
                        """ComfyUI 설정 저장"""
                        try:
                            env_config = app_instance.load_env_config()
                            
                            # ComfyUI 설정 업데이트
                            if "comfyui_settings" not in env_config:
                                env_config["comfyui_settings"] = {}
                            
                            if workflow_val:
                                # 상대 경로로 저장 (빌드된 실행 파일에서도 올바르게 작동하도록)
                                workflow_path = f"workflows/{workflow_val}"
                            else:
                                # 기본값도 상대 경로로 저장
                                workflow_path = "workflows/comfyui.json"
                            
                            env_config["comfyui_settings"]["server_port"] = int(port_val) if port_val else 8000
                            env_config["comfyui_settings"]["workflow_path"] = workflow_path
                            env_config["comfyui_settings"]["model_name"] = model_val or "Zeniji_mix_ZiT_v1.safetensors"
                            env_config["comfyui_settings"]["vae_name"] = vae_val or "zImage_vae.safetensors"
                            env_config["comfyui_settings"]["clip_name"] = clip_val or "zImage_textEncoder.safetensors"
                            env_config["comfyui_settings"]["steps"] = int(steps_val) if steps_val else 9
                            env_config["comfyui_settings"]["cfg"] = float(cfg_val) if cfg_val else 1.0
                            env_config["comfyui_settings"]["sampler_name"] = sampler_val or "euler"
                            env_config["comfyui_settings"]["scheduler"] = scheduler_val or "simple"
                            
                            # 환경설정 저장
                            if app_instance.save_env_config(env_config):
                                # ComfyClient 재초기화 (새 설정 적용)
                                try:
                                    if app_instance.comfy_client is not None:
                                        server_address = f"127.0.0.1:{env_config['comfyui_settings']['server_port']}"
                                        workflow_path = env_config['comfyui_settings'].get('workflow_path', str(config.COMFYUI_WORKFLOW_PATH))
                                        model_name = env_config['comfyui_settings']['model_name']
                                        vae_name = env_config['comfyui_settings'].get('vae_name', 'zImage_vae.safetensors')
                                        clip_name = env_config['comfyui_settings'].get('clip_name', 'zImage_textEncoder.safetensors')
                                        steps = env_config['comfyui_settings'].get('steps', 9)
                                        cfg = env_config['comfyui_settings'].get('cfg', 1.0)
                                        sampler_name = env_config['comfyui_settings'].get('sampler_name', 'euler')
                                        scheduler = env_config['comfyui_settings'].get('scheduler', 'simple')
                                        app_instance.comfy_client = ComfyClient(
                                            server_address=server_address,
                                            workflow_path=workflow_path,
                                            model_name=model_name,
                                            steps=steps,
                                            cfg=cfg,
                                            sampler_name=sampler_name,
                                            scheduler=scheduler,
                                            vae_name=vae_name,
                                            clip_name=clip_name
                                        )
                                        logger.info(f"ComfyClient 재초기화 완료: {server_address}, workflow: {workflow_path}, model: {model_name}, vae: {vae_name}, clip: {clip_name}, steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}")
                                    return "✅ ComfyUI 설정 저장 완료! (다음 이미지 생성 시 적용됩니다)"
                                except Exception as e:
                                    logger.error(f"Failed to reinitialize ComfyClient: {e}")
                                    return f"✅ ComfyUI 설정 저장 완료, 하지만 클라이언트 재연결 실패: {str(e)}"
                            else:
                                return "❌ ComfyUI 설정 저장 실패"
                        except Exception as e:
                            logger.error(f"Failed to save ComfyUI settings: {e}")
                            return f"❌ ComfyUI 설정 저장 실패: {str(e)}"
                    
                    save_comfyui_btn.click(
                        save_comfyui_settings,
                        inputs=[comfyui_port_input, comfyui_workflow_input, comfyui_model_input, comfyui_vae_input, comfyui_clip_input, comfyui_steps_input, comfyui_cfg_input, comfyui_sampler_input, comfyui_scheduler_input],
                        outputs=[comfyui_status]
                    )
                    
                    reload_workflow_btn.click(
                        reload_workflow_files,
                        inputs=[comfyui_workflow_input],
                        outputs=[comfyui_workflow_input]
                    )
            
            # 첫 탭의 버튼 클릭 시 대화 탭 컴포넌트 업데이트 (탭 밖에서 정의)
            start_btn.click(
                app_instance.validate_and_start,
                inputs=[
                    player_name, player_gender,
                    char_name, char_age, char_gender,
                    appearance, personality,
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
                    💬 <a href="https://arca.live/b/zeniji" target="_blank" style="color: #666; text-decoration: none;">커뮤니티</a><br>
                    ☕ <a href="https://buymeacoffee.com/zeniji" target="_blank" style="color: #666; text-decoration: none;">Buy Me a Coffee</a><br>
                    <span style="font-size: 0.85em; opacity: 0.7;">Version {config.VERSION}</span>
                </div>
                """
            )
        
        return demo

