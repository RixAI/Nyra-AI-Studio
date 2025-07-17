# tools/nyra_comfyui_caller.py
# Definitive Version 4.0: Upgraded to control all key parameters dynamically.

import json
import requests
import uuid
import websocket

def find_node_by_title(prompt_workflow: dict, title: str) -> str:
    """Finds a node's ID in a workflow based on its title."""
    for node_id, node_info in prompt_workflow.items():
        if node_info.get("_meta", {}).get("title") == title:
            return node_id
    raise ValueError(f"Node with title '{title}' not found in workflow.")

def find_node_by_type(prompt_workflow: dict, class_type: str) -> str:
    """Finds the first node of a given class_type."""
    for node_id, node_info in prompt_workflow.items():
        if node_info.get("class_type") == class_type:
            return node_id
    raise ValueError(f"Node of type '{class_type}' not found in workflow.")

def execute_comfyui_workflow(
    workflow_api_json_path: str,
    character_ref_path: str,
    pose_skeleton_path: str,
    positive_prompt: str,
    negative_prompt: str,
    output_path_prefix: str,
    height: int = 768,
    width: int = 512,
    seed: int = 0,
    steps: int = 25,
    cfg: float = 8.0
) -> str:
    """
    Loads a ComfyUI workflow, dynamically controls all key parameters,
    and executes it via the local server API.
    """
    print("\n[Tool: execute_comfyui_workflow] (Full Control)")
    server_address = "127.0.0.1:8188"
    client_id = str(uuid.uuid4())

    try:
        with open(workflow_api_json_path, 'r') as f:
            prompt_workflow = json.load(f)

        # --- Dynamically find all required nodes ---
        positive_prompt_node_id = find_node_by_title(prompt_workflow, "Positive Prompt")
        char_image_node_id = find_node_by_title(prompt_workflow, "Character Ref Image")
        pose_image_node_id = find_node_by_title(prompt_workflow, "Pose Skeleton Image")
        negative_prompt_node_id = find_node_by_type(prompt_workflow, "CLIPTextEncode") # Assuming the second one is negative
        latent_image_node_id = find_node_by_type(prompt_workflow, "EmptyLatentImage")
        sampler_node_id = find_node_by_type(prompt_workflow, "KSampler")
        save_image_node_id = find_node_by_type(prompt_workflow, "SaveImage")
        
        # --- Update inputs on all nodes ---
        print(" -> Updating workflow parameters...")
        prompt_workflow[positive_prompt_node_id]["inputs"]["text"] = positive_prompt
        prompt_workflow[negative_prompt_node_id]["inputs"]["text"] = negative_prompt
        prompt_workflow[char_image_node_id]["inputs"]["image"] = character_ref_path
        prompt_workflow[pose_image_node_id]["inputs"]["image"] = pose_skeleton_path
        prompt_workflow[latent_image_node_id]["inputs"]["width"] = width
        prompt_workflow[latent_image_node_id]["inputs"]["height"] = height
        prompt_workflow[sampler_node_id]["inputs"]["seed"] = seed
        prompt_workflow[sampler_node_id]["inputs"]["steps"] = steps
        prompt_workflow[sampler_node_id]["inputs"]["cfg"] = cfg
        prompt_workflow[save_image_node_id]["inputs"]["filename_prefix"] = output_path_prefix

        # --- Execute the workflow ---
        ws = websocket.WebSocket()
        ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
        data = {"prompt": prompt_workflow, "client_id": client_id}
        res = requests.post(f"http://{server_address}/prompt", json=data)
        res.raise_for_status()
        print(" -> Workflow queued successfully. Waiting for completion...")
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executed':
                    break
        ws.close()
        
        message = f"Local workflow executed. Image saved to ComfyUI output with prefix: {output_path_prefix}"
        print(f"✅ SUCCESS: {message}")
        return message

    except Exception as e:
        error_message = f"Failed to execute ComfyUI workflow. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message