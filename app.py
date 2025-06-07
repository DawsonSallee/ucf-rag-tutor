try:
    __import__('pysqlite3')
    import sys
    if 'pysqlite3' in sys.modules:
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import os
import re
from src import document_processor, vector_store_manager, rag_chain_builder, config # Your backend modules

# --- Page Configuration ---
st.set_page_config(page_title="ME Course Companion", layout="wide")

# --- Helper Functions ---
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

def load_subject_data(subject_name):
    """Loads vector store and ALL RAG chains for the selected subject."""
    if not st.session_state.get("GEMINI_API_KEY"):
        st.error("Please enter your Google AI API Key in the sidebar to load a subject.")
        return

    if subject_name:
        # Only reset history if the subject is actually changing
        if st.session_state.get('current_subject') != subject_name:
            st.session_state.chat_history = []
            st.session_state.summary_output = ""
            st.session_state.quiz_output = ""

        st.session_state.current_subject = subject_name
        with st.spinner(f"Loading data and building chains for {subject_name}..."):
            vs = vector_store_manager.create_or_load_subject_vector_store(subject_name, st.session_state.GEMINI_API_KEY)
            st.session_state.vector_store = vs
            if vs:
                api_key = st.session_state.GEMINI_API_KEY
                st.session_state.rag_qa_chain = rag_chain_builder.create_rag_qa_chain(vs, api_key)
                st.session_state.summarization_chain = rag_chain_builder.create_summarization_chain(vs, api_key)
                st.session_state.quiz_generation_chain = rag_chain_builder.create_quiz_chain(vs, api_key)
                st.success(f"Switched to subject: {subject_name}. All modes are ready.")
            else:
                st.session_state.rag_qa_chain = None
                st.session_state.summarization_chain = None
                st.session_state.quiz_generation_chain = None
                st.warning(f"No vector store found for {subject_name}. Please upload documents.")
    else: # subject_name is None
        st.session_state.current_subject = None
        st.session_state.vector_store = None
        st.session_state.rag_qa_chain = None
        st.session_state.summarization_chain = None
        st.session_state.quiz_generation_chain = None
        st.session_state.chat_history = []
        st.session_state.summary_output = ""
        st.session_state.quiz_output = ""

def handle_pdf_upload(uploaded_files, subject_name):
    """Processes uploaded PDF files for the given subject."""
    if not subject_name:
        st.error("Please select or add a subject first!")
        return
    if uploaded_files:
        files_processed_successfully = False
        for uploaded_file in uploaded_files:
            file_path = os.path.join(config.UPLOAD_DIRECTORY, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner(f"Processing {uploaded_file.name} for {subject_name}..."):
                try:
                    docs = document_processor.load_pdf(file_path)
                    split_docs = document_processor.split_documents(docs)
                    
                    # <<< MODIFY THIS LINE >>>
                    vector_store_manager.create_or_load_subject_vector_store(
                        subject_name,
                        st.session_state.GEMINI_API_KEY, # Pass the key here
                        docs_to_add=split_docs
                    )
                    st.success(f"Processed and added {uploaded_file.name} to {subject_name}.")
                    files_processed_successfully = True
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {e}")
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)

        if files_processed_successfully:
            # Reload data and rebuild all chains for the current subject as its VS has changed
            load_subject_data(subject_name)
            # Refresh subject list in case a new subject's VS was just created
            st.session_state.subjects = vector_store_manager.list_available_subjects()
            st.rerun() # Rerun to reflect updated chains and subject list


# --- Main App Logic ---
initialize_session_state()

# --- Sidebar for Subject Management ---
with st.sidebar:
    st.header("📚 Course Companion")

    # --- NEW: API Key Input Section ---
    st.subheader("API Configuration")

    # Use a password field to hide the user's key
    user_gemini_key = st.text_input(
        "Enter your Google AI API Key:", 
        type="password", 
        key="gemini_api_key_input"
    )

    # Store the entered key in session state
    if user_gemini_key:
        st.session_state.GEMINI_API_KEY = user_gemini_key
        st.success("API Key saved for this session.")

    # Expander with instructions on how to get a key
    with st.expander("How to get an API Key"):
        st.markdown("""
        1. Go to the [Google AI for Developers](https://aistudio.google.com/app/apikey) website.
        2. Sign in with your Google account.
        3. Click on the **"Create API key in new project"** button.
        4. Your new API key will be generated. Copy the key and paste it into the input box above.
        """)
    st.markdown("---") # Visual separator
    # --- END OF NEW SECTION ---

    st.subheader("Subject Management")

    new_subject_name = st.text_input("Enter New Subject Name", key="new_subject_input")
    if st.button("Add Subject", key="add_subject_btn"):
        if new_subject_name:
            normalized_new_subject = new_subject_name.strip()
            if normalized_new_subject and normalized_new_subject not in st.session_state.subjects:
                st.session_state.subjects.append(normalized_new_subject)
                st.session_state.subjects = sorted(list(set(st.session_state.subjects)))
                st.success(f"Subject '{normalized_new_subject}' added. Select it and upload documents.")
                st.rerun()
            elif not normalized_new_subject:
                 st.warning("Subject name cannot be empty.")
            else:
                st.warning(f"Subject '{normalized_new_subject}' already exists or is invalid.")
        else:
            st.warning("Subject name cannot be empty.")

    if st.session_state.subjects:
        # The on_change callback is a great way to handle subject switching
        selected_subject_from_box = st.selectbox(
            "Select Subject",
            options=st.session_state.subjects,
            index=st.session_state.subjects.index(st.session_state.current_subject) if st.session_state.current_subject in st.session_state.subjects else 0,
            key="subject_selector",
            on_change=lambda: load_subject_data(st.session_state.subject_selector)
        )
        
        # Initial load if no subject is current but subjects list is not empty
        if st.session_state.current_subject is None and st.session_state.subjects:
             load_subject_data(st.session_state.subjects[0])
             st.rerun()

        st.markdown("---")
        st.subheader(f"Documents for: {st.session_state.current_subject or 'No Subject Selected'}")
        uploaded_files = st.file_uploader(
            "Upload PDF(s) to selected subject",
            type="pdf",
            accept_multiple_files=True,
            # Unique key helps reset the uploader widget when the subject changes
            key=f"pdf_uploader_{st.session_state.current_subject or 'nosubject'}"
        )
        if st.button(f"Process Uploaded PDF(s) for {st.session_state.current_subject or ''}", key="process_pdfs_btn"):
            if uploaded_files and st.session_state.current_subject:
                handle_pdf_upload(uploaded_files, st.session_state.current_subject)
            elif not st.session_state.current_subject:
                st.warning("Please select a subject first.")
            else:
                st.warning("No files uploaded.")
        # Your delete logic is also fine
        # ... (keep your delete button logic here) ...


# --- CHANGE START 4: Implement main area with mode switcher ---
if not st.session_state.get("GEMINI_API_KEY"):
    st.title("📚 ME Course Companion")
    st.info("Welcome! Please enter your Google AI API Key in the sidebar to begin.")
elif not st.session_state.current_subject:
    st.title("📚 ME Course Companion")
    st.info("API Key accepted. Now, please select or add a subject from the sidebar to get started.")
elif not st.session_state.vector_store:
    st.title(f"📚 ME Course Companion: {st.session_state.current_subject}")
    st.info(f"No documents processed yet for '{st.session_state.current_subject}'. Please upload and process PDFs for this subject to enable the different modes.")
else:
    # This block runs ONLY when an API key is present, a subject is selected, and it has data.
    st.title(f"📚 ME Course Companion: {st.session_state.current_subject}")

    # ---- MODE SELECTION RADIO BUTTONS ----
    st.markdown("---")
    chain_options = ["Q&A", "Summarize Subject", "Generate Quiz"]
    selected_chain_type = st.radio(
         "Select Mode:",
         options=chain_options,
         index=chain_options.index(st.session_state.active_chain_type),
         horizontal=True, # Makes radio buttons appear side-by-side
    )

    if selected_chain_type != st.session_state.active_chain_type:
        st.session_state.active_chain_type = selected_chain_type
        st.rerun() # Rerun to refresh the UI for the new mode

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