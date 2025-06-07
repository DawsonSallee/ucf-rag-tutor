import os
import shutil # For deleting directories
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from src import config # Import your config module

def get_subject_db_path(subject_name: str) -> str:
    """Generates a sanitized, unique path for a subject's vector store."""
    sanitized_subject_name = "".join(c if c.isalnum() else "_" for c in subject_name.lower())
    return os.path.join(config.BASE_VECTOR_DB_PATH, f"subject_{sanitized_subject_name}_db")

def create_or_load_subject_vector_store(subject_name: str, docs_to_add=None, embeddings_model=None):
    """
    Creates a new vector store for a subject or loads an existing one.
    Adds documents if provided.
    Returns the Chroma vector store object.
    """
    if embeddings_model is None:
        # First, it's good practice to check if config.GEMINI_API_KEY actually has a value
        if not config.GEMINI_API_KEY:
            # This stops the program if the key isn't loaded, preventing further errors.
            # You could also print an error and return None, or handle it differently.
            raise ValueError("CRITICAL: GEMINI_API_KEY not found in config. Cannot create embeddings model.")
        
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            task_type="retrieval_document",
            google_api_key=config.GEMINI_API_KEY  # <<< THIS IS THE ADDED/MODIFIED PART
        )
        
    subject_db_path = get_subject_db_path(subject_name)

    if docs_to_add:
        if not os.path.exists(subject_db_path):
            # Create new store if it doesn't exist
            os.makedirs(subject_db_path, exist_ok=True)
            vector_store = Chroma.from_documents(
                documents=docs_to_add,
                embedding=embeddings_model,
                persist_directory=subject_db_path
            )
            print(f"Created new vector store for subject '{subject_name}' at {subject_db_path} with {len(docs_to_add)} documents.")
        else:
            # Load existing store and add new documents
            vector_store = Chroma(
                persist_directory=subject_db_path,
                embedding_function=embeddings_model
            )
            vector_store.add_documents(documents=docs_to_add)
            print(f"Added {len(docs_to_add)} documents to existing vector store for subject '{subject_name}'.")
    else:
        # Just load the existing store if no docs to add
        if os.path.exists(subject_db_path):
            vector_store = Chroma(
                persist_directory=subject_db_path,
                embedding_function=embeddings_model
            )
            print(f"Loaded existing vector store for subject '{subject_name}' from {subject_db_path}.")
        else:
            print(f"No existing vector store found for subject '{subject_name}' at {subject_db_path}.")
            return None # No store to load
    return vector_store

def list_available_subjects():
    """Lists subject names based on existing database directories."""
    subjects = []
    if os.path.exists(config.BASE_VECTOR_DB_PATH):
        for item in os.listdir(config.BASE_VECTOR_DB_PATH):
            if os.path.isdir(os.path.join(config.BASE_VECTOR_DB_PATH, item)) and item.startswith("subject_") and item.endswith("_db"):
                # Extract subject name (e.g., from "subject_thermodynamics_db")
                subject_name_part = item[len("subject_"):-len("_db")]
                # Convert snake_case back to something more readable if needed (simple version here)
                readable_name = subject_name_part.replace("_", " ").title()
                subjects.append(readable_name)
    return sorted(list(set(subjects))) # Ensure uniqueness and sort

def delete_subject_vector_store(subject_name: str):
    """Deletes the vector store directory for a given subject."""
    subject_db_path = get_subject_db_path(subject_name)
    if os.path.exists(subject_db_path):
        try:
            shutil.rmtree(subject_db_path)
            print(f"Successfully deleted vector store for subject '{subject_name}' at {subject_db_path}.")
            return True
        except Exception as e:
            print(f"Error deleting vector store for subject '{subject_name}': {e}")
            return False
    else:
        print(f"No vector store found to delete for subject '{subject_name}'.")
        return False
