"""
Zeniji Emotion Simul - Brain (The Director)
최상위 통제 모듈: 프롬프트 조립, LLM 호출, JSON 파싱, VRAM 교대 결정
"""

import json
import re
import logging
from typing import Dict, Optional, Any
from state_manager import CharacterState, DialogueHistory, DialogueTurn
import config
from logic_engine import (
    interpret_mood, check_badge_conditions, check_status_transition,
    apply_gacha_to_delta, get_trauma_instruction,
    get_intimacy_level, get_trust_level, get_dependency_level,
    apply_trauma_on_breakup, validate_status_transition_condition
)
from memory_manager import MemoryManager
from i18n import get_i18n
from config_manager import ConfigManager

logger = logging.getLogger("Brain")


class Brain:
    """The Director: 게임 흐름 통제"""
    
    def __init__(self, dev_mode: bool = False, provider: str = None, model_name: str = None, api_key: str = None, language: str = "en"):
        self.dev_mode = dev_mode
        self.language = language
        self.memory_manager = MemoryManager(
            dev_mode=dev_mode,
            provider=provider,
            model_name=model_name,
            api_key=api_key
        )
        self.state = CharacterState()
        self.history = DialogueHistory(max_turns=10)
        self.turns_since_image = 0
        # 초기 설정 정보
        self.initial_config: Optional[Dict] = None
        # 시간 측정용 변수
        self._last_llm_time = 0.0
    
    def set_initial_config(self, config: Dict[str, Any]):
        """초기 설정 정보 설정"""
        self.initial_config = config
        logger.info("Initial configuration set")
    
    def generate_response(self, player_input: str) -> Dict:
        """
        플레이어 입력에 대한 응답 생성
        """
        # 1. Python 기반 관계 전환 검사 (우선순위 1)
        transition_occurred, new_status = check_status_transition(self.state)
        if transition_occurred and new_status:
            logger.info(f"Status transition: {self.state.relationship_status} -> {new_status}")
            self.state.relationship_status = new_status
        
        # 2. LLM 호출 (첫 턴도 포함) - 메인 응답 생성
        llm_response = self._call_llm(player_input)
        
        # Ollama 원본 응답 로그 출력 (dev_mode일 때만)
        if self.dev_mode:
            logger.info("=" * 80)
            logger.info("📥 [OLLAMA RAW RESPONSE]")
            logger.info("=" * 80)
            logger.info(llm_response)
            logger.info("=" * 80)
        
        # 3. JSON 파싱 및 검증
        try:
            logger.debug(f"Starting JSON parsing. LLM response length: {len(llm_response)}")
            data = self._parse_json(llm_response)
            logger.debug(f"JSON parsing successful. Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            self._validate_response(data)
            logger.debug("JSON validation successful")
            
            # 파싱 및 검증된 JSON 로그 출력 (dev_mode일 때만)
            if self.dev_mode:
                logger.info("=" * 80)
                logger.info("✅ [PARSED JSON]")
                logger.info("=" * 80)
                import json as json_module
                logger.info(json_module.dumps(data, ensure_ascii=False, indent=2))
                logger.info("=" * 80)
        except Exception as e:
            import traceback
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"LLM response (first 500 chars): {llm_response[:500]}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return self._fallback_response(player_input)
        
        # 4. 가챠 적용
        proposed_delta = data.get("proposed_delta", {})
        final_delta, gacha_tier, multiplier = apply_gacha_to_delta(proposed_delta)
        
        # 5. 델타 적용 (트라우마 페널티 포함)
        self.state.apply_delta(final_delta, trauma_penalty=True)
        
        # 6. 뱃지 검사
        new_badge = check_badge_conditions(self.state)
        if new_badge:
            self.state.add_badge(new_badge)
            logger.info(f"Badge acquired: {new_badge}")
        
        # 7. 배경 업데이트 (LLM이 제공한 경우)
        background = data.get("background", "")
        previous_background = self.state.current_background  # 변경 전 배경 저장
        background_changed = False
        
        if background:
            # background가 한 글자라도 바뀌면 변경으로 간주
            if background != previous_background:
                background_changed = True
                self.state.current_background = background
                logger.info(f"Background updated: {previous_background} → {background}")
            else:
                logger.debug(f"Background unchanged: {background}")
        else:
            # 배경이 제공되지 않았으면 이전 배경 유지
            background = self.state.current_background
            logger.debug(f"Background not provided, keeping previous: {background}")
        
        # 8. 이미지 생성 필요 여부 판단
        visual_change = data.get("visual_change_detected", False)
        self.turns_since_image += 1
        
        # 이미지 생성 이유 추적
        image_generation_reasons = []
        
        # 배경 변경 체크 (한 글자라도 바뀌면 강제로 이미지 생성)
        if background_changed:
            visual_change = True
            image_generation_reasons.append(f"배경 변경: {previous_background} → {background}")
            logger.info(f"Background changed, forcing image generation")
        
        # LLM이 직접 요청한 경우
        if data.get("visual_change_detected", False):
            reason = data.get("reason", "")
            if reason:
                image_generation_reasons.append(f"LLM 요청: {reason}")
            else:
                image_generation_reasons.append("LLM 요청: visual_change_detected=true")
        
        # 강제 갱신 체크 (5턴 경과)
        if self.turns_since_image >= config.IMAGE_GENERATION_TRIGGERS["force_refresh_turns"]:
            visual_change = True
            image_generation_reasons.append(f"강제 갱신: {self.turns_since_image}턴 경과 (최대 {config.IMAGE_GENERATION_TRIGGERS['force_refresh_turns']}턴)")
        
        # 가챠 티어 체크
        if gacha_tier in config.IMAGE_GENERATION_TRIGGERS["critical_gacha_tiers"]:
            visual_change = True
            tier_name = {"jackpot": "극진한 반응", "surprise": "놀라운 반응", "critical": "강렬한 반응"}.get(gacha_tier, gacha_tier)
            image_generation_reasons.append(f"특수 반응: {tier_name} (가챠 티어: {gacha_tier})")
        
        # 관계 전환 체크
        if transition_occurred and new_status in config.IMAGE_GENERATION_TRIGGERS["status_transitions"]:
            visual_change = True
            image_generation_reasons.append(f"관계 전환: {self.state.relationship_status} → {new_status}")
        
        # 9. 히스토리 추가 (visual_prompt와 background 포함)
        self.state.total_turns += 1
        try:
            logger.debug(f"Creating DialogueTurn. History type: {type(self.history)}, history.turns type: {type(self.history.turns) if hasattr(self.history, 'turns') else 'N/A'}")
            turn = DialogueTurn(
                turn_number=self.state.total_turns,
                player_input=player_input,
                character_speech=data.get("speech", ""),
                character_thought=data.get("thought", ""),
                emotion=data.get("emotion", "neutral"),
                visual_prompt=data.get("visual_prompt", ""),
                background=background
            )
            logger.debug(f"DialogueTurn created. Adding to history...")
            self.history.add(turn)
            logger.debug(f"Turn added successfully. History length: {len(self.history.turns)}")
        except Exception as e:
            import traceback
            logger.error(f"Failed to add turn to history: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"History type: {type(self.history)}")
            logger.error(f"History.turns type: {type(self.history.turns) if hasattr(self.history, 'turns') else 'N/A'}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            # 히스토리 추가 실패해도 계속 진행

        # 10. 장기 기억 업데이트 (10턴마다 한 번, 기존 long_memory + 최근 히스토리 기반)
        try:
            self._update_long_memory_if_needed()
        except Exception as e:
            import traceback
            logger.error(f"Failed to update long-term memory: {e}")
            logger.error(traceback.format_exc())
        
        # 11. 응답 조립
        response = {
            "thought": data.get("thought", ""),
            "speech": data.get("speech", ""),
            "action_speech": data.get("action_speech", ""),  
            "emotion": data.get("emotion", "neutral"),
            "visual_change_detected": visual_change,
            "visual_prompt": data.get("visual_prompt", ""),
            "background": background,
            "reason": data.get("reason", ""),
            "image_generation_reasons": image_generation_reasons,  # 이미지 생성 이유 목록
            "final_delta": final_delta,
            "gacha_tier": gacha_tier,
            "multiplier": multiplier,
            "relationship_status": self.state.relationship_status,
            "mood": interpret_mood(self.state),
            "badges": self.state.badges.copy(),
            "stats": self.state.get_stats_dict(),
            "new_badge": new_badge
        }
        
        # LLM 보고 관계 전환 처리 (수치 조건 검증 포함)
        if data.get("relationship_status_change", False):
            new_status_name = data.get("new_status_name", "")
            # 모든 LLM 판단 상태에 대해 수치 조건 검증
            if new_status_name in ["Lover", "Fiancée", "Partner", "Master", "Slave"]:
                current_status = self.state.relationship_status
                if validate_status_transition_condition(self.state, current_status, new_status_name):
                    self.state.relationship_status = new_status_name
                    response["relationship_status"] = new_status_name
                    logger.info(f"LLM reported status change: {new_status_name} (validated)")
                else:
                    logger.warning(f"LLM reported status change to {new_status_name}, but condition not met. Current stats: P={self.state.P:.1f}, A={self.state.A:.1f}, D={self.state.D:.1f}, I={self.state.I:.1f}, T={self.state.T:.1f}, Dep={self.state.Dep:.1f}")
        
        # 이미지 생성 시 카운터 리셋
        if visual_change:
            self.turns_since_image = 0
        
        return response
    
    def _call_llm(self, player_input: str) -> str:
        """LLM 호출 (Ollama API) - 메인 응답만 반환 (장기 기억은 별도 갱신)"""
        result = self.memory_manager.get_model()
        if result is None:
            error_msg = (
                "Ollama API에 연결할 수 없습니다.\n"
                "확인 사항:\n"
                "1. Ollama가 실행 중인지 확인 (ollama serve)\n"
                "2. config.py의 OLLAMA_API_URL과 OLLAMA_MODEL_NAME 확인\n"
                "3. 모델이 다운로드되었는지 확인 (ollama pull qwen2.5:14b)"
            )
            raise RuntimeError(error_msg)
        
        # 프롬프트 조립 (메인 응답용)
        prompt = self._build_prompt(player_input)
        
        # 시스템 프롬프트 로그 출력 (dev_mode일 때만)
        if self.dev_mode:
            logger.info("=" * 80)
            logger.info("📝 [SYSTEM PROMPT]")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)
        
        logger.info("Calling LLM API...")
        try:
            # LLM 응답 시간 측정 시작
            import time
            llm_start_time = time.time()
            
            # Ollama API 호출 (메인 응답)
            response_text = self.memory_manager.generate(
                prompt,
                temperature=config.LLM_CONFIG["temperature"],
                top_p=config.LLM_CONFIG["top_p"],
                max_tokens=config.LLM_CONFIG["max_tokens"]
            )
            
            # LLM 응답 시간 측정 완료
            llm_elapsed_time = time.time() - llm_start_time
            logger.info(f"⏱️ LLM 응답 시간: {llm_elapsed_time:.2f}s")
            # 시간 정보 저장 (전체 완료 로그에서 사용)
            self._last_llm_time = llm_elapsed_time
            
            if not response_text or not response_text.strip():
                raise ValueError("Ollama returned empty response")

            return response_text
        except Exception as e:
            # 에러 발생 시에도 시간 측정
            import time
            if 'llm_start_time' in locals():
                llm_elapsed_time = time.time() - llm_start_time
                logger.error(f"⏱️ LLM 응답 시간 (에러): {llm_elapsed_time:.2f}s")
                self._last_llm_time = llm_elapsed_time
            logger.error(f"Ollama API call failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        raise RuntimeError(f"Ollama API 호출 실패: {e}")

    def _update_long_memory_if_needed(self):
        """
        장기 기억 업데이트 (10턴마다 1번)
        - 기존 long_memory + 최근 히스토리를 기반으로 LLM에 500자 이내 요약을 요청
        """
        # 10턴마다만 갱신 (0턴은 제외)
        if self.state.total_turns <= 0 or self.state.total_turns % 10 != 0:
            return

        # 모델 확인
        result = self.memory_manager.get_model()
        if result is None:
            logger.warning("long_memory 업데이트를 위해 모델을 불러올 수 없습니다. (건너뜀)")
            return

        i18n = get_i18n()
        i18n.set_language(self.language)

        # 기존 장기 기억 (없으면 기본 문구)
        existing_memory = self.state.long_memory if self.state.long_memory else i18n.get_default("no_memory")

        # 최근 히스토리 (DialogueHistory는 이미 max_turns=10이므로, format_for_prompt로 충분)
        history_text = self.history.format_for_prompt()

        # 장기 기억 요약 전용 프롬프트 구성 (단문 텍스트로 요약 요청)
        if self.language == "kr":
            prompt = f"""{i18n.get_prompt("long_memory_update_title")}

{i18n.get_prompt("long_memory_update_instruction")}
{i18n.get_prompt("long_memory_update_focus")}
{i18n.get_prompt("long_memory_update_keep")}
{i18n.get_prompt("long_memory_update_combine")}

{i18n.get_prompt("long_memory_existing", existing_memory=existing_memory)}

{i18n.get_prompt("data_context_history")}
{history_text}

위 내용을 바탕으로 중요한 기억만 500자 이하로 간단히 요약해주세요. JSON 형식이나 다른 부가 설명 없이 요약 텍스트만 작성해주세요.
"""
        else:
            prompt = f"""{i18n.get_prompt("long_memory_update_title")}

{i18n.get_prompt("long_memory_update_instruction")}
{i18n.get_prompt("long_memory_update_focus")}
{i18n.get_prompt("long_memory_update_keep")}
{i18n.get_prompt("long_memory_update_combine")}

{i18n.get_prompt("long_memory_existing", existing_memory=existing_memory)}

{i18n.get_prompt("data_context_history")}
{history_text}

Based on the above, please summarize only important memories in 500 characters or less. Please write only the summary text without JSON format or additional explanations.
"""

        logger.info(f"🔁 Updating long-term memory (turn={self.state.total_turns})")

        try:
            response_text = self.memory_manager.generate(
                prompt,
                temperature=config.LLM_CONFIG["temperature"],
                top_p=config.LLM_CONFIG["top_p"],
                max_tokens=config.LLM_CONFIG["max_tokens"]
            )

            if not response_text or not response_text.strip():
                logger.warning("long_memory 업데이트 LLM 응답이 비어 있습니다. (건너뜀)")
                return

            # 응답 텍스트를 그대로 사용 (JSON 파싱 없이)
            new_summary = response_text.strip()
            
            # JSON 형식이 포함되어 있을 수 있으므로, 중괄호나 따옴표 등 제거 시도
            # 하지만 우선 그대로 사용하고, 너무 길면 잘라냄
            if len(new_summary) > 500:
                # 500자까지만 사용 (문장 중간에서 끊어지지 않도록 공백이나 문장 부호에서 자름)
                new_summary = new_summary[:500]
                last_period = new_summary.rfind('.')
                last_space = new_summary.rfind(' ')
                if last_period > 450:  # 마지막 50자 내에 마침표가 있으면
                    new_summary = new_summary[:last_period + 1]
                elif last_space > 450:  # 마지막 50자 내에 공백이 있으면
                    new_summary = new_summary[:last_space]
            
            if new_summary:
                prev_len = len(self.state.long_memory) if self.state.long_memory else 0
                logger.info(f"장기 기억 갱신 완료 (이전 길이: {prev_len}, 새 길이: {len(new_summary)}): {new_summary[:100]}...")
                self.state.long_memory = new_summary
            else:
                logger.warning("long_memory 업데이트 응답이 비어 있습니다. (건너뜀)")
        except Exception as e:
            logger.error(f"long_memory 업데이트 LLM 호출 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _build_prompt(self, player_input: str) -> str:
        """시스템 프롬프트 조립 (다국어 지원)"""
        # I18n 인스턴스 가져오기
        i18n = get_i18n()
        i18n.set_language(self.language)
        
        # ComfyUI 스타일에 따라 visual_prompt 출력 형식 분기
        comfy_style = "QWEN/Z-image"
        try:
            cm = ConfigManager()
            env_cfg = cm.load_env_config()
            comfy_style = env_cfg.get("comfyui_settings", {}).get("style", "QWEN/Z-image")
        except Exception as e:
            logger.warning(f"Failed to load ComfyUI style for prompt building: {e}")
        visual_prompt_key = "output_visual_prompt_sdxl" if comfy_style == "SDXL" else "output_visual_prompt"
        
        mood = interpret_mood(self.state)
        intimacy_level = get_intimacy_level(self.state.I)
        trust_level = get_trust_level(self.state.T)
        dependency_level = get_dependency_level(self.state.Dep)
        
        # 트라우마 지침 (player_name은 나중에 치환)
        trauma_instruction_raw = get_trauma_instruction(self.state.trauma_level)
        
        # 관계 전환 가능성 체크
        status_check = self._get_status_transition_instruction()
        
        # 히스토리
        history_text = self.history.format_for_prompt()
        
        # 장기 기억 섹션 (long_memory가 있으면 표시, 첫 턴이어도 시나리오 복원 시 사용)
        long_memory_section = ""
        long_memory_instruction = ""
        logger.debug(f"Building prompt - total_turns: {self.state.total_turns}, long_memory exists: {bool(self.state.long_memory)}, long_memory length: {len(self.state.long_memory) if self.state.long_memory else 0}")
        if self.state.long_memory:
            # long_memory가 있으면 항상 표시 (시나리오 복원 시에도)
            long_memory_section = f"""
{i18n.get_prompt("long_memory_section")}
{self.state.long_memory}
"""
            logger.info(f"Long-term memory included in prompt (total_turns: {self.state.total_turns}): {self.state.long_memory[:100]}...")
            
            # 장기 기억 업데이트 지시 추가 (total_turns > 0이고 history.turns가 있으면)
            if self.state.total_turns > 0 and self.history.turns:
                existing_memory = self.state.long_memory if self.state.long_memory else i18n.get_default("no_memory")
                long_memory_instruction = f"""
{i18n.get_prompt("long_memory_update_title")}

{i18n.get_prompt("long_memory_update_instruction")}
{i18n.get_prompt("long_memory_update_focus")}
{i18n.get_prompt("long_memory_update_keep")}
{i18n.get_prompt("long_memory_update_combine")}

{i18n.get_prompt("long_memory_existing", existing_memory=existing_memory)}
"""
        
        # 현재 배경 정보
        current_background = self.state.current_background
        
        # 뱃지 지침
        badge_behavior = ""
        if self.state.badges:
            # badges가 set인지 list인지 확인
            if isinstance(self.state.badges, set):
                # set인 경우 리스트로 변환하거나 임의의 요소 선택
                badges_list = list(self.state.badges)
                active_badge = badges_list[-1] if badges_list else None
            else:
                # list인 경우
                active_badge = self.state.badges[-1]  # 가장 최근 뱃지
            
            if active_badge:
                badge_behavior = config.BADGE_BEHAVIORS.get(active_badge, "")
                if badge_behavior:
                    logger.debug(f"[BADGE] Active badge: {active_badge}, behavior length: {len(badge_behavior)}")
                else:
                    logger.warning(f"[BADGE] Badge '{active_badge}' found but no behavior defined in config.BADGE_BEHAVIORS")
        
        # Mood 지침
        mood_behavior = ""
        current_mood = interpret_mood(self.state)
        mood_behavior = config.MOOD_BEHAVIORS.get(current_mood, "")
        if mood_behavior:
            logger.debug(f"[MOOD] Current mood: {current_mood}, behavior length: {len(mood_behavior)}")
        else:
            logger.warning(f"[MOOD] Mood '{current_mood}' found but no behavior defined in config.MOOD_BEHAVIORS")
        
        # 주인공 정보 추출 (초기 설정이 있으면 사용, 없으면 기본값)
        player_name = i18n.get_default("player_name")
        player_gender = i18n.get_default("player_gender")
        if self.initial_config:
            player_info = self.initial_config.get("player", {})
            player_name = player_info.get("name", i18n.get_default("player_name"))
            player_gender = player_info.get("gender", i18n.get_default("player_gender"))
        
        # 트라우마 지침에 player_name 치환
        trauma_instruction = trauma_instruction_raw.replace("{player_name}", player_name) if trauma_instruction_raw else ""
        
        # 초기 설정 정보
        initial_context_section = ""
        character_profile_section = ""
        
        # 초기 설정에서 캐릭터 정보 가져오기 (모든 턴에서 사용)
        if self.initial_config:
            char_info = self.initial_config.get("character", {})
            char_name = char_info.get("name", i18n.get_default("character_name"))
            char_age = char_info.get("age", 21)
            char_gender = char_info.get("gender", i18n.get_default("character_gender"))
            appearance = char_info.get("appearance", "")
            personality = char_info.get("personality", "")
            speech_style = char_info.get("speech_style", i18n.get_default("character_speech_style"))
            initial_context = self.initial_config.get("initial_context", "")
        else:
            # 기본값 (초기 설정이 없을 때)
            char_name = i18n.get_default("character_name")
            char_age = 21
            char_gender = i18n.get_default("character_gender")
            appearance = ""
            personality = ""
            speech_style = i18n.get_default("character_speech_style")
            initial_context = ""
        
        # 캐릭터 프로필 섹션 (모든 턴에서 초기 설정의 나이 포함)
        if self.language == "kr":
            character_profile_section = f"""{i18n.get_prompt("character_profile_title")}
{i18n.get_prompt("character_name", char_name=char_name, char_age=char_age, char_gender=char_gender)}
{i18n.get_prompt("character_opponent", player_name=player_name, player_gender=player_gender)}"""
        else:
            character_profile_section = f"""{i18n.get_prompt("character_profile_title")}
{i18n.get_prompt("character_name", char_name=char_name, char_age=char_age, char_gender=char_gender)}
{i18n.get_prompt("character_opponent", player_name=player_name, player_gender=player_gender)}"""
        
        if appearance:
            character_profile_section += f"\n{i18n.get_prompt('character_appearance', appearance=appearance)}"
        if personality:
            character_profile_section += f"\n{i18n.get_prompt('character_personality', personality=personality)}"
        if speech_style:
            character_profile_section += f"\n{i18n.get_prompt('character_speech_style_custom', speech_style=speech_style)}"
        character_profile_section += f"\n{i18n.get_prompt('character_language')}"
        
        # 트라우마 지침 섹션 구성
        trauma_section = ""
        if trauma_instruction:
            trauma_section = f"""
{trauma_instruction}
"""
        
        # 특수 명령 섹션 구성 (트라우마 제외)
        special_commands = []
        if mood_behavior:
            special_commands.append(mood_behavior)
        if badge_behavior:
            special_commands.append(badge_behavior)
        if status_check:
            special_commands.append(status_check)
        
        # 특수 명령 텍스트 (언어별)
        if self.language == "kr":
            special_commands_text = " / ".join(special_commands) if special_commands else "[없음]"
        else:
            special_commands_text = " / ".join(special_commands) if special_commands else "[None]"
        
        # 트라우마 레벨 이름
        trauma_level_name = config.TRAUMA_LEVELS.get(round(self.state.trauma_level * 4) / 4, "Unknown")
        
        # 프롬프트 조립
        prompt = f"""{i18n.get_prompt("system_intro")}
{i18n.get_prompt("system_json_only")}
{i18n.get_prompt("system_no_censorship")}
{i18n.get_prompt("system_language")}

{character_profile_section}


{i18n.get_prompt("state_definition_title")}

{i18n.get_prompt("state_pleasure")}
{i18n.get_prompt("state_arousal")}
{i18n.get_prompt("state_dominance")}
{i18n.get_prompt("state_intimacy")}
{i18n.get_prompt("state_trust", player_name=player_name)}
{i18n.get_prompt("state_dependency", player_name=player_name)}
{i18n.get_prompt("state_delta_instruction")}
{i18n.get_prompt("state_delta_range")}

{i18n.get_prompt("behavior_priority_title")}

{i18n.get_prompt("behavior_priority_1", player_name=player_name, player_input=player_input)}
{i18n.get_prompt("behavior_priority_2")}
{i18n.get_prompt("behavior_quality_1")}
{i18n.get_prompt("behavior_quality_2", player_input=player_input)}
{i18n.get_prompt("behavior_quality_3")}
{i18n.get_prompt("behavior_quality_4", player_name=player_name)}
{i18n.get_prompt("background_consistency_1")}
{i18n.get_prompt("background_consistency_2", current_background=current_background)}
{i18n.get_prompt("background_consistency_3", player_name=player_name)}
{i18n.get_prompt("background_consistency_4")}
{i18n.get_prompt("background_consistency_5")}
{i18n.get_prompt("visual_change_1")}
{i18n.get_prompt("visual_change_2")}
{i18n.get_prompt("visual_change_3")}
{i18n.get_prompt("visual_change_4")}
{trauma_section}{i18n.get_prompt("data_context_title")}
{i18n.get_prompt("data_context_psychology", mood=mood, relationship_status=self.state.relationship_status)}
{i18n.get_prompt("data_context_stats", P=self.state.P, A=self.state.A, D=self.state.D, I=self.state.I, T=self.state.T, Dep=self.state.Dep)}
{i18n.get_prompt("data_context_accumulated", intimacy_level=intimacy_level, trust_level=trust_level, dependency_level=dependency_level)}
{i18n.get_prompt("data_context_trauma", trauma_level=self.state.trauma_level, trauma_level_name=trauma_level_name)}
{i18n.get_prompt("data_context_special", special_commands_text=special_commands_text)}
{i18n.get_prompt("data_context_history")}
{history_text}

{i18n.get_prompt("output_format_title")}

{i18n.get_prompt("output_format_json")}

```
{{
{i18n.get_prompt("output_thought")},
{i18n.get_prompt("output_speech")},
{i18n.get_prompt("output_action_speech")},
{i18n.get_prompt("output_emotion")},
{i18n.get_prompt("output_visual_change")},
{i18n.get_prompt(visual_prompt_key)},
{i18n.get_prompt("output_background")},
{i18n.get_prompt("output_reason")},
{i18n.get_prompt("output_delta")},
{i18n.get_prompt("output_relationship_change")},
{i18n.get_prompt("output_new_status")}
}}
``` 
{long_memory_section}
{self._get_initial_context_before_input(player_name, initial_context, i18n)}
{i18n.get_prompt("player_input_label", player_name=player_name, player_input=player_input)}
{i18n.get_prompt("player_input_instruction")}
{i18n.get_prompt("player_input_json")}
"""
        
        # 디버깅: long_memory_section이 실제로 포함되었는지 확인
        if self.state.long_memory and not long_memory_section:
            logger.error(f"⚠️ Warning: long_memory exists but long_memory_section is empty! (total_turns: {self.state.total_turns})")
        elif long_memory_section:
            logger.debug(f"✅ long_memory_section included in prompt (length: {len(long_memory_section)})")
        
        return prompt
    
    def _get_first_dialogue_emphasis(self, i18n) -> str:
        """처음 10턴 동안 초기 상황 설명의 중요성을 강조하는 지시사항"""
        if self.state.total_turns >= 10:
            return ""
        
        return f"""
{i18n.get_prompt("initial_situation_emphasis")}
"""
    
    def _get_initial_context_before_input(self, player_name: str, initial_context: str, i18n) -> str:
        """처음 10턴 동안 player_input 위에 초기 대화 세팅과 emphasis 추가"""
        if self.state.total_turns >= 10 or not initial_context:
            return ""
        
        emphasis = self._get_first_dialogue_emphasis(i18n)
        return f"""
{i18n.get_prompt("initial_situation_title")}
{initial_context}
{i18n.get_prompt("initial_situation_instruction", player_name=player_name)}{emphasis}
"""
    
    def _get_status_transition_instruction(self) -> str:
        """현재 상태에서 가능한 다음 상태 전환 지침"""
        current = self.state.relationship_status
        transitions = config.STATUS_TRANSITIONS.get(current, {})
        possible_next = transitions.get("to", [])
        
        if not possible_next:
            return ""
        
        # LLM 보고가 필요한 상태만 필터링: Lover, Fiancée, Partner, Master, Slave
        llm_states = [s for s in possible_next if s in ["Lover", "Fiancée", "Partner", "Master", "Slave"]]
        
        if not llm_states:
            return ""
        
        # 여러 상태로 갈 수 있을 때 명확하게 나열
        instruction = f"[전환 규칙] 당신은 현재 {current} 상태입니다. 다음 상태로 전환 가능합니다: {', '.join(llm_states)}. "
        instruction += "대화 맥락과 현재 감정 수치를 고려하여 가장 적합한 상태 하나만 선택하세요. 조건을 만족하는 여러 상태가 있을 수 있지만, 오직 하나만 선택해야 합니다.\n\n"
        
        # 각 상태별 조건과 키워드 나열
        state_descriptions = []
        for state in llm_states:
            if state == "Lover":
                state_descriptions.append("- Lover: I >= 80, T >= 60이고 '고백' 또는 '사랑' 키워드가 포함된 경우")
            elif state == "Fiancée":
                state_descriptions.append("- Fiancée: I >= 90, T >= 85이고 '약혼' 또는 '청혼' 키워드가 포함된 경우")
            elif state == "Partner":
                state_descriptions.append("- Partner: I가 최고치에 도달하고 '결혼' 또는 '부부' 키워드가 포함된 경우")
            elif state == "Master":
                state_descriptions.append("- Master: D >= 95, Dep >= 90이고 지배 관계가 확립된 경우")
            elif state == "Slave":
                state_descriptions.append("- Slave: D <= 5, Dep >= 100이고 복종 관계가 확립된 경우")
        
        instruction += "\n".join(state_descriptions)
        instruction += "\n\n위 조건 중 하나를 만족하고 대화 맥락이 적절하면 relationship_status_change를 true로 설정하고 new_status_name에 선택한 상태명을 보고하세요. 조건을 만족하지 않거나 전환할 맥락이 없으면 relationship_status_change를 false로 설정하세요."
        
        return instruction
    
    def _parse_json(self, text: str) -> Dict:
        """LLM 출력에서 JSON 추출 및 파싱"""
        
        # ==========================================================
        # 1. 원본 텍스트 전처리: BOM 및 모든 유니코드 공백 문자 제거
        # ==========================================================
        
        # 1-a. 코드블록 마크다운 제거 (기존 로직 유지)
        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'```\s*', '', text, flags=re.MULTILINE)
        
        # 1-b. UTF-8 BOM 문자 제거 (U+FEFF)
        BOM_CHAR = '\ufeff'
        text = text.lstrip(BOM_CHAR)
        
        # 1-c. 모든 종류의 공백 문자(줄바꿈, 탭, U+00A0 등)를 제거하고 앞뒤 공백 제거
        # - re.sub(r'\s', '', ...)는 모든 공백을 제거하므로, JSON 내부의 공백이 사라져서는 안 됨.
        # - 따라서, strip()으로 시작/끝 공백만 제거하는 것이 안전합니다.
        # - 하지만, char 2 오류는 시작 부분의 숨겨진 공백이므로, 시작 부분만 강력하게 제거합니다.
        text = text.lstrip()
        
        # 1-d. JSON 파싱 전 전처리: + 기호 제거 (JSON에서는 유효하지 않은 형식)
        text = re.sub(r'":\s*\+(\d+)', r'": \1', text)
        
        # ==========================================================
        # 2. 중괄호 매칭으로 유효 JSON 추출 (수정: 원본 텍스트 정제 후 시작)
        # ==========================================================
        
        depth = 0
        start = None
        
        # 모든 전처리를 마친 텍스트를 순회합니다.
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    # 첫 번째 유효한 '{'를 찾았을 때 시작 인덱스 설정
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                
                if depth == 0 and start is not None:
                    # 유효한 최상위 JSON 객체의 끝을 찾았을 때
                    candidate = text[start:i+1]
                    
                    # 디버깅: 파싱 시도 전후 로그
                    logger.debug(f"JSON 파싱 시도 중... (길이: {len(candidate)}자)")
                    
                    try:
                        parsed = json.loads(candidate)
                        logger.debug("JSON 파싱 성공!")
                        return parsed
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON 파싱 실패: {e}")
                        logger.warning(f"오류 위치: 문자 {e.pos}번째")
                        
                        # 오류가 났으므로, 다음 중괄호 쌍을 계속 찾습니다.
                        start = None  # 다음 '{'를 찾기 위해 start를 리셋
                        depth = 0
                        continue

        # ==========================================================
        # 3. JSON을 찾지 못한 경우 오류 로깅
        # ==========================================================
        
        logger.error("JSON을 찾을 수 없습니다.")
        logger.error(f"원본 텍스트 (처음 500자): {text[:500]}")
        raise ValueError("No valid JSON found")

    def _validate_response(self, data: Dict):
        """응답 유효성 검증"""
        required = ["thought", "speech", "emotion", "proposed_delta"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # proposed_delta 검증 및 정규화
        proposed_delta = data.get("proposed_delta", {})
        if not isinstance(proposed_delta, dict):
            raise ValueError(f"proposed_delta must be a dict, got {type(proposed_delta)}")
        
        # delta 값들을 정수로 변환하고 범위 제한 (-10 ~ +10)
        normalized_delta = {}
        for key in ["P", "A", "D", "I", "T", "Dep"]:
            value = proposed_delta.get(key, 0)
            original_value = value  # 디버깅용
            
            # 문자열인 경우 숫자로 변환 시도
            if isinstance(value, str):
                # + 기호만 제거 (음수는 - 기호가 그대로 유지됨)
                # 예: "+5" → "5" (양수), "-3" → "-3" (음수, 변화 없음)
                value = value.replace("+", "").strip()
                try:
                    value = int(value)  # int()는 "-3"을 음수 -3으로 정상 변환
                except ValueError:
                    logger.warning(f"proposed_delta.{key}를 숫자로 변환 실패: {original_value}, 0으로 설정")
                    value = 0
            elif not isinstance(value, (int, float)):
                logger.warning(f"proposed_delta.{key}가 숫자가 아님: {original_value}, 0으로 설정")
                value = 0
            else:
                value = int(value)
            
            # 범위 제한 (-10 ~ +10)
            value = max(-10, min(10, value))
            normalized_delta[key] = value
            
            # 디버깅: 값이 변경되었는지 확인
            if original_value != value and isinstance(original_value, (int, float, str)):
                logger.debug(f"proposed_delta.{key}: {original_value} → {value} (정규화됨)")
        
        data["proposed_delta"] = normalized_delta

    def _fallback_response(self, player_input: str) -> Dict:
        """파싱 실패 시 기본 응답"""
        return {
            "thought": "어... 뭐라고 해야 하지?",
            "speech": "아, 잠깐만... 무슨 말인지 다시 한번 말해줄래?",
            "emotion": "nervous",
            "visual_change_detected": False,
            "visual_prompt": "",
            "background": self.state.current_background,
            "reason": "",
            "final_delta": {},
            "gacha_tier": "normal",
            "multiplier": 1.0,
            "relationship_status": self.state.relationship_status,
            "mood": interpret_mood(self.state),
            "badges": self.state.badges.copy(),
            "stats": self.state.get_stats_dict(),
            "new_badge": None
        }
    
    def get_state(self) -> CharacterState:
        """현재 상태 반환"""
        return self.state
    
    def cleanup(self):
        """리소스 정리"""
        self.memory_manager.unload_model()

