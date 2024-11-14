import streamlit as st
import requests
import fitz  # PyMuPDF for PDF handling
from docx import Document

# Title and authentication
st.title("Enhanced Claude Chatbot with File Analysis")

# Password for app access
app_password = st.text_input("Enter the app password:", type="password")
correct_password = "your_secure_password_here"  # Set this password securely

if app_password == correct_password:
    # Claude API Key input
    claude_api_key = st.text_input("Enter Claude API Key:", type="password")
    
    # Claude API endpoints
    CLAUDE_API_MODELS_URL = "https://api.anthropic.com/v1/models"
    CLAUDE_API_CHAT_URL = "https://api.anthropic.com/v1/complete"

    # Function to get available models
    def get_available_models(api_key):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(CLAUDE_API_MODELS_URL, headers=headers)
        response.raise_for_status()
        models = response.json().get("models", [])
        return models

    # Function to interact with Claude API
    def get_claude_response(prompt, model, api_key):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "prompt": prompt,
            "model": model,
            "max_tokens_to_sample": 150
        }
        response = requests.post(CLAUDE_API_CHAT_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("completion")

    # Retrieve and display available models after API key input
    if claude_api_key:
        try:
            models = get_available_models(claude_api_key)
            selected_model = st.selectbox("Choose a Claude Model:", models)
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching models: {e}")
            models = []

    # File handling functions
    def extract_text_from_pdf(file):
        text = ""
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        for page in pdf:
            text += page.get_text("text")
        pdf.close()
        return text

    def extract_text_from_docx(file):
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])

    # File Upload and Analysis
    uploaded_file = st.file_uploader("Upload a PDF or DOCX file", type=["pdf", "docx"])

    if uploaded_file and selected_model:
        file_content = ""
        if uploaded_file.type == "application/pdf":
            file_content = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            file_content = extract_text_from_docx(uploaded_file)

        st.write("Extracted Text from File:")
        st.write(file_content)

        # Analysis with selected model
        if file_content:
            analysis_prompt = f"Analyze the following text:\n\n{file_content[:5000]}"
            try:
                analysis_response = get_claude_response(analysis_prompt, selected_model, claude_api_key)
                st.write("Claude's Analysis:")
                st.write(analysis_response)
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {e}")

    # Chat feature with selected model
    user_input = st.text_input("You:", placeholder="Type your message here...")
    if user_input and selected_model:
        try:
            bot_response = get_claude_response(user_input, selected_model, claude_api_key)
            st.write(f"Claude: {bot_response}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")
else:
    st.warning("Please enter the correct password to access the app.")
