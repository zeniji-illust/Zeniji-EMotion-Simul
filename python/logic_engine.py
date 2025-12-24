"""
Zeniji Emotion Simul - Logic Engine
게임 규칙 및 수치 처리 (가챠, 관계 전환, Mood 해석, Badge 판정)
"""

import random
from typing import Dict, Tuple, Optional
from state_manager import CharacterState
import config
from i18n import get_i18n


def roll_gacha_v3() -> Tuple[str, float]:
    """
    가챠 V3: 1000분위 주사위로 배율 결정
    Returns: (tier_name, multiplier)
    """
    roll = random.randint(1, 1000)
    
    cumulative = 0
    for tier_name, tier_data in config.GACHA_TIERS.items():
        prob = tier_data["prob"]
        cumulative += int(prob * 1000)
        if roll <= cumulative:
            return tier_name, tier_data["multiplier"]
    
    return "normal", 1.0


def apply_gacha_to_delta(proposed_delta: Dict[str, float]) -> Tuple[Dict[str, float], str, float]:
    """
    proposed_delta에 가챠 배율 적용
    Returns: (final_delta, tier_name, multiplier)
    """
    tier_name, multiplier = roll_gacha_v3()
    
    final_delta = {}
    for key, value in proposed_delta.items():
        final_delta[key] = value * multiplier
    
    return final_delta, tier_name, multiplier


def interpret_mood(state: CharacterState) -> str:
    """
    PAD 조합으로 Mood 해석
    """
    P, A, D = state.P, state.A, state.D
    
    # Exuberant: P+, A+, D+
    if P >= 70 and A >= 60 and D >= 50:
        return "Exuberant"
    
    # Relaxed: P+, A-, D+
    if P >= 60 and A < 40 and D >= 60:
        return "Relaxed"
    
    # Docile: P+, A-, D-
    if P >= 60 and A < 40 and D < 40:
        return "Docile"
    
    # Amazed: P+, A+, D-
    if P >= 60 and A >= 60 and D < 50:
        return "Amazed"
    
    # Hostile: P-, A+, D+
    if P < 30 and A >= 60 and D >= 50:
        return "Hostile"
    
    # Anxious: P-, A+, D-
    if P < 30 and A >= 60 and D < 50:
        return "Anxious"
    
    # Bored: P-, A-, D+
    if P < 30 and A < 40 and D >= 60:
        return "Bored"
    
    # Depressed: P-, A-, D-
    if P < 30 and A < 40 and D < 40:
        return "Depressed"
    
    return "Neutral"


def check_badge_conditions(state: CharacterState) -> Optional[str]:
    """
    현재 수치로 획득 가능한 뱃지 검사
    Returns: 뱃지 이름 또는 None
    """
    P, A, D, I, T, Dep = state.P, state.A, state.D, state.I, state.T, state.Dep
    
    # 카테고리 1: 지배와 소유
    if D > 80 and I > 70 and T < 30:
        return "The Warden"
    if P > 80 and D > 90 and I < 50:
        return "Sadistic Ruler"
    if I > 90 and D > 60 and Dep < 20:
        return "The Savior"
    
    # 카테고리 2: 의존과 복종
    if D <= 5 and Dep > 95 and A < 20:
        return "Broken Doll"
    if T >= 100 and I > 80:
        return "The Cultist"
    if Dep > 90 and A > 80 and P < 30:
        return "Separation Anxiety"
    
    # 카테고리 3: 불안과 애증
    if I > 95 and Dep > 95 and T < 20:
        return "Classic Yandere"
    if I > 80 and P < 10 and A > 90:
        return "The Avenger"
    if 45 <= T <= 55 and 45 <= I <= 55 and A > 80:
        return "Ambivalence"
    
    # 카테고리 4: 왜곡된 특수 상태
    if P < 30 and I > 80 and D < 10:
        return "Stockholm"
    if 45 <= P <= 55 and A < 5 and 45 <= D <= 55 and I < 5 and T < 5:
        return "Void"
    if P > 95 and A > 95:
        return "Euphoric Ruin"
    
    return None


def validate_status_transition_condition(state: CharacterState, current_status: str, target_status: str) -> bool:
    """
    상태 전환이 수치 조건을 만족하는지 검증
    Returns: 조건 만족 여부
    """
    transitions = config.STATUS_TRANSITIONS.get(current_status, {})
    possible_next = transitions.get("to", [])
    
    # 전환 가능한 상태 목록에 있는지 확인
    if target_status not in possible_next:
        return False
    
    # Slave는 특수 처리 (D <= 5, Dep >= 100)
    if target_status == "Slave":
        return state.D <= 5 and state.Dep >= 100
    
    # Master는 특수 처리 (D >= 95, Dep >= 90)
    if target_status == "Master":
        return state.D >= 95 and state.Dep >= 90
    
    # 다른 상태들은 목적지 상태로 가기 위한 조건 확인
    # Lover: I >= 80, T >= 60
    if target_status == "Lover":
        return state.I >= 80 and state.T >= 60
    
    # Fiancée: I >= 90, T >= 85
    if target_status == "Fiancée":
        return state.I >= 90 and state.T >= 85
    
    # Partner: 조건 없음 (항상 가능)
    if target_status == "Partner":
        return True
    
    return False


def check_status_transition(state: CharacterState) -> Tuple[bool, Optional[str]]:
    """
    관계 상태 전환 검사 (Python 기반)
    Returns: (전환 여부, 새 상태명)
    Note: Master/Slave는 LLM 판단으로 이동
    """
    # 1순위: 이탈 검사 (Breakup/Divorce)
    # Partner/Fiancée/Lover 상태에서만 breakup 조건 체크
    if state.relationship_status in ["Partner", "Fiancée", "Lover"]:
        if state.I <= 30 or state.T <= 30:
            # Partner/Fiancée는 Divorce, Lover는 Breakup
            if state.relationship_status in ["Partner", "Fiancée"]:
                return True, "Divorce"
            else:  # Lover
                return True, "Breakup"
    
    # 3순위: Tempted 검사
    if state.relationship_status == "Acquaintance":
        if state.P >= 80 and state.A >= 80 and state.D <= 40:
            return True, "Tempted"
    
    # 기초 상태 전환
    if state.relationship_status == "Stranger" and state.I >= 40:
        return True, "Acquaintance"
    
    if state.relationship_status == "Acquaintance" and state.I >= 60:
        # Tempted는 위에서 이미 검사했으므로 여기서는 그냥 Acquaintance 유지
        pass
    
    return False, None


def apply_trauma_on_breakup(state: CharacterState):
    """
    Breakup/Divorce 시 트라우마 증가
    """
    if state.relationship_status in ["Breakup", "Divorce"]:
        # 트라우마 증가 (0.25 단위)
        state.trauma_level = min(1.0, state.trauma_level + 0.25)
        
        # 관계 상태 초기화
        if state.relationship_status == "Breakup":
            if state.I < 40:
                state.relationship_status = "Stranger"
            else:
                state.relationship_status = "Acquaintance"
        else:  # Divorce
            state.relationship_status = "Stranger"
        
        # I, T 초기값 하향 조정 (트라우마 비례)
        state.I = max(0.0, state.I * (1.0 - state.trauma_level))
        state.T = max(0.0, state.T * (1.0 - state.trauma_level))
        state.clamp()


def get_trauma_instruction(trauma_level: float) -> str:
    """
    트라우마 레벨에 따른 LLM 연기 지침 반환
    각 단계별로 상세한 행동 지침을 제공
    """
    if trauma_level <= 0.0:
        return ""
    
    i18n = get_i18n()
    
    # 0.0 < trauma_level <= 0.25: Scarred (상처받음)
    if trauma_level <= 0.25:
        return f"""{i18n.get_prompt("trauma_title_scarred")}
{i18n.get_prompt("trauma_desc_scarred")}

{i18n.get_prompt("trauma_behavior_title")}
{i18n.get_prompt("trauma_trust_reaction_scarred")}
{i18n.get_prompt("trauma_intimacy_reaction_scarred")}
{i18n.get_prompt("trauma_tone_scarred")}
{i18n.get_prompt("trauma_emotion_scarred")}
{i18n.get_prompt("trauma_delta_scarred")}"""
    
    # 0.25 < trauma_level <= 0.50: Wary (경계함)
    if trauma_level <= 0.50:
        return f"""{i18n.get_prompt("trauma_title_wary")}
{i18n.get_prompt("trauma_desc_wary")}

{i18n.get_prompt("trauma_behavior_title")}
{i18n.get_prompt("trauma_trust_reaction_wary")}
{i18n.get_prompt("trauma_intimacy_reaction_wary")}
{i18n.get_prompt("trauma_tone_wary")}
{i18n.get_prompt("trauma_emotion_wary")}
{i18n.get_prompt("trauma_delta_wary")}"""
    
    # 0.50 < trauma_level <= 0.75: Fearful (두려움)
    if trauma_level <= 0.75:
        return f"""{i18n.get_prompt("trauma_title_fearful")}
{i18n.get_prompt("trauma_desc_fearful")}

{i18n.get_prompt("trauma_behavior_title")}
{i18n.get_prompt("trauma_trust_reaction_fearful")}
{i18n.get_prompt("trauma_intimacy_reaction_fearful")}
{i18n.get_prompt("trauma_tone_fearful")}
{i18n.get_prompt("trauma_emotion_fearful")}
{i18n.get_prompt("trauma_delta_fearful")}"""
    
    # 0.75 < trauma_level <= 1.0: Broken (파괴됨)
    return f"""{i18n.get_prompt("trauma_title_broken")}
{i18n.get_prompt("trauma_desc_broken")}

{i18n.get_prompt("trauma_behavior_title")}
{i18n.get_prompt("trauma_trust_reaction_broken")}
{i18n.get_prompt("trauma_intimacy_reaction_broken")}
{i18n.get_prompt("trauma_tone_broken")}
{i18n.get_prompt("trauma_emotion_broken")}
{i18n.get_prompt("trauma_delta_broken")}"""


def get_intimacy_level(I: float) -> str:
    """친밀도 7단계 레벨"""
    if I >= 96:
        return "Lv 7 (96~100): 맹목적 애정"
    if I >= 81:
        return "Lv 6 (81~95): 깊은 애정"
    if I >= 71:
        return "Lv 5 (71~80): 강한 호감"
    if I >= 51:
        return "Lv 4 (51~70): 안정적 관계"
    if I >= 31:
        return "Lv 3 (31~50): 친근함"
    if I >= 11:
        return "Lv 2 (11~30): 아는 사이"
    return "Lv 1 (0~10): 완전한 냉담"


def get_trust_level(T: float) -> str:
    """신뢰도 7단계 레벨"""
    if T >= 96:
        return "Lv 7 (96~100): 무조건적 숭배"
    if T >= 81:
        return "Lv 6 (81~95): 절대적 신뢰"
    if T >= 71:
        return "Lv 5 (71~80): 강한 신뢰"
    if T >= 51:
        return "Lv 4 (51~70): 균형적 신뢰"
    if T >= 31:
        return "Lv 3 (31~50): 약한 신뢰"
    if T >= 11:
        return "Lv 2 (11~30): 의심"
    return "Lv 1 (0~10): 극심한 경계"


def get_dependency_level(Dep: float) -> str:
    """의존도 7단계 레벨"""
    if Dep >= 96:
        return "Lv 7 (96~100): 완전한 집착"
    if Dep >= 81:
        return "Lv 6 (81~95): 강한 의존"
    if Dep >= 71:
        return "Lv 5 (71~80): 높은 의존"
    if Dep >= 51:
        return "Lv 4 (51~70): 상호 의존"
    if Dep >= 31:
        return "Lv 3 (31~50): 약한 의존"
    if Dep >= 11:
        return "Lv 2 (11~30): 독립적"
    return "Lv 1 (0~10): 완전한 독립"

