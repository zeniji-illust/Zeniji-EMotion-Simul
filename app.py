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
from memory_manager import MemoryManager
from PIL import Image
import io
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("App")

# 설정 파일 경로
CONFIG_FILE = Path("character_config.json")
API_KEY_DIR = Path("apikey")
OPENROUTER_API_KEY_FILE = API_KEY_DIR / "openrouter_api_key.txt"

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
        self.current_image: Optional[Image.Image] = None  # PIL Image 저장
        self.comfy_client = None
    
    def load_config(self) -> Dict:
        """설정 파일 로드 - None 값 정리"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # None 값이 있으면 기본값으로 대체
                    return self._sanitize_config(config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        return self._default_config()
    
    def _sanitize_config(self, config: Dict) -> Dict:
        """설정에서 None 값을 기본값으로 대체"""
        default = self._default_config()
        
        # initial_stats의 None 값 처리
        initial_stats = config.get("initial_stats", {}) or {}
        sanitized_stats = {}
        for key in ["P", "A", "D", "I", "T", "Dep"]:
            val = initial_stats.get(key)
            if val is None:
                val = default["initial_stats"][key]
            sanitized_stats[key] = float(val) if val is not None else default["initial_stats"][key]
        
        # character의 age 처리
        character = config.get("character", {}) or {}
        char_age = character.get("age")
        if char_age is None:
            char_age = default["character"]["age"]
        
        # None 값이 있으면 기본값으로 병합
        result = default.copy()
        result.update(config)
        result["initial_stats"] = sanitized_stats
        if "character" in result:
            result["character"]["age"] = int(char_age) if char_age is not None else default["character"]["age"]
        
        return result
    
    def _load_openrouter_api_key(self) -> str:
        """OpenRouter API 키를 파일에서 불러오기"""
        try:
            if OPENROUTER_API_KEY_FILE.exists():
                with open(OPENROUTER_API_KEY_FILE, 'r', encoding='utf-8') as f:
                    api_key = f.read().strip()
                    return api_key if api_key else ""
            return ""
        except Exception as e:
            logger.warning(f"Failed to load OpenRouter API key: {e}")
            return ""
    
    def _save_openrouter_api_key(self, api_key: str) -> bool:
        """OpenRouter API 키를 파일에 저장"""
        try:
            # apikey 디렉토리가 없으면 생성
            API_KEY_DIR.mkdir(exist_ok=True)
            
            # API 키 저장
            with open(OPENROUTER_API_KEY_FILE, 'w', encoding='utf-8') as f:
                f.write(api_key.strip())
            
            logger.info(f"OpenRouter API key saved to {OPENROUTER_API_KEY_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save OpenRouter API key: {e}")
            return False
    
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
            "initial_background": "college library table, evening light",
            "llm_settings": {
                "provider": "ollama",
                "ollama_model": "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
                "openrouter_model": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
            },
            "comfyui_settings": {
                "server_port": 8000,
                "workflow_path": "workflows/comfyui_zit.json",
                "model_name": "Zeniji_mix_ZiT_v1.safetensors",
                "steps": 9,
                "cfg": 1,
                "sampler_name": "euler",
                "scheduler": "simple"
            }
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
        """프리셋 적용 - 모든 수치가 확실히 숫자가 되도록 보장"""
        preset = PRESETS.get(preset_name, {})
        # get(key, default)를 써도 되지만, 혹시 None이 들어있는 경우를 대비해 or 처리
        return (
            float(preset.get("P") or 50.0),
            float(preset.get("A") or 40.0),
            float(preset.get("D") or 40.0),
            float(preset.get("I") or 20.0),
            float(preset.get("T") or 50.0),
            float(preset.get("Dep") or 0.0),
            str(preset.get("appearance") or ""),
            str(preset.get("personality") or "")
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
        
        # OpenRouter API 키 체크 및 우선 사용 설정
        openrouter_api_key = self._load_openrouter_api_key()
        if openrouter_api_key and openrouter_api_key.strip():
            # OpenRouter API 키가 있으면 OpenRouter를 우선 사용
            logger.info("OpenRouter API 키가 발견되었습니다. OpenRouter를 우선 사용합니다.")
            if "llm_settings" not in config_data:
                config_data["llm_settings"] = {}
            config_data["llm_settings"]["provider"] = "openrouter"
            # OpenRouter 모델이 설정되어 있지 않으면 기본값 사용
            if "openrouter_model" not in config_data["llm_settings"]:
                config_data["llm_settings"]["openrouter_model"] = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
        else:
            # OpenRouter API 키가 없으면 Ollama 사용
            logger.info("OpenRouter API 키가 없습니다. Ollama를 사용합니다.")
            if "llm_settings" not in config_data:
                config_data["llm_settings"] = {}
            config_data["llm_settings"]["provider"] = "ollama"
            # Ollama 모델이 설정되어 있지 않으면 기본값 사용
            if "ollama_model" not in config_data["llm_settings"]:
                config_data["llm_settings"]["ollama_model"] = "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest"
        
        # 저장 (LLM 설정 포함)
        if not self.save_config(config_data):
            return ("❌ 설정 저장 실패", gr.Tabs(selected=None), [], "", "", None, "", "", "")
        
        # 모델 로드
        status_msg, success = self.load_model()
        if not success:
            return (f"❌ 모델 로드 실패: {status_msg}", gr.Tabs(selected=None), [], "", "", None, "", "", "")
        
        # Brain 초기화 및 설정 적용
        try:
            # LLM 설정 읽기 (저장된 설정에서)
            llm_settings = config_data.get("llm_settings", {})
            provider = llm_settings.get("provider", "ollama")
            ollama_model = llm_settings.get("ollama_model", "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest")
            openrouter_model = llm_settings.get("openrouter_model", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
            # API 키는 파일에서 불러오기 (이미 위에서 로드했지만 다시 확인)
            if provider == "openrouter":
                openrouter_api_key = self._load_openrouter_api_key()
            else:
                openrouter_api_key = ""
            
            if self.brain is None:
                model_name = ollama_model if provider == "ollama" else openrouter_model
                api_key = openrouter_api_key if provider == "openrouter" else None
                self.brain = Brain(
                    dev_mode=self.dev_mode,
                    provider=provider,
                    model_name=model_name,
                    api_key=api_key
                )
            
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
                        # ComfyUI 설정 로드
                        comfyui_settings = config_data.get("comfyui_settings", {})
                        server_port = comfyui_settings.get("server_port", 8000)
                        workflow_path = comfyui_settings.get("workflow_path", "workflows/comfyui_zit.json")
                        model_name = comfyui_settings.get("model_name", "Zeniji_mix_ZiT_v1.safetensors")
                        steps = comfyui_settings.get("steps", 9)
                        cfg = comfyui_settings.get("cfg", 1.0)
                        sampler_name = comfyui_settings.get("sampler_name", "euler")
                        scheduler = comfyui_settings.get("scheduler", "simple")
                        server_address = f"127.0.0.1:{server_port}"
                        self.comfy_client = ComfyClient(
                            server_address=server_address,
                            workflow_path=workflow_path,
                            model_name=model_name,
                            steps=steps,
                            cfg=cfg,
                            sampler_name=sampler_name,
                            scheduler=scheduler
                        )
                        logger.info(f"ComfyClient initialized: {server_address}, workflow: {workflow_path}, model: {model_name}, steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}")
                    
                    # appearance와 background를 조합해서 이미지 생성
                    appearance = config_data["character"].get("appearance", "")
                    char_age = config_data["character"].get("age", 21)
                    background = config_data.get("initial_background", "college library table, evening light")
                    
                    # appearance에 나이 추가 (이미지 생성용)
                    if appearance and f"{char_age} years old" not in appearance.lower():
                        appearance = f"{char_age} years old, {appearance}".strip()
                    elif not appearance:
                        appearance = f"{char_age} years old"
                    
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
                        # 현재 이미지로 저장
                        self.current_image = initial_image
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
        """모델 로드 (설정에서 LLM provider 정보 읽어서 초기화)"""
        if self.model_loaded and self.brain is not None:
            return "모델이 이미 로드되어 있습니다.", True
        
        try:
            # 설정에서 LLM 설정 읽기
            config_data = self.load_config()
            llm_settings = config_data.get("llm_settings", {})
            provider = llm_settings.get("provider", "ollama")
            ollama_model = llm_settings.get("ollama_model", "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest")
            openrouter_model = llm_settings.get("openrouter_model", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
            # API 키는 파일에서 불러오기
            openrouter_api_key = self._load_openrouter_api_key()
            
            # Brain 초기화 (설정에 따라 MemoryManager도 초기화)
            if self.brain is None:
                model_name = ollama_model if provider == "ollama" else openrouter_model
                api_key = openrouter_api_key if provider == "openrouter" else None
                self.brain = Brain(
                    dev_mode=self.dev_mode,
                    provider=provider,
                    model_name=model_name,
                    api_key=api_key
                )
            else:
                # Brain이 이미 있으면 memory_manager만 재초기화
                model_name = ollama_model if provider == "ollama" else openrouter_model
                api_key = openrouter_api_key if provider == "openrouter" else None
                self.brain.memory_manager = MemoryManager(
                    dev_mode=self.dev_mode,
                    provider=provider,
                    model_name=model_name,
                    api_key=api_key
                )
            
            logger.info(f"Brain initialized with {provider.upper()}, loading model...")
            
            # 모델 로드 시도 (OpenRouter 실패 시 Ollama로 폴백)
            result = self.brain.memory_manager.load_model()
            if result is None and provider == "openrouter":
                logger.warning("OpenRouter 연결 실패, Ollama로 폴백 시도...")
                # Ollama로 폴백
                self.brain.memory_manager = MemoryManager(
                    dev_mode=self.dev_mode,
                    provider="ollama",
                    model_name=ollama_model
                )
                result = self.brain.memory_manager.load_model()
                if result is None:
                    return "⚠️ OpenRouter 연결 실패, Ollama로 폴백 시도했으나 Ollama도 연결 실패했습니다.", False
                self.model_loaded = True
                logger.info("Model loaded successfully (Ollama fallback)")
                return "⚠️ OpenRouter 연결 실패, Ollama로 폴백하여 모델 로드 완료!", True
            
            if result is None:
                raise RuntimeError("모델 로드에 실패했습니다.")
            
            self.model_loaded = True
            logger.info("Model loaded successfully")
            return f"✅ 모델 로드 완료! ({provider.upper()})", True
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
        gacha_tier = response.get("gacha_tier", "normal")  # 내부 시스템 용어
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
            # 사용자에게는 "반응 정도"로 표시
            reaction_level = {"jackpot": "극진한 반응", "surprise": "놀라운 반응", "critical": "강렬한 반응"}.get(gacha_tier, "특별한 반응")
            output_lines.append(f"{tier_emoji} **{reaction_level}** (배율: x{multiplier:.1f})")
        
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
        
        # 반응 정도 표시 (전구 아이콘)
        def format_reaction_indicators(tier: str) -> str:
            """반응 정도에 따라 전구/번개/폭발 아이콘 표시"""
            if tier == "jackpot":
                # 폭발 이모티콘 4개
                return "💥 💥 💥 💥"
            elif tier == "surprise":
                # 번개 3개, 꺼진 전구 1개
                return "⚡ ⚡ ⚡ ⚫"
            elif tier == "critical":
                # 노란 전구 2개, 꺼진 전구 2개
                return "💡 💡 ⚫ ⚫"
            else:  # normal
                # 노란 전구 1개, 꺼진 전구 3개
                return "💡 ⚫ ⚫ ⚫"
        
        reaction_indicators = format_reaction_indicators(gacha_tier)
        
        stats_text = f"""
**반응 정도:** {reaction_indicators} (x{multiplier:.1f})

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
        image_generation_reasons = response.get("image_generation_reasons", [])
        new_image_generated = False  # 새 이미지가 생성되었는지 추적
        
        if visual_change_detected and config.IMAGE_MODE_ENABLED:
            # LLM 모델 offload를 위한 2초 대기
            import time
            logger.info("Waiting 2 second for LLM model offload...")
            time.sleep(2.0)
            
            # 이미지 생성 이유 로그 출력
            if image_generation_reasons:
                logger.info("=" * 80)
                logger.info("🎨 [ComfyUI 이미지 생성 시작]")
                logger.info("=" * 80)
                logger.info("이미지 생성 이유:")
                for i, reason in enumerate(image_generation_reasons, 1):
                    logger.info(f"  {i}. {reason}")
                logger.info("=" * 80)
            else:
                logger.info("🎨 [ComfyUI 이미지 생성 시작] (이유: visual_change_detected=true)")
            
            try:
                # ComfyClient 초기화 (아직 안 되어 있으면)
                if self.comfy_client is None:
                    # ComfyUI 설정 로드
                    saved_config = self.load_config()
                    comfyui_settings = saved_config.get("comfyui_settings", {})
                    server_port = comfyui_settings.get("server_port", 8000)
                    workflow_path = comfyui_settings.get("workflow_path", "workflows/comfyui_zit.json")
                    model_name = comfyui_settings.get("model_name", "Zeniji_mix_ZiT_v1.safetensors")
                    steps = comfyui_settings.get("steps", 9)
                    cfg = comfyui_settings.get("cfg", 1.0)
                    sampler_name = comfyui_settings.get("sampler_name", "euler")
                    scheduler = comfyui_settings.get("scheduler", "simple")
                    server_address = f"127.0.0.1:{server_port}"
                    self.comfy_client = ComfyClient(
                        server_address=server_address,
                        workflow_path=workflow_path,
                        model_name=model_name,
                        steps=steps,
                        cfg=cfg,
                        sampler_name=sampler_name,
                        scheduler=scheduler
                    )
                    logger.info(f"ComfyClient initialized: {server_address}, workflow: {workflow_path}, model: {model_name}, steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}")
                
                # 설정에서 appearance와 나이 가져오기
                saved_config = self.load_config()
                appearance = saved_config["character"].get("appearance", "")
                char_age = saved_config["character"].get("age", 21)
                
                # appearance에 나이 추가 (이미지 생성용)
                if appearance and f"{char_age} years old" not in appearance.lower():
                    appearance = f"{char_age} years old, {appearance}".strip()
                elif not appearance:
                    appearance = f"{char_age} years old"
                
                # response에서 visual_prompt와 background 가져오기
                visual_prompt = response.get("visual_prompt", "")
                background = response.get("background", "")
                
                # visual_prompt가 없으면 기본값 사용
                if not visual_prompt:
                    visual_prompt = f"background: {background}, expression: {emotion}, looking at viewer"
                elif background and "background:" not in visual_prompt.lower():
                    # visual_prompt에 background가 없으면 추가
                    visual_prompt = f"{visual_prompt}, background: {background}"
                
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
                    # 현재 이미지로 저장
                    self.current_image = image
                    new_image_generated = True  # 새 이미지 생성됨
                    logger.info("Image generated successfully")
                else:
                    logger.warning("Failed to generate image (returned None)")
            except Exception as e:
                logger.error(f"Failed to generate image: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 이미지 생성 실패해도 대화는 계속 진행
        
        # 새 이미지가 생성되지 않았으면 이전 이미지 그대로 반환 (로딩 창 방지)
        if not new_image_generated:
            image = self.current_image
        
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
                        for preset_name in PRESETS.keys():
                            preset_btn = gr.Button(preset_name, variant="secondary")
                            # lambda 클로저 문제 해결 및 fn 명시
                            def make_preset_handler(name):
                                def handler():
                                    return self.apply_preset(name)
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
                    
                    # 이미지 업데이트 트리거용 hidden state
                    image_update_trigger = gr.State(value=None)
                    
                    def on_submit(message, history):
                        if not self.model_loaded:
                            return history, "", "", "", "", None  # 마지막은 trigger
                        new_history, output, stats, image, choices, thought, action = self.process_turn(message, history)
                        
                        # image가 새로 생성됐으면 trigger에 넣고, 아니면 None
                        return new_history, "", stats, thought, action, image
                    
                    def update_image_if_needed(trigger_image):
                        """트리거에 이미지가 있을 때만 반환, 없으면 업데이트 안 함"""
                        if trigger_image is not None:
                            return trigger_image
                        return gr.skip()  # Gradio 6.x: 업데이트 건너뛰기
                    
                    # 메인 submit - 이미지 제외
                    submit_btn.click(
                        on_submit,
                        inputs=[user_input, chatbot],
                        outputs=[chatbot, user_input, stats_display, thought_display, action_display, image_update_trigger]
                    ).then(
                        update_image_if_needed,
                        inputs=[image_update_trigger],
                        outputs=[image_display]
                    )
                    
                    user_input.submit(
                        on_submit,
                        inputs=[user_input, chatbot],
                        outputs=[chatbot, user_input, stats_display, thought_display, action_display, image_update_trigger]
                    ).then(
                        update_image_if_needed,
                        inputs=[image_update_trigger],
                        outputs=[image_display]
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
                    gr.Markdown("## LLM 설정")
                    
                    # LLM 설정 로드
                    llm_settings = saved_config.get("llm_settings", {})
                    provider = llm_settings.get("provider", "ollama")
                    ollama_model = llm_settings.get("ollama_model", "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest")
                    openrouter_model = llm_settings.get("openrouter_model", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
                    # API 키는 파일에서 불러오기
                    openrouter_api_key = self._load_openrouter_api_key()
                    
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
                            config_data = self.load_config()
                            
                            # OpenRouter API 키는 별도 파일에 저장
                            if provider_val == "openrouter" and openrouter_key_val:
                                if not self._save_openrouter_api_key(openrouter_key_val):
                                    return "❌ OpenRouter API 키 저장 실패"
                            
                            # LLM 설정 업데이트 (API 키는 제외)
                            config_data["llm_settings"] = {
                                "provider": provider_val,
                                "ollama_model": ollama_model_val or "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
                                "openrouter_model": openrouter_model_val or "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
                            }
                            
                            # 설정 저장
                            if self.save_config(config_data):
                                # Brain 재초기화 (새 설정 적용)
                                try:
                                    if self.brain is not None:
                                        # 기존 Brain의 memory_manager를 새 설정으로 재초기화
                                        llm_settings = config_data["llm_settings"]
                                        # API 키는 파일에서 불러오기
                                        api_key = self._load_openrouter_api_key() if llm_settings["provider"] == "openrouter" else None
                                        self.brain.memory_manager = MemoryManager(
                                            dev_mode=self.dev_mode,
                                            provider=llm_settings["provider"],
                                            model_name=llm_settings["ollama_model"] if llm_settings["provider"] == "ollama" else llm_settings["openrouter_model"],
                                            api_key=api_key
                                        )
                                        
                                        # 모델 로드 시도 (OpenRouter 실패 시 Ollama로 폴백)
                                        result = self.brain.memory_manager.load_model()
                                        if result is None and llm_settings["provider"] == "openrouter":
                                            logger.warning("OpenRouter 연결 실패, Ollama로 폴백 시도...")
                                            # Ollama로 폴백
                                            config_data["llm_settings"]["provider"] = "ollama"
                                            self.brain.memory_manager = MemoryManager(
                                                dev_mode=self.dev_mode,
                                                provider="ollama",
                                                model_name=llm_settings["ollama_model"]
                                            )
                                            result = self.brain.memory_manager.load_model()
                                            if result is None:
                                                return "⚠️ OpenRouter 연결 실패, Ollama로 폴백 시도했으나 Ollama도 연결 실패했습니다."
                                            return "⚠️ OpenRouter 연결 실패, Ollama로 폴백하여 설정 저장 완료."
                                        
                                        self.model_loaded = (result is not None)
                                        if self.model_loaded:
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
                    comfyui_settings = saved_config.get("comfyui_settings", {})
                    comfyui_port = comfyui_settings.get("server_port", 8000)
                    workflow_path = comfyui_settings.get("workflow_path", "workflows/comfyui_zit.json")
                    comfyui_model = comfyui_settings.get("model_name", "Zeniji_mix_ZiT_v1.safetensors")
                    comfyui_steps = comfyui_settings.get("steps", 9)
                    comfyui_cfg = comfyui_settings.get("cfg", 1)
                    comfyui_sampler = comfyui_settings.get("sampler_name", "euler")
                    comfyui_scheduler = comfyui_settings.get("scheduler", "simple")
                    
                    # workflows 폴더의 .json 파일 목록 가져오기
                    workflows_dir = Path("workflows")
                    workflow_files = []
                    if workflows_dir.exists():
                        workflow_files = sorted([f.name for f in workflows_dir.glob("*.json")])
                    
                    if not workflow_files:
                        workflow_files = ["comfyui_zit.json"]  # 기본값
                    
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
                            comfyui_workflow_input = gr.Dropdown(
                                label="워크플로우 파일",
                                value=current_workflow,
                                choices=workflow_files,
                                info="workflows 폴더에서 사용할 워크플로우 파일 선택"
                            )
                            comfyui_model_input = gr.Textbox(
                                label="ComfyUI 모델 이름",
                                value=comfyui_model,
                                placeholder="예: Zeniji_mix_ZiT_v1.safetensors",
                                info="ComfyUI에서 사용할 모델 파일 이름 (확장자 포함)"
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
                    
                    def save_comfyui_settings(port_val, workflow_val, model_val, steps_val, cfg_val, sampler_val, scheduler_val):
                        """ComfyUI 설정 저장"""
                        try:
                            config_data = self.load_config()
                            
                            # ComfyUI 설정 업데이트
                            if "comfyui_settings" not in config_data:
                                config_data["comfyui_settings"] = {}
                            
                            workflow_path = f"workflows/{workflow_val}" if workflow_val else "workflows/comfyui_zit.json"
                            
                            config_data["comfyui_settings"]["server_port"] = int(port_val) if port_val else 8000
                            config_data["comfyui_settings"]["workflow_path"] = workflow_path
                            config_data["comfyui_settings"]["model_name"] = model_val or "Zeniji_mix_ZiT_v1.safetensors"
                            config_data["comfyui_settings"]["steps"] = int(steps_val) if steps_val else 9
                            config_data["comfyui_settings"]["cfg"] = float(cfg_val) if cfg_val else 1.0
                            config_data["comfyui_settings"]["sampler_name"] = sampler_val or "euler"
                            config_data["comfyui_settings"]["scheduler"] = scheduler_val or "simple"
                            
                            # 설정 저장
                            if self.save_config(config_data):
                                # ComfyClient 재초기화 (새 설정 적용)
                                try:
                                    if self.comfy_client is not None:
                                        server_address = f"127.0.0.1:{config_data['comfyui_settings']['server_port']}"
                                        workflow_path = config_data['comfyui_settings'].get('workflow_path', 'workflows/comfyui_zit.json')
                                        model_name = config_data['comfyui_settings']['model_name']
                                        steps = config_data['comfyui_settings'].get('steps', 9)
                                        cfg = config_data['comfyui_settings'].get('cfg', 1.0)
                                        sampler_name = config_data['comfyui_settings'].get('sampler_name', 'euler')
                                        scheduler = config_data['comfyui_settings'].get('scheduler', 'simple')
                                        self.comfy_client = ComfyClient(
                                            server_address=server_address,
                                            workflow_path=workflow_path,
                                            model_name=model_name,
                                            steps=steps,
                                            cfg=cfg,
                                            sampler_name=sampler_name,
                                            scheduler=scheduler
                                        )
                                        logger.info(f"ComfyClient 재초기화 완료: {server_address}, workflow: {workflow_path}, model: {model_name}, steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}")
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
                        inputs=[comfyui_port_input, comfyui_workflow_input, comfyui_model_input, comfyui_steps_input, comfyui_cfg_input, comfyui_sampler_input, comfyui_scheduler_input],
                        outputs=[comfyui_status]
                    )
            
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
            
            # Footer 추가
            gr.Markdown(
                """
                <div style="text-align: center; margin-top: 20px; padding: 10px; color: #666;">
                    ❤️ <a href="https://zeniji.love" target="_blank" style="color: #666; text-decoration: none;">zeniji.love</a>
                </div>
                """
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
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True)


if __name__ == "__main__":
    main()
