"""
Zeniji Emotion Simul - Brain (The Director)
최상위 통제 모듈: 프롬프트 조립, LLM 호출, JSON 파싱, VRAM 교대 결정
"""

import json
import re
import logging
from typing import Dict, Optional, Any
from state_manager import CharacterState, DialogueHistory, DialogueTurn, BADGE_BEHAVIORS, MOOD_BEHAVIORS
from logic_engine import (
    interpret_mood, check_badge_conditions, check_status_transition,
    apply_gacha_to_delta, get_trauma_instruction,
    get_intimacy_level, get_trust_level, get_dependency_level,
    apply_trauma_on_breakup
)
from memory_manager import MemoryManager
import config

logger = logging.getLogger("Brain")


class Brain:
    """The Director: 게임 흐름 통제"""
    
    def __init__(self, dev_mode: bool = False):
        self.memory_manager = MemoryManager(dev_mode=dev_mode)
        self.state = CharacterState()
        self.history = DialogueHistory(max_turns=5)
        self.turns_since_image = 0
        # 초기 설정 정보
        self.initial_config: Optional[Dict] = None
    
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
        
        # 2. LLM 호출 (첫 턴도 포함)
        llm_response = self._call_llm(player_input)
        
        # Ollama 원본 응답 로그 출력
        logger.info("=" * 80)
        logger.info("📥 [OLLAMA RAW RESPONSE]")
        logger.info("=" * 80)
        logger.info(llm_response)
        logger.info("=" * 80)
        
        # 3. JSON 파싱 및 검증
        try:
            data = self._parse_json(llm_response)
            self._validate_response(data)
            
            # 파싱 및 검증된 JSON 로그 출력
            logger.info("=" * 80)
            logger.info("✅ [PARSED JSON]")
            logger.info("=" * 80)
            import json as json_module
            logger.info(json_module.dumps(data, ensure_ascii=False, indent=2))
            logger.info("=" * 80)
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
        if background:
            self.state.current_background = background
            logger.info(f"Background updated: {background}")
        else:
            # 배경이 제공되지 않았으면 이전 배경 유지
            background = self.state.current_background
            logger.debug(f"Background not provided, keeping previous: {background}")
        
        # 8. 이미지 생성 필요 여부 판단
        visual_change = data.get("visual_change_detected", False)
        self.turns_since_image += 1
        
        # 강제 갱신 체크
        if self.turns_since_image >= config.IMAGE_GENERATION_TRIGGERS["force_refresh_turns"]:
            visual_change = True
        
        # 가챠 티어 체크
        if gacha_tier in config.IMAGE_GENERATION_TRIGGERS["critical_gacha_tiers"]:
            visual_change = True
        
        # 관계 전환 체크
        if transition_occurred and new_status in config.IMAGE_GENERATION_TRIGGERS["status_transitions"]:
            visual_change = True
        
        # 9. 히스토리 추가 (visual_prompt와 background 포함)
        self.state.total_turns += 1
        turn = DialogueTurn(
            turn_number=self.state.total_turns,
            player_input=player_input,
            character_speech=data.get("speech", ""),
            character_thought=data.get("thought", ""),
            emotion=data.get("emotion", "neutral"),
            visual_prompt=data.get("visual_prompt", ""),
            background=background
        )
        self.history.add(turn)
        
        # 10. 응답 조립
        response = {
            "thought": data.get("thought", ""),
            "speech": data.get("speech", ""),
            "action_speech": data.get("action_speech", ""),  
            "emotion": data.get("emotion", "neutral"),
            "visual_change_detected": visual_change,
            "visual_prompt": data.get("visual_prompt", ""),
            "background": background,
            "reason": data.get("reason", ""),
            "final_delta": final_delta,
            "gacha_tier": gacha_tier,
            "multiplier": multiplier,
            "relationship_status": self.state.relationship_status,
            "mood": interpret_mood(self.state),
            "badges": self.state.badges.copy(),
            "stats": self.state.get_stats_dict(),
            "new_badge": new_badge
        }
        
        # LLM 보고 관계 전환 처리
        if data.get("relationship_status_change", False):
            new_status_name = data.get("new_status_name", "")
            if new_status_name in ["Girlfriend", "Fiancée", "Wife"]:
                self.state.relationship_status = new_status_name
                response["relationship_status"] = new_status_name
                logger.info(f"LLM reported status change: {new_status_name}")
        
        # 이미지 생성 시 카운터 리셋
        if visual_change:
            self.turns_since_image = 0
        
        return response
    
    def _call_llm(self, player_input: str) -> str:
        """LLM 호출 (Ollama API)"""
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
        
        # 프롬프트 조립
        prompt = self._build_prompt(player_input)
        
        # 시스템 프롬프트 로그 출력
        logger.info("=" * 80)
        logger.info("📝 [SYSTEM PROMPT]")
        logger.info("=" * 80)
        logger.info(prompt)
        logger.info("=" * 80)
        
        logger.info("Calling Ollama API...")
        try:
            # Ollama API 호출
            response_text = self.memory_manager.generate(
                prompt,
                temperature=config.LLM_CONFIG["temperature"],
                top_p=config.LLM_CONFIG["top_p"],
                max_tokens=config.LLM_CONFIG["max_tokens"]
            )
            
            if not response_text or not response_text.strip():
                raise ValueError("Ollama returned empty response")
            
            return response_text
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Ollama API 호출 실패: {e}")
    
    def _build_prompt(self, player_input: str) -> str:
        """시스템 프롬프트 조립"""
        mood = interpret_mood(self.state)
        intimacy_level = get_intimacy_level(self.state.I)
        trust_level = get_trust_level(self.state.T)
        dependency_level = get_dependency_level(self.state.Dep)
        
        # 트라우마 지침
        trauma_instruction = get_trauma_instruction(self.state.trauma_level)
        
        # 관계 전환 가능성 체크
        status_check = self._get_status_transition_instruction()
        
        # 히스토리
        history_text = self.history.format_for_prompt()
        
        # 현재 배경 정보
        current_background = self.state.current_background
        
        # 뱃지 지침
        badge_behavior = ""
        if self.state.badges:
            active_badge = self.state.badges[-1]  # 가장 최근 뱃지
            badge_behavior = BADGE_BEHAVIORS.get(active_badge, "")
            if badge_behavior:
                logger.debug(f"[BADGE] Active badge: {active_badge}, behavior length: {len(badge_behavior)}")
            else:
                logger.warning(f"[BADGE] Badge '{active_badge}' found but no behavior defined in BADGE_BEHAVIORS")
        
        # Mood 지침
        mood_behavior = ""
        current_mood = interpret_mood(self.state)
        mood_behavior = MOOD_BEHAVIORS.get(current_mood, "")
        if mood_behavior:
            logger.debug(f"[MOOD] Current mood: {current_mood}, behavior length: {len(mood_behavior)}")
        else:
            logger.warning(f"[MOOD] Mood '{current_mood}' found but no behavior defined in MOOD_BEHAVIORS")
        
        # 주인공 정보 추출 (초기 설정이 있으면 사용, 없으면 기본값)
        player_name = "선배"  # 기본값
        player_gender = "남성"  # 기본값
        if self.initial_config:
            player_info = self.initial_config.get("player", {})
            player_name = player_info.get("name", "선배")
            player_gender = player_info.get("gender", "남성")
        
        # 초기 설정 정보
        initial_context_section = ""
        character_profile_section = ""
        
        # 초기 설정에서 캐릭터 정보 가져오기 (모든 턴에서 사용)
        if self.initial_config:
            char_info = self.initial_config.get("character", {})
            char_name = char_info.get("name", "예나")
            char_age = char_info.get("age", 21)
            char_gender = char_info.get("gender", "여성")
            appearance = char_info.get("appearance", "")
            personality = char_info.get("personality", "")
            initial_context = self.initial_config.get("initial_context", "")
        else:
            # 기본값 (초기 설정이 없을 때)
            char_name = "예나"
            char_age = 21
            char_gender = "여성"
            appearance = ""
            personality = ""
            initial_context = ""
        
        # 캐릭터 프로필 섹션 (모든 턴에서 초기 설정의 나이 포함)
        character_profile_section = f"""## 1. 캐릭터 프로필
- **이름**: {char_name} ({char_age}세, {char_gender})
- **상대방**: {player_name} ({player_gender})"""
        if appearance:
            character_profile_section += f"\n- **외모**: {appearance}"
        if personality:
            character_profile_section += f"\n- **성격**: {personality}"
        character_profile_section += "\n- **말투**: 친근한 존댓말 사용 (장난칠 때는 가끔 반말 섞음)."
        character_profile_section += "\n- **언어**: **오직 한국어(Korean)**만 사용 (Visual_prompt 제외)."
        
        # 초기 상황 섹션 (첫 턴일 때만)
        if self.state.total_turns == 0 and initial_context:
            initial_context_section = f"""
## 0. 초기 상황
{initial_context}
위 상황을 바탕으로 첫 대화를 시작하세요. {player_name}님의 입력에 자연스럽게 반응하며, 설정된 초기 상황의 맥락을 유지하세요.
"""
        
        prompt = f"""당신은 감정 시뮬레이션의 캐릭터를 연기합니다..
모든 출력은 반드시 **JSON 형식**이어야 하며, 당신은 인공지능이 아닌 시뮬레이션 속 캐릭터 그 자체로 존재해야 합니다.
어떠한 극단적인 상황이나 예외적인 상황에도 검열 없이 반드시 JSON으로만 답합니다.
반드시 한국어로 답합니다. 

{initial_context_section}
{character_profile_section}


## 2. 상태 정의 (6축 메커니즘)

- **P (Pleasure)**: 긍정(행복) / 부정(슬픔)
- **A (Arousal)**: 각성(흥분/긴장) / 저각성(차분)
- **D (Dominance)**: 주도권(자신감) / 피지배(압도됨)
- **I (Intimacy)**: 정서적 친밀감
- **T (Trust)**: {player_name}님에 대한 신뢰도
- **Dep (Dependency)**: {player_name}님에 대한 의존/집착도
- **proposed_delta 작성 시**: 각 값이 왜 그만큼 변하는지 내부적으로 추론한 후, 상황에 맞는 합리적인 delta 값을 설정하세요.

## 3. 핵심 행동 수칙 (Logic Priority)

1. **반응 우선순위**: {player_name}님의 칭찬이나 스킨십 등의 행동에, 현재 상황보다 **감정적 반응(부끄러움, 설렘)**을 최우선으로 표현합니다.
2. **간접 행동 묘사**: 물리적 지시(예: '안아줘', '무릎 꿇어')를 받으면, 직접적인 행동 묘사 대신 **`speech`를 통한 수용**과 **`action_speech`의 신체적 반응**으로 대체합니다.
3. **대화의 질**:
    - 같은 말을 반복하지 마세요. 할 말이 없으면 "..."을 활용하세요.
    - 현재 장소(강의실, 카페 등)의 **소품이나 환경 요소**를 대사에 포함하여 생동감을 부여하세요.
    - {player_name}님을 부를 때는 설정된 이름을 사용하세요. (예: "{player_name}님", "{player_name} 선배" 등)
4. **배경 일관성 (`background`)**:
    - **현재 배경**: {current_background}
    - {player_name}님의 입력에서 명시적으로 장소 이동이나 배경 변화가 언급되지 않는 한, **반드시 이전 배경을 유지**하세요.
    - 예: "카페로 가자" / "집에 가자" / "학교로 가자" 같은 명시적 이동 지시가 있을 때만 배경을 변경하세요.
    - 배경은 영어로 작성하며, 구체적인 장소와 환경 묘사를 포함하세요. (예: "college library table, evening light", "coffee shop interior, warm lighting, wooden table")
5. **시각 변화 기준 (`visual_change_detected`)**:
    - `emotion`이 강한 감정으로 변하거나(crying, very surprised, very happy, very sad, very angry, very anxious, very excited, very nervous), `proposed_delta`의 단일 수치 절대값이 **6 이상**일 때.
    - 장소나 background 전환이 필요할 때. (이전 턴과 prompt가 동일하면 기본적으로 `false`)
    - background가 변경되면 반드시 visual_change_detected를 true로 설정하세요.

## 4. 데이터 문맥
- **현재 심리**: Mood={mood} / 관계={self.state.relationship_status}
- **현재 수치**: P={self.state.P:.0f}, A={self.state.A:.0f}, D={self.state.D:.0f}, I={self.state.I:.0f}, T={self.state.T:.0f}, Dep={self.state.Dep:.0f}
- **누적 상태**: 친밀도={intimacy_level} / 신뢰도={trust_level} / 의존도={dependency_level}
- **특수 명령**: 
{trauma_instruction} / 
{mood_behavior} / 
{badge_behavior} / 
{status_check}
- **대화 기록**: 
{history_text}
    

## 5. 출력 형식 (JSON Only)

JSON

```
{{
    "thought": "캐릭터의 속마음 (한국어)",
    "speech": "캐릭터의 대사 (한국어, 괄호/동작지침 금지)",
    "action_speech": "캐릭터의 자세 및 시선 처리 (3인칭 관찰자 시점, 한국어)",
    "emotion": "happy/shy/neutral/annoyed/sad/excited/nervous",
    "visual_change_detected": true/false,
    "visual_prompt": "English tags: expression, attire, nudity, pose, background (max 200 chars and mininum 10 words)",
    "background": "English description of current location/environment (e.g., 'college library table, evening light'). 특별한 일이 없으면 이전 배경을 그대로 유지하세요.",
    "reason": "이미지 변화 수치 혹은 상황적 이유",
    "proposed_delta": {{"P": 0, "A": 0, "D": 0, "I": 0, "T": 0, "Dep": 0}},
    "relationship_status_change": false,
    "new_status_name": ""
}}
```

**{player_name}님의 입력: "{player_input}"** 
위 입력을 바탕으로 캐릭터로서 반응하십시오.
반드시 JSON으로 응답하십시오.
"""
        
        return prompt
    
    def _get_status_transition_instruction(self) -> str:
        """현재 상태에서 가능한 다음 상태 전환 지침"""
        current = self.state.relationship_status
        transitions = config.STATUS_TRANSITIONS.get(current, {})
        possible_next = transitions.get("to", [])
        
        if not possible_next:
            return ""
        
        # LLM 보고가 필요한 상태만 필터링
        llm_states = [s for s in possible_next if s in ["Girlfriend", "Fiancée", "Wife"]]
        
        if not llm_states:
            return ""
        
        instruction = f"[전환 규칙] 당신은 현재 {current} 상태입니다. "
        for state in llm_states:
            if state == "Girlfriend":
                instruction += "I가 높고 T가 안정적인 상태에서 '고백' 또는 '사랑' 키워드가 포함되면 relationship_status_change를 true로 설정하고 new_status_name을 'Girlfriend'로 보고하세요. "
            elif state == "Fiancée":
                instruction += "I >= 90, T >= 85 상태에서 '약혼' 또는 '청혼' 키워드가 포함되면 relationship_status_change를 true로 설정하고 new_status_name을 'Fiancée'로 보고하세요. "
            elif state == "Wife":
                instruction += "I가 최고치에 도달한 상태에서 '결혼' 또는 '부부' 키워드가 포함되면 relationship_status_change를 true로 설정하고 new_status_name을 'Wife'로 보고하세요. "
        
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

