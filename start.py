import streamlit as st
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import fitz  # PyMuPDF for PDF handling
from docx import Document

# Initialize session state for conversation history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# App Title and Introduction
st.title("Enhanced Claude Chatbot with File Analysis")
st.write("Chat with Claude or upload a document for analysis.")

# Retrieve secrets
try:
    claude_api_key = st.secrets["claude_api_key"]
    correct_password = st.secrets["app_password"]
except KeyError as e:
    st.error(f"Missing secret: {e}. Please check your Streamlit secrets.")
    st.stop()

# Authentication
app_password = st.text_input("Enter the app password:", type="password")

if app_password == correct_password:
    # Define available models
    available_models = [
        "claude-3-5-sonnet-20241022",
        # Add other supported models if available
    ]

    # Model Selection
    selected_model = st.selectbox("Choose a Claude Model:", available_models)

    # Initialize Anthropic client
    anthropic_client = Anthropic(api_key=claude_api_key)

    # Function to build the prompt
    def build_prompt(conversation):
        prompt = ""
        for message in conversation:
            if message["role"] == "user":
                prompt += f"{HUMAN_PROMPT} {message['content']}"
            else:
                prompt += f"{AI_PROMPT} {message['content']}"
        prompt += AI_PROMPT
        return prompt

    # Function to interact with the Claude API using the SDK
    def get_claude_response(conversation, model, client, max_tokens=4800):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=conversation,
        )

        # Debug: Print the response object
        # st.write("**API Response:**")
        # st.json(response.to_dict())

        # The assistant's reply is in response.content, which is a list of content blocks
        assistant_reply = ""

        for content_block in response.content:
            if content_block.type == 'text':
                assistant_reply += content_block.text

        return assistant_reply.strip()

    # Functions for text extraction from files
    def extract_text_from_pdf(file):
        text = ""
        try:
            pdf = fitz.open(stream=file.read(), filetype="pdf")
            for page in pdf:
                text += page.get_text("text")
            pdf.close()
        except Exception as e:
            st.error(f"Error reading PDF file: {e}")
        return text

    def extract_text_from_docx(file):
        text = ""
        try:
            doc = Document(file)
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            st.error(f"Error reading DOCX file: {e}")
        return text

    # File Upload and Analysis
    st.subheader("File Upload and Analysis")
    uploaded_file = st.file_uploader("Upload a PDF or DOCX file", type=["pdf", "docx"], accept_multiple_files=False)

    if uploaded_file:
        file_content = ""
        if uploaded_file.type == "application/pdf":
            file_content = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            file_content = extract_text_from_docx(uploaded_file)

        if file_content:
            st.write("**Extracted Text from File:**")
            st.write(file_content[:1000] + "...")  # Display only the first 1000 characters for brevity

            # Claude Analysis for the uploaded file
            analysis_prompt = f"Please analyze the following text:\n\n{file_content[:5000]}"  # Limit text length
            analysis_conversation = [{"role": "user", "content": analysis_prompt}]

            try:
                analysis_response = get_claude_response(analysis_conversation, selected_model, anthropic_client, max_tokens=500)
                if analysis_response:
                    with st.chat_message("assistant"):
                        st.markdown(analysis_response)
                else:
                    st.error("Claude did not return a response.")
            except Exception as e:
                st.error(f"Error during analysis: {e}")

    # Chat Feature with Claude using Streamlit chat elements
    st.subheader("Chat with Claude")

    # Display previous chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare conversation for API call
        conversation = st.session_state.messages.copy()

        try:
            # Get response from Claude
            bot_response = get_claude_response(conversation, selected_model, anthropic_client, max_tokens=150)
            if bot_response:
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                with st.chat_message("assistant"):
                    st.markdown(bot_response)
            else:
                st.error("Claude did not return a response.")
        except Exception as e:
            st.error(f"Error during chat: {e}")

else:
    st.warning("Please enter the correct password to access the app.")
