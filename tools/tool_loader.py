# tools/tool_loader.py
# DEFINITIVE VERSION 2.0: Adds global warning suppression.

import os
import importlib

# DEFINITIVE FIX: Suppress warnings here to ensure they are silenced before any
# other tool modules that might trigger them are imported.
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module='controlnet_aux.*')

from google.genai.types import Tool

def load_all_tools():
    """
    Dynamically scans the 'tools' directory, imports modules starting with 'nyra_',
    and aggregates their schemas and function registries.
    """
    all_function_declarations = []
    tool_registry = {}
    tools_dir = os.path.dirname(__file__)
    
    # Correctly resolve the path to the tools directory
    if not tools_dir:
        tools_dir = 'tools'

    for filename in os.listdir(tools_dir):
        if filename.startswith('nyra_') and filename.endswith('.py'):
            module_name = f"tools.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, 'get_tool_declarations') and hasattr(module, 'get_tool_registry'):
                    all_function_declarations.extend(module.get_tool_declarations())
                    tool_registry.update(module.get_tool_registry())
            except Exception as e:
                print(f"Warning: Could not load tools from {module_name}. Error: {e}")
                
    return Tool(function_declarations=all_function_declarations), tool_registry

ALL_TOOLS_SCHEMA, TOOL_REGISTRY = load_all_tools()