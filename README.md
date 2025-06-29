# AI-Powered Course Companion

## Project Overview

The AI-Powered Course Companion is a full-stack, RAG-based web application designed to act as a personalized AI tutor for technical documents. Developed for a small business, this application enhances learning by providing an interactive and intelligent platform for users to engage with course materials. It features a secure proxy backend and a conversational agent with advanced tool-use capabilities, all deployed on Azure.

## Features

*   **Personalized AI Tutoring:** Get instant, context-aware answers and explanations from your technical documents.
*   **Conversational Agent:** Interact naturally with the AI through a chat interface.
*   **Tool-Use Capabilities:** The AI agent can leverage various tools to provide more comprehensive and accurate responses.
*   **Secure Proxy Backend:** Ensures secure and efficient communication between the frontend and AI services.
*   **RAG (Retrieval-Augmented Generation) Architecture:** Combines retrieval of relevant information with generative AI for highly accurate and contextually rich responses.

## Technologies Used

The project leverages a modern tech stack to deliver a robust and scalable solution:

*   **Frontend:**
    *   Streamlit (Python) for interactive web application development.
    *   JavaScript for dynamic client-side functionalities.
*   **Backend:**
    *   Python
    *   FastAPI for building robust APIs.
    *   LangChain for orchestrating AI workflows and integrating various models.
    *   VectorDB for efficient storage and retrieval of document embeddings.
*   **Deployment & Infrastructure:**
    *   Azure for cloud hosting and services.
    *   Docker for containerization, ensuring consistent environments across development and deployment.

## Setup and Installation

To set up the AI-Powered Course Companion locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Environment Setup:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt # (Assuming a requirements.txt file exists)
    ```
4.  **Configuration:**
    Set up necessary environment variables (e.g., API keys for AI services, database connection strings). Refer to a `.env.example` file if available.
5.  **Database Setup:**
    Initialize your VectorDB and ingest your technical documents. Specific instructions will depend on the chosen VectorDB.
6.  **Run the Application:**
    *   **Backend:**
        ```bash
        uvicorn main:app --host 0.0.0.0 --port 8000 # (Example for FastAPI)
        ```
    *   **Frontend:**
        ```bash
        streamlit run app.py # (Example for Streamlit)
        ```

## Usage

Once the application is running, navigate to the Streamlit frontend in your web browser. You can then:

*   Upload or select technical documents to be used by the AI.
*   Ask questions related to the documents in the chat interface.
*   Receive personalized explanations and insights from the AI tutor.

## Deployment

The application is designed for deployment on Azure, utilizing Docker containers for scalability and ease of management. Specific deployment instructions for Azure will be provided in a separate `DEPLOYMENT.md` or similar document.

## Contributing

Contributions are welcome! Please refer to `CONTRIBUTING.md` for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.