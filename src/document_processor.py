from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_pdf(file_path):
    """Loads a PDF file and returns a list of Document objects."""
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return documents

def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """Splits a list of Document objects into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = text_splitter.split_documents(documents)
    return split_docs
