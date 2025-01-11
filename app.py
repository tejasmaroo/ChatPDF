import streamlit as st
import PyPDF2
from langchain_groq import ChatGroq
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load the Groq API key
groq_api_key = os.environ['GROQ_API_KEY']

# Streamlit app setup
st.title("Chat with PDF")

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# File uploader for multiple PDFs
pdf_files = st.file_uploader("Upload your PDF files", type="pdf", accept_multiple_files=True)

if pdf_files:
    all_text = ""
    
    # Extract text from each uploaded PDF
    for pdf_file in pdf_files:
        pdf_text = extract_text_from_pdf(pdf_file)
        all_text += pdf_text  # Concatenate text from all PDFs
    
    # Split the concatenated text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    text_chunks = text_splitter.split_text(all_text)

    # Create Document objects from the chunks
    documents = [Document(page_content=chunk) for chunk in text_chunks]

    # Create the vector store using Chroma
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = Chroma.from_documents(documents, embeddings, persist_directory='db_dir')

    # Set up Groq model
    llm = ChatGroq(groq_api_key=groq_api_key, model_name="mixtral-8x7b-32768")

    # Create the prompt template
    prompt = ChatPromptTemplate.from_template(
        """
        Answer the questions based on the provided context only.
        Please provide the most accurate response based on the question.
        <context>
        {context}
        </context>
        Questions: {input}
        """
    )

    # Create the document chain
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Set up retriever using Chroma vector store
    retriever = vector_store.as_retriever()

    # Create retrieval chain
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    # Input prompt from user
    prompt_input = st.text_input("Input your prompt here")

    if prompt_input:
        start = time.process_time()  # Measure time for response
        response = retrieval_chain.invoke({"input": prompt_input})
        st.write(f"Response time: {time.process_time() - start:.2f} seconds")

        # Display the response
        st.write(response['answer'])
