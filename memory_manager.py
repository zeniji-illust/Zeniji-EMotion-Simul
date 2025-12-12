"""
Zeniji Emotion Simul - Memory Manager
Ollama API를 통한 LLM 호출 관리
"""

import logging
import time
import requests
from typing import Optional, Tuple

import config

logger = logging.getLogger("MemoryManager")


class MemoryManager:
    """Ollama API를 통한 LLM 관리"""
    
    def __init__(self, dev_mode: bool = False):
        self.api_url = config.OLLAMA_API_URL
        self.model_name = config.OLLAMA_MODEL_NAME
        self.is_loaded = False
        self.dev_mode = dev_mode
    
    def load_model(self, force_reload: bool = False) -> Optional[Tuple[str, str]]:
        """
        Ollama 모델 로드 확인 (실제로는 API 연결 확인)
        Returns: (model_name, api_url) 튜플 (호환성을 위해)
        """
        if self.is_loaded and not force_reload:
            logger.info("Ollama model already loaded.")
            return self.model_name, self.api_url
        
        logger.info(f"[VRAM MANAGER] Checking Ollama API connection...")
        logger.info(f"[VRAM MANAGER] API URL: {self.api_url}")
        logger.info(f"[VRAM MANAGER] Model: {self.model_name}")
        
        start = time.time()
        try:
            # Ollama API 연결 확인
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API 연결 실패: HTTP {response.status_code}")
            
            # 모델 존재 확인 (정확한 일치 사용)
            models = response.json().get("models", [])
            available_names = [m.get("name") for m in models]
            
            # 정확한 일치 확인 (태그 포함한 전체 이름 비교)
            model_exists = self.model_name in available_names
            
            if not model_exists:
                logger.error(f"❌ FATAL ERROR: 설정된 모델 '{self.model_name}'이 Ollama에 등록되지 않았습니다.")
                logger.error(f"📋 Ollama에 현재 다운로드된 모델 목록:")
                for name in available_names:
                    logger.error(f"   - {name}")
                logger.error("")
                logger.error("🔧 해결 방법:")
                logger.error(f"   1. 터미널에서 'ollama list' 명령으로 정확한 모델 이름을 확인하세요.")
                logger.error(f"   2. config.py의 OLLAMA_MODEL_NAME을 정확한 모델 이름으로 수정하세요.")
                logger.error(f"   3. 모델을 다운로드하려면: ollama pull {self.model_name}")
                logger.error("")
                logger.warning("⚠️  모델 이름이 일치하지 않으면 /api/generate 호출 시 404 오류가 발생합니다.")
                # 경고만 하고 계속 진행 (실제 오류는 /api/generate에서 발생)
            else:
                logger.info(f"✅ 모델 '{self.model_name}' 확인됨")
            
            self.is_loaded = True
            duration = time.time() - start
            logger.info(f"[VRAM MANAGER] Ollama API 연결 확인 완료. ({duration:.2f} s)")
            
            if self.dev_mode:
                self._log_dev_info(duration, available_names if not model_exists else None)
            
            # 호환성을 위해 튜플 반환 (model_name, api_url)
            return self.model_name, self.api_url
        except requests.exceptions.ConnectionError:
            error_msg = (
                f"Ollama 서버에 연결할 수 없습니다.\n"
                f"확인 사항:\n"
                f"1. Ollama가 실행 중인지 확인 (ollama serve)\n"
                f"2. API URL이 올바른지 확인: {self.api_url}\n"
                f"3. 방화벽 설정 확인"
            )
            logger.error(error_msg)
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _log_dev_info(self, duration: float, available_models: Optional[list] = None):
        """Dev Mode: 상세 로드 정보 출력"""
        logger.info("[DEV] Ollama API URL: %s", self.api_url)
        logger.info("[DEV] Ollama Model: %s", self.model_name)
        logger.info("[DEV] Connection check time: %.2f s", duration)
        if available_models:
            logger.info("[DEV] Available models: %s", available_models)
        logger.info("[DEV] Note: Ollama는 별도 프로세스로 실행되며, 모델은 Ollama가 관리합니다.")
    
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Ollama API를 통한 텍스트 생성
        Args:
            prompt: 입력 프롬프트
            **kwargs: 추가 파라미터 (temperature, top_p, max_tokens 등)
        Returns:
            생성된 텍스트
        """
        if not self.is_loaded:
            logger.warning("Model not loaded. Attempting to load...")
            if self.load_model() is None:
                return None
        
        try:
            # Ollama API 호출
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", config.LLM_CONFIG["temperature"]),
                    "top_p": kwargs.get("top_p", config.LLM_CONFIG["top_p"]),
                    "num_predict": kwargs.get("max_tokens", config.LLM_CONFIG["max_tokens"]),
                }
            }
            
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=300  # 5분 타임아웃
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Ollama API 호출 실패: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                
                # 404 오류 시 모델 이름 불일치 가능성 안내
                if response.status_code == 404:
                    logger.error("")
                    logger.error("🔍 모델을 찾을 수 없습니다. 가능한 원인:")
                    logger.error(f"   1. 모델 이름 불일치: '{self.model_name}'이 Ollama에 없습니다.")
                    logger.error("   2. 'ollama list' 명령으로 정확한 모델 이름을 확인하세요.")
                    logger.error(f"   3. config.py의 OLLAMA_MODEL_NAME을 수정하세요.")
                    logger.error("")
                
                return None
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            if not generated_text:
                logger.warning("Ollama returned empty response")
                return None
            
            return generated_text
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def offload_model(self):
        """Ollama는 별도 프로세스이므로 언로드 불필요 (로깅만)"""
        logger.info("[VRAM MANAGER] Ollama는 별도 프로세스로 실행되므로 언로드가 필요 없습니다.")
    
    def reload_model(self):
        """Ollama는 별도 프로세스이므로 재로드 불필요 (로깅만)"""
        logger.info("[VRAM MANAGER] Ollama는 별도 프로세스로 실행되므로 재로드가 필요 없습니다.")
    
    def unload_model(self):
        """Ollama는 별도 프로세스이므로 언로드 불필요"""
        self.is_loaded = False
        logger.info("Ollama connection marked as unloaded (Ollama 서버는 계속 실행됩니다).")
    
    def get_model(self) -> Optional[Tuple[str, str]]:
        """현재 연결된 모델 정보 반환 (없으면 연결 시도)"""
        if not self.is_loaded:
            return self.load_model()
        return self.model_name, self.api_url
    
    def ensure_loaded(self) -> bool:
        """모델이 로드되어 있는지 확인하고 필요시 로드"""
        if not self.is_loaded:
            return self.load_model() is not None
        return True
