import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
import google.generativeai as genai
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# API Configuration
if not GOOGLE_API_KEY or not HUGGINGFACEHUB_API_TOKEN:
    st.error("API keys are missing. Please configure them in the .env file.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Initialize the knowledge base
vectorstore = None

# Initialize session state for conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Load PDF and create knowledge base
def load_pdf_to_knowledge_base(pdf_file):
    global vectorstore
    reader = PdfReader(pdf_file)
    texts = [page.extract_text() for page in reader.pages]
    vectorstore = FAISS.from_texts(texts, embedding=embedding_model)
    st.success("PDF uploaded and knowledge base created!")

# Retrieve documents
def retrieve_documents(query, k=2):
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return retriever.invoke(query)

# Generate response
def generate_response(query, context):
    prompt = f"You are a helpful AI assistant. Use the following context to answer the user's question:\n\nContext: {context}\n\nQuestion: {query}\nAnswer:, also make sure the answer is more than just the context and more creative"
    response = model.generate_content(prompt)
    return response.text


def reset():
    global vectorstore
    vectorstore = None  # Clear the knowledge base
    st.session_state.conversation_history.clear()  # Clear conversation history

# UI Components
st.title("SmartReader PDF")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload a PDF file as a Knowledge Base", type=["pdf"])
if uploaded_pdf:
    load_pdf_to_knowledge_base(uploaded_pdf)

# Reset button to clear everything
if st.button("Reset"):
    reset()

# Display conversation history
for entry in st.session_state.conversation_history:
    st.markdown(f"**You:** {entry['query']}")
    st.markdown(f"**Chatbot:** {entry['response']}")
    st.markdown("---")
    
# Input for new query
query = st.text_input("Ask a question about the uploaded PDF")
if st.button("Get Response"):
    if not vectorstore:
        st.error("Please upload a PDF to create a knowledge base.")
    else:
        relevant_docs = retrieve_documents(query)
        context = "\n".join([doc.page_content for doc in relevant_docs])
        response = generate_response(query, context)
        
        # Add the new query and response to the conversation history
        st.session_state.conversation_history.append({"query": query, "response": response})
        
        # Display the latest response
        st.markdown(f"**Chatbot:** {response}")
