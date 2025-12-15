"""
Zeniji Emotion Simul - Main Application
Gradio UI 및 게임 루프
"""

import gradio as gr
import logging
import argparse
import json
import sys
import socket
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

# PyInstaller 호환성을 위한 경로 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 경우
    base_path = Path(sys.executable).parent
    python_path = base_path / 'python'
    if python_path.exists():
        sys.path.insert(0, str(python_path))
else:
    # 개발 모드
    base_path = Path(__file__).parent.parent
    python_path = Path(__file__).parent
    if str(python_path) not in sys.path:
        sys.path.insert(0, str(python_path))

from brain import Brain
from state_manager import CharacterState
from comfy_client import ComfyClient
from memory_manager import MemoryManager
from PIL import Image, ImageDraw, ImageFont
import io
import config
import plotly.graph_objects as go
from encryption import EncryptionManager
from config_manager import ConfigManager
from ui_components import UIComponents
from game_initializer import GameInitializer
from ui_builder import UIBuilder
from i18n import set_global_language, get_i18n

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("App")


class GameApp:
    """게임 애플리케이션"""
    
    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode
        self.brain = None
        self.model_loaded = False
        self.current_image: Optional[Image.Image] = None  # PIL Image 저장
        self.current_chart: Optional[go.Figure] = None  # 이전 차트 저장 (로딩 중 유지용)
        self.comfy_client = None
        self.previous_relationship: Optional[str] = None  # 이전 관계 상태 (모달용)
        self.previous_badges: set = set()  # 이전 턴의 뱃지 목록 (알림용)
        self.last_image_generation_info: Optional[Dict[str, str]] = None  # 마지막 이미지 생성 정보 (visual_prompt, appearance)
        
        # 분리된 모듈 초기화
        self.encryption_manager = EncryptionManager()
        self.config_manager = ConfigManager()
        self.ui_components = UIComponents()
    
    # 설정 관리 메서드 (config_manager 위임)
    def load_config(self) -> Dict:
        """설정 파일 로드 - None 값 정리"""
        return self.config_manager.load_config()
    
    def save_config(self, config_data: Dict) -> bool:
        """설정 파일 저장 (하위 호환성용)"""
        return self.config_manager.save_config(config_data)
    
    def load_env_config(self) -> Dict:
        """환경설정 파일 로드 (LLM 및 ComfyUI 설정)"""
        return self.config_manager.load_env_config()
    
    def save_env_config(self, env_config: Dict) -> bool:
        """환경설정 파일 저장"""
        return self.config_manager.save_env_config(env_config)
    
    def get_character_files(self) -> list:
        """character 폴더의 JSON 파일 목록 가져오기"""
        return self.config_manager.get_character_files()
    
    def save_character_config(self, config_data: Dict, filename: str) -> bool:
        """character 폴더에 설정 파일 저장"""
        return self.config_manager.save_character_config(config_data, filename)
    
    def load_character_config(self, filename: str) -> Dict:
        """character 폴더에서 설정 파일 로드"""
        return self.config_manager.load_character_config(filename)
    
    def get_scenario_files(self) -> list:
        """scenarios 폴더의 JSON 파일 목록 가져오기"""
        return self.config_manager.get_scenario_files()
    
    def save_scenario(self, scenario_data: dict, scenario_name: str) -> bool:
        """시나리오 데이터를 파일로 저장 (JSON 형식) - 대화 + 상태 정보 포함"""
        return self.config_manager.save_scenario(scenario_data, scenario_name)
    
    def _overlay_text_on_image(self, image: Image.Image, overlay_text: str) -> Image.Image:
        """
        주어진 이미지 하단에 overlay_text를 반투명 박스와 함께 오버레이해서 반환
        (원본 이미지는 변경하지 않고 새 이미지를 반환)
        """
        if not overlay_text:
            return image

        # RGBA로 변환
        img = image.convert("RGBA")
        W, H = img.size

        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 폰트 로드 - Gradio 폰트 스택 순서대로 시도
        # Gradio font stack: IBM Plex Sans, ui-sans-serif, system-ui, -apple-system, 
        # BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif
        try:
            # 글자 조금 더 크게
            font_size = max(18, W // 45)

            font = None
            font_candidates = []
            
            import os
            import platform

            # 1. IBM Plex Sans (Gradio 기본 폰트, 일반적으로 설치되어 있지 않을 수 있음)
            # Windows Fonts 폴더와 일반 경로 체크
            if os.name == "nt":
                windir = os.environ.get("WINDIR", r"C:\Windows")
                plex_paths = [
                    os.path.join(windir, "Fonts", "IBMPlexSans-Regular.ttf"),
                    os.path.join(windir, "Fonts", "IBMPlexSans-Medium.ttf"),
                ]
                font_candidates.extend(plex_paths)
            # Linux/Mac 경로도 시도
            common_font_paths = [
                "/usr/share/fonts/truetype/ibm-plex/IBMPlexSans-Regular.ttf",
                "/usr/share/fonts/truetype/ibm-plex/IBMPlexSans-Medium.ttf",
                "/Library/Fonts/IBMPlexSans-Regular.ttf",
                "~/.fonts/IBMPlexSans-Regular.ttf",
            ]
            font_candidates.extend(common_font_paths)
            font_candidates.append("IBMPlexSans-Regular.ttf")  # 시스템 폰트 경로에 있을 수도

            # 2. Segoe UI (Windows 시스템 UI 폰트)
            if os.name == "nt":
                windir = os.environ.get("WINDIR", r"C:\Windows")
                font_candidates.append(os.path.join(windir, "Fonts", "segoeui.ttf"))
            font_candidates.extend(["segoeui.ttf", "Segoe UI", "segoe ui"])

            # 3. Arial (범용 sans-serif)
            if os.name == "nt":
                windir = os.environ.get("WINDIR", r"C:\Windows")
                font_candidates.append(os.path.join(windir, "Fonts", "arial.ttf"))
            font_candidates.extend(["arial.ttf", "Arial"])

            # 4. Roboto (Android/Chrome OS)
            font_candidates.extend(["Roboto-Regular.ttf", "Roboto", "roboto.ttf"])

            # 5. Helvetica Neue (macOS)
            if platform.system() == "Darwin":
                font_candidates.extend(["HelveticaNeue.ttc", "Helvetica Neue"])

            # 6. 시스템 기본 sans-serif 폰트들
            font_candidates.extend(["calibri.ttf", "Calibri", "tahoma.ttf", "Tahoma", "verdana.ttf", "Verdana"])

            # 7. Noto Sans (다국어 지원)
            font_candidates.extend(["NotoSans-Regular.ttf", "Noto Sans"])

            # 폰트 시도
            for font_name in font_candidates:
                try:
                    # 경로 확장 (~ -> 홈 디렉토리)
                    if font_name.startswith("~"):
                        font_name = os.path.expanduser(font_name)
                    font = ImageFont.truetype(font_name, font_size)
                    logger.debug(f"Font loaded: {font_name}")
                    break
                except Exception:
                    font = None
                    continue

            # 폰트를 찾지 못한 경우 폴백
            if font is None:
                # Windows 한글 폰트 시도
                if os.name == "nt":
                    try:
                        windir = os.environ.get("WINDIR", r"C:\Windows")
                        font = ImageFont.truetype(os.path.join(windir, "Fonts", "malgun.ttf"), font_size)
                        logger.debug("Font fallback: malgun.ttf")
                    except Exception:
                        try:
                            windir = os.environ.get("WINDIR", r"C:\Windows")
                            font = ImageFont.truetype(os.path.join(windir, "Fonts", "gulim.ttc"), font_size)
                            logger.debug("Font fallback: gulim.ttc")
                        except Exception:
                            font = ImageFont.load_default()
                            logger.debug("Font fallback: default")
                else:
                    font = ImageFont.load_default()
                    logger.debug("Font fallback: default")
        except Exception as e:
            logger.warning(f"Font loading error: {e}, using default")
            font = ImageFont.load_default()

        # 줄 단위로 나누고, 각 줄을 다시 폭에 맞춰 wrap
        max_width = int(W * 0.9)
        wrapped_lines = []
        for raw_line in overlay_text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            words = line.split()
            current = ""
            for w in words:
                test = (current + " " + w).strip()
                if draw.textlength(test, font=font) <= max_width:
                    current = test
                else:
                    if current:
                        wrapped_lines.append(current)
                    current = w
            if current:
                wrapped_lines.append(current)

        if not wrapped_lines:
            return image

        # 텍스트 높이 계산 (줄 간격을 더 넉넉하게)
        bbox = font.getbbox("A")
        base_line_height = bbox[3] - bbox[1]
        # 줄 간격을 조금 더 크게 (1.5배)
        line_height = int(base_line_height * 1.5)
        # 상하 패딩도 약간 증가
        padding_y = int(base_line_height * 0.9)
        padding_x = int(font_size * 0.6) if 'font_size' in locals() else 10
        total_text_h = line_height * len(wrapped_lines) + padding_y * 2

        # 바탕 반투명 박스 (하단)
        box_y0 = H - total_text_h
        box_y1 = H
        draw.rectangle(
            [(0, box_y0), (W, box_y1)],
            fill=(0, 0, 0, 170)
        )

        # 텍스트 중앙 정렬로 그리기
        y = box_y0 + padding_y
        for line in wrapped_lines:
            text_w = draw.textlength(line, font=font)
            x = (W - text_w) / 2
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        return Image.alpha_composite(img, overlay).convert("RGB")

    def _build_overlay_text(self, stats: Dict[str, float], relationship: str, mood: str, badges: list) -> str:
        """
        Build overlay text for image.
        - Do NOT show any raw numerical stats (6-axis values are omitted for clarity).
        - Relationship: show the current relationship status text as-is (e.g. Lover, Master, Slave, Breakup, Divorce, Tempted, etc).
        - Mood: show mood text only (no label).
        - Badges: show badge names only, comma-separated (no label).
        """
        # Relationship: show any non-empty relationship status (e.g. Lover, Master, Slave, Breakup, Divorce, Tempted, etc.)
        relationship_line = relationship.strip() if isinstance(relationship, str) else ""

        # 기분도 라벨 없이 내용만
        mood_line = mood.strip() if isinstance(mood, str) else ""

        # 뱃지는 이름만 나열 (레이블 없음)
        badges_line = ""
        if isinstance(badges, (list, set, tuple)):
            names = [str(b).strip() for b in badges if str(b).strip()]
            if names:
                badges_line = ", ".join(names)

        lines = []
        if relationship_line:
            lines.append(relationship_line)
        if mood_line:
            lines.append(mood_line)
        if badges_line:
            lines.append(badges_line)

        return "\n".join(lines).strip()

    def _save_generated_image(self, image: Image.Image, turn_number: Optional[int] = None) -> Optional[str]:
        """
        생성된 이미지를 파일로 저장
        Args:
            image: PIL Image 객체
            turn_number: 턴 번호 (None이면 재생성 이미지)
        Returns:
            저장된 파일 경로 (실패 시 None)
        """
        try:
            # 이미지 폴더가 없으면 생성
            config.IMAGE_DIR.mkdir(exist_ok=True)
            
            # 파일명 생성 (타임스탬프 + 턴 번호)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if turn_number is not None:
                filename = f"image_turn{turn_number:04d}_{timestamp}.png"
            else:
                filename = f"image_retry_{timestamp}.png"
            
            file_path = config.IMAGE_DIR / filename
            
            # 이미지 저장
            image.save(file_path, "PNG")
            logger.info(f"Generated image saved to: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save generated image: {e}")
            return None
    
    def load_scenario(self, scenario_name: str) -> dict:
        """시나리오 파일을 불러오기 (JSON 형식) - 대화 + 상태 정보 포함"""
        return self.config_manager.load_scenario(scenario_name)
    
    def apply_preset(self, preset_name: str) -> Tuple[float, float, float, float, float, float, str, str]:
        """프리셋 적용 - 모든 수치가 확실히 숫자가 되도록 보장"""
        return self.config_manager.apply_preset(preset_name)
    
    # 암호화 관련 메서드 (encryption_manager 위임)
    def _load_openrouter_api_key(self) -> str:
        """OpenRouter API 키를 파일에서 복호화하여 불러오기"""
        return self.encryption_manager.load_openrouter_api_key()
    
    def _save_openrouter_api_key(self, api_key: str) -> bool:
        """OpenRouter API 키를 암호화하여 파일에 저장"""
        return self.encryption_manager.save_openrouter_api_key(api_key)
    

    # 게임 시작 메서드 (GameInitializer로 위임)
    def validate_and_start(
        self,
        player_name, player_gender,
        char_name, char_age, char_gender,
        appearance, personality,
        p_val, a_val, d_val, i_val, t_val, dep_val,
        initial_context, initial_background
    ) -> Tuple[str, str, list, str, str, str, str, str, str, Any, Any, Any]:
        """설정 검증 및 시작 (첫 대화 자동 생성) - GameInitializer로 위임"""
        return GameInitializer.validate_and_start(
            self,
            player_name, player_gender,
            char_name, char_age, char_gender,
            appearance, personality,
            p_val, a_val, d_val, i_val, t_val, dep_val,
            initial_context, initial_background
        )
    
    def load_model(self) -> Tuple[str, bool]:
        """모델 로드 (설정에서 LLM provider 정보 읽어서 초기화)"""
        if self.model_loaded and self.brain is not None:
            i18n = get_i18n()
            return i18n.get_text("msg_model_already_loaded", category="ui"), True
        
        try:
            # 설정에서 LLM 설정 읽기
            env_config = self.load_env_config()
            language = env_config.get("language", "en")
            # 전역 언어 설정
            set_global_language(language)
            
            llm_settings = env_config.get("llm_settings", {})
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
                    api_key=api_key,
                    language=language
                )
            else:
                # Brain이 이미 있으면 memory_manager만 재초기화하고 언어 업데이트
                model_name = ollama_model if provider == "ollama" else openrouter_model
                api_key = openrouter_api_key if provider == "openrouter" else None
                self.brain.language = language
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
    
    # UI 컴포넌트 메서드 (ui_components 위임)
    def create_radar_chart(self, stats: Dict[str, float], deltas: Dict[str, float] = None) -> go.Figure:
        """6축 수치를 위한 radar chart 생성"""
        return self.ui_components.create_radar_chart(stats, deltas)
    
    def create_event_notification(self, event_type: str, event_data: dict) -> str:
        """이벤트 알림 HTML 생성 (Gradio 호환)"""
        return self.ui_components.create_event_notification(event_type, event_data)
    
    def process_turn(self, user_input: str, history: list) -> Tuple[list, str, str, str, str, str, str, Any, str]:
        """턴 처리"""
        if not user_input.strip():
            return history, "", "", None, "", "", "", None, ""
        
        if self.brain is None:
            return history, "**오류**: Brain이 초기화되지 않았습니다.", "", None, "", "", "", None, ""
        
        try:
            response = self.brain.generate_response(user_input)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Turn processing failed: {e}")
            logger.error(f"Error traceback:\n{error_traceback}")
            logger.error(f"History type: {type(history)}, value: {history}")
            logger.error(f"User input: {user_input}")
            return history, f"**오류 발생**: {str(e)}\n\n상세 정보는 콘솔 로그를 확인하세요.", "", None, "", "", "", None, ""
        
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
        # Gradio 6.x Chatbot은 딕셔너리 형식 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]을 사용함
        # Gradio에서 전달되는 history가 set이나 다른 타입일 수 있으므로 안전하게 처리
        try:
            if history is None:
                history = []
            elif isinstance(history, set):
                # set인 경우 리스트로 변환
                history = list(history)
            elif not isinstance(history, list):
                # 다른 타입인 경우 리스트로 변환 시도
                try:
                    history = list(history)
                except (TypeError, ValueError):
                    logger.warning(f"History type {type(history)} cannot be converted to list, using empty list")
                    history = []
            else:
                # 이미 리스트인 경우 복사본 생성
                history = list(history)
            
            # 딕셔너리 형식으로 추가
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": speech})
        except Exception as e:
            logger.error(f"Failed to update history: {e}, history type: {type(history)}")
            # 오류 발생 시 새 리스트로 시작 (딕셔너리 형식)
            history = [{"role": "user", "content": user_input}, {"role": "assistant", "content": speech}]
        
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
        
        # 이벤트 알림 생성 (여러 개 수집 가능)
        events_to_show = []
        
        # 1. 관계 상태 변경 체크
        relationship_changed = False
        if self.previous_relationship is not None and self.previous_relationship != relationship:
            relationship_changed = True
            logger.info(f"Relationship changed: {self.previous_relationship} -> {relationship}")
        
        # 관계 상태가 특정 상태로 변경된 경우 (대소문자 구분 없이 비교)
        relationship_lower = relationship.lower() if relationship else ""
        trigger_list = ["lover", "partner", "divorce", "tempted", "slave", "master", "fiancee", "breakup"]
        if relationship_changed and relationship_lower in trigger_list:
            logger.info(f"Creating relationship change notification: {relationship}")
            events_to_show.append((relationship, {
                "new_status": relationship,
                "old_status": self.previous_relationship
            }))
        elif relationship_changed:
            # 관계가 변경되었지만 특정 상태가 아닌 경우에도 로깅
            logger.debug(f"Relationship changed but not in trigger list: {relationship}")
        
        # 2. Badge 이벤트 체크 (뱃지는 중요해서 관계와 겹쳐도 표시)
        # 이전 턴의 뱃지 목록과 비교하여 새로 획득한 뱃지만 알림 표시
        if new_badge:
            # 이전 턴에 없던 뱃지인 경우에만 알림 표시
            if new_badge not in self.previous_badges:
                logger.info(f"Creating badge notification for new badge: {new_badge}")
                events_to_show.append(("badge", {
                    "badge_name": new_badge
                }))
            else:
                logger.debug(f"Badge {new_badge} already owned in previous turn, skipping notification")
        
        # 3. Gacha tier 이벤트 체크 (다른 이벤트가 없을 때만)
        if not events_to_show and gacha_tier in ["jackpot", "surprise"]:
            events_to_show.append((gacha_tier, {
                "message": f"{'극진한 반응' if gacha_tier == 'jackpot' else '놀라운 반응'}이 발생했습니다! (배율: x{multiplier:.1f})"
            }))
        
        # 여러 알림 생성 (없으면 빈 문자열)
        event_notification = ""
        if events_to_show:
            event_notification = self.ui_components.create_multiple_notifications(events_to_show)
        
        # 이전 관계 상태 업데이트 (첫 턴이거나 변경되지 않은 경우에도 업데이트)
        if self.previous_relationship is None:
            logger.info(f"Initializing previous_relationship: {relationship}")
        self.previous_relationship = relationship
        
        # 이전 뱃지 목록 업데이트 (현재 뱃지 목록 저장)
        current_badges = response.get('badges', [])
        if isinstance(current_badges, list):
            self.previous_badges = set(current_badges)
        elif isinstance(current_badges, set):
            self.previous_badges = current_badges.copy()
        else:
            self.previous_badges = set()
        
        # Radar chart 생성 (이전 차트가 있으면 먼저 반환하고, 새 차트 생성 후 업데이트)
        # 이전 차트를 먼저 반환하여 로딩 중에도 차트가 보이도록 함
        if self.current_chart is not None:
            # 이전 차트를 먼저 반환 (임시)
            radar_chart = self.current_chart
        else:
            # 첫 차트 생성 (빠르게 생성)
            radar_chart = self.create_radar_chart(stats, final_delta)
        
        # 새 차트 생성 (백그라운드에서 업데이트될 예정)
        new_radar_chart = self.create_radar_chart(stats, final_delta)
        self.current_chart = new_radar_chart  # 다음 번을 위해 저장
        
        # 작은 글씨로 6축 수치와 delta 표시 (2열 레이아웃)
        stats_text = f"""
<div style="font-size: 0.85em; color: #666;">
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
<div>
<strong>6축 수치:</strong><br>
P (쾌락): {stats.get('P', 0):.0f} {format_delta('P')}<br>
A (각성): {stats.get('A', 0):.0f} {format_delta('A')}<br>
D (지배): {stats.get('D', 0):.0f} {format_delta('D')}<br>
</div>
<div>
<strong>변화량:</strong><br>
I (친밀): {stats.get('I', 0):.0f} {format_delta('I')}<br>
T (신뢰): {stats.get('T', 0):.0f} {format_delta('T')}<br>
Dep (의존): {stats.get('Dep', 0):.0f} {format_delta('Dep')}<br>
</div>
</div>
<br>
<strong>반응 정도:</strong> {reaction_indicators} (x{multiplier:.1f})<br>
<strong>관계:</strong> {relationship} | <strong>기분:</strong> {mood}<br>
<strong>뱃지:</strong> {', '.join(response.get('badges', [])) or 'None'}
</div>
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
                    env_config = self.load_env_config()
                    comfyui_settings = env_config.get("comfyui_settings", {})
                    server_port = comfyui_settings.get("server_port", 8000)
                    workflow_path = comfyui_settings.get("workflow_path", config.COMFYUI_CONFIG["workflow_path"])
                    model_name = comfyui_settings.get("model_name", "Zeniji_mix_ZiT_v1.safetensors")
                    vae_name = comfyui_settings.get("vae_name", "zImage_vae.safetensors")
                    clip_name = comfyui_settings.get("clip_name", "zImage_textEncoder.safetensors")
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
                        scheduler=scheduler,
                        vae_name=vae_name,
                        clip_name=clip_name
                    )
                    logger.info(f"ComfyClient initialized: {server_address}, workflow: {workflow_path}, model: {model_name}, vae: {vae_name}, clip: {clip_name}, steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}")
                
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
                
                # 현재 턴 번호 가져오기
                turn_number = self.brain.state.total_turns if self.brain and self.brain.state else None
                
                image_bytes = self.comfy_client.generate_image(
                    visual_prompt=visual_prompt,
                    appearance=appearance,
                    seed=-1
                )
                
                if image_bytes:
                    # PIL Image로 변환 (오버레이 없이 원본 그대로 저장)
                    image = Image.open(io.BytesIO(image_bytes))
                    # 현재 이미지로 저장
                    self.current_image = image
                    # 원본 이미지를 바로 파일로 저장
                    self._save_generated_image(image, turn_number)
                    # 마지막 이미지 생성 정보 저장 (재시도용)
                    self.last_image_generation_info = {
                        "visual_prompt": visual_prompt,
                        "appearance": appearance
                    }
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
        
        return history, output_text, stats_text, image, choices_text, thought_text, action_text, radar_chart, event_notification
    
    def retry_image_generation(self) -> Tuple[Optional[Image.Image], str]:
        """마지막 이미지 생성 정보를 재사용하여 이미지 재생성"""
        if not self.last_image_generation_info:
            return None, "⚠️ 재생성할 이미지 정보가 없습니다."
        
        if self.comfy_client is None:
            return None, "⚠️ ComfyUI 클라이언트가 초기화되지 않았습니다."
        
        try:
            visual_prompt = self.last_image_generation_info.get("visual_prompt", "")
            appearance = self.last_image_generation_info.get("appearance", "")
            
            if not visual_prompt:
                return None, "⚠️ 저장된 visual_prompt가 없습니다."
            
            logger.info("🔄 이미지 재생성 시작 (저장된 visual_prompt 재사용)")
            logger.info(f"  appearance: {appearance[:50] if appearance else 'None'}...")
            logger.info(f"  visual_prompt: {visual_prompt[:100]}...")
            
            # ComfyUI에 이미지 생성 요청 (seed는 랜덤으로)
            image_bytes = self.comfy_client.generate_image(
                visual_prompt=visual_prompt,
                appearance=appearance,
                seed=-1  # 랜덤 시드
            )
            
            if image_bytes:
                # PIL Image로 변환 (오버레이 없이 원본 그대로)
                image = Image.open(io.BytesIO(image_bytes))
                # 현재 이미지로 업데이트
                self.current_image = image
                # 이미지 파일로 저장 (재생성 이미지는 turn_number 없이 저장)
                self._save_generated_image(image, None)
                logger.info("✅ 이미지 재생성 완료")
                return image, "✅ 이미지가 재생성되었습니다."
            else:
                logger.warning("이미지 재생성 실패 (None 반환)")
                return None, "❌ 이미지 재생성에 실패했습니다."
        except Exception as e:
            logger.error(f"이미지 재생성 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, f"❌ 이미지 재생성 중 오류: {str(e)}"
    
    def create_ui(self):
        """Gradio UI 생성 - UIBuilder로 위임"""
        return UIBuilder.create_ui(self)


def parse_args():
    parser = argparse.ArgumentParser(description="Zeniji Emotion Simul")
    parser.add_argument("--dev-mode", action="store_true", help="개발자 모드 활성화")
    parser.add_argument("--log-level", default="INFO", help="로깅 레벨 설정")
    return parser.parse_args()


def main():
    """메인 실행"""
    # PyInstaller 환경에서 uvicorn 로깅 문제 해결
    if getattr(sys, 'frozen', False):
        import os
        import io
        
        # 안전한 stdout/stderr 래퍼 클래스
        class SafeStream:
            def __init__(self, original_stream, name='stdout'):
                self._original = original_stream
                self._name = name
                self._buffer = io.BytesIO() if original_stream is None else None
                self.encoding = 'utf-8'
            
            def write(self, s):
                if self._original is not None:
                    try:
                        return self._original.write(s)
                    except (AttributeError, OSError):
                        pass
                if self._buffer is not None:
                    if isinstance(s, bytes):
                        self._buffer.write(s)
                    else:
                        self._buffer.write(s.encode(self.encoding))
                    return len(s)
                return 0
            
            def flush(self):
                if self._original is not None:
                    try:
                        self._original.flush()
                    except (AttributeError, OSError):
                        pass
            
            def isatty(self):
                return False
            
            def fileno(self):
                return 1 if self._name == 'stdout' else 2
            
            def __getattr__(self, name):
                # 다른 속성은 원본 스트림에서 가져오기 시도
                if self._original is not None:
                    try:
                        return getattr(self._original, name)
                    except AttributeError:
                        pass
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        # stdout/stderr 안전하게 설정
        if sys.stdout is None or (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty is None):
            sys.stdout = SafeStream(sys.stdout, 'stdout')
        elif not hasattr(sys.stdout, 'isatty'):
            original_stdout = sys.stdout
            sys.stdout = SafeStream(original_stdout, 'stdout')
        
        if sys.stderr is None or (hasattr(sys.stderr, 'isatty') and sys.stderr.isatty is None):
            sys.stderr = SafeStream(sys.stderr, 'stderr')
        elif not hasattr(sys.stderr, 'isatty'):
            original_stderr = sys.stderr
            sys.stderr = SafeStream(original_stderr, 'stderr')
        
        # uvicorn 로깅 문제 해결을 위한 환경 변수 설정
        os.environ['UVICORN_LOG_LEVEL'] = 'warning'
    
    args = parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    app = GameApp(dev_mode=args.dev_mode)
    demo = app.create_ui()
    
    # 사용 가능한 포트 찾기
    def find_free_port(start_port=7860, max_attempts=10):
        """사용 가능한 포트 찾기"""
        for i in range(max_attempts):
            port = start_port + i
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        # 모든 포트가 사용 중이면 None 반환 (Gradio가 자동으로 찾도록)
        return None
    
    server_port = find_free_port(7860)
    
    print("\n" + "=" * 60)
    print("🚀 Gradio 서버 시작 중...")
    print("=" * 60)
    if server_port:
        print(f"📍 로컬 접속: http://localhost:{server_port}")
        print(f"📍 네트워크 접속: http://127.0.0.1:{server_port}")
    else:
        print("📍 포트를 자동으로 찾는 중...")
    if args.dev_mode:
        print("🛠  Dev Mode ON")
    print("=" * 60 + "\n")
    
    demo.launch(server_name="127.0.0.1", server_port=server_port, share=False, inbrowser=True, show_error=False, theme=gr.themes.Soft())


if __name__ == "__main__":
    main()
