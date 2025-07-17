# check_auth.py (Corrected Version)
import google.auth
import os

print("--- Running Authentication Diagnosis ---")

# Check if the environment variable is set
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    print(f"\n[INFO] GOOGLE_APPLICATION_CREDENTIALS is set to: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    print("This will override 'gcloud auth application-default login'.")
else:
    print("\n[INFO] GOOGLE_APPLICATION_CREDENTIALS is not set.")
    print("Using credentials from 'gcloud auth application-default login'.")

try:
    # This is the standard way Google libraries find credentials.
    credentials, project_id = google.auth.default()

    print("\n--- Diagnosis Result ---")
    print(f"✅ Successfully loaded credentials.")
    print(f"Project ID discovered by library: {project_id}")

    # Check for service account email OR user email
    if hasattr(credentials, 'service_account_email'):
         print(f"Credential Type: Service Account ({credentials.service_account_email})")
    elif hasattr(credentials, 'signer_email'):
         print(f"Credential Type: User Account ({credentials.signer_email})")
    else:
         print(f"Credential Type: Unknown (but valid)")


    if project_id == "nick-466006":
        print("\n\033[92m[SUCCESS] Your Python environment is correctly authenticating for project 'nick-466006'.\033[0m")
    else:
        print(f"\n\033[91m[FAILURE] CRITICAL MISMATCH! Your environment is pointing to project '{project_id}'.\033[0m")

except Exception as e:
    print("\n\033[91m--- Authentication Diagnosis FAILED ---")
    print(f"Error: {e}\033[0m")