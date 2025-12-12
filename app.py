"""
Zeniji Emotion Simul - Main Application
Gradio UI 및 게임 루프
"""

import gradio as gr
import logging
import argparse
import json
import os
from pathlib import Path
from typing import Tuple, Optional, Dict
from brain import Brain
from state_manager import CharacterState
from comfy_client import ComfyClient
from PIL import Image
import io
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("App")

# 설정 파일 경로
CONFIG_FILE = Path("character_config.json")

# 프리셋 정의
PRESETS = {
    "소꿉친구": {
        "P": 60.0, "A": 50.0, "D": 45.0, "I": 70.0, "T": 70.0, "Dep": 30.0,
        "appearance": "korean beauty, friendly face, warm expression, casual clothes, childhood friend",
        "personality": "밝고 활발하며, 오랜 친구라서 편하게 대화함. 때로는 장난스럽지만 진심이 담겨있음."
    },
    "혐관 라이벌": {
        "P": 20.0, "A": 70.0, "D": 80.0, "I": 10.0, "T": 10.0, "Dep": 0.0,
        "appearance": "korean beauty, sharp eyes, confident expression, competitive look, strong presence",
        "personality": "항상 경쟁하고 싶어하며, 당신을 라이벌로 인식. 도전적이고 자존심이 강함."
    },
    "피폐/집착": {
        "P": 30.0, "A": 80.0, "D": 20.0, "I": 90.0, "T": 20.0, "Dep": 90.0,
        "appearance": "korean beauty, tired eyes, intense gaze, unstable expression, obsessive look",
        "personality": "당신에게 강하게 집착하며, 떨어지면 불안해함. 감정 기복이 심하고 의존적."
    }
}


class GameApp:
    """게임 애플리케이션"""
    
    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode
        self.brain = None
        self.model_loaded = False
        self.current_image: Optional[bytes] = None
        self.comfy_client = None
    
    def load_config(self) -> Dict:
        """설정 파일 로드"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """기본 설정 반환"""
        return {
            "player": {
                "name": "",
                "gender": "남성"
            },
            "character": {
                "name": "예나",
                "age": 21,
                "gender": "여성",
                "appearance": "korean beauty, short hair, brown eyes, cute face, casual outfit",
                "personality": "밝고 활발하지만 좋아하는 사람 앞에서는 수줍음이 많음"
            },
            "initial_stats": {
                "P": 50.0,
                "A": 40.0,
                "D": 40.0,
                "I": 20.0,
                "T": 50.0,
                "Dep": 0.0
            },
            "initial_context": "",
            "initial_background": "college library table, evening light"
        }
    
    def save_config(self, config_data: Dict) -> bool:
        """설정 파일 저장"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Config saved to {CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def apply_preset(self, preset_name: str) -> Tuple[float, float, float, float, float, float, str, str]:
        """프리셋 적용"""
        preset = PRESETS.get(preset_name, {})
        return (
            preset.get("P", 50.0),
            preset.get("A", 40.0),
            preset.get("D", 40.0),
            preset.get("I", 20.0),
            preset.get("T", 50.0),
            preset.get("Dep", 0.0),
            preset.get("appearance", ""),
            preset.get("personality", "")
        )
    
    def validate_and_start(
        self,
        player_name, player_gender,
        char_name, char_age, char_gender,
        appearance, personality,
        p_val, a_val, d_val, i_val, t_val, dep_val,
        initial_context, initial_background
    ) -> Tuple[str, str, list, str, str, str, str, str, str]:
        """설정 검증 및 시작 (첫 대화 자동 생성)"""
        # 최대값 검증 (70 제한)
        max_val = 70.0
        stats = {"P": p_val, "A": a_val, "D": d_val, "I": i_val, "T": t_val, "Dep": dep_val}
        exceeded = [k for k, v in stats.items() if v > max_val]
        
        # 에러 시 기본값 반환
        empty_result = (
            "⚠️ 경고: 다음 수치가 70을 초과합니다: " + ", ".join(exceeded) if exceeded else "❌ 오류 발생",
            gr.Tabs(selected=None),
            [], "", "", None, "", "", ""
        )
        
        if exceeded:
            return empty_result
        
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
                "P": float(p_val),
                "A": float(a_val),
                "D": float(d_val),
                "I": float(i_val),
                "T": float(t_val),
                "Dep": float(dep_val)
            },
            "initial_context": initial_context or "",
            "initial_background": initial_background or "college library table, evening light"
        }
        
        # 저장
        if not self.save_config(config_data):
            return ("❌ 설정 저장 실패", gr.Tabs(selected=None), [], "", "", None, "", "", "")
        
        # 모델 로드
        status_msg, success = self.load_model()
        if not success:
            return (f"❌ 모델 로드 실패: {status_msg}", gr.Tabs(selected=None), [], "", "", None, "", "", "")
        
        # Brain 초기화 및 설정 적용
        try:
            if self.brain is None:
                self.brain = Brain(dev_mode=self.dev_mode)
            
            # 초기 설정 정보 전달
            self.brain.set_initial_config(config_data)
            
            # 초기 상태 적용
            self.brain.state.P = config_data["initial_stats"]["P"]
            self.brain.state.A = config_data["initial_stats"]["A"]
            self.brain.state.D = config_data["initial_stats"]["D"]
            self.brain.state.I = config_data["initial_stats"]["I"]
            self.brain.state.T = config_data["initial_stats"]["T"]
            self.brain.state.Dep = config_data["initial_stats"]["Dep"]
            self.brain.state.current_background = config_data["initial_background"]
            self.brain.state.clamp()
            
            logger.info("Initial configuration applied to Brain")
        except Exception as e:
            logger.error(f"Failed to apply config: {e}")
            return (f"❌ 설정 적용 실패: {str(e)}", gr.Tabs(selected=None), [], "", "", None, "", "", "")
        
        # 첫 대화 자동 생성
        try:
            logger.info("Generating first dialogue automatically...")
            history, output_text, stats_text, image, choices_text, thought_text, action_text = self.process_turn("대화 시작", [])
            
            # 첫 화면 이미지 생성 (appearance + background)
            initial_image = None
            if config.IMAGE_MODE_ENABLED:
                try:
                    # ComfyClient 초기화 (아직 안 되어 있으면)
                    if self.comfy_client is None:
                        self.comfy_client = ComfyClient()
                        logger.info("ComfyClient initialized")
                    
                    # appearance와 background를 조합해서 이미지 생성
                    appearance = config_data["character"].get("appearance", "")
                    background = config_data.get("initial_background", "college library table, evening light")
                    
                    # visual_prompt 생성: background를 포함한 시각적 묘사
                    visual_prompt = f"background: {background}, expression: neutral, looking at viewer"
                    
                    logger.info(f"Generating initial image with appearance: {appearance[:50]}... and background: {background}")
                    image_bytes = self.comfy_client.generate_image(
                        visual_prompt=visual_prompt,
                        appearance=appearance,
                        seed=-1
                    )
                    
                    if image_bytes:
                        # PIL Image로 변환
                        initial_image = Image.open(io.BytesIO(image_bytes))
                        logger.info("Initial image generated successfully")
                    else:
                        logger.warning("Failed to generate initial image")
                except Exception as e:
                    logger.error(f"Failed to generate initial image: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            status_msg = "✅ 설정 저장 및 첫 대화 생성 완료!"
            # 탭 전환: chat_tab의 id를 사용
            return (status_msg, gr.Tabs(selected="chat_tab"), history, output_text, stats_text, initial_image, choices_text, thought_text, action_text)
        except Exception as e:
            logger.error(f"Failed to generate first dialogue: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return (f"✅ 설정 저장 완료, 하지만 첫 대화 생성 실패: {str(e)}", gr.Tabs(selected="chat_tab"), [], "", "", None, "", "", "")
    
    def load_model(self) -> Tuple[str, bool]:
        """모델 로드"""
        if self.model_loaded and self.brain is not None:
            return "모델이 이미 로드되어 있습니다.", True
        
        try:
            if self.brain is None:
                self.brain = Brain(dev_mode=self.dev_mode)
            logger.info("Brain initialized, loading model...")
            
            result = self.brain.memory_manager.load_model()
            if result is None:
                raise RuntimeError("모델 로드에 실패했습니다.")
            
            self.model_loaded = True
            logger.info("Model loaded successfully")
            return "✅ 모델 로드 완료!", True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ 모델 로드 실패: {str(e)}", False
    
    def process_turn(self, user_input: str, history: list) -> Tuple[list, str, str, str, str, str, str]:
        """턴 처리"""
        if not user_input.strip():
            return history, "", "", None, "", "", ""
        
        if self.brain is None:
            return history, "**오류**: Brain이 초기화되지 않았습니다.", "", None, "", "", ""
        
        try:
            response = self.brain.generate_response(user_input)
        except Exception as e:
            logger.error(f"Turn processing failed: {e}")
            return history, f"**오류 발생**: {str(e)}", "", None, "", "", ""
        
        # 응답 파싱
        speech = response.get("speech", "")
        thought = response.get("thought", "")
        action_speech = response.get("action_speech", "")
        emotion = response.get("emotion", "neutral")
        stats = response.get("stats", {})
        mood = response.get("mood", "Neutral")
        relationship = response.get("relationship_status", "Stranger")
        gacha_tier = response.get("gacha_tier", "normal")
        multiplier = response.get("multiplier", 1.0)
        final_delta = response.get("final_delta", {})
        new_badge = response.get("new_badge")
        
        # 히스토리 업데이트
        history = history or []
        history = list(history)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": speech})
        
        # 출력 텍스트
        output_lines = [
            f"**{speech}**",
            "",
            f"*속마음: {thought}*",
            "",
            f"감정: {emotion} | 기분: {mood} | 관계: {relationship}"
        ]
        
        if gacha_tier != "normal":
            tier_emoji = {"jackpot": "🎰", "surprise": "✨", "critical": "💥"}.get(gacha_tier, "🎲")
            output_lines.append(f"{tier_emoji} **{gacha_tier.upper()}** (배율: x{multiplier:.1f})")
        
        if new_badge:
            output_lines.append(f"🏆 **뱃지 획득: {new_badge}**")
        
        delta_parts = []
        for key, value in final_delta.items():
            if value != 0:
                sign = "+" if value > 0 else ""
                color = "green" if value > 0 else "red"
                delta_parts.append(f"<span style='color: {color}'>{key}: {sign}{value:.1f}</span>")
        
        if delta_parts:
            output_lines.append(f"변화: {' | '.join(delta_parts)}")
        
        output_text = "\n".join(output_lines)
        
        def format_delta(key: str) -> str:
            delta_value = final_delta.get(key, 0)
            if delta_value > 0:
                return f'<span style="color: blue;">(+{delta_value:.0f})</span>'
            elif delta_value < 0:
                return f'<span style="color: red;">({delta_value:.0f})</span>'
            else:
                return '<span style="color: black;">(0)</span>'
        
        stats_text = f"""
**6축 수치:**
- P (쾌락): {stats.get('P', 0):.0f} {format_delta('P')}
- A (각성): {stats.get('A', 0):.0f} {format_delta('A')}
- D (지배): {stats.get('D', 0):.0f} {format_delta('D')}
- I (친밀): {stats.get('I', 0):.0f} {format_delta('I')}
- T (신뢰): {stats.get('T', 0):.0f} {format_delta('T')}
- Dep (의존): {stats.get('Dep', 0):.0f} {format_delta('Dep')}

**상태:**
- 관계: {relationship}
- 기분: {mood}
- 뱃지: {', '.join(response.get('badges', [])) or 'None'}
"""
        
        # 이미지 생성 (visual_change_detected가 true이거나 5턴 이상 지났을 때)
        image = None
        visual_change_detected = response.get("visual_change_detected", False)
        
        if visual_change_detected and config.IMAGE_MODE_ENABLED:
            try:
                # ComfyClient 초기화 (아직 안 되어 있으면)
                if self.comfy_client is None:
                    self.comfy_client = ComfyClient()
                    logger.info("ComfyClient initialized")
                
                # 설정에서 appearance 가져오기
                saved_config = self.load_config()
                appearance = saved_config["character"].get("appearance", "")
                
                # response에서 visual_prompt와 background 가져오기
                visual_prompt = response.get("visual_prompt", "")
                background = response.get("background", "")
                
                # visual_prompt가 없으면 기본값 사용
                if not visual_prompt:
                    visual_prompt = f"background: {background}, expression: {emotion}, looking at viewer"
                elif background and "background:" not in visual_prompt.lower():
                    # visual_prompt에 background가 없으면 추가
                    visual_prompt = f"{visual_prompt}, background: {background}"
                
                logger.info(f"Generating image - visual_change_detected: {visual_change_detected}")
                logger.info(f"  appearance: {appearance[:50]}...")
                logger.info(f"  visual_prompt: {visual_prompt[:100]}...")
                
                image_bytes = self.comfy_client.generate_image(
                    visual_prompt=visual_prompt,
                    appearance=appearance,
                    seed=-1
                )
                
                if image_bytes:
                    # PIL Image로 변환
                    image = Image.open(io.BytesIO(image_bytes))
                    logger.info("Image generated successfully")
                else:
                    logger.warning("Failed to generate image (returned None)")
            except Exception as e:
                logger.error(f"Failed to generate image: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 이미지 생성 실패해도 대화는 계속 진행
        
        choices_text = "다음 대사를 입력하세요."
        thought_text = f"💭 **속마음**: {thought}" if thought else ""
        action_text = f"🎭 **행동**: {action_speech}" if action_speech else ""
        
        return history, output_text, stats_text, image, choices_text, thought_text, action_text
    
    def create_ui(self):
        """Gradio UI 생성"""
        # 설정 로드
        saved_config = self.load_config()
        
        with gr.Blocks(title="Zeniji Emotion Simul") as demo:
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
                            char_age = gr.Slider(
                                label="나이",
                                minimum=18,
                                maximum=100,
                                value=saved_config["character"].get("age", 21),
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
                    
                    with gr.Row():
                        with gr.Column():
                            p_val = gr.Slider(
                                label="P (Pleasure) - 쾌락",
                                minimum=0,
                                maximum=100,
                                value=saved_config["initial_stats"].get("P", 50.0),
                                step=1.0,
                                info="관계의 긍정/부정"
                            )
                            a_val = gr.Slider(
                                label="A (Arousal) - 각성",
                                minimum=0,
                                maximum=100,
                                value=saved_config["initial_stats"].get("A", 40.0),
                                step=1.0,
                                info="긴장감/에너지"
                            )
                            d_val = gr.Slider(
                                label="D (Dominance) - 지배",
                                minimum=0,
                                maximum=100,
                                value=saved_config["initial_stats"].get("D", 40.0),
                                step=1.0,
                                info="관계의 주도권"
                            )
                        with gr.Column():
                            i_val = gr.Slider(
                                label="I (Intimacy) - 친밀",
                                minimum=0,
                                maximum=100,
                                value=saved_config["initial_stats"].get("I", 20.0),
                                step=1.0,
                                info="정서적 친밀감"
                            )
                            t_val = gr.Slider(
                                label="T (Trust) - 신뢰",
                                minimum=0,
                                maximum=100,
                                value=saved_config["initial_stats"].get("T", 50.0),
                                step=1.0,
                                info="신뢰도"
                            )
                            dep_val = gr.Slider(
                                label="Dep (Dependency) - 의존",
                                minimum=0,
                                maximum=100,
                                value=saved_config["initial_stats"].get("Dep", 0.0),
                                step=1.0,
                                info="의존/집착도"
                            )
                    
                    gr.Markdown("### 🎭 프리셋")
                    with gr.Row():
                        for preset_name in PRESETS.keys():
                            preset_btn = gr.Button(preset_name, variant="secondary")
                            preset_btn.click(
                                lambda name=preset_name: self.apply_preset(name),
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
                    start_btn = gr.Button("💾 저장 및 바로 시작", variant="primary", size="lg")
                
                # ========== 탭 2: 대화 ==========
                with gr.Tab("💬 대화", id="chat_tab") as chat_tab:
                    with gr.Row():
                        with gr.Column(scale=2):
                            chatbot = gr.Chatbot(label="대화", height=400)
                            
                            # 속마음: Accordion으로 접기/펼치기 가능하게
                            with gr.Accordion("💭 속마음 보기", open=False, visible=True) as thought_accordion:
                                thought_display = gr.Markdown(label="", visible=True)
                            
                            action_display = gr.Markdown(label="🎭 행동", visible=True)
                            user_input = gr.Textbox(label="입력", placeholder="말을 입력하세요...", interactive=False)
                            submit_btn = gr.Button("전송", variant="primary", interactive=False)
                        
                        with gr.Column(scale=1):
                            stats_display = gr.Markdown(label="상태")
                            image_display = gr.Image(label="캐릭터", height=400)
                    
                    def on_submit(message, history):
                        if not self.model_loaded:
                            return history, "**오류**: 먼저 초기 설정에서 '저장 및 바로 시작'을 눌러주세요.", "", None, "", "", ""
                        new_history, output, stats, image, choices, thought, action = self.process_turn(message, history)
                        return new_history, "", stats, image, choices, thought, action
                    
                    submit_btn.click(
                        on_submit,
                        inputs=[user_input, chatbot],
                        outputs=[chatbot, user_input, stats_display, image_display, gr.Textbox(visible=False), thought_display, action_display]
                    )
                    user_input.submit(
                        on_submit,
                        inputs=[user_input, chatbot],
                        outputs=[chatbot, user_input, stats_display, image_display, gr.Textbox(visible=False), thought_display, action_display]
                    )
                    
                    # 모델 로드 완료 시 UI 활성화
                    def enable_chat_ui():
                        if self.model_loaded:
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
                    gr.Markdown("## 환경설정")
                    gr.Markdown("(준비 중...)")
            
            # 첫 탭의 버튼 클릭 시 대화 탭 컴포넌트 업데이트 (탭 밖에서 정의)
            start_btn.click(
                self.validate_and_start,
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
                    gr.Textbox(visible=False), thought_display, action_display
                ]
            )
            
            # 설정 로드 시 UI 업데이트
            demo.load(
                enable_chat_ui,
                inputs=[],
                outputs=[submit_btn, user_input]
            )
        
        return demo


def parse_args():
    parser = argparse.ArgumentParser(description="Zeniji Emotion Simul")
    parser.add_argument("--dev-mode", action="store_true", help="개발자 모드 활성화")
    parser.add_argument("--log-level", default="INFO", help="로깅 레벨 설정")
    return parser.parse_args()


def main():
    """메인 실행"""
    args = parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    app = GameApp(dev_mode=args.dev_mode)
    demo = app.create_ui()
    print("\n" + "=" * 60)
    print("🚀 Gradio 서버 시작 중...")
    print("=" * 60)
    print(f"📍 로컬 접속: http://localhost:7860")
    print(f"📍 네트워크 접속: http://127.0.0.1:7860")
    if args.dev_mode:
        print("🛠  Dev Mode ON")
    print("=" * 60 + "\n")
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)


if __name__ == "__main__":
    main()
