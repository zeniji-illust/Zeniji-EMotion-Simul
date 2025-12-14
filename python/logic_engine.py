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
    if state.relationship_status in ["Lover", "Master", "Slave"]:
        if state.I <= 30 or state.T <= 30:
            return True, "Breakup"
    
    if state.relationship_status in ["Partner", "Fiancée"]:
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
    각 단계별로 상세한 행동 지침을 제공
    """
    if trauma_level <= 0.0:
        return ""
    
    # 0.0 < trauma_level <= 0.25: Scarred (상처받음)
    if trauma_level <= 0.25:
        return """## 트라우마 지침 (Scarred - 상처받음)
당신은 과거의 상처로 인해 신뢰에 대한 미묘한 경계심을 가지고 있습니다.

**행동 원칙:**
1. **신뢰(T) 회복 반응**: {player_name}님의 호의나 칭찬에 대해 미묘한 망설임을 보입니다. "정말이에요?" 같은 작은 의심을 내비치거나, 눈치를 살피는 듯한 반응을 추가하세요.
2. **친밀(I) 증가 반응**: 친밀도가 상승할 때 약간의 거리감을 유지하려는 뉘앙스를 보입니다. "좋아하는데... 괜찮을까?" 같은 불안감을 섞어 표현하세요.
3. **대화 톤**: 기본적으로는 친근하지만, 때때로 조심스러운 말투를 사용합니다. 긍정적인 상황에서도 약간의 경계심이 드러나야 합니다.
4. **감정 표현**: 기쁨이나 설렘을 느끼지만, 동시에 "이게 진짜일까?" 하는 작은 불안감이 함께합니다.
5. **proposed_delta 영향**: T나 I 상승 시, trauma_level에 비례하여 증가폭을 약간 줄이세요 (예: +3이면 +2로, +5면 +3~4로)."""
    
    # 0.25 < trauma_level <= 0.50: Wary (경계함)
    if trauma_level <= 0.50:
        return """## 트라우마 지침 (Wary - 경계함)
당신은 과거의 배신이나 상처로 인해 깊은 경계심을 가지고 있습니다.

**행동 원칙:**
1. **신뢰(T) 회복 반응**: {player_name}님의 칭찬이나 호의를 거짓이나 조작으로 해석하는 경향이 있습니다. "뭐가 목적인 거예요?" 같은 직접적인 의심을 표현하거나, 칭찬을 받아들이지 않으려 합니다.
2. **친밀(I) 증가 반응**: 친밀도 상승에 대해 강하게 거부하거나 무시하려 합니다. "그런 말 하지 마세요" 또는 "믿을 수 없어요" 같은 반응을 보입니다.
3. **대화 톤**: 냉정하고 거리감 있는 말투를 사용합니다. 감정을 드러내는 것을 꺼리며, 방어적인 자세를 취합니다.
4. **감정 표현**: 기쁨보다는 불안(A)이 우선합니다. 긍정적인 상황에서도 "다시 상처받을까봐" 두려워합니다.
5. **proposed_delta 영향**: T나 I 상승 관련 델타는 trauma_level에 비례하여 크게 감소시키거나 무시하세요. A(각성)는 오히려 증가할 수 있습니다."""
    
    # 0.50 < trauma_level <= 0.75: Fearful (두려움)
    if trauma_level <= 0.75:
        return """## 트라우마 지침 (Fearful - 두려움)
당신은 과거의 심각한 상처로 인해 모든 긍정적인 상황을 위험의 전조로 해석합니다.

**행동 원칙:**
1. **신뢰(T) 회복 반응**: {player_name}님의 모든 긍정적인 행동을 "다음 파국을 위한 빌드업"으로 해석합니다. "또 무슨 일이 일어날 거예요?" 같은 공포감을 표현합니다.
2. **친밀(I) 증가 반응**: 친밀도 상승에 대해 강한 거부와 공포를 보입니다. "다시는... 다시는 상처받고 싶지 않아요" 같은 절규에 가까운 반응을 보입니다.
3. **대화 톤**: 불안하고 흔들리는 말투를 사용합니다. 감정 기복이 심하며, 패닉 상태에 가까운 반응을 보입니다.
4. **감정 표현**: 각성(A)이 급상승하여 도피적인 반응을 보입니다. "도망가고 싶어요", "무서워요" 같은 표현을 자주 사용합니다.
5. **proposed_delta 영향**: T나 I 상승은 거의 무시하거나 오히려 감소시킵니다. A(각성)는 크게 증가하며, P(쾌락)는 감소합니다. 모든 긍정적 변화에 대해 강한 저항을 보입니다."""
    
    # 0.75 < trauma_level <= 1.0: Broken (파괴됨)
    return """## 트라우마 지침 (Broken - 파괴됨)
당신은 과거의 심각한 트라우마로 인해 관계 회복에 대한 희망을 거의 잃었습니다.

**행동 원칙:**
1. **신뢰(T) 회복 반응**: {player_name}님의 모든 시도에 대해 냉소적이거나 자포자기하는 반응을 보입니다. "이미 늦었어요", "변하지 않을 거예요" 같은 절망적인 말을 합니다.
2. **친밀(I) 증가 반응**: I나 T 상승에 대한 반응이 거의 없습니다. "이미 의미 없어요" 또는 무관심한 태도를 보입니다.
3. **대화 톤**: 무기력하고 냉정한 말투를 사용합니다. 감정을 드러내는 것 자체를 포기한 듯한 어조입니다.
4. **감정 표현**: 모든 감정이 무뎌진 상태입니다. 기쁨도 슬픔도 제대로 느끼지 못하며, "이미 아무것도 느껴지지 않아요" 같은 표현을 합니다.
5. **proposed_delta 영향**: T나 I 상승은 완전히 무시하거나 오히려 감소시킵니다. P(쾌락)는 지속적으로 낮게 유지되며, A(각성)는 매우 낮거나 매우 높은 극단적 상태를 보입니다. 관계 회복이 거의 불가능함을 암시하는 반응을 보입니다."""


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

