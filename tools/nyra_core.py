# tools/nyra_core.py
# The definitive core engine for Nyra AI Studio.
# Consolidates helpers, schema generation, model definitions, and the dynamic tool loader.

import os
import sys
import time
import inspect
from pathlib import Path
from enum import Enum
from typing import Optional, List

# --- Path Setup (for imports within this file) ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# --- Dependency Imports ---
from google import genai
from google.cloud import storage
import importlib
import warnings

# ======================================================================
# --- MODEL DEFINITIONS (from models.py) ---
# ======================================================================
MODELS = {
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
    "lyria": ["lyria-002"],
    "imagen_gen": [
        "imagen-4.0-ultra-generate-preview-06-06",
        "imagen-4.0-generate-preview-06-06",
        "imagen-4.0-fast-generate-preview-06-06",
        "imagen-3.0-generate-002",
        "imagen-3.0-fast-generate-001"
    ],
    "imagen_edit": ["imagen-3.0-capability-001"],
    "veo": [
        "veo-3.0-generate-preview",
        "veo-3.0-fast-generate-preview",
        "veo-2.0-generate-001",
        "veo-2.0-generate-exp"
    ],
    "chirp": ["en-US-Chirp3-HD-Charon", "hi-IN-Chirp3-HD-Vindemiatrix"]
}

# ======================================================================
# --- HELPER FUNCTIONS (from _helpers.py) ---
# ======================================================================
def resolve_path_in_workspace(user_path: str) -> Path:
    """Resolves and validates a path within the workspace."""
    workspace_root = Path(config.WORKSPACE_DIR).resolve()
    target_path = (workspace_root / user_path).resolve()
    if workspace_root not in target_path.parents and target_path != workspace_root:
        raise PermissionError(f"Access denied: Path '{user_path}' is outside the allowed workspace.")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path

def upload_to_gcs(local_path: Path, gcs_prefix: str) -> str:
    """Uploads a local file to GCS and returns its URI."""
    storage_client = storage.Client(project=config.PROJECT_ID)
    gcs_path = f"gcs_uploads/{gcs_prefix}/{int(time.time())}_{local_path.name}"
    blob = storage_client.bucket(config.GCS_BUCKET_NAME).blob(gcs_path)
    blob.upload_from_filename(str(local_path))
    uri = f"gs://{config.GCS_BUCKET_NAME}/{gcs_path}"
    print(f"-> GCS Upload: {uri}")
    return uri

def download_from_gcs(gcs_uri: str, output_path: str) -> str:
    """Downloads a file from a GCS bucket to the local workspace."""
    storage_client = storage.Client(project=config.PROJECT_ID)
    print(f"\n[HELPER: download_from_gcs] to '{output_path}'")
    if not gcs_uri or not gcs_uri.startswith("gs://"): raise ValueError("Invalid GCS URI.")
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    destination_path = resolve_path_in_workspace(output_path)
    blob.download_to_filename(str(destination_path))
    print(f"✅ SUCCESS: Download complete.")
    return str(destination_path)

def handle_video_operation(operation) -> str:
    """Polls a video operation for its result."""
    gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
    print("-> Operation submitted. Polling for video result...")
    while not operation.done:
        time.sleep(20)
        operation = gcp_client.operations.get(operation)
        print("  -> Polling for status...")
    if operation.error: raise Exception(f"API Error: {str(operation.error)}")
    if hasattr(operation.result, 'generated_videos'):
        return operation.result.generated_videos[0].video.uri
    elif hasattr(operation.response, 'generated_videos'):
         return operation.response.generated_videos[0].video.uri
    else:
        raise ValueError("Could not find generated video URI in operation result.")

# ======================================================================
# --- SCHEMA GENERATION (from _schema_helper.py) ---
# ======================================================================
TYPE_MAP = {str: "string", int: "integer", float: "number", bool: "boolean"}

def create_function_declaration(func):
    """Inspects a Python function and creates a FunctionDeclaration schema."""
    signature = inspect.signature(func)
    description = inspect.getdoc(func) or ""
    properties = {}
    required = []
    for name, param in signature.parameters.items():
        param_schema = {}
        param_type = param.annotation
        
        # Handle complex types like Optional and List
        origin_type = getattr(param_type, '__origin__', None)
        if origin_type is list or origin_type is List:
            inner_type = param_type.__args__[0]
            param_schema["type"] = "array"
            param_schema["items"] = {"type": TYPE_MAP.get(inner_type, "string")}
        elif isinstance(param_type, type) and issubclass(param_type, Enum):
            param_schema["type"] = "string"
            param_schema["enum"] = [e.value for e in param_type]
        else:
            param_schema["type"] = TYPE_MAP.get(param_type, "string")
            
        properties[name] = param_schema
        if param.default is inspect.Parameter.empty:
            required.append(name)
            
    return genai.types.FunctionDeclaration(
        name=func.__name__,
        description=description,
        parameters={"type": "object", "properties": properties, "required": required}
    )

# ======================================================================
# --- DYNAMIC TOOL LOADER (from tool_loader.py) ---
# ======================================================================
warnings.filterwarnings("ignore")

def load_all_tools():
    """
    Dynamically scans the 'tools' directory, imports modules, and returns
    a full tool schema, a registry of functions, and diagnostic information.
    """
    all_function_declarations = []
    tool_registry = {}
    successful_modules = []
    failed_modules = []
    
    tools_dir = os.path.dirname(__file__)
    if not tools_dir:
        tools_dir = 'tools'

    for filename in sorted(os.listdir(tools_dir)):
        # Load only files that are tool modules (nyra_*), excluding this core file.
        if filename.startswith('nyra_') and filename.endswith('.py') and filename != 'nyra_core.py':
            module_name_short = filename[:-3]
            module_name_full = f"tools.{module_name_short}"
            try:
                module = importlib.import_module(module_name_full)
                if hasattr(module, 'get_tool_declarations') and hasattr(module, 'get_tool_registry'):
                    all_function_declarations.extend(module.get_tool_declarations())
                    tool_registry.update(module.get_tool_registry())
                    successful_modules.append(module_name_short)
                else:
                    failed_modules.append((module_name_short, "Does not contain required get_tool_* functions."))
            except Exception as e:
                failed_modules.append((module_name_short, str(e)))
                
    return genai.types.Tool(function_declarations=all_function_declarations), tool_registry, successful_modules, failed_modules