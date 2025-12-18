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
from typing import Tuple, Optional, Dict, Any, List
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
        # 최근 턴 정보 (순간 저장용)
        self.last_speech: str = ""
        self.last_thought: str = ""
        self.last_action: str = ""
        self.last_relationship: str = ""
        self.last_mood: str = ""
        self.last_badges: list = []
        
        # 분리된 모듈 초기화
        self.encryption_manager = EncryptionManager()
        self.config_manager = ConfigManager()
        self.ui_components = UIComponents()
    
    def _write_error_report_md(self, context: str, error: Exception, traceback_text: str, extra: Optional[Dict[str, Any]] = None) -> Optional[Path]:
        """에러 리포트를 Markdown 파일로 저장 (사용자 공유용)
        
        Args:
            context: 에러가 발생한 컨텍스트 설명 (예: 'process_turn')
            error: 발생한 예외 객체
            traceback_text: traceback.format_exc() 결과
            extra: 추가로 기록할 컨텍스트 정보 딕셔너리
        
        Returns:
            생성된 파일 경로 (실패 시 None)
        """
        try:
            from datetime import datetime
            import platform
            
            # 디렉터리 생성
            config.ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_{timestamp}.md"
            file_path = config.ERROR_LOG_DIR / filename
            
            # Markdown 형식으로 에러 리포트 작성
            lines = []
            lines.append(f"# Zeniji Emotion Simul Error Report")
            lines.append("")
            lines.append(f"- Version: {getattr(config, 'VERSION', 'unknown')}")
            lines.append(f"- Timestamp: {timestamp}")
            lines.append(f"- Context: {context}")
            lines.append(f"- Error Type: {type(error).__name__}")
            lines.append(f"- Error Message: {str(error)}")
            lines.append(f"- Dev Mode: {self.dev_mode}")
            lines.append(f"- Python: {platform.python_version()}")
            lines.append(f"- OS: {platform.system()} {platform.release()} ({platform.version()})")
            lines.append("")
            
            if extra:
                lines.append("## Extra Context")
                lines.append("")
                for key, value in extra.items():
                    try:
                        lines.append(f"- **{key}**: {value}")
                    except Exception:
                        # 값 직렬화에 실패해도 전체 리포트는 계속 작성
                        lines.append(f"- **{key}**: <unserializable>")
                lines.append("")
            
            lines.append("## Traceback")
            lines.append("")
            lines.append("```text")
            lines.append(traceback_text.rstrip())
            lines.append("```")
            lines.append("")
            
            file_path.write_text("\n".join(lines), encoding="utf-8")
            logger.error(f"에러 리포트가 생성되었습니다: {file_path}")
            return file_path
        except Exception as log_err:
            logger.error(f"에러 리포트 생성 중 오류 발생: {log_err}")
            return None
    
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
        """이미지 하단에 모던한 그라데이션 오버레이와 텍스트"""
        if not overlay_text:
            return image

        img = image.convert("RGBA")
        W, H = img.size

        # 폰트 설정 - 이미지 크기에 비례하되 적당한 범위 유지
        font_size = max(14, min(W // 45, 28))
        font = self._load_font(font_size)

        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        # 텍스트 래핑
        wrapped_lines = self._wrap_text(overlay_text, draw, font, int(W * 0.88))
        if not wrapped_lines:
            return image
        # 타이포그래피 설정
        bbox = font.getbbox("Ag")  # ascender + descender 기준
        base_height = bbox[3] - bbox[1]
        line_height = int(base_height * 1.45)  # 적당한 줄간격

        padding_x = int(W * 0.06)
        padding_y = int(base_height * 0.8)
        text_block_height = line_height * len(wrapped_lines) + padding_y * 2
        # 그라데이션 오버레이 (아래로 갈수록 진해짐)
        gradient_height = int(text_block_height * 1.8)
        gradient_top = H - gradient_height

        for y in range(gradient_height):
            # easeInQuad 커브로 자연스러운 그라데이션
            progress = y / gradient_height
            alpha = int(180 * (progress ** 1.8))
            draw.line([(0, gradient_top + y), (W, gradient_top + y)], fill=(0, 0, 0, alpha))
        # 텍스트 렌더링
        text_top = H - text_block_height + padding_y
        y = text_top

        for i, line in enumerate(wrapped_lines):
            # 좌측 정렬 (더 모던한 느낌)
            x = padding_x

            # 살짝 투명한 흰색 (눈이 편함)
            text_alpha = 245 if i == 0 else 230  # 첫 줄 약간 강조
            draw.text((x, y), line, font=font, fill=(255, 255, 255, text_alpha))
            y += line_height
        return Image.alpha_composite(img, overlay).convert("RGB")

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """모던한 폰트 우선 로드"""
        import os
        import platform

        # 세련된 폰트 우선순위
        fonts = [
            # 모던 한글
            "Pretendard-Regular.otf", "PretendardVariable.ttf",
            "SUIT-Regular.otf", "SUIT-Variable.ttf",
            "SpoqaHanSansNeo-Regular.ttf",
            # Noto Sans (범용)
            "NotoSansKR-Regular.otf", "NotoSansCJK-Regular.ttc",
            # 시스템 폰트
            "malgun.ttf", "AppleSDGothicNeo.ttc",
        ]

        # OS별 폰트 디렉토리
        if os.name == "nt":
            windir = os.environ.get("WINDIR", r"C:\Windows")
            dirs = [os.path.join(windir, "Fonts")]
        elif platform.system() == "Darwin":
            dirs = ["/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
        else:
            dirs = [
                "/usr/share/fonts/opentype/pretendard",
                "/usr/share/fonts/truetype/noto",
                "/usr/share/fonts/truetype/nanum",
            ]

        # 폰트 탐색
        for font_name in fonts:
            for font_dir in dirs + ["."]:
                try:
                    path = os.path.join(font_dir, font_name)
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                pass

        return ImageFont.load_default()
    
    # ===== ComfyUI / 이미지 처리 보조 메서드 =====
    def _is_sdxl_style(self) -> bool:
        """현재 ComfyUI 스타일이 SDXL인지 여부 (없으면 False)"""
        try:
            if self.comfy_client is None:
                return False
            style = getattr(self.comfy_client, "style", None)
            return style == "SDXL"
        except Exception:
            return False

    def _wrap_text(self, text: str, draw: ImageDraw.Draw, font, max_width: int) -> List[str]:
        """텍스트 래핑 - 자연스러운 줄바꿈"""
        lines: List[str] = []
        for paragraph in text.split("\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            words = paragraph.split()
            current = ""

            for word in words:
                test = f"{current} {word}".strip()
                if draw.textlength(test, font=font) <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word

            if current:
                lines.append(current)

        return lines

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
            
            # 스타일에 따라 리사이즈 비율 결정 (SDXL: 1.2배, 그 외: 1.5배)
            scale = 1.2 if self._is_sdxl_style() else 1.5
            width, height = image.size
            resized_image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
            
            # 이미지 저장
            resized_image.save(file_path, "PNG")
            logger.info(f"Generated image saved to: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save generated image: {e}")
            return None

    def _build_moment_overlay_text(self) -> str:
        """
        최근 턴의 대사/속마음/행동과 관계/기분/뱃지를 한 번에 표시할 오버레이 텍스트 생성
        """
        lines = []

        speech = getattr(self, "last_speech", "") or ""
        thought = getattr(self, "last_thought", "") or ""
        action = getattr(self, "last_action", "") or ""
        relationship = getattr(self, "last_relationship", "") or ""
        mood = getattr(self, "last_mood", "") or ""
        badges = getattr(self, "last_badges", []) or []

        # 1) 비어 있는 항목은 최근 턴 기록(history)에서 보충
        if self.brain is not None:
            try:
                history_obj = getattr(self.brain, "history", None)
                history_turns = getattr(history_obj, "turns", None) if history_obj else None
                if history_turns:
                    last_turn = history_turns[-1]
                    speech = speech or getattr(last_turn, "character_speech", "") or ""
                    thought = thought or getattr(last_turn, "character_thought", "") or ""
                    # action_speech가 turn에 없을 수 있으니 안전하게 접근
                    action = action or getattr(last_turn, "action_speech", "") or getattr(last_turn, "character_action", "") or action
            except Exception:
                pass

        # 2) 상태 정보로 관계/기분/뱃지 보충
        if self.brain is not None and getattr(self.brain, "state", None) is not None:
            state = self.brain.state
            if not relationship:
                relationship = getattr(state, "relationship_status", "") or relationship
            if not mood:
                try:
                    from logic_engine import interpret_mood
                    mood = interpret_mood(state) or mood
                except Exception:
                    pass
            if not badges:
                try:
                    badges = list(getattr(state, "badges", [])) or badges
                except Exception:
                    pass

        if speech:
            label = get_i18n().get_text("save_moment_overlay_speech", category="ui")
            lines.append(f"{label}: {speech}")
        if thought:
            label = get_i18n().get_text("save_moment_overlay_thought", category="ui")
            lines.append(f"{label}: {thought}")
        if action:
            label = get_i18n().get_text("save_moment_overlay_action", category="ui")
            lines.append(f"{label}: {action}")

        badge_names = [str(b).strip() for b in badges if str(b).strip()]
        info_parts = []
        if relationship:
            label = get_i18n().get_text("save_moment_overlay_relationship", category="ui")
            info_parts.append(f"{label}: {relationship}")
        if mood:
            label = get_i18n().get_text("save_moment_overlay_mood", category="ui")
            info_parts.append(f"{label}: {mood}")
        if badge_names:
            label = get_i18n().get_text("save_moment_overlay_badge", category="ui")
            info_parts.append(f"{label}: {', '.join(badge_names)}")

        if info_parts:
            if lines:
                lines.append("")  # 위/아래 구분을 위해 한 줄 비우기
            lines.append(" | ".join(info_parts))

        return "\n".join([line for line in lines if line]).strip()

    def _save_moment_image_file(self, image: Image.Image) -> Optional[str]:
        """
        순간 캡처 이미지를 파일로 저장 (turn 번호를 파일명에 포함)
        이미지는 이미 리사이즈되어 전달되므로 그대로 저장
        """
        try:
            config.IMAGE_DIR.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            turn_number = None
            if self.brain is not None and getattr(self.brain, "state", None) is not None:
                turn_number = getattr(self.brain.state, "total_turns", None)

            if turn_number is not None:
                filename = f"moment_turn{turn_number:04d}_{timestamp}.png"
            else:
                filename = f"moment_{timestamp}.png"

            file_path = config.IMAGE_DIR / filename
            
            # 이미 리사이즈된 이미지를 그대로 저장 (중복 리사이즈 방지)
            image.save(file_path, "PNG")
            logger.info(f"Moment image saved to: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save moment image: {e}")
            return None

    def save_moment_image(self) -> Optional[str]:
        """
        현재 이미지를 2배(Lanczos)로 확대한 뒤 대사/속마음/행동/관계/기분/뱃지 오버레이를 얹어 저장
        """
        if self.current_image is None:
            return None

        try:
            base_image = self.current_image

            # 스타일에 따라 업스케일 비율 결정 (SDXL: 1.2배, 그 외: 1.5배)
            scale = 1.2 if self._is_sdxl_style() else 1.5

            # Pillow 버전별 Lanczos 상수 대응
            try:
                resample_filter = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
            except Exception:
                resample_filter = getattr(Image, "LANCZOS", Image.BICUBIC)

            target_image = base_image.resize(
                (
                    max(1, int(round(base_image.width * scale))),
                    max(1, int(round(base_image.height * scale))),
                ),
                resample=resample_filter,
            )

            overlay_text = self._build_moment_overlay_text()
            if overlay_text:
                target_image = self._overlay_text_on_image(target_image, overlay_text)

            return self._save_moment_image_file(target_image)
        except Exception as e:
            logger.error(f"Failed to save moment image with overlay: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
        appearance, personality, speech_style,
        p_val, a_val, d_val, i_val, t_val, dep_val,
        initial_context, initial_background
    ) -> Tuple[str, str, list, str, str, str, str, str, str, Any, Any, Any]:
        """설정 검증 및 시작 (첫 대화 자동 생성) - GameInitializer로 위임"""
        return GameInitializer.validate_and_start(
            self,
            player_name, player_gender,
            char_name, char_age, char_gender,
            appearance, personality, speech_style,
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
            # LLM 파라미터 적용 (env_config 우선, 없으면 config 기본값)
            config.LLM_CONFIG["temperature"] = float(llm_settings.get("temperature", config.LLM_CONFIG["temperature"]))
            config.LLM_CONFIG["top_p"] = float(llm_settings.get("top_p", config.LLM_CONFIG["top_p"]))
            config.LLM_CONFIG["max_tokens"] = int(llm_settings.get("max_tokens", config.LLM_CONFIG["max_tokens"]))
            config.LLM_CONFIG["presence_penalty"] = float(llm_settings.get("presence_penalty", config.LLM_CONFIG["presence_penalty"]))
            config.LLM_CONFIG["frequency_penalty"] = float(llm_settings.get("frequency_penalty", config.LLM_CONFIG["frequency_penalty"]))
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
        i18n = get_i18n()
        labels = {
            "categories": [
                i18n.get_text("stat_p_short", category="ui"),
                i18n.get_text("stat_a_short", category="ui"),
                i18n.get_text("stat_d_short", category="ui"),
                i18n.get_text("stat_i_short", category="ui"),
                i18n.get_text("stat_t_short", category="ui"),
                i18n.get_text("stat_dep_short", category="ui"),
            ],
            "current_name": i18n.get_text("radar_current_label", category="ui"),
            "delta_name": i18n.get_text("radar_delta_label", category="ui"),
        }
        return self.ui_components.create_radar_chart(stats, deltas, labels=labels)
    
    def create_event_notification(self, event_type: str, event_data: dict) -> str:
        """이벤트 알림 HTML 생성 (Gradio 호환)"""
        return self.ui_components.create_event_notification(event_type, event_data)
    
    def process_turn(self, user_input: str, history: list) -> Tuple[list, str, str, str, str, str, str, Any, str]:
        """턴 처리"""
        if not user_input.strip():
            return history, "", "", None, "", "", "", None, ""
        
        if self.brain is None:
            return history, "**오류**: Brain이 초기화되지 않았습니다.", "", None, "", "", "", None, ""
        
        # 전체 완료 시간 측정 시작
        import time
        total_start_time = time.time()
        
        i18n = get_i18n()
        thought_label = i18n.get_text("thought_label", category="ui")
        action_label = i18n.get_text("action_label", category="ui")
        
        try:
            response = self.brain.generate_response(user_input)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Turn processing failed: {e}")
            logger.error(f"Error traceback:\n{error_traceback}")
            logger.error(f"History type: {type(history)}, value: {history}")
            logger.error(f"User input: {user_input}")
            
            # 사용자 공유용 에러 리포트(md) 생성
            extra_context = {
                "user_input": user_input,
                "history_type": str(type(history)),
                "history_length": len(history) if hasattr(history, "__len__") else "unknown",
            }
            report_path = self._write_error_report_md("process_turn", e, error_traceback, extra_context)
            if report_path is not None:
                user_msg = (
                    f"**Error occurred**: {str(e)}\n\n"
                    f"Please send the generated `{report_path.name}` file from the `error_logs` folder "
                    f"in your program directory to the developer."
                )
            else:
                user_msg = (
                    f"**Error occurred**: {str(e)}\n\n"
                    f"Please check the console logs for more details."
                )
            
            return history, user_msg, "", None, "", "", "", None, ""
        
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
        badges_list_raw = response.get("badges", [])
        if isinstance(badges_list_raw, (list, set, tuple)):
            badges_list = list(badges_list_raw)
        elif badges_list_raw:
            badges_list = [str(badges_list_raw)]
        else:
            badges_list = []

        # 최근 턴 정보 저장 (순간 저장용)
        self.last_speech = speech or ""
        self.last_thought = thought or ""
        self.last_action = action_speech or ""
        self.last_relationship = relationship or ""
        self.last_mood = mood or ""
        self.last_badges = badges_list
        
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
        ]
        
        if thought:
            output_lines.extend([
                f"*{thought_label}: {thought}*",
                "",
            ])
        
        output_lines.append(f"감정: {emotion} | 기분: {mood} | 관계: {relationship}")
        
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
        self.previous_badges = set(badges_list)
        
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
        
        # 작은 글씨로 6축 수치와 delta 표시 (2열 레이아웃) - i18n 적용
        stats_axis_title = i18n.get_text("stats_axis_title", category="ui")
        stats_change_title = i18n.get_text("stats_change_title", category="ui")
        reaction_label = i18n.get_text("reaction_level_label", category="ui")
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
{p_label}: {stats.get('P', 0):.0f} {format_delta('P')}<br>
{a_label}: {stats.get('A', 0):.0f} {format_delta('A')}<br>
{d_label}: {stats.get('D', 0):.0f} {format_delta('D')}<br>
</div>
<div>
<strong>{stats_change_title}:</strong><br>
{i_label}: {stats.get('I', 0):.0f} {format_delta('I')}<br>
{t_label}: {stats.get('T', 0):.0f} {format_delta('T')}<br>
{dep_label}: {stats.get('Dep', 0):.0f} {format_delta('Dep')}<br>
</div>
</div>
<br>
<strong>{reaction_label}:</strong> {reaction_indicators} (x{multiplier:.1f})<br>
<strong>{relationship_label}:</strong> {relationship} | <strong>{mood_label}:</strong> {mood}<br>
<strong>{badge_label}:</strong> {', '.join(badges_list) or badge_none}
</div>
"""
        
        # 이미지 생성 (visual_change_detected가 true이거나 5턴 이상 지났을 때)
        image = None
        visual_change_detected = response.get("visual_change_detected", False)
        image_generation_reasons = response.get("image_generation_reasons", [])
        new_image_generated = False  # 새 이미지가 생성되었는지 추적

        # 첫 턴 또는 아직 한 번도 이미지가 생성되지 않은 경우, 강제로 한 번은 이미지 생성 시도
        if config.IMAGE_MODE_ENABLED and self.current_image is None and not visual_change_detected:
            visual_change_detected = True
            if image_generation_reasons is None:
                image_generation_reasons = []
            image_generation_reasons.append("첫 턴 또는 초기 상태: 아직 이미지가 없어 강제로 한 번 생성합니다.")
        
        if visual_change_detected and config.IMAGE_MODE_ENABLED:
            # LLM Provider에 따라 모델 offload 대기 여부 결정
            env_config = self.load_env_config()
            llm_settings = env_config.get("llm_settings", {})
            provider = llm_settings.get("provider", "ollama")

            if provider == "ollama":
                # 로컬 Ollama 모델을 VRAM에서 내리기 위한 대기
                import time
                logger.info("Waiting 2 second for LLM model offload... (provider=ollama)")
                time.sleep(2.0)
            else:
                # OpenRouter 등 외부 API 사용 시에는 대기 불필요
                logger.info(f"Skip LLM offload wait (provider={provider})")
            
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
                    # ComfyUI 설정 로드 (이미 불러온 env_config 재사용)
                    comfyui_settings = env_config.get("comfyui_settings", {})
                    server_port = comfyui_settings.get("server_port", 8000)
                    style = comfyui_settings.get("style", "QWEN/Z-image")
                    use_lora = comfyui_settings.get("use_lora", False)
                    # 스타일별 설정 (하위 호환성을 위해 공통 키도 함께 확인)
                    if style == "SDXL":
                        workflow_path = comfyui_settings.get("workflow_path_sdxl") or config.COMFYUI_CONFIG["workflow_path"]
                        model_name = comfyui_settings.get("model_name_sdxl") or "Zeniji_mix_ZiT_v1.safetensors"
                        vae_name = comfyui_settings.get("vae_name_sdxl") or "zImage_vae.safetensors"
                        clip_name = comfyui_settings.get("clip_name_sdxl") or "zImage_textEncoder.safetensors"
                        if use_lora:
                            lora_name = comfyui_settings.get("lora_name_sdxl") or ""
                            lora_strength_model = comfyui_settings.get("lora_strength_model_sdxl")
                            if lora_strength_model in (None, ""):
                                lora_strength_model = 1.0
                        else:
                            lora_name = None
                            lora_strength_model = None
                        steps = comfyui_settings.get("steps_sdxl") or 9
                        cfg = comfyui_settings.get("cfg_sdxl") or 1.0
                        sampler_name = comfyui_settings.get("sampler_name_sdxl") or "euler"
                        scheduler = comfyui_settings.get("scheduler_sdxl") or "simple"
                    else:
                        workflow_path = comfyui_settings.get("workflow_path_qwen") or config.COMFYUI_CONFIG["workflow_path"]
                        model_name = comfyui_settings.get("model_name_qwen") or "Zeniji_mix_ZiT_v1.safetensors"
                        vae_name = comfyui_settings.get("vae_name_qwen") or "zImage_vae.safetensors"
                        clip_name = comfyui_settings.get("clip_name_qwen") or "zImage_textEncoder.safetensors"
                        if use_lora:
                            lora_name = comfyui_settings.get("lora_name_qwen") or ""
                            lora_strength_model = comfyui_settings.get("lora_strength_model_qwen")
                            if lora_strength_model in (None, ""):
                                lora_strength_model = 1.0
                        else:
                            lora_name = None
                            lora_strength_model = None
                        steps = comfyui_settings.get("steps_qwen") or 9
                        cfg = comfyui_settings.get("cfg_qwen") or 1.0
                        sampler_name = comfyui_settings.get("sampler_name_qwen") or "euler"
                        scheduler = comfyui_settings.get("scheduler_qwen") or "simple"
                    quality_tag = comfyui_settings.get("quality_tag", "")
                    negative_prompt = comfyui_settings.get("negative_prompt", "")
                    upscale_model_name = comfyui_settings.get("upscale_model_name", "4x-UltraSharp.pth")
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
                            f"ComfyClient initialized: {server_address}, "
                            f"workflow: {workflow_path}, model: {model_name}, vae: {vae_name}, clip: {clip_name}, "
                            f"LoRA enabled: name={lora_name}, strength_model={lora_strength_model}, "
                            f"steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}"
                        )
                    else:
                        logger.info(
                            f"ComfyClient initialized: {server_address}, "
                            f"workflow: {workflow_path}, model: {model_name}, vae: {vae_name}, clip: {clip_name}, "
                            f"LoRA disabled, steps: {steps}, cfg: {cfg}, sampler: {sampler_name}, scheduler: {scheduler}"
                        )
                
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
                
                # visual_prompt가 리스트인 경우 문자열로 변환
                if isinstance(visual_prompt, list):
                    visual_prompt = ", ".join(str(item) for item in visual_prompt)
                
                # visual_prompt가 없으면 기본값 사용
                if not visual_prompt:
                    visual_prompt = f"background: {background}, expression: {emotion}, looking at viewer"
                elif background and isinstance(visual_prompt, str) and "background:" not in visual_prompt.lower():
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
                    # 마지막 이미지 생성 정보 저장 (재시도용)
                    self.last_image_generation_info = {
                        "visual_prompt": visual_prompt,
                        "appearance": appearance
                    }
                    new_image_generated = True  # 새 이미지 생성됨
                    logger.info("Image generated successfully")
                else:
                    logger.warning("⚠️ 이미지 생성 실패 (None 반환) - 대화는 계속 진행됩니다")
            except Exception as e:
                logger.error(f"⚠️ 이미지 생성 중 오류 발생: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 이미지 생성 실패해도 대화는 계속 진행
        
        # 새 이미지가 생성되지 않았으면 이전 이미지 그대로 반환 (로딩 창 방지)
        if not new_image_generated:
            image = self.current_image
        
        # 전체 완료 시간 측정 완료
        total_elapsed_time = time.time() - total_start_time
        
        # LLM 응답 시간 가져오기
        llm_time = getattr(self.brain, '_last_llm_time', 0.0)
        
        # ComfyUI 응답 시간 가져오기 (이미지 생성이 있었을 때만)
        comfyui_time = 0.0
        if self.comfy_client is not None:
            comfyui_time = getattr(self.comfy_client, '_last_comfyui_time', 0.0)
        
        # 마지막 로그에 모든 시간 정보 표시
        logger.info("=" * 80)
        logger.info("⏱️ [전체 완료 시간 요약]")
        logger.info("=" * 80)
        logger.info(f"  LLM 응답 시간: {llm_time:.2f}s")
        if comfyui_time > 0:
            logger.info(f"  ComfyUI 응답 시간: {comfyui_time:.2f}s")
        else:
            logger.info(f"  ComfyUI 응답 시간: (이미지 생성 없음)")
        logger.info(f"  전체 완료 시간: {total_elapsed_time:.2f}s")
        logger.info("=" * 80)
        
        choices_text = "다음 대사를 입력하세요."
        thought_text = f"**{thought_label}**: {thought}" if thought else ""
        action_text = f"**{action_label}**: {action_speech}" if action_speech else ""
        
        return history, output_text, stats_text, image, choices_text, thought_text, action_text, radar_chart, event_notification
    
    def retry_image_generation(self) -> Tuple[Optional[Image.Image], str]:
        """마지막 이미지 생성 정보를 재사용하여 이미지 재생성"""
        i18n = get_i18n()
        if not self.last_image_generation_info:
            return None, i18n.get_text("msg_retry_no_info", category="ui")
        
        if self.comfy_client is None:
            return None, i18n.get_text("msg_comfyui_not_initialized", category="ui")
        
        try:
            visual_prompt = self.last_image_generation_info.get("visual_prompt", "")
            appearance = self.last_image_generation_info.get("appearance", "")
            
            if not visual_prompt:
                return None, i18n.get_text("msg_no_visual_prompt", category="ui")
            
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
                logger.info("✅ 이미지 재생성 완료")
                return image, i18n.get_text("msg_retry_success", category="ui")
            else:
                logger.warning("이미지 재생성 실패 (None 반환)")
                return None, i18n.get_text("msg_retry_failed", category="ui")
        except Exception as e:
            logger.error(f"이미지 재생성 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, i18n.get_text("retry_error", category="ui", error=str(e))
    
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
