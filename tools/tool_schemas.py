# tools/tool_schemas.py
# Definitive Version 2.1: Converts all relative imports to absolute imports
# to resolve a circular dependency/import order conflict.
#
import inspect
from enum import Enum
from google import genai
from typing import Optional, List

# DEFINITIVE FIX: Changed all relative imports (e.g., '.nyra_storyboarder')
# to absolute imports (e.g., 'tools.nyra_storyboarder') to fix the ImportError.
# CORRECTED: Removed 'assemble_character_sheet' as it does not exist in nyra_character_tools.
from tools.nyra_storyboarder import create_production_plan
from tools.nyra_system_tools import list_files, save_text_file, read_text_file, move_file, copy_file, delete_file, make_directory, frames_to_video, compile_final_video
from tools.nyra_imagen_gen import generate_image, AspectRatio
from tools.nyra_imagen_edit import edit_image
from tools.nyra_veo3_gen import generate_veo3_video
from tools.nyra_veo2_gen import generate_veo2_video
from tools.nyra_veo2_edit import extend_video, inpaint_video
from tools.nyra_lyria import generate_music
from tools.nyra_chirp3 import generate_speech
# CORRECTED: Import actual functions from nyra_character_tools.
from tools.nyra_character_tools import split_and_layout_character_sheet, create_hologram_effect


TYPE_MAP = { str: "string", int: "integer", float: "number", bool: "boolean", Optional[str]: "string", Optional[int]: "integer", Optional[bool]: "boolean" }

def _create_function_declaration(func):
    """Inspects a Python function and creates a FunctionDeclaration schema, with List and Enum support."""
    signature = inspect.signature(func)
    description = inspect.getdoc(func) or ""
    properties = {}
    required = []

    for name, param in signature.parameters.items():
        param_schema = {}
        
        origin_type = getattr(param.annotation, '__origin__', None)
        if origin_type is list or origin_type is List:
            inner_type = param.annotation.__args__[0]
            param_schema["type"] = "array"
            param_schema["items"] = {"type": TYPE_MAP.get(inner_type, "string")}
        elif isinstance(param.annotation, type) and issubclass(param.annotation, Enum):
            param_schema["type"] = "string"
            param_schema["enum"] = [e.value for e in param.annotation]
        else:
            param_schema["type"] = TYPE_MAP.get(param.annotation, "string")

        properties[name] = param_schema
        
        if param.default is inspect.Parameter.empty:
            required.append(name)
            
    return genai.types.FunctionDeclaration(
        name=func.__name__,
        description=description,
        parameters={"type": "object", "properties": properties, "required": required}
    )

# CORRECTED: Updated ALL_FUNCTIONS to include actual functions from nyra_character_tools.
ALL_FUNCTIONS = [
    create_production_plan,
    list_files, save_text_file, read_text_file, move_file, copy_file, delete_file, make_directory, frames_to_video, compile_final_video,
    generate_image, edit_image,
    generate_veo3_video, generate_veo2_video, extend_video, inpaint_video,
    generate_music, generate_speech,
    split_and_layout_character_sheet, # Added actual function
    create_hologram_effect # Added actual function
]

TOOL_REGISTRY = {func.__name__: func for func in ALL_FUNCTIONS}
function_declarations = [_create_function_declaration(func) for func in ALL_FUNCTIONS]
ALL_TOOLS_SCHEMA = genai.types.Tool(function_declarations=function_declarations)