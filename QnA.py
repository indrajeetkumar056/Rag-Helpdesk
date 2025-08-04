import streamlit as st
import os
import time
from dotenv import load_dotenv

from langchain_ollama import OllamaLLM
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
import pandas as pd
from langchain.docstore.document import Document
# Load environment variables
load_dotenv()

st.set_page_config(page_title="Help-Desk", layout="wide")
st.title("🧠 NSE Help desk")

# Load the Ollama model
llm = OllamaLLM(model="gemma:2b")  # or "gema:2b", "mistral", etc.

# Prompt Template
# prompt = ChatPromptTemplate.from_template("""
# Given the following historical customer queries and agent responses, answer the new question. 
# Try to infer from the context, even if information appears indirectly or varies across examples.

# <context>
# {context}
# </context>

# Question: {input}

# If the context provides enough signal, answer confidently. If it clearly contradicts itself, explain both sides.
# """)
prompt = ChatPromptTemplate.from_template("""
You are an expert support assistant. Use the following historical Q&A examples to answer a new client query.

If different answers exist in different scenarios (e.g., activation vs reactivation), explain the difference clearly.

<context>
{context}
</context>

Question: {input}

Be confident and clear. If necessary, break down the context before concluding.
""")
def vector_embedding():
    if "vectors" not in st.session_state:
        st.session_state.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Load your CSV
        df = pd.read_csv("call.csv")  # Replace with actual filename

        # Construct documents as Q/A pairs
        docs = []
        for _, row in df.iterrows():
            content = f"Client Question: {row['Query']}\nAgent Response: {row['Response']}"
            docs.append(Document(page_content=content, metadata={"id": row["Sr no."]}))

        # Chunk (optional — you may skip if one QA per doc is enough)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        final_docs = text_splitter.split_documents(docs)

        # Embed
        st.session_state.vectors = FAISS.from_documents(final_docs, st.session_state.embeddings)
        st.success("✅ CSV embedded and vector store created.")


# UI
st.subheader("🔍 Ask a question from your documents")
query = st.text_input("Enter your question")

col1, col2 = st.columns(2)

with col1:
    if st.button("1️⃣ Embed Documents"):
        vector_embedding()

with col2:
    if st.button("2️⃣ Reset Vector Store"):
        for key in ["vectors", "docs", "embeddings"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success("✅ Vector store and state cleared.")

# RAG chain
if query and "vectors" in st.session_state:
    retriever = st.session_state.vectors.as_retriever()
    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    start = time.time()
    response = retrieval_chain.invoke({"input": query})
    st.write("⏱️ Response time:", round(time.time() - start, 2), "sec")

    st.markdown("### 📜 Answer")
    st.write(response["answer"])

    with st.expander("🧾 Sources"):
        for i, doc in enumerate(response["context"]):
            st.markdown(f"**Chunk {i+1}:**")
            st.write(doc.page_content)
            st.write("---")

elif query:
    st.warning("⚠️ Please embed documents first.")
