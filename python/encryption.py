"""
Zeniji Emotion Simul - Encryption Module
API 키 암호화 및 복호화 기능
"""

import os
import base64
import logging
from pathlib import Path
from cryptography.fernet import Fernet
import config

logger = logging.getLogger("Encryption")


class EncryptionManager:
    """암호화 관리 클래스"""
    
    def __init__(self):
        self.key_file = Path.home() / ".zeniji_encryption_key"
    
    def _get_encryption_key(self) -> bytes:
        """암호화 키 가져오기 또는 생성"""
        if self.key_file.exists():
            # 기존 키 로드
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load encryption key: {e}, generating new key")
                # 키 로드 실패 시 새로 생성
                key = Fernet.generate_key()
                try:
                    self.key_file.parent.mkdir(exist_ok=True)
                    with open(self.key_file, 'wb') as f:
                        f.write(key)
                    # Windows에서는 chmod가 작동하지 않을 수 있음
                    try:
                        os.chmod(self.key_file, 0o600)
                    except:
                        pass
                    return key
                except Exception as e2:
                    logger.error(f"Failed to save encryption key: {e2}")
                    raise
        else:
            # 새 키 생성
            key = Fernet.generate_key()
            try:
                self.key_file.parent.mkdir(exist_ok=True)
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Windows에서는 chmod가 작동하지 않을 수 있음
                try:
                    os.chmod(self.key_file, 0o600)
                except:
                    pass
                logger.info(f"Encryption key generated at {self.key_file}")
                return key
            except Exception as e:
                logger.error(f"Failed to create encryption key: {e}")
                raise
    
    def encrypt_api_key(self, api_key: str) -> str:
        """API 키 암호화"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted = fernet.encrypt(api_key.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """API 키 복호화"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted = base64.b64decode(encrypted_key.encode())
            return fernet.decrypt(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            raise
    
    def is_encrypted(self, content: str) -> bool:
        """파일 내용이 암호화되어 있는지 확인"""
        # 암호화된 내용은 base64로 인코딩되어 있고, 특정 패턴을 가짐
        try:
            # base64 디코딩 시도
            decoded = base64.b64decode(content.encode())
            # Fernet 암호화된 데이터는 항상 32바이트 키 + 특정 구조를 가짐
            return len(decoded) > 0 and len(content) > 50
        except:
            return False
    
    def migrate_plaintext_key(self) -> bool:
        """기존 평문 API 키를 암호화하여 마이그레이션"""
        try:
            if not config.OPENROUTER_API_KEY_FILE.exists():
                return False

            # 파일 읽기
            with open(config.OPENROUTER_API_KEY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                return False
            
            # 이미 암호화되어 있으면 마이그레이션 불필요
            if self.is_encrypted(content):
                return False
            
            # 평문 키를 암호화하여 저장
            encrypted = self.encrypt_api_key(content)
            with open(config.OPENROUTER_API_KEY_FILE, 'w', encoding='utf-8') as f:
                f.write(encrypted)
            
            logger.info("Migrated plaintext API key to encrypted format")
            return True
        except Exception as e:
            logger.warning(f"Failed to migrate plaintext API key: {e}")
            return False
    
    def load_openrouter_api_key(self) -> str:
        """OpenRouter API 키를 파일에서 복호화하여 불러오기"""
        try:
            # 마이그레이션 시도 (기존 평문 파일이 있으면 암호화)
            self.migrate_plaintext_key()
            
            if config.OPENROUTER_API_KEY_FILE.exists():
                with open(config.OPENROUTER_API_KEY_FILE, 'r', encoding='utf-8') as f:
                    encrypted = f.read().strip()
                    if encrypted:
                        # 암호화되어 있으면 복호화, 아니면 그대로 반환 (하위 호환성)
                        if self.is_encrypted(encrypted):
                            return self.decrypt_api_key(encrypted)
                        else:
                            # 평문이면 자동으로 암호화하여 저장
                            logger.warning("Found plaintext API key, encrypting...")
                            self.save_openrouter_api_key(encrypted)
                            return encrypted
            return ""
        except Exception as e:
            logger.warning(f"Failed to load OpenRouter API key: {e}")
            return ""
    
    def save_openrouter_api_key(self, api_key: str) -> bool:
        """OpenRouter API 키를 암호화하여 파일에 저장"""
        try:
            # apikey 디렉토리가 없으면 생성
            config.API_KEY_DIR.mkdir(exist_ok=True)
            
            # API 키 암호화하여 저장
            encrypted = self.encrypt_api_key(api_key.strip())
            with open(config.OPENROUTER_API_KEY_FILE, 'w', encoding='utf-8') as f:
                f.write(encrypted)
            
            logger.info(f"OpenRouter API key saved (encrypted) to {config.OPENROUTER_API_KEY_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save OpenRouter API key: {e}")
            return False

