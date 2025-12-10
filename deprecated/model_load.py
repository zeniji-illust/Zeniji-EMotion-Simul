import logging
from pathlib import Path
import sys
from typing import Optional

from llama_cpp import Llama

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    """
    llama-cpp 기반 Qwen GGUF 로더
    - 대상 파일: models/qwen2.5-14b-instruct-q6_k.gguf
    - GPU 전체 오프로딩(n_gpu_layers=-1)
    - 컨텍스트 길이 넉넉히 설정(n_ctx=8192 기본)
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.qwen: Optional[Llama] = None

    def _ensure_exists(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

    def load_qwen(
        self,
        filename: str = "qwen2.5-14b-instruct-q6_k.gguf",
        n_ctx: int = 8192,
        n_gpu_layers: int = -1,
        n_threads: Optional[int] = None,
        force_reload: bool = False,
    ) -> Llama:
        """
        Qwen 14B GGUF 로드 (llama-cpp)
        - n_gpu_layers=-1: 전체 GPU 오프로딩
        - n_ctx: 컨텍스트 길이 (기본 8192)
        """
        if self.qwen is not None and not force_reload:
            logger.info("Qwen model already loaded. Skipping reload.")
            return self.qwen

        model_path = self.models_dir / filename
        self._ensure_exists(model_path)

        logger.info(f"Loading Qwen GGUF from {model_path}")
        self.qwen = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            n_threads=n_threads,
            verbose=False,
        )
        logger.info("Qwen GGUF load complete.")
        return self.qwen

    def unload_qwen(self):
        """모델 언로드 및 메모리 해제"""
        self.qwen = None
        logger.info("Qwen model unloaded.")


if __name__ == "__main__":
    loader = ModelLoader()
    model = loader.load_qwen()
    # 짧은 테스트 프롬프트
    prompt = "다음 문장을 1문장으로 응답해줘: 안녕, 기분 어때?"
    out = model(prompt, max_tokens=64)
    logger.info(out.get("choices", [{}])[0].get("text", "").strip())