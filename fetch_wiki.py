import wikipediaapi
import os

# Topics you want LinguaBot to know about
TOPICS = [
    # Technology
    "Artificial intelligence",
    "Retrieval-augmented generation",
    "Large language model",
    "Natural language processing",
    "Machine learning",
    "Deep learning",
    "Transformer model",

    # India general knowledge
    "Constitution of India",
    "India",
    "Indian culture",
    "History of India",

    # Women safety
    "Women's rights in India",
    "Domestic violence",
     "Hindi language",
"Tamil language", 
"Bengali language",
"Women safety in India",
"Indian languages",
"Artificial intelligence in India",
    # Science
    "Photosynthesis",
    "Solar system",
    "Climate change",
]

def fetch_wikipedia_data():
    wiki = wikipediaapi.Wikipedia(
        language="en",
        user_agent="LinguaBot/1.0"
    )

    os.makedirs("data", exist_ok=True)

    for topic in TOPICS:
        print(f"Fetching: {topic}...")
        page = wiki.page(topic)

        if not page.exists():
            print(f"  ❌ Not found: {topic}")
            continue

        # Clean filename
        filename = topic.replace(" ", "_").replace("/", "_") + ".txt"
        filepath = os.path.join("data", filename)

        # Save only first 5000 chars to keep chunks manageable
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Title: {page.title}\n\n")
            f.write(page.text[:5000])

        print(f"  ✅ Saved: {filename}")

    print(f"\nDone! {len(TOPICS)} topics fetched into data/")

if __name__ == "__main__":
    fetch_wikipedia_data()