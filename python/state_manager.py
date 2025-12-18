"""
Zeniji Emotion Simul - State Manager
캐릭터 상태 데이터 정의 및 관리
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class CharacterState:
    """
    6축 PAD/ITDep 벡터 + 관계 상태 + 트라우마 + 뱃지
    """
    # 6축 감정 벡터 (0-100)
    P: float = 50.0  # Pleasure (쾌락)
    A: float = 40.0  # Arousal (각성)
    D: float = 40.0  # Dominance (지배)
    I: float = 20.0  # Intimacy (친밀)
    T: float = 50.0  # Trust (신뢰)
    Dep: float = 0.0  # Dependency (의존)
    
    # 관계 상태
    relationship_status: str = "Stranger"
    
    # 트라우마 (Hidden, UI에 노출 안 함)
    trauma_level: float = 0.0
    
    # 뱃지 목록
    badges: List[str] = field(default_factory=list)
    
    # 턴 수
    total_turns: int = 0
    
    # 현재 배경 (장소/환경)
    current_background: str = "college library table, evening light"
    
    # 장기 기억 (LLM이 요약한 중요 기억)
    long_memory: str = ""
    
    def clamp(self):
        """모든 수치를 0-100 범위로 제한"""
        self.P = max(0.0, min(100.0, self.P))
        self.A = max(0.0, min(100.0, self.A))
        self.D = max(0.0, min(100.0, self.D))
        self.I = max(0.0, min(100.0, self.I))
        self.T = max(0.0, min(100.0, self.T))
        self.Dep = max(0.0, min(100.0, self.Dep))
    
    def apply_delta(self, delta: Dict[str, float], trauma_penalty: bool = True):
        """
        델타 적용 (트라우마 페널티 포함)
        """
        # 트라우마가 있으면 I, T의 긍정 델타에 페널티 적용
        if trauma_penalty and self.trauma_level > 0.0:
            for key in ["I", "T"]:
                if key in delta and delta[key] > 0:
                    delta[key] = delta[key] * (1.0 - self.trauma_level)
        
        # 델타 적용
        if "P" in delta:
            self.P += delta["P"]
        if "A" in delta:
            self.A += delta["A"]
        if "D" in delta:
            self.D += delta["D"]
        if "I" in delta:
            self.I += delta["I"]
        if "T" in delta:
            self.T += delta["T"]
        if "Dep" in delta:
            self.Dep += delta["Dep"]
        
        self.clamp()
    
    def add_badge(self, badge_name: str):
        """뱃지 추가 (중복 방지)"""
        if badge_name not in self.badges:
            # badges가 set인지 list인지 확인
            if isinstance(self.badges, set):
                self.badges.add(badge_name)
            else:
                # list인 경우
                self.badges.append(badge_name)
    
    def get_stats_dict(self) -> Dict[str, float]:
        """6축 수치를 딕셔너리로 반환"""
        return {
            "P": self.P,
            "A": self.A,
            "D": self.D,
            "I": self.I,
            "T": self.T,
            "Dep": self.Dep
        }
    
    def to_dict(self) -> Dict:
        """전체 상태를 딕셔너리로 변환 (UI용)"""
        return {
            "stats": self.get_stats_dict(),
            "relationship_status": self.relationship_status,
            "badges": self.badges,
            "total_turns": self.total_turns
            # trauma_level은 UI에 노출하지 않음
        }
    
    def from_dict(self, data: Dict):
        """딕셔너리에서 상태 복원"""
        if "stats" in data:
            stats = data["stats"]
            self.P = stats.get("P", 50.0)
            self.A = stats.get("A", 40.0)
            self.D = stats.get("D", 40.0)
            self.I = stats.get("I", 20.0)
            self.T = stats.get("T", 50.0)
            self.Dep = stats.get("Dep", 0.0)
        
        self.relationship_status = data.get("relationship_status", "Stranger")
        self.badges = data.get("badges", [])
        self.total_turns = data.get("total_turns", 0)
        self.trauma_level = data.get("trauma_level", 0.0)  # 저장은 하지만 UI에 안 보임
        self.current_background = data.get("current_background", "college library table, evening light")
        self.long_memory = data.get("long_memory", "")  # 장기 기억 복원
        self.clamp()


@dataclass
class DialogueTurn:
    """한 턴의 대화 기록"""
    turn_number: int
    player_input: str
    character_speech: str
    character_thought: str
    emotion: str
    visual_prompt: str = ""
    background: str = ""


class DialogueHistory:
    """대화 히스토리 관리 (최근 5턴)"""
    
    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self.turns: List[DialogueTurn] = []
    
    def add(self, turn: DialogueTurn):
        """턴 추가"""
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)
    
    def format_for_prompt(self) -> str:
        """프롬프트용 히스토리 포맷팅"""
        if not self.turns:
            return "(첫 대화입니다)"
        
        lines = []
        for i, turn in enumerate(self.turns):
            lines.append(f"[턴 {turn.turn_number}]")
            lines.append(f"플레이어: {turn.player_input}")
            lines.append(f"캐릭터 (대사): {turn.character_speech}")
            lines.append(f"캐릭터 (속마음): {turn.character_thought}")
            # visual_prompt는 마지막 1턴 것만 포함
            if i == len(self.turns) - 1 and turn.visual_prompt:
                lines.append(f"시각적 묘사: {turn.visual_prompt}")
            if turn.background:
                lines.append(f"배경: {turn.background}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_recent_turns(self, n: int = 3) -> List[DialogueTurn]:
        """최근 N턴 반환"""
        return self.turns[-n:] if len(self.turns) >= n else self.turns