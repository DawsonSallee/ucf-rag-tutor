import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
# It's good practice to specify the path to .env if it's not in the same directory as this script
# or if the script might be run from different locations.
# Assuming .env is in the project root, and this config.py is in src/
# We can construct the path to the .env file.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Gets the parent directory of 'src'
dotenv_path = os.path.join(project_root, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    # Fallback if .env is not found where expected, try loading from current dir or environment
    load_dotenv()
    print(f"Warning: .env file not found at {dotenv_path}. Attempting to load from default locations or environment variables.")


# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # This provides a more informative error if the key isn't found.
    # In a real application, you might handle this more gracefully or have other ways to configure.
    print("ERROR: GEMINI_API_KEY not found. Please ensure it is set in your .env file or as an environment variable.")
    # You might want to raise an exception here or exit if the API key is critical for startup:
    # raise ValueError("GEMINI_API_KEY not found. Application cannot start.")


# --- File Paths and Directories ---

# Base path for storing all subject-specific ChromaDB vector stores
# This will create a 'chroma_stores' directory in your project root if it doesn't exist.
BASE_VECTOR_DB_PATH = os.path.join(project_root, "chroma_stores")

# Directory for temporarily storing uploaded PDF files (used by the Streamlit app later)
# This will create an 'uploaded_files' directory in your project root if it doesn't exist.
UPLOAD_DIRECTORY = os.path.join(project_root, "uploaded_files")

# Ensure these directories exist when the config module is loaded.
# This is a good place to create them if they are essential for the app's operation.
# os.makedirs(BASE_VECTOR_DB_PATH, exist_ok=True) # We'll let vector_store_manager handle this for BASE_VECTOR_DB_PATH
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


# --- Optional: Other Configurations ---
# You can add other settings here as your project grows, for example:
# DEFAULT_CHUNK_SIZE = 1000
# DEFAULT_CHUNK_OVERLAP = 200
# DEFAULT_EMBEDDING_MODEL = "models/embedding-001"
# DEFAULT_LLM_MODEL = "gemini-pro"

# --- Sanity Check (Optional, for debugging during development) ---
# print(f"Project Root: {project_root}")
# print(f".env Path: {dotenv_path}")
# print(f"Gemini API Key Loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
# print(f"Base Vector DB Path: {BASE_VECTOR_DB_PATH}")
# print(f"Upload Directory: {UPLOAD_DIRECTORY}")
  