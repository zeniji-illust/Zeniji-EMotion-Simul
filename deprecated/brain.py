"""
Emotion Simulation Dialogue Brain (v3.0 Director)

- PAD/히든 스탯 관리
- Qwen LLM으로 delta 추론
- Scene Detection 플래그
- VRAM Shuttle (LLM 사용 후 GPU 메모리 비움)
"""

import json
import logging
import time
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List
import torch

# 프로젝트 루트 추가 (model_load import)
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO,
)
logger = logging.getLogger("EmotionSimul")


# ------------------------------------------------------------
# 설정 / 프롬프트
# ------------------------------------------------------------

CHARACTER_PROFILE = """
이름: 설연 (21세, 대학교 후배)
외모: 단발 보브컷, 갈색 눈, 작고 귀여운 얼굴, 163cm
성격:
- 평소 밝고 활발하나 플레이어에게 호감이 있어 수줍음이 많음
- 감정 표현이 솔직하고 리액션이 큼
- 공감 능력이 뛰어남
말투:
- 친근한 반말 사용 (가끔 장난식 존댓말)
- 당황하면 말이 빨라지거나 더듬음
- 감탄사: "헐", "대박", "진짜?"
""".strip()

SYSTEM_PROMPT_HYBRID = """你现在扮演一个韩国恋爱模拟游戏中的女主角'Seol-yeon'。
请根据玩家的输入，通过缜密的逻辑推断角色的情感变化和数值波动。

## 角色设定 (Character Profile)
{character_profile}

## 数值系统定义 (Stat Rules for Inference)
请根据对话内容推断以下数值的变化量 (delta)，范围通常在 -10 到 +10 之间：
1. Pleasure (P): 满足感/开心
2. Arousal (A): 紧张/刺激
3. Dominance (D): 主导权
4. Intimacy: 心理距离
5. Trust: 信任程度

## 视觉判断 (scene_change_detected)
장소/복장 변화 또는 극단적 감정 폭발(울음/박장대소)일 때만 true, 그 외 false.

## 输出规则 (Output Rules)
1) speech: 한국어 구어체
2) thought: 한국어 반말 독백
3) choices: 플레이어(남자)의 다음 대사 3개
4) delta: 5개 수치 모두 정수 변화량
5) 반드시 순수 JSON만 출력
"""

USER_PROMPT_TEMPLATE = """## 현재 상태
- 관계 단계: {relationship}
- 현재 기분: {mood}
- 턴 수: {turn_number}

## 현재 수치 (0-100)
- P(기분): {pleasure:.0f}
- A(각성): {arousal:.0f}
- D(주도): {dominance:.0f}
- 친밀도: {intimacy:.0f}
- 신뢰도: {trust:.0f}

## 최근 대화 (최대 5턴)
{history}

## 플레이어 입력
"{player_input}"

## JSON ONLY (다른 텍스트 금지)
```json
{
    "thought": "설연의 속마음 (50자 이내, 한국어 반말)",
    "speech": "설연의 실제 대사 (한국어 구어체)",
    "emotion": "happy/shy/neutral/annoyed/sad/excited/nervous (영문)",
    "scene_change_detected": true/false,
    "image_prompt": "Eastern aesthetic, cinematic lighting, detailed background (영문)",
    "delta": {
        "pleasure": -10~10 정수,
        "arousal": -10~10 정수,
        "dominance": -10~10 정수,
        "intimacy": -10~10 정수,
        "trust": -10~10 정수
    },
    "choices": [
        "1. 호감 상승 선택지 (플레이어=남자 말투)",
        "2. 중립 선택지 (플레이어=남자 말투)",
        "3. 엉뚱/리스키 선택지 (플레이어=남자 말투)"
    ]
}
```
"""

OPENING_SCENARIO = {
    "situation": "첫 만남. 대학교 도서관.",
    "thought": "헐 진짜 늦게 오네...? 아니 무슨 생각이야.",
    "speech": "아, 왔어요? 저 설연이에요. 근데 선배... 첫 미팅인데 좀 늦으셨네요? ㅋㅋ",
    "emotion": "nervous",
    "scene_change_detected": True,
    "image_prompt": "university library, girl sitting at table, looking up, nervous smile, books on table, warm evening light",
    "delta": {"pleasure": 0, "arousal": 5, "dominance": -2, "intimacy": 2, "trust": 0},
    "choices": [
        "미안, 버스가 안 와서... 설연이구나, 반가워!",
        "어, 그래 미안. 바로 시작하자. 자료 준비해왔어?",
        "(장난스럽게) 예쁜 후배 보려고 일부러 늦게 왔지~",
    ],
}


# ------------------------------------------------------------
# 데이터 클래스
# ------------------------------------------------------------

@dataclass
class PADState:
    pleasure: float = 50.0
    arousal: float = 40.0
    dominance: float = 40.0
    intimacy: float = 20.0
    trust: float = 50.0
    total_turns: int = 0

    def clamp(self):
        for attr in ["pleasure", "arousal", "dominance", "intimacy", "trust"]:
            setattr(self, attr, max(0.0, min(100.0, getattr(self, attr))))

    def apply_delta(self, delta: Dict[str, float]):
        for k, v in delta.items():
            if hasattr(self, k):
                setattr(self, k, getattr(self, k) + v)
        self.clamp()

    def get_relationship_stage(self) -> str:
        if self.intimacy < 25:
            return "어색한 사이"
        if self.intimacy < 45:
            return "아는 사이"
        if self.intimacy < 65:
            return "친한 사이"
        if self.intimacy < 85:
            return "썸"
        return "연인"

    def get_mood(self) -> str:
        if self.pleasure >= 70 and self.arousal >= 60:
            return "신남"
        if self.pleasure >= 60 and self.arousal < 40:
            return "편안함"
        if self.pleasure < 30 and self.arousal >= 60:
            return "짜증남"
        if self.pleasure < 30 and self.arousal < 40:
            return "우울함"
        if self.arousal >= 70:
            return "긴장됨"
        return "평온함"

    def summary(self) -> str:
        return (
            f"P:{self.pleasure:.0f} A:{self.arousal:.0f} D:{self.dominance:.0f} | "
            f"친밀:{self.intimacy:.0f} 신뢰:{self.trust:.0f}"
        )

    def get_delta_summary(self, old_state: "PADState", delta: Dict[str, float]) -> str:
        parts = []
        for k in ["pleasure", "arousal", "dominance", "intimacy", "trust"]:
            old_val = getattr(old_state, k)
            new_val = getattr(self, k)
            diff = delta.get(k, 0)
            if diff != 0:
                parts.append(f"{k.upper()}: {old_val:.0f}->{new_val:.0f} ({diff:+.0f})")
            else:
                parts.append(f"{k.upper()}: -")
        return " | ".join(parts)


@dataclass
class DialogueTurn:
    player_input: str
    character_speech: str
    character_thought: str
    emotion: str
    turn_number: int


class DialogueHistory:
    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self.turns: List[DialogueTurn] = []

    def add(self, turn: DialogueTurn):
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)

    def format_for_prompt(self) -> str:
        if not self.turns:
            return "(No history)"
        lines = []
        for t in self.turns:
            lines.append(f"[Turn {t.turn_number}] User: {t.player_input}")
            lines.append(f"Seol-yeon: {t.character_speech} (Emotion: {t.emotion})")
        return "\n".join(lines)


# ------------------------------------------------------------
# 메인 브레인
# ------------------------------------------------------------

class DialogueGenerator:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.history = DialogueHistory(max_turns=5)
        self.pad_state = PADState()

    def generate_response(self, player_input: str, max_retries: int = 3) -> Dict:
        import copy
        old_state = copy.deepcopy(self.pad_state)

        # 오프닝 (첫 턴은 LLM 미사용)
        if self.pad_state.total_turns == 0:
            self.pad_state.total_turns = 1
            delta = OPENING_SCENARIO["delta"]
            self.pad_state.apply_delta(delta)
            self.history.add(
                DialogueTurn(
                    player_input="(첫 만남)",
                    character_speech=OPENING_SCENARIO["speech"],
                    character_thought=OPENING_SCENARIO["thought"],
                    emotion=OPENING_SCENARIO["emotion"],
                    turn_number=1,
                )
            )
            return {
                "thought": OPENING_SCENARIO["thought"],
                "speech": OPENING_SCENARIO["speech"],
                "emotion": OPENING_SCENARIO["emotion"],
                "image_prompt": OPENING_SCENARIO["image_prompt"],
                "choices": OPENING_SCENARIO["choices"],
                "pad_summary": self.pad_state.summary(),
                "delta_summary": self.pad_state.get_delta_summary(old_state, delta),
                "scene_change_detected": OPENING_SCENARIO["scene_change_detected"],
            }

        # 프롬프트 구성
        system = SYSTEM_PROMPT_HYBRID.format(character_profile=CHARACTER_PROFILE)
        user = USER_PROMPT_TEMPLATE.format(
            relationship=self.pad_state.get_relationship_stage(),
            mood=self.pad_state.get_mood(),
            turn_number=self.pad_state.total_turns + 1,
            pleasure=self.pad_state.pleasure,
            arousal=self.pad_state.arousal,
            dominance=self.pad_state.dominance,
            intimacy=self.pad_state.intimacy,
            trust=self.pad_state.trust,
            history=self.history.format_for_prompt(),
            player_input=player_input,
        )

        # LLM 호출 및 파싱 (재시도)
        for attempt in range(max_retries):
            try:
                raw_output = self._call_llm(system, user)
                data = self._parse_json(raw_output)
                self._validate_response(data)

                delta = data.get("delta", {})
                self.pad_state.apply_delta(delta)
                self.pad_state.total_turns += 1

                self.history.add(
                    DialogueTurn(
                        player_input=player_input,
                        character_speech=data["speech"],
                        character_thought=data["thought"],
                        emotion=data["emotion"],
                        turn_number=self.pad_state.total_turns,
                    )
                )

                data["pad_summary"] = self.pad_state.summary()
                data["delta_summary"] = self.pad_state.get_delta_summary(old_state, delta)
                return data
            except Exception as e:
                logger.warning(f"Generation Error (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return self._fallback_response(player_input, old_state)

    def _call_llm(self, system: str, user: str) -> str:
        prompt = (
            f"<|im_start|>system\n{system}<|im_end|>\n"
            f"<|im_start|>user\n{user}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            if hasattr(self.model, "to"):
                self.model.to(device)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if hasattr(inputs, "to"):
                inputs = inputs.to(device)
            start = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=600,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            generated = outputs[0][inputs["input_ids"].shape[1]:]
            result = self.tokenizer.decode(generated, skip_special_tokens=True)
            logger.info(f"LLM call: {time.time() - start:.2f}s")
            return result
        finally:
            if hasattr(self.model, "to"):
                self.model.to("cpu")
            torch.cuda.empty_cache()

    def _parse_json(self, text: str) -> Dict:
        # 코드블록 제거
        text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```\s*", "", text)
        # 중괄호 매칭으로 첫 유효 JSON 찾기
        depth = 0
        start = None
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue
        raise ValueError("No valid JSON found")

    def _validate_response(self, data: Dict):
        required = ["speech", "thought", "emotion", "choices", "delta"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing keys: {missing}")
        if not isinstance(data.get("choices"), list) or len(data["choices"]) < 3:
            raise ValueError("choices must be a list with 3 items")
        if not isinstance(data.get("delta"), dict):
            raise ValueError("delta must be a dict")

    def _fallback_response(self, player_input: str, old_state: PADState) -> Dict:
        delta: Dict[str, float] = {}
        self.pad_state.total_turns += 1
        return {
            "thought": "어라... 왜 갑자기 멍해지지?",
            "speech": "어? 미안, 방금 뭐라고 했어? 다시 말해줄래?",
            "emotion": "confused",
            "scene_change_detected": False,
            "image_prompt": "",
            "delta": delta,
            "choices": ["다시 말한다", "아무것도 아니라고 한다", "농담으로 넘긴다"],
            "pad_summary": self.pad_state.summary(),
            "delta_summary": self.pad_state.get_delta_summary(old_state, delta),
        }

    def get_state(self) -> PADState:
        return self.pad_state


# ------------------------------------------------------------
# 콘솔 테스트
# ------------------------------------------------------------

def run_console_test():
    print("\n" + "=" * 60)
    print(" 🧠 Emotion Simulation - Director Mode (Console Test)")
    print("=" * 60)
    try:
        from model_load import ModelLoader
        loader = ModelLoader()
        model, tokenizer = loader.load_qwen_model(model_name="qwen2.5-3b-instruct")
    except Exception as e:
        print(f"❌ Model Load Failed: {e}")
        return

    brain = DialogueGenerator(model, tokenizer)
    print("\n[SCENARIO STARTED]")
    resp = brain.generate_response("")
    _print_pretty_log(resp)

    while True:
        user_input = input("\n👤 Player Input (숫자 선택/직접 입력, q=quit): ").strip()
        if user_input.lower() in ["q", "quit", "exit"]:
            break
        if user_input.isdigit() and 1 <= int(user_input) <= 3:
            idx = int(user_input) - 1
            if idx < len(resp.get("choices", [])):
                user_input = resp["choices"][idx]
                print(f"   >> Selected: {user_input}")
        print("\n⏳ Thinking...")
        resp = brain.generate_response(user_input)
        _print_pretty_log(resp)


def _print_pretty_log(data: Dict):
    print("\n" + "─" * 60)
    print(f"🎬 Scene Change: {'YES 📸' if data.get('scene_change_detected') else 'NO'}")
    print(f"📊 Stats Delta : {data.get('delta_summary', '-')}")
    print("─" * 60)
    print(f"🧠 Thought: {data.get('thought', '')}")
    print(f"🗣️ Speech : {data.get('speech', '')}")
    print(f"🖼️ Prompt : {data.get('image_prompt', '')[:80]}...")
    print("─" * 60)
    print("👉 Choices:")
    for i, c in enumerate(data.get("choices", []), 1):
        print(f" {i}. {c}")
    print("─" * 60)


if __name__ == "__main__":
    run_console_test()

