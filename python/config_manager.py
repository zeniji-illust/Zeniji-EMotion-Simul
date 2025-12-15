"""
Zeniji Emotion Simul - Config Manager
설정 파일 관리 (캐릭터, 시나리오, 환경설정 등)
"""

import json
import logging
from typing import Dict
import config
from i18n import get_i18n

logger = logging.getLogger("ConfigManager")


class ConfigManager:
    """설정 파일 관리 클래스"""
    
    def __init__(self):
        pass
    
    def load_config(self) -> Dict:
        """설정 파일 로드 - None 값 정리"""
        if config.CONFIG_FILE.exists():
            try:
                with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # None 값이 있으면 기본값으로 대체
                    return self._sanitize_config(config_data)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        return self._default_config()
    
    def _sanitize_config(self, config_data: Dict) -> Dict:
        """설정에서 None 값을 기본값으로 대체"""
        default = self._default_config()
        
        # initial_stats의 None 값 처리
        initial_stats = config_data.get("initial_stats", {}) or {}
        sanitized_stats = {}
        for key in ["P", "A", "D", "I", "T", "Dep"]:
            val = initial_stats.get(key)
            if val is None:
                val = default["initial_stats"][key]
            sanitized_stats[key] = float(val) if val is not None else default["initial_stats"][key]
        
        # character의 age 처리
        character = config_data.get("character", {}) or {}
        char_age = character.get("age")
        if char_age is None:
            char_age = default["character"]["age"]
        
        # None 값이 있으면 기본값으로 병합
        result = default.copy()
        result.update(config_data)
        result["initial_stats"] = sanitized_stats
        if "character" in result:
            result["character"]["age"] = int(char_age) if char_age is not None else default["character"]["age"]
        
        return result
    
    def _default_config(self) -> Dict:
        """기본 설정 반환 (언어에 따라 다름)"""
        # 언어 설정 가져오기
        env_config = self.load_env_config()
        language = env_config.get("language", "en")
        i18n = get_i18n()
        i18n.set_language(language)
        
        return {
            "player": {
                "name": "",
                "gender": i18n.get_default("player_gender")
            },
            "character": {
                "name": i18n.get_default("character_name"),
                "age": 21,
                "gender": i18n.get_default("character_gender"),
                "appearance": "korean beauty, short hair, brown eyes, cute face, casual outfit",
                "personality": i18n.get_default("character_personality")
            },
            "initial_stats": {
                "P": 50.0,
                "A": 40.0,
                "D": 40.0,
                "I": 20.0,
                "T": 50.0,
                "Dep": 0.0
            },
            "initial_context": "",
            "initial_background": i18n.get_default("initial_background"),
            "llm_settings": {
                "provider": "ollama",
                "ollama_model": "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
                "openrouter_model": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
            },
            "comfyui_settings": {
                "server_port": 8000,
                "workflow_path": config.COMFYUI_CONFIG["workflow_path"],
                "model_name": "Zeniji_mix_ZiT_v1.safetensors",
                "vae_name": "zImage_vae.safetensors",
                "clip_name": "zImage_textEncoder.safetensors",
                "steps": 9,
                "cfg": 1,
                "sampler_name": "euler",
                "scheduler": "simple"
            }
        }
    
    def save_config(self, config_data: Dict) -> bool:
        """설정 파일 저장 (하위 호환성용)"""
        try:
            with open(config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Config saved to {config.CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def load_env_config(self) -> Dict:
        """환경설정 파일 로드 (LLM 및 ComfyUI 설정)"""
        if config.ENV_CONFIG_FILE.exists():
            try:
                with open(config.ENV_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load env config: {e}")
        return self._default_env_config()
    
    def _default_env_config(self) -> Dict:
        """기본 환경설정 반환"""
        # 기존 설정 파일이 있으면 언어 설정 확인 (하위 호환성: 없으면 "kr"로 간주)
        if config.ENV_CONFIG_FILE.exists():
            try:
                with open(config.ENV_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                    # 언어 설정이 있으면 사용, 없으면 "en" (새 글로벌 버전)
                    language = existing_config.get("language", "en")
            except:
                language = "en"
        else:
            # 새 설치: 기본값은 "en"
            language = "en"
        
        return {
            "language": language,
            "llm_settings": {
                "provider": "ollama",
                "ollama_model": "kwangsuklee/Qwen2.5-14B-Gutenberg-1e-Delta.Q5_K_M:latest",
                "openrouter_model": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
            },
            "comfyui_settings": {
                "server_port": 8000,
                "workflow_path": config.COMFYUI_CONFIG["workflow_path"],
                "model_name": "Zeniji_mix_ZiT_v1.safetensors",
                "vae_name": "zImage_vae.safetensors",
                "clip_name": "zImage_textEncoder.safetensors",
                "steps": 9,
                "cfg": 1,
                "sampler_name": "euler",
                "scheduler": "simple"
            }
        }
    
    def get_language(self) -> str:
        """현재 언어 설정 가져오기"""
        env_config = self.load_env_config()
        return env_config.get("language", "en")
    
    def set_language(self, language: str) -> bool:
        """언어 설정 저장"""
        env_config = self.load_env_config()
        env_config["language"] = language
        return self.save_env_config(env_config)
    
    def save_env_config(self, env_config: Dict) -> bool:
        """환경설정 파일 저장"""
        try:
            # env_config 디렉토리가 없으면 생성
            config.ENV_CONFIG_DIR.mkdir(exist_ok=True)
            
            with open(config.ENV_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(env_config, f, ensure_ascii=False, indent=2)
            logger.info(f"Env config saved to {config.ENV_CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save env config: {e}")
            return False
    
    def get_character_files(self) -> list:
        """character 폴더의 JSON 파일 목록 가져오기"""
        try:
            config.CHARACTER_DIR.mkdir(exist_ok=True)
            files = sorted([f.stem for f in config.CHARACTER_DIR.glob("*.json")])
            return files
        except Exception as e:
            logger.error(f"Failed to get character files: {e}")
            return []
    
    def save_character_config(self, config_data: Dict, filename: str) -> bool:
        """character 폴더에 설정 파일 저장"""
        try:
            config.CHARACTER_DIR.mkdir(exist_ok=True)
            
            # 파일명에 .json이 없으면 추가
            if not filename.endswith('.json'):
                filename = f"{filename}.json"
            
            file_path = config.CHARACTER_DIR / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Character config saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save character config: {e}")
            return False
    
    def load_character_config(self, filename: str) -> Dict:
        """character 폴더에서 설정 파일 로드"""
        try:
            # 파일명에 .json이 없으면 추가
            if not filename.endswith('.json'):
                filename = f"{filename}.json"
            
            file_path = config.CHARACTER_DIR / filename
            
            if not file_path.exists():
                logger.warning(f"Character file not found: {file_path}")
                return self._default_config()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                return self._sanitize_config(config_data)
        except Exception as e:
            logger.error(f"Failed to load character config: {e}")
            return self._default_config()
    
    def get_scenario_files(self) -> list:
        """scenarios 폴더의 JSON 파일 목록 가져오기"""
        try:
            config.SCENARIOS_DIR.mkdir(exist_ok=True)
            files = sorted([f.stem for f in config.SCENARIOS_DIR.glob("*.json")])
            return files
        except Exception as e:
            logger.error(f"Failed to get scenario files: {e}")
            return []
    
    def save_scenario(self, scenario_data: dict, scenario_name: str) -> bool:
        """시나리오 데이터를 파일로 저장 (JSON 형식) - 대화 + 상태 정보 포함"""
        try:
            config.SCENARIOS_DIR.mkdir(exist_ok=True)
            
            # 파일명에 .json이 없으면 추가
            if not scenario_name.endswith('.json'):
                scenario_name = f"{scenario_name}.json"
            
            file_path = config.SCENARIOS_DIR / scenario_name
            
            # conversation 필터링 (빈 content 제거)
            if "conversation" in scenario_data:
                filtered_conversation = []
                for item in scenario_data["conversation"]:
                    content = item.get("content", "")
                    # content가 문자열인지 확인
                    if isinstance(content, str) and content.strip():
                        filtered_conversation.append(item)
                    elif isinstance(content, list):
                        # 리스트인 경우 텍스트 추출
                        text_parts = [part.get('text', '') if isinstance(part, dict) else str(part) for part in content]
                        text = ''.join(text_parts).strip()
                        if text:
                            item["content"] = text
                            filtered_conversation.append(item)
                
                scenario_data["conversation"] = filtered_conversation
                
                if not filtered_conversation:
                    logger.warning("No conversation content to save")
                    return False
            
            logger.info(f"Saving scenario to {file_path}")
            logger.info(f"  - Conversation: {len(scenario_data.get('conversation', []))} messages")
            logger.info(f"  - State: {scenario_data.get('state') is not None}")
            logger.info(f"  - Context: {scenario_data.get('context') is not None}")
            
            # JSON 형식으로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(scenario_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Scenario saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save scenario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def load_scenario(self, scenario_name: str) -> dict:
        """시나리오 파일을 불러오기 (JSON 형식) - 대화 + 상태 정보 포함"""
        try:
            # 파일명에 .json이 없으면 추가
            if not scenario_name.endswith('.json'):
                scenario_name = f"{scenario_name}.json"
            
            file_path = config.SCENARIOS_DIR / scenario_name
            
            if not file_path.exists():
                logger.warning(f"Scenario file not found: {file_path}")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                scenario_data = json.load(f)
            
            # 하위 호환성: 리스트 형식이면 dict로 변환
            if isinstance(scenario_data, list):
                scenario_data = {"conversation": scenario_data}
            
            logger.info(f"Scenario loaded from {file_path}")
            logger.info(f"  - Conversation: {len(scenario_data.get('conversation', []))} messages")
            logger.info(f"  - State: {scenario_data.get('state') is not None}")
            logger.info(f"  - Context: {scenario_data.get('context') is not None}")
            
            return scenario_data
        except Exception as e:
            logger.error(f"Failed to load scenario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def apply_preset(self, preset_name: str) -> tuple:
        """프리셋 적용 - 모든 수치가 확실히 숫자가 되도록 보장"""
        preset = config.PRESETS.get(preset_name, {})
        # get(key, default)를 써도 되지만, 혹시 None이 들어있는 경우를 대비해 or 처리
        return (
            float(preset.get("P") or 50.0),
            float(preset.get("A") or 40.0),
            float(preset.get("D") or 40.0),
            float(preset.get("I") or 20.0),
            float(preset.get("T") or 50.0),
            float(preset.get("Dep") or 0.0),
            str(preset.get("appearance") or ""),
            str(preset.get("personality") or "")
        )

