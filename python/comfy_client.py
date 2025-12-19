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
    
    def __init__(self, server_address: str = None, workflow_path: str = None, model_name: str = None, steps: int = None, cfg: float = None, sampler_name: str = None, scheduler: str = None, vae_name: str = None, clip_name: str = None, style: str = "QWEN/Z-image", quality_tag: str = "", negative_prompt: str = "", upscale_model_name: str = None, lora_name: str = None, lora_strength_model: float = None):
        self.server_address = server_address or config.COMFYUI_CONFIG["server_address"]
        self.workflow_path = workflow_path or config.COMFYUI_CONFIG["workflow_path"]
        self.model_name = model_name or config.COMFYUI_CONFIG.get("model_name", "Zeniji_mix_ZiT_v1.safetensors")
        self.steps = steps if steps is not None else 9
        self.cfg = cfg if cfg is not None else 1.0
        self.sampler_name = sampler_name or "euler"
        self.scheduler = scheduler or "simple"
        self.vae_name = vae_name or "zImage_vae.safetensors"
        self.clip_name = clip_name or "zImage_textEncoder.safetensors"
        self.style = style or "QWEN/Z-image"
        self.quality_tag = quality_tag or ""
        self.negative_prompt = negative_prompt or ""
        self.upscale_model_name = upscale_model_name or config.COMFYUI_CONFIG.get("upscale_model_name", "4x-UltraSharp.pth")
        self.lora_name = lora_name
        self.lora_strength_model = lora_strength_model
        self.client_id = str(uuid.uuid4())
        self.ws: Optional[websocket.WebSocketApp] = None
        self.ws_connected = False
        self.pending_images: Dict[str, Dict[str, Any]] = {}  # prompt_id -> {filename, subfolder, type}
        self.execution_completed: Dict[str, bool] = {}  # prompt_id -> execution completed flag
        self.execution_errors: Dict[str, str] = {}  # prompt_id -> error message
        # 시간 측정용 변수
        self._last_comfyui_time = 0.0
    
    def _on_message(self, ws, message):
        """웹소켓 메시지 핸들러"""
        if isinstance(message, str):
            data = json.loads(message)
            
            if data.get("type") == "execution_cached":
                logger.debug("Execution cached")
            elif data.get("type") == "executing":
                node = data.get("data", {}).get("node")
                prompt_id = data.get("data", {}).get("prompt_id")
                if node is None:
                    # 실행 완료
                    logger.info("Execution completed")
                    if prompt_id:
                        self.execution_completed[prompt_id] = True
            elif data.get("type") == "progress":
                progress = data.get("data", {}).get("value", 0)
                logger.debug(f"Progress: {progress}%")
            elif data.get("type") == "executed":
                node_id = data.get("data", {}).get("node")
                output = data.get("data", {}).get("output", {})
                prompt_id = data.get("data", {}).get("prompt_id")
                
                # SaveImage 노드의 출력 확인 (노드 ID가 "9"가 아닐 수도 있으므로 동적으로 확인)
                if "images" in output:
                    images = output["images"]
                    if images:
                        image_info = images[0]
                        if prompt_id and prompt_id in self.pending_images:
                            self.pending_images[prompt_id].update({
                                "filename": image_info.get("filename"),
                                "subfolder": image_info.get("subfolder", ""),
                                "type": image_info.get("type", "output")
                            })
                            logger.info(f"Image saved (node {node_id}): {image_info.get('filename')}")
            elif data.get("type") == "execution_error":
                # 실행 에러 처리
                error_data = data.get("data", {})
                prompt_id = error_data.get("prompt_id")
                error_info = error_data.get("error", {})
                error_message = error_info.get("message", "Unknown error")
                error_type = error_info.get("type", "")
                error_details = error_info.get("details", "")
                
                # 업스케일 모델 파일을 찾을 수 없는 경우 더 명확한 메시지
                if "not found" in error_message and "upscale" in error_message.lower():
                    logger.error(f"⚠️ 업스케일 모델 파일을 찾을 수 없습니다: {error_message}")
                    logger.error(f"   환경설정 탭에서 업스케일 모델 이름을 확인하세요.")
                    logger.error(f"   ComfyUI의 upscale_models 폴더에 해당 파일이 있는지 확인하세요.")
                
                if prompt_id:
                    full_error = f"{error_type}: {error_message}" if error_type else error_message
                    if error_details:
                        full_error += f" ({error_details})"
                    self.execution_errors[prompt_id] = full_error
                    logger.error(f"Execution error for prompt {prompt_id}: {full_error}")
    
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
    
    def _check_server_connection(self) -> bool:
        """HTTP 서버 연결 가능 여부 확인"""
        try:
            http_url = f"http://{self.server_address}/system_stats"
            req = urllib.request.Request(http_url)
            req.add_header('Content-Type', 'application/json')
            response = urllib.request.urlopen(req, timeout=3)
            logger.debug(f"ComfyUI 서버 연결 확인 성공: {self.server_address}")
            return True
        except urllib.error.URLError as e:
            logger.error(f"ComfyUI 서버 연결 실패: {self.server_address}")
            logger.error(f"  - 에러: {e}")
            logger.error(f"  - 확인 사항:")
            logger.error(f"    1. ComfyUI 서버가 실행 중인지 확인하세요")
            logger.error(f"    2. 포트 번호가 올바른지 확인하세요 (현재: {self.server_address})")
            logger.error(f"    3. 방화벽이 포트를 차단하지 않는지 확인하세요")
            return False
        except Exception as e:
            logger.error(f"서버 연결 확인 중 예상치 못한 오류: {e}")
            return False
    
    def _connect_websocket(self):
        """웹소켓 연결"""
        if self.ws_connected and self.ws:
            return
        
        # 먼저 HTTP 서버 연결 확인
        if not self._check_server_connection():
            logger.error("ComfyUI HTTP 서버에 연결할 수 없습니다. WebSocket 연결을 시도하지 않습니다.")
            return
        
        ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
        logger.info(f"WebSocket 연결 시도: {ws_url}")
        
        # 기존 연결이 있으면 정리
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            self.ws_connected = False
        
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
            logger.error(f"WebSocket connection timeout: {ws_url}")
            logger.error("ComfyUI 서버가 실행 중인지 확인하세요.")
            logger.error(f"  - 서버 주소: {self.server_address}")
            logger.error(f"  - WebSocket URL: {ws_url}")
    
    def _find_workflow_nodes(self, workflow: dict) -> Dict[str, Any]:
        """워크플로우에서 모든 노드 ID를 찾아서 반환 (fallback 포함)
        
        Returns:
            노드 ID 딕셔너리:
            {
                'positive_prompt': node_id or None,
                'negative_prompt': node_id or None,
                'checkpoint': node_id or None,
                'unet': node_id or None,
                'clip': node_id or None,
                'vae': node_id or None,
                'lora': [node_id, ...],
                'upscale': node_id or None,
                'ksampler_1': node_id or None,
                'ksampler_2': node_id or None,
            }
        """
        nodes = {
            'positive_prompt': None,
            'negative_prompt': None,
            'checkpoint': None,
            'unet': None,
            'clip': None,
            'vae': None,
            'lora': [],
            'upscale': None,
            'ksampler_1': None,
            'ksampler_2': None,
        }
        
        # Positive Prompt (노드 "6")
        if "6" in workflow and isinstance(workflow["6"], dict) and workflow["6"].get("class_type") == "CLIPTextEncode":
            nodes['positive_prompt'] = "6"
        else:
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
                    nodes['positive_prompt'] = node_id
                    logger.warning(f"Positive Prompt 노드를 고정 노드(6)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        # Negative Prompt (노드 "7")
        if "7" in workflow and isinstance(workflow["7"], dict) and workflow["7"].get("class_type") == "CLIPTextEncode":
            nodes['negative_prompt'] = "7"
        else:
            for node_id, node_data in workflow.items():
                if (isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode" 
                    and node_id != nodes['positive_prompt']):
                    nodes['negative_prompt'] = node_id
                    logger.warning(f"Negative Prompt 노드를 고정 노드(7)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        # CheckpointLoaderSimple (노드 "19")
        if "19" in workflow and isinstance(workflow["19"], dict) and workflow["19"].get("class_type") == "CheckpointLoaderSimple":
            nodes['checkpoint'] = "19"
        else:
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "CheckpointLoaderSimple":
                    nodes['checkpoint'] = node_id
                    logger.warning(f"CheckpointLoaderSimple을 고정 노드(19)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        # UNETLoader (노드 "16")
        if "16" in workflow and isinstance(workflow["16"], dict) and workflow["16"].get("class_type") == "UNETLoader":
            nodes['unet'] = "16"
        else:
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "UNETLoader":
                    nodes['unet'] = node_id
                    logger.warning(f"UNETLoader를 고정 노드(16)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        # CLIPLoader (노드 "18")
        if "18" in workflow and isinstance(workflow["18"], dict) and workflow["18"].get("class_type") == "CLIPLoader":
            nodes['clip'] = "18"
        else:
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPLoader":
                    nodes['clip'] = node_id
                    logger.warning(f"CLIPLoader를 고정 노드(18)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        # VAELoader (노드 "17")
        if "17" in workflow and isinstance(workflow["17"], dict) and workflow["17"].get("class_type") == "VAELoader":
            nodes['vae'] = "17"
        else:
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "VAELoader":
                    nodes['vae'] = node_id
                    logger.warning(f"VAELoader를 고정 노드(17)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        # LoraLoader (노드 "35", "28")
        if "35" in workflow and isinstance(workflow["35"], dict) and workflow["35"].get("class_type") == "LoraLoader":
            nodes['lora'].append("35")
        if "28" in workflow and isinstance(workflow["28"], dict) and workflow["28"].get("class_type") == "LoraLoader":
            nodes['lora'].append("28")
        
        if not nodes['lora']:
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "LoraLoader":
                    nodes['lora'].append(node_id)
                    logger.warning(f"LoraLoader를 고정 노드(35, 28)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
        
        # UpscaleModelLoader (노드 "21")
        if "21" in workflow and isinstance(workflow["21"], dict) and workflow["21"].get("class_type") == "UpscaleModelLoader":
            nodes['upscale'] = "21"
        else:
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "UpscaleModelLoader":
                    nodes['upscale'] = node_id
                    logger.warning(f"UpscaleModelLoader를 고정 노드(21)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        # KSampler 첫 번째 (노드 "3")
        if "3" in workflow and isinstance(workflow["3"], dict) and workflow["3"].get("class_type") == "KSampler":
            nodes['ksampler_1'] = "3"
        else:
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "KSampler":
                    nodes['ksampler_1'] = node_id
                    logger.warning(f"KSampler를 고정 노드(3)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        # KSampler 두 번째 (노드 "31", 첫 번째가 아닌 것)
        if "31" in workflow and isinstance(workflow["31"], dict) and workflow["31"].get("class_type") == "KSampler" and nodes['ksampler_1'] != "31":
            nodes['ksampler_2'] = "31"
        else:
            for node_id, node_data in workflow.items():
                if (isinstance(node_data, dict) and node_data.get("class_type") == "KSampler" 
                    and node_id != nodes['ksampler_1']):
                    nodes['ksampler_2'] = node_id
                    if node_id != "31":
                        logger.warning(f"두 번째 KSampler를 고정 노드(31)에서 찾지 못해 순회로 찾음: 노드 {node_id}")
                    break
        
        return nodes
    
    def queue_prompt(self, prompt: dict, nodes: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """프롬프트를 큐에 추가하고 실행
        
        Args:
            prompt: 워크플로우 딕셔너리
            nodes: 노드 ID 딕셔너리 (없으면 자동으로 찾음)
        """
        # 노드 정보가 없으면 다시 찾기 (queue_prompt가 직접 호출된 경우)
        if nodes is None:
            nodes = self._find_workflow_nodes(prompt)
        
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        req.add_header('Content-Type', 'application/json')
        
        # 디버깅: 전송되는 워크플로우 정보 로깅 (값을 주입하는 모든 노드, 찾은 노드 ID 사용)
        logger.debug(f"Queueing prompt to: http://{self.server_address}/prompt")
        logger.debug(f"Client ID: {self.client_id}")
        logger.debug(f"Workflow nodes: {list(prompt.keys())}")
        
        # KSampler 첫 번째
        if nodes['ksampler_1'] and nodes['ksampler_1'] in prompt and isinstance(prompt[nodes['ksampler_1']], dict):
            inputs = prompt[nodes['ksampler_1']].get("inputs", {})
            logger.debug(f"Node {nodes['ksampler_1']} (KSampler): seed={inputs.get('seed', 'N/A')}, steps={inputs.get('steps', 'N/A')}, cfg={inputs.get('cfg', 'N/A')}, sampler={inputs.get('sampler_name', 'N/A')}, scheduler={inputs.get('scheduler', 'N/A')}")
        
        # Positive Prompt
        if nodes['positive_prompt'] and nodes['positive_prompt'] in prompt and isinstance(prompt[nodes['positive_prompt']], dict):
            text = prompt[nodes['positive_prompt']].get("inputs", {}).get("text", "")
            logger.debug(f"Node {nodes['positive_prompt']} (Positive Prompt): text length={len(text)}, preview={text[:100]}..." if len(text) > 100 else f"Node {nodes['positive_prompt']} (Positive Prompt): text={text}")
        
        # Negative Prompt
        if nodes['negative_prompt'] and nodes['negative_prompt'] in prompt and isinstance(prompt[nodes['negative_prompt']], dict):
            text = prompt[nodes['negative_prompt']].get("inputs", {}).get("text", "")
            logger.debug(f"Node {nodes['negative_prompt']} (Negative Prompt): text length={len(text)}, preview={text[:100]}..." if len(text) > 100 else f"Node {nodes['negative_prompt']} (Negative Prompt): text={text}")
        
        # UNETLoader
        if nodes['unet'] and nodes['unet'] in prompt and isinstance(prompt[nodes['unet']], dict):
            logger.debug(f"Node {nodes['unet']} (UNETLoader): model={prompt[nodes['unet']].get('inputs', {}).get('unet_name', 'N/A')}")
        
        # VAELoader
        if nodes['vae'] and nodes['vae'] in prompt and isinstance(prompt[nodes['vae']], dict):
            logger.debug(f"Node {nodes['vae']} (VAELoader): vae={prompt[nodes['vae']].get('inputs', {}).get('vae_name', 'N/A')}")
        
        # CLIPLoader
        if nodes['clip'] and nodes['clip'] in prompt and isinstance(prompt[nodes['clip']], dict):
            logger.debug(f"Node {nodes['clip']} (CLIPLoader): clip={prompt[nodes['clip']].get('inputs', {}).get('clip_name', 'N/A')}")
        
        # CheckpointLoaderSimple
        if nodes['checkpoint'] and nodes['checkpoint'] in prompt and isinstance(prompt[nodes['checkpoint']], dict):
            logger.debug(f"Node {nodes['checkpoint']} (CheckpointLoaderSimple): ckpt={prompt[nodes['checkpoint']].get('inputs', {}).get('ckpt_name', 'N/A')}")
        
        # UpscaleModelLoader
        if nodes['upscale'] and nodes['upscale'] in prompt and isinstance(prompt[nodes['upscale']], dict):
            logger.debug(f"Node {nodes['upscale']} (UpscaleModelLoader): model={prompt[nodes['upscale']].get('inputs', {}).get('model_name', 'N/A')}")
        
        # KSampler 두 번째
        if nodes['ksampler_2'] and nodes['ksampler_2'] in prompt and isinstance(prompt[nodes['ksampler_2']], dict):
            logger.debug(f"Node {nodes['ksampler_2']} (KSampler 두 번째): seed={prompt[nodes['ksampler_2']].get('inputs', {}).get('seed', 'N/A')}")
        
        # LoraLoader 노드들
        for lora_node_id in nodes['lora']:
            if lora_node_id in prompt and isinstance(prompt[lora_node_id], dict):
                inputs = prompt[lora_node_id].get("inputs", {})
                logger.debug(f"Node {lora_node_id} (LoraLoader): lora_name={inputs.get('lora_name', 'N/A')}, strength_model={inputs.get('strength_model', 'N/A')}")
        
        try:
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read())
            prompt_id = result.get("prompt_id")
            if prompt_id:
                logger.info(f"Prompt queued successfully: {prompt_id}")
            else:
                logger.warning(f"Prompt queued but no prompt_id returned: {result}")
            return prompt_id
        except urllib.error.HTTPError as e:
            # HTTP 에러의 경우 응답 본문 읽기
            error_body = ""
            try:
                error_body = e.read().decode('utf-8')
            except:
                error_body = "Could not read error response body"
            
            logger.error(f"❌ 프롬프트 큐 추가 실패: HTTP {e.code} {e.reason}")
            logger.error(f"  - 서버 주소: http://{self.server_address}/prompt")
            logger.error(f"  - 에러 응답: {error_body[:500]}")  # 처음 500자만 표시
            logger.error(f"  - 요청 데이터 크기: {len(data)} bytes")
            
            # 워크플로우 구조 검증
            logger.debug("워크플로우 구조 검증:")
            logger.debug(f"  - 총 노드 수: {len(prompt)}")
            invalid_nodes = []
            for node_id, node_data in prompt.items():
                if not isinstance(node_data, dict):
                    invalid_nodes.append(f"Node {node_id}: not a dict")
                    continue
                if "inputs" not in node_data:
                    invalid_nodes.append(f"Node {node_id}: missing 'inputs' field")
                if "class_type" not in node_data:
                    invalid_nodes.append(f"Node {node_id}: missing 'class_type' field")
            
            if invalid_nodes:
                logger.warning(f"  - 문제가 있는 노드들: {invalid_nodes}")
            else:
                logger.debug("  - 워크플로우 구조는 유효합니다")
            
            return None
        except urllib.error.URLError as e:
            logger.error(f"❌ 서버 연결 실패: {e}")
            logger.error(f"  - 서버 주소: http://{self.server_address}/prompt")
            logger.error(f"  - ComfyUI 서버가 실행 중인지 확인하세요")
            return None
        except Exception as e:
            logger.error(f"❌ 프롬프트 큐 추가 중 예상치 못한 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Optional[bytes]:
        """생성된 이미지 다운로드"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        image_url = f"http://{self.server_address}/view?{url_values}"
        try:
            req = urllib.request.Request(image_url)
            response = urllib.request.urlopen(req, timeout=10)
            image_data = response.read()
            if image_data:
                logger.info(f"이미지 다운로드 성공: {filename} ({len(image_data)} bytes)")
                return image_data
            else:
                logger.warning(f"이미지 데이터가 비어있습니다: {filename}")
                return None
        except urllib.error.HTTPError as e:
            logger.error(f"❌ 이미지 다운로드 실패 (HTTP {e.code}): {filename}")
            logger.error(f"  - URL: {image_url}")
            logger.error(f"  - 서브폴더: {subfolder}, 타입: {folder_type}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"❌ 이미지 다운로드 중 서버 연결 실패: {e}")
            logger.error(f"  - URL: {image_url}")
            return None
        except Exception as e:
            logger.error(f"❌ 이미지 다운로드 중 예상치 못한 오류: {e}")
            logger.error(f"  - URL: {image_url}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_image(self, visual_prompt: str, appearance: str = None, negative_prompt: str = "", seed: int = -1) -> Optional[bytes]:
        """
        이미지 생성
        visual_prompt: LLM이 생성한 상황 묘사
        appearance: 초기 설정에서 받은 외모 묘사 (영어 태그 형식)
        negative_prompt: 네거티브 프롬프트
        seed: 시드값 (-1이면 랜덤)
        """
        # ComfyUI 응답 시간 측정 시작
        comfyui_start_time = time.time()
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
            logger.error(f"❌ 워크플로우 파일을 찾을 수 없습니다: {workflow_path}")
            logger.error(f"  - 프로젝트 루트: {config.PROJECT_ROOT}")
            logger.error(f"  - 원본 경로: {workflow_path_str}")
            logger.error(f"  - 해결 방법:")
            logger.error(f"    1. workflows 폴더에 해당 파일이 있는지 확인하세요")
            logger.error(f"    2. 환경설정 탭에서 워크플로우 경로를 확인하세요")
            return None
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            logger.debug(f"워크플로우 파일 로드 성공: {workflow_path}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ 워크플로우 JSON 파싱 실패: {e}")
            logger.error(f"  - 파일 경로: {workflow_path}")
            logger.error(f"  - 파일이 유효한 JSON 형식인지 확인하세요")
            return None
        except Exception as e:
            logger.error(f"❌ 워크플로우 파일 로드 실패: {e}")
            logger.error(f"  - 파일 경로: {workflow_path}")
            import traceback
            logger.error(traceback.format_exc())
            return None
        
        # 프롬프트 조립: appearance와 visual_prompt를 그대로 합치기
        if appearance:
            full_prompt = f"{appearance}, {visual_prompt}"
        else:
            full_prompt = visual_prompt
        
        # 2D 스타일일 때 quality_tag 추가
        if self.style == "SDXL" and self.quality_tag:
            full_prompt = f"{self.quality_tag}, {full_prompt}"
        
        logger.info(f"Full prompt: {full_prompt}...")
        
        # 노드 찾기 (한 번만 수행)
        nodes = self._find_workflow_nodes(workflow)
        
        # 워크플로우 수정 (찾은 노드 ID 사용)
        if nodes['positive_prompt']:
            workflow[nodes['positive_prompt']]["inputs"]["text"] = full_prompt
        
        if nodes['negative_prompt']:
            # 2D 스타일일 때만 negative_prompt 사용, Real 스타일일 때는 빈 문자열 또는 전달받은 값 사용
            if self.style == "SDXL" and self.negative_prompt:
                workflow[nodes['negative_prompt']]["inputs"]["text"] = self.negative_prompt
            elif negative_prompt:
                # Real 스타일이지만 전달받은 negative_prompt가 있으면 사용
                workflow[nodes['negative_prompt']]["inputs"]["text"] = negative_prompt
            else:
                # 기본값: 빈 문자열
                workflow[nodes['negative_prompt']]["inputs"]["text"] = ""
        
        if nodes['checkpoint']:
            # SDXL 스타일: CheckpointLoaderSimple의 ckpt_name 설정
            workflow[nodes['checkpoint']]["inputs"]["ckpt_name"] = self.model_name
            logger.info(f"CheckpointLoaderSimple (node {nodes['checkpoint']}) model name set to: {self.model_name}")
        
        if nodes['unet']:
            workflow[nodes['unet']]["inputs"]["unet_name"] = self.model_name
            logger.info(f"UNETLoader (node {nodes['unet']}) model name set to: {self.model_name}")
        
        if nodes['clip']:
            workflow[nodes['clip']]["inputs"]["clip_name"] = self.clip_name
            logger.info(f"CLIPLoader (node {nodes['clip']}) clip name set to: {self.clip_name}")
        
        if nodes['vae']:
            workflow[nodes['vae']]["inputs"]["vae_name"] = self.vae_name
            logger.info(f"VAELoader (node {nodes['vae']}) VAE name set to: {self.vae_name}")
        
        # LoRA 설정: LoraLoader 노드에 적용
        if nodes['lora']:
            for node_id in nodes['lora']:
                lora_inputs = workflow[node_id].setdefault("inputs", {})
                if self.lora_name is not None:
                    lora_inputs["lora_name"] = self.lora_name
                if self.lora_strength_model is not None:
                    try:
                        lora_inputs["strength_model"] = float(self.lora_strength_model)
                    except (TypeError, ValueError):
                        logger.warning(f"Invalid LoRA strength_model '{self.lora_strength_model}' for node {node_id}, keeping workflow default")
            logger.info(f"LoRA 설정 적용: nodes {', '.join(nodes['lora'])} name={self.lora_name}, strength_model={self.lora_strength_model}")
        else:
            logger.debug("LoraLoader 노드가 없어 LoRA 설정을 건너뜁니다.")
        
        # UpscaleModelLoader - 업스케일 모델 이름 설정 (설정된 경우에만)
        if nodes['upscale']:
            if self.upscale_model_name:
                current_model_name = workflow[nodes['upscale']]["inputs"].get("model_name", "")
                if current_model_name != self.upscale_model_name:
                    workflow[nodes['upscale']]["inputs"]["model_name"] = self.upscale_model_name
                    logger.info(f"UpscaleModelLoader (node {nodes['upscale']}) model name set to: {self.upscale_model_name}")
                else:
                    logger.debug(f"UpscaleModelLoader (node {nodes['upscale']}) using workflow default: {current_model_name}")
            else:
                # 업스케일 모델 이름이 설정되지 않았으면 워크플로우 기본값 사용
                current_model_name = workflow[nodes['upscale']]["inputs"].get("model_name", "")
                logger.debug(f"UpscaleModelLoader (node {nodes['upscale']}) using workflow default: {current_model_name}")
        
        # KSampler 노드 설정: 시드 및 생성 파라미터 설정
        max_seed = 4294967295
        random_seed = random.randint(1, max_seed)
        
        # 첫 번째 KSampler: 메인 생성 파라미터 사용
        if nodes['ksampler_1']:
            workflow[nodes['ksampler_1']]["inputs"]["seed"] = random_seed
            workflow[nodes['ksampler_1']]["inputs"]["steps"] = self.steps
            workflow[nodes['ksampler_1']]["inputs"]["cfg"] = self.cfg
            workflow[nodes['ksampler_1']]["inputs"]["sampler_name"] = self.sampler_name
            workflow[nodes['ksampler_1']]["inputs"]["scheduler"] = self.scheduler
            logger.info(f"KSampler (node {nodes['ksampler_1']}) 설정: seed={random_seed}, steps={self.steps}, cfg={self.cfg}, sampler={self.sampler_name}, scheduler={self.scheduler}")
        
        # 두 번째 KSampler (2d만): 시드만 랜덤으로 설정 (리파인용이므로 기존 파라미터 유지)
        if nodes['ksampler_2']:
            workflow[nodes['ksampler_2']]["inputs"]["seed"] = random.randint(1, max_seed)
            logger.info(f"KSampler (node {nodes['ksampler_2']}) 시드 설정: {workflow[nodes['ksampler_2']]['inputs']['seed']}")
        
        # 워크플로우 최종 검증 및 로깅
        logger.debug("=" * 50)
        logger.debug("Final workflow validation before sending:")
        logger.debug(f"  - Workflow nodes: {list(workflow.keys())}")
        logger.debug(f"  - Found nodes: {nodes}")
        
        # CheckpointLoaderSimple 노드 확인
        if nodes['checkpoint']:
            logger.debug(f"  - CheckpointLoaderSimple found at node {nodes['checkpoint']}")
            logger.debug(f"    * ckpt_name: {workflow[nodes['checkpoint']].get('inputs', {}).get('ckpt_name', 'MISSING')}")
        
        # 노드 연결 검증
        if nodes['ksampler_1'] and nodes['ksampler_1'] in workflow and isinstance(workflow[nodes['ksampler_1']], dict):
            inputs = workflow[nodes['ksampler_1']].get("inputs", {})
            logger.debug(f"  - Node {nodes['ksampler_1']} connections:")
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
            logger.error("Failed to connect WebSocket to ComfyUI server")
            logger.error("이미지 생성을 중단합니다. ComfyUI 서버 상태를 확인하세요.")
            return None
        
        try:
            # 프롬프트 큐에 추가 (찾은 노드 ID 전달)
            prompt_id = self.queue_prompt(workflow, nodes)
            if not prompt_id:
                return None
            
            # 이미지 정보 대기용 딕셔너리 초기화
            self.pending_images[prompt_id] = {}
            self.execution_completed[prompt_id] = False
            
            # 이미지 생성 완료 대기 (최대 180초)
            max_wait = 180
            wait_interval = 0.5
            waited = 0
            execution_completed_time = None
            post_completion_timeout = 10  # 실행 완료 후 10초 내에 이미지가 없으면 실패
            
            while waited < max_wait:
                # 에러 체크
                if prompt_id in self.execution_errors:
                    error_msg = self.execution_errors[prompt_id]
                    # ComfyUI 응답 시간 측정 완료 (에러)
                    comfyui_elapsed_time = time.time() - comfyui_start_time
                    logger.error(f"❌ 이미지 생성 실패 (ComfyUI 실행 오류): {error_msg}")
                    logger.error(f"  - 프롬프트 ID: {prompt_id}")
                    logger.error(f"⏱️ ComfyUI 응답 시간 (에러): {comfyui_elapsed_time:.2f}s")
                    logger.error(f"  - 가능한 원인:")
                    logger.error(f"    1. 모델 파일을 찾을 수 없음 (모델 이름 확인)")
                    logger.error(f"    2. VAE/CLIP 파일을 찾을 수 없음 (파일 이름 확인)")
                    logger.error(f"    3. 워크플로우 노드 연결 오류")
                    logger.error(f"    4. 메모리 부족 또는 하드웨어 오류")
                    # 정리
                    if prompt_id in self.pending_images:
                        del self.pending_images[prompt_id]
                    if prompt_id in self.execution_completed:
                        del self.execution_completed[prompt_id]
                    del self.execution_errors[prompt_id]
                    # 시간 정보 저장
                    self._last_comfyui_time = comfyui_elapsed_time
                    return None
                
                # 실행 완료 플래그 확인
                if prompt_id in self.execution_completed and self.execution_completed[prompt_id]:
                    if execution_completed_time is None:
                        execution_completed_time = waited
                        logger.info("Execution completed, waiting for image...")
                    
                    # 실행 완료 후 일정 시간 내에 이미지가 없으면 실패 처리
                    if waited - execution_completed_time > post_completion_timeout:
                        logger.error(f"❌ 실행 완료 후 {post_completion_timeout}초 내에 이미지를 받지 못했습니다")
                        logger.error(f"  - 프롬프트 ID: {prompt_id}")
                        logger.error(f"  - 가능한 원인:")
                        logger.error(f"    1. SaveImage 노드가 워크플로우에 없음")
                        logger.error(f"    2. 이미지 저장 경로 문제")
                        logger.error(f"    3. ComfyUI 서버 내부 오류")
                        # 정리
                        if prompt_id in self.pending_images:
                            del self.pending_images[prompt_id]
                        if prompt_id in self.execution_completed:
                            del self.execution_completed[prompt_id]
                        return None
                
                # 이미지 확인
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
                            if prompt_id in self.pending_images:
                                del self.pending_images[prompt_id]
                            if prompt_id in self.execution_completed:
                                del self.execution_completed[prompt_id]
                            # ComfyUI 응답 시간 측정 완료
                            comfyui_elapsed_time = time.time() - comfyui_start_time
                            logger.info(f"Image generated successfully: {filename}")
                            logger.info(f"⏱️ ComfyUI 응답 시간: {comfyui_elapsed_time:.2f}s")
                            # 시간 정보를 인스턴스 변수에 저장 (나중에 전체 완료 로그에서 사용)
                            self._last_comfyui_time = comfyui_elapsed_time
                            return image_data
                
                time.sleep(wait_interval)
                waited += wait_interval
            
            # ComfyUI 응답 시간 측정 완료 (타임아웃)
            comfyui_elapsed_time = time.time() - comfyui_start_time
            logger.error(f"❌ 이미지 생성 타임아웃 ({max_wait}초 초과)")
            logger.error(f"  - 프롬프트 ID: {prompt_id}")
            logger.error(f"  - 실행 완료 여부: {prompt_id in self.execution_completed and self.execution_completed.get(prompt_id, False)}")
            logger.error(f"  - 이미지 정보: {self.pending_images.get(prompt_id, '없음')}")
            logger.error(f"⏱️ ComfyUI 응답 시간 (타임아웃): {comfyui_elapsed_time:.2f}s")
            logger.error(f"  - 가능한 원인:")
            logger.error(f"    1. ComfyUI 서버가 응답하지 않음")
            logger.error(f"    2. 이미지 생성 시간이 너무 오래 걸림")
            logger.error(f"    3. 워크플로우 실행 중 오류 발생 (ComfyUI 콘솔 확인)")
            # 정리
            if prompt_id in self.pending_images:
                del self.pending_images[prompt_id]
            if prompt_id in self.execution_completed:
                del self.execution_completed[prompt_id]
            if prompt_id in self.execution_errors:
                del self.execution_errors[prompt_id]
            # 시간 정보 저장
            self._last_comfyui_time = comfyui_elapsed_time
            return None
            
        except Exception as e:
            # ComfyUI 응답 시간 측정 완료 (에러)
            comfyui_elapsed_time = time.time() - comfyui_start_time
            logger.error(f"❌ 이미지 생성 중 예상치 못한 오류: {e}")
            logger.error(f"⏱️ ComfyUI 응답 시간 (에러): {comfyui_elapsed_time:.2f}s")
            import traceback
            logger.error(traceback.format_exc())
            # 시간 정보 저장
            self._last_comfyui_time = comfyui_elapsed_time
            return None

