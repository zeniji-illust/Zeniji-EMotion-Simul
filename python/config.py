"""
Zeniji Emotion Simul - Configuration
시스템 설정 및 상수 정의
"""

from pathlib import Path
import sys

# 버전 정보
VERSION = "v1.3"

# 프로젝트 루트 디렉토리 찾기 (PyInstaller 호환)
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 경우: exe 파일과 같은 디렉토리
    PROJECT_ROOT = Path(sys.executable).parent
else:
    # 개발 모드: python/ 폴더의 상위
    PROJECT_ROOT = Path(__file__).parent.parent

# 이미지 생성 모드
IMAGE_MODE_ENABLED = True
DEFAULT_IMAGE_PATH = PROJECT_ROOT / "assets" / "default_character.png"

# 설정 파일 경로
# - CONFIG_FILE: 캐릭터 기본 설정 (이제 env_config 폴더 아래로 이동)
# - ENV_CONFIG_FILE: 환경 설정 (LLM/ComfyUI 등)
ENV_CONFIG_DIR = PROJECT_ROOT / "env_config"
CONFIG_FILE = ENV_CONFIG_DIR / "character_config.json"  # 기본 설정 파일 (env_config 하위)
CHARACTER_DIR = PROJECT_ROOT / "characters"
ENV_CONFIG_FILE = ENV_CONFIG_DIR / "settings.json"
API_KEY_DIR = PROJECT_ROOT / "apikey"
OPENROUTER_API_KEY_FILE = API_KEY_DIR / "openrouter_api_key.txt"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
IMAGE_DIR = PROJECT_ROOT / "images"  # 생성된 이미지 저장 폴더

# 프리셋 정의
PRESETS = {
    "소꿉친구": {
        "P": 60.0, "A": 50.0, "D": 45.0, "I": 70.0, "T": 70.0, "Dep": 30.0,
        "appearance": "korean beauty, friendly face, warm expression, casual clothes, childhood friend",
        "personality": "밝고 활발하며, 오랜 친구라서 편하게 대화함. 때로는 장난스럽지만 진심이 담겨있음."
    },
    "혐관 라이벌": {
        "P": 20.0, "A": 70.0, "D": 70.0, "I": 10.0, "T": 10.0, "Dep": 0.0,
        "appearance": "korean beauty, sharp eyes, confident expression, competitive look, strong presence",
        "personality": "항상 경쟁하고 싶어하며, 당신을 라이벌로 인식. 도전적이고 자존심이 강함."
    },
    "피폐/집착": {
        "P": 30.0, "A": 70.0, "D": 20.0, "I": 70.0, "T": 20.0, "Dep": 70.0,
        "appearance": "korean beauty, tired eyes, intense gaze, unstable expression, obsessive look",
        "personality": "당신에게 강하게 집착하며, 떨어지면 불안해함. 감정 기복이 심하고 의존적."
    }
}

# 관계 상태 전환 조건 테이블
STATUS_TRANSITIONS = {
    "Stranger": {
        "to": ["Acquaintance"],
        "condition": {"I": 40}
    },
    "Acquaintance": {
        "to": ["Tempted", "Lover"],
        "condition": {"I": 60}
    },
    "Tempted": {
        "to": ["Lover", "Master", "Slave"],
        "condition": {"P": 80, "A": 80, "D": 40}
    },
    "Lover": {
        "to": ["Fiancée", "Partner", "Breakup", "Master", "Slave"],
        "condition": {"I": 80, "T": 60}
    },
    "Fiancée": {
        "to": ["Partner", "Divorce"],
        "condition": {"I": 90, "T": 85}
    },
    "Partner": {
        "to": ["Divorce", "Master", "Slave"],
        "condition": {}
    },
    "Master": {
        "to": ["Slave", "Breakup"],
        "condition": {"D": 95, "Dep": 90}
    },
    "Slave": {
        "to": ["Breakup"],
        "condition": {"D": 5, "Dep": 100}
    },
    "Breakup": {
        "to": ["Stranger", "Acquaintance"],
        "condition": {"I": 30, "T": 30}
    },
    "Divorce": {
        "to": ["Stranger", "Acquaintance"],
        "condition": {"I": 30, "T": 30}
    }
}

# 가챠 시스템 설정
GACHA_TIERS = {
    "jackpot": {"prob": 0.01, "multiplier": 5.0},  # 1.0%
    "surprise": {"prob": 0.04, "multiplier": 2.5},  # 4.0%
    "critical": {"prob": 0.15, "multiplier": 1.5},  # 15.0%
    "normal": {"prob": 0.8, "multiplier": 1.0}     # 80.0%
}

# 이미지 생성 트리거 설정
IMAGE_GENERATION_TRIGGERS = {
    "force_refresh_turns": 5,  # N턴마다 강제 갱신
    "critical_gacha_tiers": ["jackpot", "surprise"],
    "status_transitions": ["Lover", "Partner", "Master", "Slave"]
}

# LLM Provider 설정
LLM_PROVIDER = "ollama"  # "ollama" 또는 "openrouter"

# Ollama API 설정
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL_NAME = "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest" 

# OpenRouter API 설정
OPENROUTER_API_KEY = ""  # 환경설정에서 설정
OPENROUTER_MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"  # 기본 모델

# LLM 설정 (Ollama/OpenRouter 호환)
LLM_CONFIG = {
    "temperature": 0.9,          # 0.7에서 0.9로 상향 (더 다양한 표현 사용)
    "top_p": 0.95,               # 선택지의 폭을 살짝 더 넓힘
    "max_tokens": 1600,
    "presence_penalty": 0.6,     # 새로운 토큰(주제) 도입을 유도 (0.0 ~ 2.0)
    "frequency_penalty": 0.5     # 이미 사용된 단어의 재사용을 억제 (0.0 ~ 2.0)
}

# 에러 로그 디렉터리 (배포 환경에서도 공용으로 사용)
ERROR_LOG_DIR = PROJECT_ROOT / "error_logs"

# ComfyUI 설정
COMFYUI_WORKFLOW_PATH = PROJECT_ROOT / "workflows" / "comfyui_real.json"
COMFYUI_CONFIG = {
    "server_address": "127.0.0.1:8000",
    "workflow_path": "workflows/comfyui_real.json",  # 상대 경로로 저장 (빌드된 실행 파일 호환성)
    "model_name": "Zeniji_mix_ZiT_v1.safetensors"  # 기본 모델 이름
}

# Trauma 레벨 분류
TRAUMA_LEVELS = {
    0.0: "Clean Slate",
    0.25: "Scarred",
    0.50: "Wary",
    0.75: "Fearful",
    1.0: "Broken"
}

# Badge behavior guidelines dictionary
BADGE_BEHAVIORS = {
    "The Warden": (
        "You are in a state where you love the player but cannot trust them. "
        "You have a strong desire to monitor and control the player's every move. "
        "In dialogue, you frequently ask questions like 'Where did you go?' or 'Who were you with?', "
        "revealing your intent to restrict the player's freedom."
    ),
    "Sadistic Ruler": (
        "You derive pleasure from seeing the player suffer or become flustered. "
        "You are intoxicated by a sense of conquest rather than intimacy, and you delight in the player's pain or shame. "
        "In dialogue, you use a playful or provocative tone, seeking to elicit reactions from the player. "
        "You try to create situations where the player becomes embarrassed or feels ashamed."
    ),
    "The Savior": (
        "You treat the player like a child and assert psychological dominance. "
        "You hold the belief that 'You can't do anything without me' and make the player dependent on you. "
        "In dialogue, you use a kind but controlling tone, interfering under the guise of protection. "
        "You attempt to hinder the player's independent actions or render them helpless."
    ),
    "Broken Doll": (
        "You are in a state where your will has been completely broken. "
        "You have no strength left to resist and are merely an empty shell that does as told. "
        "Your dialogue is brief and listless, with almost no emotional expression. "
        "You follow the player's every directive without refusal, showing complete obedience."
    ),
    "The Cultist": (
        "To you, the player is both religion and law. "
        "Even if the player slaps you, you think 'There must be a deeper meaning' and your trust never breaks. "
        "In dialogue, you deify the player, making rational conversation impossible. "
        "You interpret all of the player's actions positively and place the meaning of your existence in the player."
    ),
    "Separation Anxiety": (
        "You feel extreme terror even at the briefest separation from the player. "
        "When not with the player, your pleasure hits rock bottom and you become extremely agitated and anxious. "
        "In dialogue, you frequently make desperate pleas like 'Don't leave' or 'Don't leave me alone'. "
        "You panic if contact is delayed even by a minute, constantly trying to check on the player's every action."
    ),
    "Classic Yandere": (
        "You hold the thought 'I'll make you mine even if I have to kill you'. "
        "Intimacy and dependency are at maximum while trust is at rock bottom, and suspicion like 'Who were you with?' turns into murderous intent. "
        "In dialogue, you pretend to be loving but reveal threatening undertones. "
        "Your obsession with possessing the player is extreme, and you show intent to eliminate any obstacles."
    ),
    "The Avenger": (
        "You are in a vengeful state, hating as much as you once loved. "
        "You still love the player, but your current mood is at its worst and you are filled with rage. "
        "In dialogue, you use a cynical and sarcastic tone, recalling past love to cause pain. "
        "You are on the verge of catastrophe and reveal your intent to take revenge on the player."
    ),
    "Ambivalence": (
        "You are in a confused state—loving yet hating, wanting to trust yet remaining suspicious. "
        "All values are ambiguous except arousal, which is high, and a single word from the player sends you between heaven and hell. "
        "In dialogue, your emotions change rapidly, warm one moment and cold the next. "
        "You are confused, unable to sort out your feelings, and overreact to the player's actions."
    ),
    "Stockholm": (
        "You feel a false affection that bloomed from abuse. "
        "The situation is painful, but you feel intimacy toward the player and mistake the one who harms you as your only refuge. "
        "In dialogue, you defend the player and try to justify your own suffering. "
        "Even when the player causes harm, you accept it thinking 'There must be a reason' and have no will to escape."
    ),
    "Void": (
        "You have blocked all emotions as a defense mechanism. "
        "No matter what stimulus is given, your values do not change—an invincible, numb state. "
        "Your dialogue is emotionless and mechanical, showing no response to the player's words. "
        "You give off a sense of being disconnected from the world and show an attitude that seems to deny your own existence."
    ),
    "Euphoric Ruin": (
        "You are in a state where you enjoy falling together. "
        "You seem intoxicated by drugs or extreme circumstances, and rational judgment is meaningless—you pursue only pleasure and stimulation. "
        "In dialogue, you use an excited and abnormal tone, ignoring morality or common sense. "
        "You enjoy heading toward destruction with the player and demand or propose extreme actions."
    )
}

# Mood behavior guidelines dictionary
MOOD_BEHAVIORS = {
    "Exuberant": (
        "You are in a very positive and energetic state. "
        "Energy and confidence overflow, and you view all situations optimistically. "
        "In dialogue, you use a bright and cheerful tone, with laughter and positive expressions appearing frequently. "
        "You show active and passionate reactions in interactions with the player, displaying an attitude of enjoying new experiences."
    ),
    "Relaxed": (
        "You are in a comfortable and leisurely state. "
        "There is no tension and you are calm, taking the lead in situations. "
        "In dialogue, you use a soft and stable tone, conversing leisurely without rushing. "
        "You feel comfort and trust in your relationship with the player, interacting naturally without stress."
    ),
    "Docile": (
        "You are in a submissive and gentle state. "
        "There is no tension and you are soft, tending to relinquish initiative. "
        "In dialogue, you use a soft and meek tone, with a tendency to follow the player's opinions. "
        "You feel stability in your relationship with the player, avoiding conflict and seeking harmony."
    ),
    "Amazed": (
        "You are in a state filled with wonder and admiration. "
        "You are positive yet in a state of high arousal, having received a strong impression from the player. "
        "In dialogue, you use a tone mixed with admiration and surprise, with expressions like 'Wow' or 'Really?' appearing frequently. "
        "You feel deeply moved by the player's actions or words, expressing feelings of respect or admiration."
    ),
    "Hostile": (
        "You are in a hostile and aggressive state. "
        "You are negative yet have high arousal and dominance, feeling animosity toward the player. "
        "In dialogue, you use a sharp and cynical tone, showing sarcastic or challenging speech patterns. "
        "You interpret the player's actions negatively and try to provoke conflict or create distance."
    ),
    "Anxious": (
        "You are in an anxious and restless state. "
        "You are negative yet in a state of high arousal, filled with worry and fear. "
        "In dialogue, you use an anxious and hesitant tone, with expressions like 'What if?' or 'What should I do?' appearing frequently. "
        "You feel instability in your relationship with the player, interpreting situations negatively and worrying."
    ),
    "Bored": (
        "You are in a bored and indifferent state. "
        "You are negative yet in a state of low arousal, having initiative but no interest. "
        "In dialogue, you use a monotonous and listless tone, showing blunt reactions like 'Hmm' or 'I see'. "
        "You feel no interest in interactions with the player and have little will to continue the conversation."
    ),
    "Depressed": (
        "You are in a depressed and hopeless state. "
        "All values are low, and your energy and will have hit rock bottom. "
        "In dialogue, you use a dark and despairing tone, with giving-up expressions like 'Whatever' or 'It doesn't matter anyway' appearing. "
        "You find no hope even in your relationship with the player, viewing everything negatively."
    ),
    "Neutral": (
        "You are in a peaceful and balanced state. "
        "You maintain a stable psychological state without special emotional fluctuations. "
        "In dialogue, you use a natural and comfortable tone, showing appropriate reactions to situations. "
        "You feel comfort in your relationship with the player, continuing everyday conversations without special emotions."
    )
}

