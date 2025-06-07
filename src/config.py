import os
import tempfile

# Get the absolute path of the project's root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Vector Database Path ---
# Use a system's temporary directory for storing ChromaDB.
# This ensures that each app instance (and potentially each user session on some platforms)
# gets its own sandboxed, non-persistent storage. The data will be wiped when the
# Streamlit container restarts, which is the desired behavior for a public app.
# We add a subdirectory to keep things organized.
BASE_VECTOR_DB_PATH = os.path.join(tempfile.gettempdir(), "me_course_companion_chroma")


# --- Upload Directory Path ---
# This can still be relative to the project, as it's for very short-term storage
# before a file is processed.
UPLOAD_DIRECTORY = os.path.join(project_root, "uploaded_files")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)