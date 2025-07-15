#
# config.py
# Nyra AI Studio - Central Configuration (Updated for nick-466006)
#
import os

# --- Google Cloud Project Configuration ---
PROJECT_ID = "nick-466006"
LOCATION = "us-central1"

# --- Google Cloud Storage Configuration ---
GCS_BUCKET_NAME = "nick-storage"

# --- Local Workspace Configuration ---
WORKSPACE_DIR = r"C:\Storage\Workspace\Nyra-AI-Studio"

# --- Authentication Configuration ---
SERVICE_ACCOUNT_KEY_PATH = os.path.join(WORKSPACE_DIR, r"auth\nick-466006-6fb113bb2d1f.json")