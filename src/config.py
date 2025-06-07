import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_VECTOR_DB_PATH = os.path.join(project_root, "chroma_stores")
UPLOAD_DIRECTORY = os.path.join(project_root, "uploaded_files")

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)