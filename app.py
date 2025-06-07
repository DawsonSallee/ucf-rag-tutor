__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os
import re
from src import document_processor, vector_store_manager, rag_chain_builder, config # Your backend modules

# --- Page Configuration ---
st.set_page_config(page_title="ME Course Companion", layout="wide")

# --- Helper Functions ---

@st.cache_resource
def load_and_build_chains_for_subject(_subject_name, _gemini_api_key):
    """
    Loads a vector store and builds all AI chains for a given subject and API key.
    This function is cached by Streamlit. The underscores in the arguments (_subject_name, 
    _gemini_api_key) are a convention to show they are used as cache keys.
    """
    if not _subject_name or not _gemini_api_key:
        return None, None, None, None

    # Load the specific vector store using the user's key for the embedding model
    vs = vector_store_manager.create_or_load_subject_vector_store(_subject_name, _gemini_api_key)
    
    if vs:
        # If the store exists, build all AI chains using it and the user's key
        rag_qa_chain = rag_chain_builder.create_rag_qa_chain(vs, _gemini_api_key)
        summarization_chain = rag_chain_builder.create_summarization_chain(vs, _gemini_api_key)
        quiz_generation_chain = rag_chain_builder.create_quiz_chain(vs, _gemini_api_key)
        return vs, rag_qa_chain, summarization_chain, quiz_generation_chain
    else:
        # Return nothing if no database exists for this subject
        return None, None, None, None
    
def initialize_session_state():
    """Initializes Streamlit session state variables."""

    if "GEMINI_API_KEY" not in st.session_state:
        st.session_state.GEMINI_API_KEY = None
    
    if "subjects" not in st.session_state:
        st.session_state.subjects = vector_store_manager.list_available_subjects()
    if "current_subject" not in st.session_state:
        st.session_state.current_subject = st.session_state.subjects[0] if st.session_state.subjects else None
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None

    # Chain related state
    if "active_chain_type" not in st.session_state:
        st.session_state.active_chain_type = "Q&A" # Default to Q&A
    if "rag_qa_chain" not in st.session_state:
        st.session_state.rag_qa_chain = None
    if "summarization_chain" not in st.session_state:
        st.session_state.summarization_chain = None
    if "quiz_generation_chain" not in st.session_state:
        st.session_state.quiz_generation_chain = None

    # Output related state
    if "chat_history" not in st.session_state: # Used for Q&A
        st.session_state.chat_history = []
    if "summary_output" not in st.session_state: # Used for Summarization
        st.session_state.summary_output = ""
    if "quiz_output" not in st.session_state: # Used for Quiz
        st.session_state.quiz_output = ""

# --- Main App Logic ---
initialize_session_state()

# --- Sidebar for Subject Management ---
# <<< REPLACE YOUR ENTIRE 'with st.sidebar:' BLOCK WITH THIS >>>
with st.sidebar:
    st.header("📚 Course Companion")
    st.subheader("API Configuration")

    # Get API key from user
    user_gemini_key = st.text_input(
        "Enter your Google AI API Key:", type="password", help="Your key is only used for this session."
    )

    # Logic to handle a new or updated API key
    if user_gemini_key and st.session_state.get("GEMINI_API_KEY") != user_gemini_key:
        # A new key was entered. This is our trigger for a "new instance".
        # We clear the resource cache to force all AI chains to be rebuilt.
        st.cache_resource.clear()
        # We also reset the chat history for the new user.
        st.session_state.chat_history = []
        st.session_state.GEMINI_API_KEY = user_gemini_key
        st.success("API Key accepted. App has been reset for the new key.")
        st.rerun() # Rerun to apply changes immediately
    elif user_gemini_key:
        # If the key is the same, just make sure it's stored
        st.session_state.GEMINI_API_KEY = user_gemini_key

    with st.expander("How to get an API Key"):
        st.markdown("""
        1. Go to the [Google AI for Developers](https://aistudio.google.com/app/apikey) website.
        2. Sign in with your Google account.
        3. Click on the **"Create API key in new project"** button.
        4. Your new API key will be generated. Copy the key and paste it into the input box above.
        """)

    st.markdown("---")
    st.subheader("Subject Management")

    subjects = vector_store_manager.list_available_subjects()
    new_subject_name = st.text_input("Add New Subject")
    if st.button("Add") and new_subject_name.strip():
        if new_subject_name.strip() not in subjects:
            subjects.append(new_subject_name.strip())
            subjects.sort()
            # No DB is created yet, just updating the list for the UI
    
    st.selectbox(
        "Select Subject", 
        options=subjects, 
        key="current_subject" # This directly binds the dropdown's selection to our session state
    )
    
    st.markdown("---")
    st.subheader(f"Documents for: {st.session_state.current_subject or '...'}")
    
    uploaded_files = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True)
    if st.button("Process Uploaded PDF(s)"):
        if uploaded_files and st.session_state.current_subject and st.session_state.GEMINI_API_KEY:
            # When new files are processed, we must clear the cache so the chains are rebuilt
            load_and_build_chains_for_subject.clear()
            
            with st.spinner("Processing documents..."):
                for uploaded_file in uploaded_files:
                    # Simplified upload handling
                    file_path = os.path.join(config.UPLOAD_DIRECTORY, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    try:
                        docs = document_processor.load_pdf(file_path)
                        split_docs = document_processor.split_documents(docs)
                        vector_store_manager.create_or_load_subject_vector_store(
                            st.session_state.current_subject, st.session_state.GEMINI_API_KEY, docs_to_add=split_docs
                        )
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {e}")
                    finally:
                        if os.path.exists(file_path):
                            os.remove(file_path)
            st.success("Documents processed successfully. Reloading...")
            st.rerun()
        else:
            st.warning("Please select a subject, provide an API key, and upload a file.")


# --- CHANGE START 4: Implement main area with mode switcher ---
st.title("📚 ME Course Companion")

# 1. Main Gatekeeping Logic
if not st.session_state.get("GEMINI_API_KEY"):
    st.info("Welcome! Please enter your Google AI API Key in the sidebar to begin.")
elif not st.session_state.get("current_subject"):
    st.info("API Key accepted. Now, please add or select a subject from the sidebar to get started.")
else:
    # 2. Call the cached function to get the necessary objects for the current state.
    # This will be instant if the chains have already been built for this subject/key.
    with st.spinner(f"Loading resources for {st.session_state.current_subject}..."):
        vector_store, rag_qa_chain, summarization_chain, quiz_generation_chain = load_and_build_chains_for_subject(
            st.session_state.current_subject,
            st.session_state.GEMINI_API_KEY
        )

    # 3. Check if the subject has processed documents yet
    if not vector_store:
        st.warning(f"No documents have been processed for '{st.session_state.current_subject}'. Please upload a PDF for this subject in the sidebar.")
    else:
        # 4. If everything is ready, display the main app interface
        st.markdown(f"### Current Subject: {st.session_state.current_subject}")
        st.markdown("---")
        
        chain_options = ["Q&A", "Summarize Subject", "Generate Quiz"]
        st.radio(
            "Select Mode:",
            options=chain_options,
            key="active_chain_type",
            horizontal=True
        )
        st.markdown("---")

    # --- Q&A Mode ---
    if st.session_state.active_chain_type == "Q&A":
        st.subheader("💬 Chat Q&A")
        if st.session_state.rag_qa_chain:
            # Display chat history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # User input
            if prompt := st.chat_input(f"Ask a question about {st.session_state.current_subject}..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response_dict = st.session_state.rag_qa_chain.invoke(prompt)
                        answer = response_dict.get("answer", "Sorry, I couldn't find an answer.")
                        st.markdown(answer)
                        # Store assistant response in history
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})

                    # Optional: Display sources
                    sources = response_dict.get("context", [])
                    if sources:
                        with st.expander("View Sources Used"):
                            for i, doc in enumerate(sources):
                                source_name = doc.metadata.get('source', 'Unknown')
                                page_num = doc.metadata.get('page', 'N/A')
                                st.markdown(f"**Source {i+1}:** `{os.path.basename(source_name)}` (Page: {page_num})")
                                st.caption(f"> {doc.page_content[:250].replace(chr(10), ' ')}...")
        else:
            st.warning("Q&A chain not available. An error might have occurred during loading.")

    # --- Summarize Subject Mode ---
    elif st.session_state.active_chain_type == "Summarize Subject":
        st.subheader("📝 Comprehensive Subject Summary")
        if st.session_state.summarization_chain:
            
            # We can still allow for an optional topic for more targeted summaries
            summary_topic_input = st.text_input(
                "Enter a specific topic to summarize (optional):",
                placeholder=f"Leave blank for a summary of the whole subject"
            )
            
            if st.button("Generate Comprehensive Summary", key="summarize_btn"):
                with st.spinner("Generating comprehensive summary... This may take a moment."):
                    
                    # Use the user's topic if provided, otherwise summarize the whole subject
                    if summary_topic_input.strip():
                        final_topic = summary_topic_input.strip()
                    else:
                        final_topic = f"A comprehensive overview of the key topics in {st.session_state.current_subject}"

                    summary = st.session_state.summarization_chain.invoke(final_topic)
                    st.session_state.summary_output = summary

            if st.session_state.summary_output:
                st.markdown("### Summary:")
                # Use st.code() to match the quiz UI for a clean look
                st.code(st.session_state.summary_output, language="markdown")
        else:
            st.warning("Summarization chain not available. An error might have occurred during loading.")
    # --- Generate Quiz Mode ---
    elif st.session_state.active_chain_type == "Generate Quiz":
        st.subheader("❓ Generate Quiz")
        if 'quiz_sources' not in st.session_state:
            st.session_state.quiz_sources = []

        if st.session_state.quiz_generation_chain:
            topic_input = st.text_input(
                "Enter a specific topic for the quiz (e.g., 'Carnot Cycle', 'Fluid Viscosity'):",
                placeholder="Leave blank to quiz on the whole subject"
            )
            num_questions = st.number_input("Number of questions to generate:", min_value=1, max_value=10, value=3, step=1)

            if st.button("Generate Quiz", key="quiz_btn"):
                if not topic_input.strip() and not st.session_state.current_subject:
                    st.warning("Please enter a topic or select a subject.")
                else:
                    with st.spinner(f"Generating a {num_questions}-question quiz..."):
                        if topic_input.strip():
                            final_query = topic_input.strip()
                        else:
                            final_query = f"Key concepts from the subject {st.session_state.current_subject}"

                        quiz_input = {"context_query": final_query, "num_questions": num_questions}
                        quiz_result_dict = st.session_state.quiz_generation_chain.invoke(quiz_input)
                        
                        st.session_state.quiz_output = quiz_result_dict.get("quiz_text", "")
                        st.session_state.quiz_sources = quiz_result_dict.get("context_docs", [])

            if st.session_state.quiz_output:
                st.markdown("---")
                st.markdown("### Generated Quiz:")

                raw_quiz_text = st.session_state.quiz_output
                
                # 1. Check if the LLM refused to generate a quiz.
                refusal_message = "The retrieved context is not suitable"
                if refusal_message in raw_quiz_text:
                    # If it refused, display the refusal message as a warning.
                    st.warning(raw_quiz_text)
                else:
                    # 2. If it did NOT refuse, proceed with the normal parsing logic.
                    source_docs = st.session_state.quiz_sources
                    question_blocks = raw_quiz_text.strip().split('Q:')[1:]
                    
                    processed_text_parts = []
                    for block in question_blocks:
                        full_question_text = "Q:" + block.strip()
                        match = re.search(r"Source: \[SOURCE (\d+)\]", full_question_text)
                        
                        if match and source_docs:
                            source_num = int(match.group(1))
                            if 1 <= source_num <= len(source_docs):
                                doc = source_docs[source_num - 1]
                                source_name = os.path.basename(doc.metadata.get('source', 'Unknown'))
                                page_num = doc.metadata.get('page', 'N/A')
                                
                                cleaned_content = re.sub(r'[^a-zA-Z0-9\s.,()-]+', '', doc.page_content)
                                normalized_text = re.sub(r'\s+', ' ', cleaned_content).strip()
                                snippet_words = normalized_text.split()[:20]
                                snippet = " ".join(snippet_words) + "..." if snippet_words else ""
                                
                                rich_source_info = f'Source: {source_name} (Page: {page_num}) - "{snippet}"'
                                final_question_block = full_question_text.replace(match.group(0), rich_source_info)
                                processed_text_parts.append(final_question_block)
                            else:
                                processed_text_parts.append(full_question_text)
                        else:
                            processed_text_parts.append(full_question_text)
                    
                    final_display_text = "\n\n".join(processed_text_parts)
                    st.code(final_display_text, language=None)
                
        else:
            st.warning("Quiz generation chain not available. An error might have occurred during loading.")

# Placeholder for other features (Summarization, Quiz) to be added in Phase 3
# if st.session_state.current_subject and st.session_state.vector_store:
#     st.markdown("---")
#     st.subheader("Other Tools")
#     # Add buttons/inputs for Summary, Compare, Quiz here