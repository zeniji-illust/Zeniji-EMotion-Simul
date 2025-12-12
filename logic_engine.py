"""
Zeniji Emotion Simul - Logic Engine
게임 규칙 및 수치 처리 (가챠, 관계 전환, Mood 해석, Badge 판정)
"""

import random
from typing import Dict, Tuple, Optional
from state_manager import CharacterState
import config


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
    if P >= 70 and A >= 60 and D >= 60:
        return "Exuberant"
    
    # Relaxed: P+, A-, D+
    if P >= 60 and A < 40 and D >= 60:
        return "Relaxed"
    
    # Docile: P+, A-, D-
    if P >= 60 and A < 40 and D < 40:
        return "Docile"
    
    # Amazed: P+, A+, D-
    if P >= 60 and A >= 60 and D < 40:
        return "Amazed"
    
    # Hostile: P-, A+, D+
    if P < 30 and A >= 60 and D >= 60:
        return "Hostile"
    
    # Anxious: P-, A+, D-
    if P < 30 and A >= 60 and D < 40:
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


def check_status_transition(state: CharacterState) -> Tuple[bool, Optional[str]]:
    """
    관계 상태 전환 검사 (Python 기반)
    Returns: (전환 여부, 새 상태명)
    """
    # 1순위: 극단 상태 오버라이드 (Master/Slave)
    if state.D >= 95 and state.Dep >= 90:
        if state.relationship_status != "Master":
            return True, "Master"
    
    if state.D <= 5 and state.Dep >= 100:
        if state.relationship_status != "Slave":
            return True, "Slave"
    
    # 1순위: 이탈 검사 (Breakup/Divorce)
    if state.relationship_status in ["Girlfriend", "Master", "Slave"]:
        if state.I <= 30 or state.T <= 30:
            return True, "Breakup"
    
    if state.relationship_status in ["Wife", "Fiancée"]:
        if state.I <= 30 or state.T <= 30:
            return True, "Divorce"
    
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
    """
    if trauma_level <= 0.0:
        return ""
    
    if trauma_level <= 0.25:
        return "[지침] 신뢰(T) 회복에 미묘한 망설임을 보입니다. 호의에도 불구하고 눈치를 살피는 듯한 반응을 추가합니다."
    
    if trauma_level <= 0.50:
        return "[지침] 친밀(I)과 신뢰(T) 관련 델타는 즉시 무시하고 싶어 합니다. 칭찬을 거짓이나 조작으로 해석하는 뉘앙스를 반영해야 합니다."
    
    if trauma_level <= 0.75:
        return "[지침] 플레이어의 모든 긍정적인 행동을 다음 파국을 위한 빌드업으로 해석하며, 각성(A)이 급상승하여 패닉이나 도피적인 반응을 보입니다."
    
    return "[지침] I나 T 상승에 대한 반응이 거의 없습니다. 냉소적이거나 자포자기하는 듯한 어투를 사용하여, 관계 회복이 거의 불가능함을 암시해야 합니다."


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

