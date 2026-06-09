import streamlit as st
from sentence_transformers import CrossEncoder                          # ADDED
from rag import load_vectorstore, keyword_search, vrsd_search
from translator import translate_to_english, translate_to_user_lang, detect_language
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="mistral")

# ADDED: Load CrossEncoder reranker (same model as cloud version)
# Paper Section 3.3: BAAI/bge-reranker-v2-m3 used for multilingual reranking
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

# Unpack both db and embedder
@st.cache_resource
def load_db():
    return load_vectorstore()

db, embedder = load_db()


def build_prompt(context, question, history):
    history_text = ""
    if history:
        for msg in history[-4:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

    return f"""You are a helpful multilingual assistant.

First, try to answer using the context below.
If the context contains the answer, use it and say so.
If the context does NOT contain the answer, use your general knowledge to answer helpfully.
Never say "I don't know" — always try to give a useful response.

Context:
{context}

Conversation so far:
{history_text}
User: {question}
Assistant:"""


def chatbot(query, history=None):
    if history is None:
        history = []

    lang = detect_language(query)
    english_query = translate_to_english(query)

    # Step 1: embed the query vector
    query_vec = embedder.embed_query(english_query)

    # Step 2: get broad candidate pool from FAISS
    pre_candidates = db.similarity_search(english_query, k=15)

    # Step 3: VRSD — diverse dense retrieval
    dense_docs = vrsd_search(pre_candidates, query_vec, embedder, k=5)

    # Step 4: sparse keyword retrieval
    keyword_docs = keyword_search(db._raw_chunks, english_query, k=5)

    # Step 5: merge, deduplicate by content
    combined = {doc.page_content: doc for doc in dense_docs + keyword_docs}
    docs = list(combined.values())

    # ADDED Step 6: CrossEncoder reranking — same as cloud version
    # Scores each (query, chunk) pair and picks top 3
    pairs = [(english_query, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)
    docs = [doc for _, doc in sorted(zip(scores, docs), reverse=True)][:3]

    context = "\n\n".join([doc.page_content for doc in docs])[:1500]
    prompt = build_prompt(context, english_query, history)

    response = llm.invoke(prompt)
    response = str(response).strip()

    final_answer = translate_to_user_lang(response, lang)
    return final_answer