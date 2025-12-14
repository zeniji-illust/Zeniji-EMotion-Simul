"""
Zeniji Emotion Simul - ComfyUI Client
ComfyUI API 통신 전담 (이미지 생성)
"""

import json
import websocket
import uuid
import urllib.request
import urllib.error
import urllib.parse
import logging
import time
import threading
import random
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
import io
import config

logger = logging.getLogger("ComfyClient")


class ComfyClient:
    """ComfyUI API 클라이언트"""
    
    def __init__(self, server_address: str = None, workflow_path: str = None, model_name: str = None, steps: int = None, cfg: float = None, sampler_name: str = None, scheduler: str = None, vae_name: str = None, clip_name: str = None):
        self.server_address = server_address or config.COMFYUI_CONFIG["server_address"]
        self.workflow_path = workflow_path or config.COMFYUI_CONFIG["workflow_path"]
        self.model_name = model_name or config.COMFYUI_CONFIG.get("model_name", "Zeniji_mix_ZiT_v1.safetensors")
        self.steps = steps if steps is not None else 9
        self.cfg = cfg if cfg is not None else 1.0
        self.sampler_name = sampler_name or "euler"
        self.scheduler = scheduler or "simple"
        self.vae_name = vae_name or "zImage_vae.safetensors"
        self.clip_name = clip_name or "zImage_textEncoder.safetensors"
        self.client_id = str(uuid.uuid4())
        self.ws: Optional[websocket.WebSocketApp] = None
        self.ws_connected = False
        self.pending_images: Dict[str, Dict[str, Any]] = {}  # prompt_id -> {filename, subfolder, type}
    
    def _on_message(self, ws, message):
        """웹소켓 메시지 핸들러"""
        if isinstance(message, str):
            data = json.loads(message)
            
            if data.get("type") == "execution_cached":
                logger.debug("Execution cached")
            elif data.get("type") == "executing":
                if data.get("data", {}).get("node") is None:
                    # 실행 완료
                    logger.info("Execution completed")
            elif data.get("type") == "progress":
                progress = data.get("data", {}).get("value", 0)
                logger.debug(f"Progress: {progress}%")
            elif data.get("type") == "executed":
                node_id = data.get("data", {}).get("node")
                output = data.get("data", {}).get("output", {})
                
                # SaveImage 노드(9)의 출력 확인
                if node_id == "9" and "images" in output:
                    images = output["images"]
                    if images:
                        image_info = images[0]
                        prompt_id = data.get("data", {}).get("prompt_id")
                        if prompt_id and prompt_id in self.pending_images:
                            self.pending_images[prompt_id].update({
                                "filename": image_info.get("filename"),
                                "subfolder": image_info.get("subfolder", ""),
                                "type": image_info.get("type", "output")
                            })
                            logger.info(f"Image saved: {image_info.get('filename')}")
    
    def _on_error(self, ws, error):
        """웹소켓 에러 핸들러"""
        error_msg = str(error)
        if "10061" in error_msg or "connection refused" in error_msg.lower():
            logger.error(f"WebSocket 연결 실패: ComfyUI 서버에 연결할 수 없습니다.")
            logger.error(f"  - 서버 주소: {self.server_address}")
            logger.error(f"  - 확인 사항:")
            logger.error(f"    1. ComfyUI 서버가 실행 중인지 확인하세요")
            logger.error(f"    2. 포트 번호가 올바른지 확인하세요 (환경설정 탭에서 확인)")
            logger.error(f"    3. ComfyUI 서버 주소가 {self.server_address}인지 확인하세요")
        else:
            logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """웹소켓 종료 핸들러"""
        logger.info("WebSocket closed")
        self.ws_connected = False
    
    def _on_open(self, ws):
        """웹소켓 연결 핸들러"""
        logger.info("WebSocket connected")
        self.ws_connected = True
    
    def _connect_websocket(self):
        """웹소켓 연결"""
        if self.ws_connected and self.ws:
            return
        
        ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
        logger.info(f"WebSocket 연결 시도: {ws_url}")
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        # 별도 스레드에서 웹소켓 실행
        ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        ws_thread.start()
        
        # 연결 대기 (최대 5초)
        for _ in range(50):
            if self.ws_connected:
                break
            time.sleep(0.1)
        
        if not self.ws_connected:
            logger.warning(f"WebSocket connection timeout: {ws_url}")
            logger.warning("ComfyUI 서버가 실행 중인지 확인하세요.")
    
    def queue_prompt(self, prompt: dict) -> Optional[str]:
        """프롬프트를 큐에 추가하고 실행"""
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        req.add_header('Content-Type', 'application/json')
        
        # 디버깅: 전송되는 워크플로우 정보 로깅
        logger.debug(f"Queueing prompt to: http://{self.server_address}/prompt")
        logger.debug(f"Client ID: {self.client_id}")
        logger.debug(f"Workflow nodes: {list(prompt.keys())}")
        if "3" in prompt:
            logger.debug(f"Node 3 (KSampler) inputs: {json.dumps(prompt['3'].get('inputs', {}), indent=2)}")
        if "6" in prompt:
            logger.debug(f"Node 6 (Positive Prompt) text length: {len(prompt['6'].get('inputs', {}).get('text', ''))}")
        if "16" in prompt:
            logger.debug(f"Node 16 (UNETLoader) model: {prompt['16'].get('inputs', {}).get('unet_name', 'N/A')}")
        
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read())
            prompt_id = result.get("prompt_id")
            logger.info(f"Prompt queued: {prompt_id}")
            return prompt_id
        except urllib.error.HTTPError as e:
            # HTTP 에러의 경우 응답 본문 읽기
            error_body = ""
            try:
                error_body = e.read().decode('utf-8')
            except:
                error_body = "Could not read error response body"
            
            logger.error(f"Failed to queue prompt: HTTP Error {e.code}: {e.reason}")
            logger.error(f"Error response body: {error_body}")
            logger.error(f"Request URL: http://{self.server_address}/prompt")
            logger.error(f"Request data size: {len(data)} bytes")
            
            # 워크플로우 구조 검증
            logger.debug("Workflow structure validation:")
            logger.debug(f"  - Total nodes: {len(prompt)}")
            for node_id, node_data in prompt.items():
                if "inputs" not in node_data:
                    logger.warning(f"  - Node {node_id} missing 'inputs' field")
                if "class_type" not in node_data:
                    logger.warning(f"  - Node {node_id} missing 'class_type' field")
            
            return None
        except Exception as e:
            logger.error(f"Failed to queue prompt: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Optional[bytes]:
        """생성된 이미지 다운로드"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        try:
            req = urllib.request.Request(f"http://{self.server_address}/view?{url_values}")
            response = urllib.request.urlopen(req)
            return response.read()
        except Exception as e:
            logger.error(f"Failed to get image: {e}")
            return None
    
    def generate_image(self, visual_prompt: str, appearance: str = None, negative_prompt: str = "", seed: int = -1) -> Optional[bytes]:
        """
        이미지 생성
        visual_prompt: LLM이 생성한 상황 묘사
        appearance: 초기 설정에서 받은 외모 묘사 (영어 태그 형식)
        negative_prompt: 네거티브 프롬프트
        seed: 시드값 (-1이면 랜덤)
        """
        # 워크플로우 로드
        workflow_path_str = self.workflow_path
        
        # 절대 경로인 경우에도 PROJECT_ROOT 기준으로 재계산 (빌드된 실행 파일 호환성)
        # workflows 폴더가 포함되어 있으면 PROJECT_ROOT 기준으로 변환
        if "workflows" in workflow_path_str:
            # workflows 이후의 경로 추출 (절대/상대 경로 모두 처리)
            workflows_idx = workflow_path_str.find("workflows")
            relative_part = workflow_path_str[workflows_idx:]
            workflow_path = config.PROJECT_ROOT / relative_part
            logger.debug(f"Resolved workflow path: {workflow_path} (from: {workflow_path_str})")
        else:
            # workflows가 없는 경우 (예외 상황)
            workflow_path = config.PROJECT_ROOT / workflow_path_str
            logger.warning(f"Workflow path doesn't contain 'workflows', using as-is: {workflow_path}")
        
        if not workflow_path.exists():
            logger.error(f"Workflow file not found: {workflow_path}")
            logger.error(f"PROJECT_ROOT: {config.PROJECT_ROOT}")
            logger.error(f"Original path: {workflow_path_str}")
            return None
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            return None
        
        # 프롬프트 조립: appearance와 visual_prompt를 그대로 합치기
        if appearance:
            full_prompt = f"{appearance}, {visual_prompt}"
        else:
            full_prompt = visual_prompt
        
        logger.info(f"Full prompt: {full_prompt[:200]}...")
        
        # 워크플로우 수정
        # 노드 "6": CLIPTextEncode (Positive Prompt)
        if "6" in workflow:
            workflow["6"]["inputs"]["text"] = full_prompt
        
        # 노드 "7": CLIPTextEncode (Negative Prompt)
        if "7" in workflow and negative_prompt:
            workflow["7"]["inputs"]["text"] = negative_prompt
        
        # 노드 "16": UNETLoader - 모델 이름 설정
        if "16" in workflow:
            workflow["16"]["inputs"]["unet_name"] = self.model_name
            logger.info(f"Model name set to: {self.model_name}")
        
        # 노드 "17": VAELoader - VAE 이름 설정
        if "17" in workflow:
            workflow["17"]["inputs"]["vae_name"] = self.vae_name
            logger.info(f"VAE name set to: {self.vae_name}")
        
        # 노드 "18": CLIPLoader - CLIP 이름 설정
        if "18" in workflow:
            workflow["18"]["inputs"]["clip_name"] = self.clip_name
            logger.info(f"CLIP name set to: {self.clip_name}")
        
        # 노드 "3": KSampler - 시드 및 생성 파라미터 설정
        if "3" in workflow:
            # 시드 설정 (항상 랜덤)
            max_seed = 4294967295
            random_seed = random.randint(1, max_seed)
            workflow["3"]["inputs"]["seed"] = random_seed
            
            # 생성 파라미터 설정
            workflow["3"]["inputs"]["steps"] = self.steps
            workflow["3"]["inputs"]["cfg"] = self.cfg
            workflow["3"]["inputs"]["sampler_name"] = self.sampler_name
            workflow["3"]["inputs"]["scheduler"] = self.scheduler
            
            logger.info(f"KSampler 설정: seed={random_seed}, steps={self.steps}, cfg={self.cfg}, sampler={self.sampler_name}, scheduler={self.scheduler}")
        
        # 워크플로우 최종 검증 및 로깅
        logger.debug("=" * 50)
        logger.debug("Final workflow validation before sending:")
        logger.debug(f"  - Workflow nodes: {list(workflow.keys())}")
        logger.debug(f"  - Node 3 (KSampler) exists: {'3' in workflow}")
        logger.debug(f"  - Node 6 (Positive Prompt) exists: {'6' in workflow}")
        logger.debug(f"  - Node 7 (Negative Prompt) exists: {'7' in workflow}")
        logger.debug(f"  - Node 16 (UNETLoader) exists: {'16' in workflow}")
        
        # 노드 연결 검증
        if "3" in workflow:
            inputs = workflow["3"].get("inputs", {})
            logger.debug(f"  - Node 3 connections:")
            logger.debug(f"    * model: {inputs.get('model', 'MISSING')}")
            logger.debug(f"    * positive: {inputs.get('positive', 'MISSING')}")
            logger.debug(f"    * negative: {inputs.get('negative', 'MISSING')}")
            logger.debug(f"    * latent_image: {inputs.get('latent_image', 'MISSING')}")
        
        # 워크플로우 JSON 직렬화 테스트
        try:
            test_json = json.dumps(workflow)
            logger.debug(f"  - Workflow JSON serialization: OK ({len(test_json)} chars)")
        except Exception as json_err:
            logger.error(f"  - Workflow JSON serialization FAILED: {json_err}")
            return None
        
        logger.debug("=" * 50)
        
        # 웹소켓 연결
        self._connect_websocket()
        if not self.ws_connected:
            logger.error("Failed to connect WebSocket")
            return None
        
        try:
            # 프롬프트 큐에 추가
            prompt_id = self.queue_prompt(workflow)
            if not prompt_id:
                return None
            
            # 이미지 정보 대기용 딕셔너리 초기화
            self.pending_images[prompt_id] = {}
            
            # 이미지 생성 완료 대기 (최대 180초)
            max_wait = 180
            wait_interval = 0.5
            waited = 0
            
            while waited < max_wait:
                if prompt_id in self.pending_images:
                    image_info = self.pending_images[prompt_id]
                    if "filename" in image_info:
                        # 이미지 다운로드
                        filename = image_info["filename"]
                        subfolder = image_info.get("subfolder", "")
                        folder_type = image_info.get("type", "output")
                        
                        image_data = self.get_image(filename, subfolder, folder_type)
                        if image_data:
                            # 정리
                            del self.pending_images[prompt_id]
                            logger.info(f"Image generated successfully: {filename}")
                            return image_data
                
                time.sleep(wait_interval)
                waited += wait_interval
            
            logger.error(f"Image generation timeout after {max_wait} seconds")
            if prompt_id in self.pending_images:
                del self.pending_images[prompt_id]
            return None
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

