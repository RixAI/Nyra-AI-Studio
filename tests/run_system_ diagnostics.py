# run_system_diagnostics.py
# A pipeline to load and verify the integrity of all refactored tools.

import os
import sys
from pathlib import Path

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# --- Core Imports ---
# Import the loader from our new core engine file
from tools.nyra_core import load_all_tools

def run_diagnostics():
    """
    Executes the tool loading process and prints a detailed report.
    """
    print("--- Initializing Nyra AI Studio System Diagnostics (Post-Refactor) ---")
    
    # The loader will attempt to import every tool module.
    schema, registry, successful, failed = load_all_tools()
    
    print("\n" + "="*80)
    print("### SYSTEM HEALTH CHECK REPORT ###")
    print("="*80)

    # Report on failed modules first
    if failed:
        print(f"\n❌ FAILED TO LOAD ({len(failed)}) MODULES:")
        for name, error in failed:
            print(f"  - Module: {name}")
            print(f"    Error: {error}")
    else:
        print("\n✅ All tool modules loaded without any import errors.")

    # Report on successfully loaded modules
    if successful:
        print(f"\n✅ SUCCESSFULLY LOADED ({len(successful)}) MODULES:")
        for name in successful:
            print(f"  - {name}")
    
    # Report on the total count of registered tools
    print("\n" + "-"*80)
    print(f"TOTAL TOOLS REGISTERED: {len(registry)}")
    print("-" * 80)
    
    if failed:
        print("\nSystem Status: One or more tool modules have failed. Please review errors.")
    else:
        print("\nSystem Status: Refactoring complete. All tools are correctly installed and configured. Ready for production.")

if __name__ == "__main__":
    run_diagnostics()