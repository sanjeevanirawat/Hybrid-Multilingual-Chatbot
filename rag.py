import os
import re
import numpy as np
from numpy.linalg import norm
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def get_splitter():
    # Recursive splitting respects document structure better than fixed-size chunks
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", "!", "?", " ", ""]
    )

def load_documents():
    docs = []
    if not os.path.exists("data"):
        os.makedirs("data")

    for file in os.listdir("data"):
        file_path = os.path.join("data", file)
        try:
            if file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                docs.extend(loader.load())
            elif file.endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                docs.extend(loader.load())
        except Exception as e:
            print(f"Could not load {file}: {e}")

    if not docs:
        docs = [Document(
            page_content="This is LinguaBot, a multilingual AI assistant.",
            metadata={"source": "default"}
        )]
    return docs

def load_vectorstore():
    documents = load_documents()
    splitter = get_splitter()
    
    # Prepend metadata to chunk text for a free retrieval boost
    chunks = splitter.split_documents(documents)
    for chunk in chunks:
        source = chunk.metadata.get("source", "Unknown")
        chunk.page_content = f"Source: {source} - {chunk.page_content}"

    print(f"Loaded {len(chunks)} chunks from documents")
    
    # 🔥 Initialize Code-Mixed Embeddings (HingBERT)
    embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-small",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
    )
    
    
    # Create the FAISS database 
    db = FAISS.from_documents(chunks, embeddings)
    
    # 🔥 Store raw chunks for Hybrid Keyword Search
    db._raw_chunks = chunks  
    
    return db, embeddings

# 🔥 Phase 2: Sparse Keyword Search
# Phase 2: Sparse Keyword Search
def keyword_search(chunks, query, k=5):
    import re
    query_words = set(re.findall(r'\w+', query.lower()))
    scored = []
    for chunk in chunks:
        text_words = set(re.findall(r'\w+', chunk.page_content.lower()))
        if not query_words:
            score = 0
        else:
            score = len(query_words & text_words)
        scored.append((score, chunk))

    # 🔥 THE ACTUAL FIX: x tells Python to extract and sort ONLY by the score!
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:k]]

# 🔥 Phase 2: Vector Retrieval with Similarity and Diversity (VRSD) Algorithm
def vrsd_search(candidates, query_vector, embedder, k=5):
    """
    Parameter-free heuristic that maximizes the similarity between 
    the query vector and the SUM of the selected candidate vectors.
    """
    if not candidates:
        return []
        
    cand_texts = [c.page_content for c in candidates]
    cand_vecs = embedder.embed_documents(cand_texts)
    
    S_docs = []
    s_vec = np.zeros(len(query_vector))
    
    R_docs = list(candidates)
    R_vecs = list(cand_vecs)
    
    for _ in range(min(k, len(candidates))):
        max_cos = -1
        best_idx = -1
        
        for i, v in enumerate(R_vecs):
            t = s_vec + np.array(v)
            # Cosine similarity between new sum vector and query vector
            cos_sim = np.dot(t, query_vector) / (norm(t) * norm(query_vector) + 1e-10)
            
            if cos_sim > max_cos:
                max_cos = cos_sim
                best_idx = i
                
        S_docs.append(R_docs[best_idx])
        s_vec = s_vec + np.array(R_vecs[best_idx])
        R_docs.pop(best_idx)
        R_vecs.pop(best_idx)
        
    return S_docs
def merge_documents_into_db(db, file_bytes, filename):
    import tempfile
    from langchain_community.document_loaders import TextLoader, PyPDFLoader
    from langchain_core.documents import Document

    ext = filename.lower().split(".")[-1]
    docs = []

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if ext == "pdf":
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
        elif ext == "txt":
            loader = TextLoader(tmp_path, encoding="utf-8")
            docs = loader.load()
        elif ext == "docx":
            from docx import Document as DocxDocument
            docx = DocxDocument(tmp_path)
            full_text = "\n".join([p.text for p in docx.paragraphs if p.text.strip()])
            docs = [Document(page_content=full_text, metadata={"source": filename})]
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    finally:
        os.unlink(tmp_path)

    if not docs:
        return db, 0

    for doc in docs:
        doc.metadata["source"] = filename

    splitter = get_splitter()
    chunks = splitter.split_documents(docs)

    # Prepend metadata just like load_vectorstore does
    for chunk in chunks:
        source = chunk.metadata.get("source", "Unknown")
        chunk.page_content = f"Source: {source} - {chunk.page_content}"

    # Get the embedder from the db object and add new chunks
    db.add_documents(chunks)

    # Keep raw chunks accessible for keyword search
    db._raw_chunks.extend(chunks)

    return db, len(chunks)

# import os
# import re
# import streamlit as st
# from langchain_community.document_loaders import TextLoader, PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_core.documents import Document

# # ── Simple in-memory document store ──
# # No FAISS, no embeddings, no model downloads
# # Uses keyword matching — reliable on any server

# def get_splitter():
#     return RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=100,
#         separators=["\n\n", "\n", ".", "!", "?", " ", ""]
#     )

# def load_documents():
#     docs = []

#     if not os.path.exists("data"):
#         os.makedirs("data")

#     if os.path.exists("data/sample.txt"):
#         try:
#             loader = TextLoader("data/sample.txt", encoding="utf-8")
#             docs.extend(loader.load())
#         except Exception as e:
#             print(f"Could not load sample.txt: {e}")

#     for file in os.listdir("data"):
#         if file.endswith(".pdf"):
#             try:
#                 loader = PyPDFLoader(os.path.join("data", file))
#                 docs.extend(loader.load())
#             except Exception as e:
#                 print(f"Could not load {file}: {e}")

#     if not docs:
#         docs = [Document(
#             page_content="This is LinguaBot, a multilingual AI assistant. Upload documents to get started.",
#             metadata={"source": "default"}
#         )]

#     return docs

# class SimpleDocStore:
#     """
#     Lightweight document store using keyword search.
#     No FAISS, no embeddings, no downloads — works everywhere.
#     """

#     def __init__(self, chunks):
#         self.chunks = chunks

#     def _score(self, query, text):
#         query_words = set(re.findall(r'\w+', query.lower()))
#         text_words  = set(re.findall(r'\w+', text.lower()))
#         if not query_words:
#             return 0
#         overlap = query_words & text_words
#         return len(overlap) / len(query_words)

#     def similarity_search(self, query, k=3):
#         scored = [
#             (self._score(query, chunk.page_content), chunk)
#             for chunk in self.chunks
#         ]
#         scored.sort(key=lambda x: x[0], reverse=True)
#         return [chunk for _, chunk in scored[:k]]

#     def merge_chunks(self, new_chunks):
#         self.chunks.extend(new_chunks)


# def load_vectorstore():
#     documents = load_documents()
#     splitter  = get_splitter()
#     chunks    = splitter.split_documents(documents)
#     print(f"Loaded {len(chunks)} chunks from documents")
#     return SimpleDocStore(chunks)


# def merge_documents_into_db(db, file_bytes, filename):
#     import tempfile

#     ext  = filename.lower().split(".")[-1]
#     docs = []

#     with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
#         tmp.write(file_bytes)
#         tmp_path = tmp.name

#     try:
#         if ext == "pdf":
#             loader = PyPDFLoader(tmp_path)
#             docs   = loader.load()
#         elif ext == "txt":
#             loader = TextLoader(tmp_path, encoding="utf-8")
#             docs   = loader.load()
#         elif ext == "docx":
#             from docx import Document as DocxDocument
#             docx      = DocxDocument(tmp_path)
#             full_text = "\n".join([p.text for p in docx.paragraphs if p.text.strip()])
#             docs      = [Document(page_content=full_text, metadata={"source": filename})]
#         else:
#             raise ValueError(f"Unsupported file type: {ext}")
#     finally:
#         os.unlink(tmp_path)

#     if not docs:
#         return db, 0

#     for doc in docs:
#         doc.metadata["source"] = filename

#     splitter = get_splitter()
#     chunks   = splitter.split_documents(docs)
#     db.merge_chunks(chunks)

#     return db, len(chunks)