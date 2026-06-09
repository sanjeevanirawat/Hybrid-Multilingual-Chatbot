from rag import load_vectorstore
from translator import translate_to_english, translate_to_user_lang, detect_language
from chatbot_engine import chatbot
import time

print("Loading vector database...")
db, embedder = load_vectorstore()

if __name__ == "__main__":
    print("Multilingual Chatbot Running (type 'exit')\n")
    history = []

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        start = time.time()
        answer = chatbot(user_input, history=history)
        elapsed = time.time() - start

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": answer})

        # Keep history manageable
        if len(history) > 10:
            history = history[-10:]

        print(f"Bot: {answer}")
        print(f"({elapsed:.2f}s)\n")