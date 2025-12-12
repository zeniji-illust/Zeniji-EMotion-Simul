"""
Zeniji Emotion Simul - ComfyUI Client
ComfyUI API 통신 전담 (이미지 생성)
"""

import json
import websocket
import uuid
import urllib.request
import urllib.parse
import logging
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
import io
import config

logger = logging.getLogger("ComfyClient")


class ComfyClient:
    """ComfyUI API 클라이언트"""
    
    def __init__(self, server_address: str = None):
        self.server_address = server_address or config.COMFYUI_CONFIG["server_address"]
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
            logger.warning("WebSocket connection timeout")
    
    def queue_prompt(self, prompt: dict) -> Optional[str]:
        """프롬프트를 큐에 추가하고 실행"""
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        req.add_header('Content-Type', 'application/json')
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read())
            prompt_id = result.get("prompt_id")
            logger.info(f"Prompt queued: {prompt_id}")
            return prompt_id
        except Exception as e:
            logger.error(f"Failed to queue prompt: {e}")
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
        workflow_path = Path(config.COMFYUI_CONFIG["workflow_path"])
        if not workflow_path.exists():
            logger.error(f"Workflow file not found: {workflow_path}")
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
        
        # 노드 "3": KSampler - 시드 설정
        if "3" in workflow and seed >= 0:
            workflow["3"]["inputs"]["seed"] = seed
        
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
            
            # 이미지 생성 완료 대기 (최대 60초)
            max_wait = 60
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

