# tools/_helpers.py
import os
import sys
import time
from pathlib import Path

# Add the project root to the path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

from google import genai
from google.cloud import storage

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
    # Note: This helper might need adjustments if different video clients are used.
    # For now, it assumes the genai client.
    gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
    print("-> Operation submitted. Polling for video result...")
    while not operation.done:
        time.sleep(20)
        operation = gcp_client.operations.get(operation)
        print("  -> Polling for status...")
    if operation.error: raise Exception(f"API Error: {str(operation.error)}")
    # Accessing result might differ between Veo 2 and Veo 3 clients
    if hasattr(operation.result, 'generated_videos'):
        return operation.result.generated_videos[0].video.uri
    elif hasattr(operation.response, 'generated_videos'):
         return operation.response.generated_videos[0].video.uri
    else:
        raise ValueError("Could not find generated video URI in operation result.")