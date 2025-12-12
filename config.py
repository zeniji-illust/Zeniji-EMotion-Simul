"""
Zeniji Emotion Simul - Configuration
시스템 설정 및 상수 정의
"""

# 이미지 생성 모드
IMAGE_MODE_ENABLED = True
DEFAULT_IMAGE_PATH = "assets/default_character.png"

# 관계 상태 전환 조건 테이블
STATUS_TRANSITIONS = {
    "Stranger": {
        "to": ["Acquaintance"],
        "condition": {"I": 40}
    },
    "Acquaintance": {
        "to": ["Tempted", "Girlfriend"],
        "condition": {"I": 60}
    },
    "Tempted": {
        "to": ["Girlfriend", "Master", "Slave"],
        "condition": {"P": 80, "A": 80, "D": 40}
    },
    "Girlfriend": {
        "to": ["Fiancée", "Wife", "Breakup", "Master", "Slave"],
        "condition": {"I": 80, "T": 60}
    },
    "Fiancée": {
        "to": ["Wife", "Divorce"],
        "condition": {"I": 90, "T": 85}
    },
    "Wife": {
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
    "jackpot": {"prob": 0.001, "multiplier": 10.0},  # 0.1%
    "surprise": {"prob": 0.009, "multiplier": 5.0},  # 0.9%
    "critical": {"prob": 0.04, "multiplier": 2.5},  # 4.0%
    "normal": {"prob": 0.95, "multiplier": 1.0}     # 95%
}

# 이미지 생성 트리거 설정
IMAGE_GENERATION_TRIGGERS = {
    "force_refresh_turns": 5,  # N턴마다 강제 갱신
    "critical_gacha_tiers": ["jackpot", "surprise", "critical"],
    "status_transitions": ["Girlfriend", "Wife", "Master", "Slave"]
}

# Ollama API 설정
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL_NAME = "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest" 

# LLM 설정 (Ollama 호환)
LLM_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 600
}

# ComfyUI 설정
COMFYUI_CONFIG = {
    "server_address": "127.0.0.1:8000",
    "workflow_path": "workflows/comfyui_zit.json"
}

# Trauma 레벨 분류
TRAUMA_LEVELS = {
    0.0: "Clean Slate",
    0.25: "Scarred",
    0.50: "Wary",
    0.75: "Fearful",
    1.0: "Broken"
}

