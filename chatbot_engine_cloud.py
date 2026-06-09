import os
import streamlit as st
from sentence_transformers import CrossEncoder
from huggingface_hub import InferenceClient

from rag import load_vectorstore, keyword_search, vrsd_search
from translator import detect_language, translate_to_english, translate_to_user_lang, is_codemixed

# 🔥 Initialize Multilingual Cross-Encoder Reranker
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

# Load DB and the HingBERT Embedder
db, embedder = load_vectorstore()

# ══════════════════════════════════════════════
# NEW: FRONTEND INTERFACE BRIDGE FOR UPLOADS
# ══════════════════════════════════════════════
class VectorStoreWrapper:
    """
    Bridges the frontend expander upload panel with the 
    underlying RAG vector store.
    """
    def __init__(self, vector_db, text_embedder):
        self.db = vector_db
        self.embedder = text_embedder

    def add(self, file_bytes: bytes, filename: str) -> int:
        """
        Processes uploaded documents, converts them to vector chunks, 
        and updates the dynamic index.
        """
        # Extract file extension to parse appropriately
        file_ext = filename.split(".")[-1].lower()
        text_content = ""

        if file_ext == "txt":
            text_content = file_bytes.decode("utf-8", errors="ignore")
        elif file_ext == "pdf":
            # Lazy import to avoid loading memory overhead unless invoked
            import pypdf
            import io
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_content = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        elif file_ext == "docx":
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_bytes))
            text_content = "\n".join([p.text for p in doc.paragraphs])

        if not text_content.strip():
            raise ValueError(f"Could not extract meaningful text from {filename}")

        # Basic naive text splitter (Replace with your own custom RAG recursive chunker if preferred)
        words = text_content.split()
        chunk_size = 150
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        
        # Guard layer to verify chunks list isn't empty
        if not chunks:
            return 0

        # Optional: Generate tracking embeddings and append directly to your LangChain/VectorDB instance
        # if hasattr(self.db, "add_texts"):
        #     self.db.add_texts(chunks)
        
        # Track dynamically inside the raw chunk collection for your hybrid keyword search loop
        if hasattr(self.db, "_raw_chunks"):
            if isinstance(self.db._raw_chunks, list):
                self.db._raw_chunks.extend(chunks)
        
        return len(chunks)

def load_store():
    """Exposes the database instance to app_cloud.py frontend script."""
    return VectorStoreWrapper(db, embedder)

# ══════════════════════════════════════════════
# HUGGING FACE CLIENT INTERFACE
# ══════════════════════════════════════════════
HF_TOKEN = st.secrets["HF_TOKEN"]
client = InferenceClient(api_key=HF_TOKEN)

# Cascading fallback chain — paper Section 3.4
MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",                        # Primary
    "mistralai/Mixtral-8x7B-Instruct-v0.1",            # Fallback 1
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",      # Fallback 2
]

def generate_response(prompt):
    for model in MODELS:
        try:
            print(f"Trying model: {model}")
            response = client.chat_completion(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.3
            )
            answer = response.choices[0].message["content"]
            if answer and answer.strip():
                print(f"Success with: {model}")
                return answer.strip()
        except Exception as e:
            print(f"Model {model} failed: {e} — trying next...")
            continue
    return None

# ══════════════════════════════════════════════
# CORE CHATBOT ENGINE LOGIC
# ══════════════════════════════════════════════
def chatbot(user_query, history=None):
    if history is None:
        history = []

    # 1. Detect language on ORIGINAL query (before any normalization)
    user_lang = detect_language(user_query)

    # Always translate — Google Translate handles Roman code-mixed well
    english_query = translate_to_english(user_query)
    if not english_query or english_query.strip() == "":
        english_query = user_query

    # 2. Embed query
    query_vec = embedder.embed_query(english_query)

    # 3. Hybrid Retrieval
    pre_candidates = db.similarity_search(english_query, k=15)
    dense_docs = vrsd_search(pre_candidates, query_vec, embedder, k=5)
    keyword_docs = keyword_search(db._raw_chunks, english_query, k=5)

    # Merge results
    combined = {doc.page_content: doc for doc in dense_docs + keyword_docs}
    docs = list(combined.values())

    # 4. Cross-Encoder Reranking
    pairs = [(english_query, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)
    docs = [doc for _, doc in sorted(zip(scores, docs), reverse=True)][:3]

    # 5. Translate context to English if needed (CrossRAG bridge)
    english_context = []
    for d in docs:
        chunk_lang = detect_language(d.page_content)
        if chunk_lang != "en":
            english_context.append(translate_to_english(d.page_content))
        else:
            english_context.append(d.page_content)

    context_str = "\n\n".join(english_context)

    # 6. Check if user asked for a specific language style
    style_keywords = [
        "hinglish", "hindi mein", "hindi me", "hindi mai",
        "tanglish", "tamil mein", "tamil la", "tamil me",
        "benglish", "bengali mein", "bangla te", "bengali me",
        "telglish", "telugu lo", "telugu mein",
        "kanglish", "kannada mein", "kannada alli", "kannada me",
        "manglish", "malayalam il", "malayalam mein", "malayalam me",
        "marathish", "marathi mein", "marathi madhe", "marathi me",
        "in hindi", "in tamil", "in bengali", "in telugu",
        "in kannada", "in malayalam", "in marathi",
    ]
    user_asked_style = any(kw in user_query.lower() for kw in style_keywords)

    # 7. Build prompt
    prompt = f"""
You are LinguaBot, a helpful multilingual AI assistant specializing in Indian languages.
Rules:
1. If the context below contains the answer, use it.
2. If the context does NOT contain the answer, use your general knowledge — never refuse.
3. If the user asks to explain in a specific language or style, respond in exactly that style.
4. You fully understand and can respond in all 7 Indian code-mixed language pairs:
   - Hinglish (Hindi + English)
   - Tanglish (Tamil + English)
   - Benglish (Bengali + English)
   - Telglish (Telugu + English)
   - Kanglish (Kannada + English)
   - Manglish (Malayalam + English)
   - Marathish (Marathi + English)
5. You also understand pure Hindi, Tamil, Bengali, Telugu, Kannada, Malayalam, Marathi, Urdu, Gujarati, Punjabi.
6. Never say "I cannot answer" or "not in context" — always give a helpful response.

Context:
{context_str}

Question: {english_query}

Answer:
"""

    # 8. Generate response
    english_answer = generate_response(prompt)

    if not english_answer:
        return "I am currently experiencing high cloud latency. Please try again."

    # 9. Back-translate — but skip if user typed in Roman code-mixed or asked for style
    if user_asked_style or user_lang == "en" or is_codemixed(user_query, user_lang):
        final_answer = english_answer
    else:
        final_answer = translate_to_user_lang(english_answer, user_lang)

    return final_answer

# import os
# from sentence_transformers import CrossEncoder
# from huggingface_hub import InferenceClient

# from rag import load_vectorstore, keyword_search, vrsd_search
# from translator import detect_language, translate_to_english, translate_to_user_lang, is_codemixed

# # 🔥 Initialize Multilingual Cross-Encoder Reranker
# reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

# # Load DB and the HingBERT Embedder
# db, embedder = load_vectorstore()

# # 🔥 Hugging Face Client (NEW WORKING METHOD)
# import streamlit as st
# HF_TOKEN = st.secrets["HF_TOKEN"]
# client = InferenceClient(api_key=HF_TOKEN)

# # 🔥 NEW: Model Response Function (replaces old API calls)
# # Cascading fallback chain — paper Section 3.4
# MODELS = [
#     "Qwen/Qwen2.5-7B-Instruct",                         # Primary
#     "mistralai/Mixtral-8x7B-Instruct-v0.1",             # Fallback 1
#     "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",      # Fallback 2
# ]

# def generate_response(prompt):
#     for model in MODELS:
#         try:
#             print(f"Trying model: {model}")
#             response = client.chat_completion(
#                 model=model,
#                 messages=[
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=512,
#                 temperature=0.3
#             )
#             answer = response.choices[0].message["content"]
#             if answer and answer.strip():
#                 print(f"Success with: {model}")
#                 return answer.strip()
#         except Exception as e:
#             print(f"Model {model} failed: {e} — trying next...")
#             continue
#     return None

# def chatbot(user_query, history=None):
#     # Safely initialize history
#     if history is None:
#         history = []

#     # 1. Detect language on ORIGINAL query (before any normalization)
#     user_lang = detect_language(user_query)

#     # Always translate — Google Translate handles Roman code-mixed well
#     english_query = translate_to_english(user_query)
#     if not english_query or english_query.strip() == "":
#         english_query = user_query

#     # 2. Embed query
#     query_vec = embedder.embed_query(english_query)

#     # 3. Hybrid Retrieval
#     pre_candidates = db.similarity_search(english_query, k=15)
#     dense_docs = vrsd_search(pre_candidates, query_vec, embedder, k=5)
#     keyword_docs = keyword_search(db._raw_chunks, english_query, k=5)

#     # Merge results
#     combined = {doc.page_content: doc for doc in dense_docs + keyword_docs}
#     docs = list(combined.values())

#     # 4. Cross-Encoder Reranking
#     pairs = [(english_query, doc.page_content) for doc in docs]
#     scores = reranker.predict(pairs)
#     docs = [doc for _, doc in sorted(zip(scores, docs), reverse=True)][:3]

#     # 5. Translate context to English if needed (CrossRAG bridge)
#     english_context = []
#     for d in docs:
#         chunk_lang = detect_language(d.page_content)
#         if chunk_lang != "en":
#             english_context.append(translate_to_english(d.page_content))
#         else:
#             english_context.append(d.page_content)

#     context_str = "\n\n".join(english_context)

#     # 6. Check if user asked for a specific language style
#     style_keywords = [
#         # Hinglish
#         "hinglish", "hindi mein", "hindi me", "hindi mai",
#         # Tanglish
#         "tanglish", "tamil mein", "tamil la", "tamil me",
#         # Benglish
#         "benglish", "bengali mein", "bangla te", "bengali me",
#         # Telglish
#         "telglish", "telugu lo", "telugu mein",
#         # Kanglish
#         "kanglish", "kannada mein", "kannada alli", "kannada me",
#         # Manglish
#         "manglish", "malayalam il", "malayalam mein", "malayalam me",
#         # Marathish
#         "marathish", "marathi mein", "marathi madhe", "marathi me",
#         # Generic
#         "in hindi", "in tamil", "in bengali", "in telugu",
#         "in kannada", "in malayalam", "in marathi",
#     ]
#     user_asked_style = any(kw in user_query.lower() for kw in style_keywords)

#     # 7. Build prompt
#     prompt = f"""
# You are LinguaBot, a helpful multilingual AI assistant specializing in Indian languages.
# Rules:
# 1. If the context below contains the answer, use it.
# 2. If the context does NOT contain the answer, use your general knowledge — never refuse.
# 3. If the user asks to explain in a specific language or style, respond in exactly that style.
# 4. You fully understand and can respond in all 7 Indian code-mixed language pairs:
#    - Hinglish (Hindi + English)
#    - Tanglish (Tamil + English)
#    - Benglish (Bengali + English)
#    - Telglish (Telugu + English)
#    - Kanglish (Kannada + English)
#    - Manglish (Malayalam + English)
#    - Marathish (Marathi + English)
# 5. You also understand pure Hindi, Tamil, Bengali, Telugu, Kannada, Malayalam, Marathi, Urdu, Gujarati, Punjabi.
# 6. Never say "I cannot answer" or "not in context" — always give a helpful response.

# Context:
# {context_str}

# Question: {english_query}

# Answer:
# """

#     # 8. Generate response
#     english_answer = generate_response(prompt)

#     if not english_answer:
#         return "I am currently experiencing high cloud latency. Please try again."

#     # 9. Back-translate — but skip if user typed in Roman code-mixed or asked for style
#     if user_asked_style or user_lang == "en" or is_codemixed(user_query, user_lang):
#         final_answer = english_answer
#     else:
#         final_answer = translate_to_user_lang(english_answer, user_lang)

#     return final_answer