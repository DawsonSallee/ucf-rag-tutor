# --- 1. Standard library imports ---
from operator import itemgetter

# --- 2. Third-party imports ---
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 3. Local application imports ---
from src import config

# --- SHARED HELPER FUNCTIONS ---

def get_llm(gemini_api_key: str):
    """Initializes and returns the Gemini LLM using a provided API key."""
    # CHANGE THIS CHECK
    if not gemini_api_key:
        raise ValueError("CRITICAL: A valid Gemini API Key must be provided.")

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            # CHANGE THIS LINE
            google_api_key=gemini_api_key,
            temperature=0.2
        )
        return llm
    except Exception as e:
        print(f"ERROR: Failed to initialize ChatGoogleGenerativeAI: {e}")
        raise

def format_docs(docs):
    """Joins the page_content of multiple documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)  

# --- CHAIN CREATION FUNCTIONS ---

def create_rag_qa_chain(vector_store, gemini_api_key: str):
    """Creates a RAG chain for question-answering."""
    llm = get_llm(gemini_api_key) 
    retriever = vector_store.as_retriever()

    rag_prompt_template = """You are an expert Mechanical Engineering Professor and a world-class technical writer. Your goal is to provide a comprehensive, in-depth, and pedagogical answer to the student's question, using the provided context as your primary source.

    **Instructions for Generating the Answer:**

    1.  **Assume No Prior Knowledge:** Start your explanation from fundamental principles. Do not assume the student already understands the topic. Build the answer from the ground up.

    2.  **Synthesize and Structure:**
        - Do not simply repeat sentences from the context. Synthesize the information from all provided context documents into a single, cohesive, well-structured response.
        - Use markdown for formatting: Use headings (###), bold text (**bold**), and bulleted lists (-) to make the answer easy to read and understand.

    3.  **Explain, Don't Just State:**
        - If the context provides a formula, first present the formula, then explain what each variable and symbol in the formula represents.
        - If the context provides a technical term, define it clearly.
        - Explain the "why" behind the concepts. Why is this principle important? What is the application?

    4.  **Use All Relevant Context:** Your answer should be as long and detailed as necessary to be fully comprehensive, drawing from all relevant parts of the provided context.

    5.  **Admit Limitations Gracefully:** If the context is insufficient to provide a detailed answer, first explain everything you *can* from the provided text, and then state what information is missing. For example: "Based on the provided documents, we can see that... However, the documents do not provide the specific formula for calculating X."

    ---
    **CONTEXT FROM COURSE MATERIALS:**
    {context}
    ---

    **STUDENT'S QUESTION:**
    {question}

    **PROFESSOR'S DETAILED TECHNICAL RESPONSE:**
    """
    rag_prompt = PromptTemplate.from_template(rag_prompt_template)

    rag_chain_from_docs = (
        RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
        | rag_prompt
        | llm
        | StrOutputParser()
    )

    rag_chain_with_source = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    ).assign(answer=rag_chain_from_docs)

    return rag_chain_with_source # Returns dict with 'question', 'context' (docs), 'answer'

def create_summarization_chain(vector_store, gemini_api_key: str):
    """
    Creates a RAG chain for generating a comprehensive, multi-part summary using a simple retriever.
    """
    llm = get_llm(gemini_api_key) 

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    summary_prompt_template = """You are an expert academic assistant tasked with creating a comprehensive study guide from the provided text.

    Based on the context below, generate a detailed, multi-section summary. The summary should be easy to read and well-structured.

    ### High-Level Overview
    A single paragraph that concisely summarizes the main subject of the provided text.

    ### Key Topics & Concepts
    - Identify the 3-5 most important topics discussed in the text.
    - For each topic, provide a short, clear explanation.

    ### Concluding Summary
    A final paragraph that ties the key topics together and reiterates the overall importance of the subject matter.

    ---
    Context:
    {context}
    ---

    Comprehensive Summary:
    """
    summary_prompt = PromptTemplate.from_template(summary_prompt_template)

    summarization_chain = (
        # The input to this chain is the topic string (e.g., "bearings").
        {"context": retriever | format_docs, "topic_or_question": RunnablePassthrough()}
        | summary_prompt
        | llm
        | StrOutputParser()
    )
    return summarization_chain

def create_quiz_chain(vector_store, gemini_api_key: str):
    """
    Creates a chain for generating a quiz with cited sources from the vector store.
    The chain returns a dictionary with 'quiz_text' and 'context_docs'.
    """
    llm = get_llm(gemini_api_key) 
    retriever = vector_store.as_retriever()
    quiz_prompt_template = """You are an expert engineering professor creating a quiz.
    Use the following research notes to generate {num_questions} multiple-choice questions. Your goal is to create a helpful study tool, even if the notes are slightly imperfect.

    **CRITICAL RULES:**
    1.  Prioritize creating questions from any substantive technical concepts, equations, or definitions you can find in the notes.
    2.  The text of the question (the 'Q:' line) MUST NOT contain the words "Source", "note", "context", or "document".

    If the notes are suitable, format each question EXACTLY as follows:
    Q: [Question text]
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Option D]
    Answer: [Correct Letter]
    Source: [The exact source identifier, e.g., "[SOURCE 1]"]

    ---
    Research Notes:
    {context}
    ---

    Quiz Questions:"""
    quiz_prompt = PromptTemplate.from_template(quiz_prompt_template)

    # This helper function adds "[SOURCE X]" to each document chunk. It's perfect as is.
    def format_docs_with_sources(docs):
        """Formats docs and adds a source identifier to each."""
        formatted_docs = []
        for i, doc in enumerate(docs):
            source_header = f"[SOURCE {i+1}]"
            formatted_docs.append(f"{source_header}\n{doc.page_content}")
        return "\n\n".join(formatted_docs)

    # This function retrieves docs and prepares them. It also works perfectly as is.
    def retrieve_and_prepare_context(input_dict):
        docs = retriever.invoke(input_dict["context_query"])
        formatted_context = format_docs_with_sources(docs)
        return {
            "formatted_context": formatted_context,
            "num_questions": input_dict["num_questions"],
            "original_docs": docs
        }

    # The LLM part of the chain generates the text with the placeholders.
    llm_quiz_chain = (
        {
            "context": itemgetter("formatted_context"),
            "num_questions": itemgetter("num_questions")
        }
        | quiz_prompt
        | llm
        | StrOutputParser()
    )

    # The final chain returns both the generated text and the source documents for lookup.
    quiz_generation_chain_with_sources = (
        RunnableLambda(retrieve_and_prepare_context)
        | RunnableParallel(
            {
                "quiz_text": llm_quiz_chain,
                "context_docs": itemgetter("original_docs")
            }
        )
    )

    return quiz_generation_chain_with_sources