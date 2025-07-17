# config.py (Updated for the brand new 'nicki-one' project)
import os

# --- Google Cloud Project Configuration ---
# 1. Using your new Project ID
PROJECT_ID = "nicki-one"

LOCATION = "us-central1"

# --- Google Cloud Storage Configuration ---
# 2. Using your new bucket name
GCS_BUCKET_NAME = "nicki-one-storage"

# --- Local Workspace Configuration ---
WORKSPACE_DIR = r"C:\Storage\Workspace\Nyra-AI-Studio"

# --- Authentication Configuration ---
# 3. Using the new JSON key file you provided
SERVICE_ACCOUNT_KEY_PATH = os.path.join(WORKSPACE_DIR, r"auth\nicki-one-5a90ea8f1d61.json")