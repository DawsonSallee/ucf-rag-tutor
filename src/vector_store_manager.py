import os
import shutil
import tempfile
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from streamlit.runtime.scriptrunner import get_script_run_ctx # <<< ADD THIS IMPORT

# --- NEW HELPER FUNCTION TO GET A UNIQUE SESSION ID ---
def get_session_id():
    """Returns the unique ID for the current user's browser session."""
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            # This can happen in a non-Streamlit context (like local testing).
            # We'll return a static ID for that case.
            return "local_test_session"
        return ctx.session_id
    except Exception:
        # Fallback if get_script_run_ctx is not available
        return "fallback_session_id"


# --- MODIFIED FUNCTION TO CREATE A SESSION-SPECIFIC PATH ---
def get_subject_db_path(subject_name: str) -> str:
    """Generates a session-specific, unique path for a subject's vector store."""
    session_id = get_session_id()
    # Create a unique base path for this session inside the system's temp directory
    session_base_path = os.path.join(tempfile.gettempdir(), session_id)
    
    sanitized_subject_name = "".join(c if c.isalnum() else "_" for c in subject_name.lower())
    return os.path.join(session_base_path, f"subject_{sanitized_subject_name}_db")


# --- MODIFIED FUNCTION TO LIST SUBJECTS FROM THE SESSION-SPECIFIC PATH ---
def list_available_subjects():
    """Lists subject names based ONLY on the current session's database directories."""
    session_id = get_session_id()
    session_base_path = os.path.join(tempfile.gettempdir(), session_id)
    
    subjects = []
    if os.path.exists(session_base_path):
        for item in os.listdir(session_base_path):
            item_path = os.path.join(session_base_path, item)
            # Check if it's a directory with the expected naming convention
            if os.path.isdir(item_path) and item.startswith("subject_") and item.endswith("_db"):
                subject_name_part = item[len("subject_"):-len("_db")]
                readable_name = subject_name_part.replace("_", " ").title()
                subjects.append(readable_name)
    return sorted(list(set(subjects)))


# --- This function is now PERFECT because it uses the new get_subject_db_path ---
def create_or_load_subject_vector_store(subject_name: str, gemini_api_key: str, docs_to_add=None, embeddings_model=None):
    """
    Creates or loads a vector store in a session-specific directory.
    """
    if embeddings_model is None:
        if not gemini_api_key:
            raise ValueError("CRITICAL: A Gemini API Key must be provided to create the embeddings model.")
        
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            task_type="retrieval_document",
            google_api_key=gemini_api_key
        )
        
    subject_db_path = get_subject_db_path(subject_name)

    if docs_to_add:
        if not os.path.exists(subject_db_path):
            os.makedirs(subject_db_path, exist_ok=True)
            vector_store = Chroma.from_documents(
                documents=docs_to_add,
                embedding=embeddings_model,
                persist_directory=subject_db_path
            )
        else:
            vector_store = Chroma(
                persist_directory=subject_db_path,
                embedding_function=embeddings_model
            )
            vector_store.add_documents(documents=docs_to_add)
    else:
        if os.path.exists(subject_db_path):
            vector_store = Chroma(
                persist_directory=subject_db_path,
                embedding_function=embeddings_model
            )
        else:
            return None
    return vector_store


# --- This function is also PERFECT because it uses the new get_subject_db_path ---
def delete_subject_vector_store(subject_name: str):
    """Deletes the vector store directory for a given subject from the session's storage."""
    subject_db_path = get_subject_db_path(subject_name)
    if os.path.exists(subject_db_path):
        try:
            shutil.rmtree(subject_db_path)
            return True
        except Exception as e:
            print(f"Error deleting session-specific vector store: {e}")
            return False
    else:
        return False