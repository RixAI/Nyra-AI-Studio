# tools/_schema_helper.py
import inspect
from enum import Enum
from google import genai
from typing import Optional, List

TYPE_MAP = {str: "string", int: "integer", float: "number", bool: "boolean", Optional[str]: "string", Optional[int]: "integer", Optional[bool]: "boolean"}

def create_function_declaration(func):
    """Inspects a Python function and creates a FunctionDeclaration schema."""
    signature = inspect.signature(func)
    description = inspect.getdoc(func) or ""
    properties = {}
    required = []
    for name, param in signature.parameters.items():
        param_schema = {}
        param_type = param.annotation
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