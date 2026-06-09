from langdetect import detect
from functools import lru_cache
import re
from deep_translator import GoogleTranslator
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

SUPPORTED_LANGS = {"hi", "ta", "bn", "mr", "te", "ur", "en", "gu", "pa", "kn", "ml"}

DIALECT_MAP = {
    "kyaaa": "kya", "kia": "kya",
    "rha": "raha", "rh": "raha",
    "kr": "kar", "h": "hai",
    "bhaiya": "bhai", "bhaii": "bhai",
    "acha": "achha", "accha": "achha"
}

HINDI_MARKERS = {
    "hai", "kya", "nahi", "aur", "mein", "se", "kar",
    "ho", "tha", "bhi", "to", "mat", "karo", "yeh", "woh",
    "hota", "hoti", "kaise", "kyun", "kaun", "kab", "kahan"
}
TAMIL_MARKERS = {
    "vanakkam", "epdi", "inge", "enna", "sollu", "iruku",
    "pongo", "nalla", "romba", "paaru", "theriyuma", "illai",
    "seri", "avan", "aval", "yenna", "yeppo", "yengey"
}
BENGALI_MARKERS = {
    "ki", "ache", "ami", "tumi", "kemon", "bolo", "jano",
    "achho", "ektu", "dekho", "koro", "hobe", "niye", "bolchi",
    "tomake", "amake", "kintu", "tahole", "thakbe"
}
TELUGU_MARKERS = {
    "emi", "undi", "ante", "cheppu", "chusta", "vasta",
    "ledu", "ayindi", "cheyyi", "ekkada", "enduku", "evaru",
    "naaku", "meeru", "mee", "nenu", "okka", "anni"
}
KANNADA_MARKERS = {
    "enu", "ide", "hellu", "illa", "beku", "hogona",
    "eno", "yaako", "haege", "avru", "nimdu", "naanu",
    "bekagide", "madtini", "bartini", "kelsa", "gottilla"
}
MALAYALAM_MARKERS = {
    "anu", "evide", "ipo", "alle", "undo", "engane",
    "enthanu", "paranju", "poyi", "varu", "cheyyu", "nokku",
    "adipoli", "pakshe", "pinne", "athu", "ithanu", "sheriyanu"
}
MARATHI_MARKERS = {
    "kay", "aahe", "nahi", "bara", "mala", "tula",
    "aplya", "amhi", "tumhi", "kasa", "kiti", "hote",
    "sangto", "bagha", "chala", "zala", "aahet", "naahi"
}

CODEMIX_LANG_MAP = {
    "hindi": "hi", "tamil": "ta", "bengali": "bn",
    "telugu": "te", "kannada": "kn", "malayalam": "ml", "marathi": "mr",
}

# Tracks which languages are code-mixed (Roman script) vs native script
CODEMIX_ROMAN = {"hi", "ta", "bn", "te", "kn", "ml", "mr"}

LANG_MAP = {
    "en": "eng_Latn", "hi": "hin_Deva", "ta": "tam_Taml",
    "bn": "ben_Beng", "mr": "mar_Deva", "te": "tel_Telu",
    "ur": "urd_Arab", "gu": "guj_Gujr", "pa": "pan_Guru",
    "kn": "kan_Knda", "ml": "mal_Mlym"
}


def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    return " ".join([DIALECT_MAP.get(w, w) for w in words])


def detect_language(text: str) -> str:
    try:
        normalized = normalize_text(str(text))
        words = set(normalized.split())

        scores = {
            "hindi":     len(words & HINDI_MARKERS),
            "tamil":     len(words & TAMIL_MARKERS),
            "bengali":   len(words & BENGALI_MARKERS),
            "telugu":    len(words & TELUGU_MARKERS),
            "kannada":   len(words & KANNADA_MARKERS),
            "malayalam": len(words & MALAYALAM_MARKERS),
            "marathi":   len(words & MARATHI_MARKERS),
        }

        best_lang = max(scores, key=scores.get)
        if scores[best_lang] >= 2:
            return CODEMIX_LANG_MAP[best_lang]

        lang = detect(normalized)
        return lang if lang in SUPPORTED_LANGS else "en"

    except:
        return "en"


def is_codemixed(text: str, lang: str) -> bool:
    """Check if text is Roman-script code-mixed (not native script)"""
    # If detected as Indian language but text is mostly ASCII = code-mixed Roman
    if lang in CODEMIX_ROMAN:
        ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
        return ascii_ratio > 0.8  # mostly ASCII = Roman script code-mixed
    return False


@lru_cache(maxsize=512)
def translate_to_english(text: str) -> str:
    try:
        text = str(text)
        lang = detect_language(text)

        if lang == "en":
            return text

        # For Roman-script code-mixed — use Google Translate (handles Hinglish well)
        if is_codemixed(text, lang):
            try:
                return GoogleTranslator(source="auto", target="en").translate(text)
            except:
                pass

        # For native script — use NLLB-200
        normalized = normalize_text(text)
        inputs = tokenizer(normalized, return_tensors="pt")
        output = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.lang_code_to_id["eng_Latn"]
        )
        return tokenizer.decode(output[0], skip_special_tokens=True)

    except:
        return text


@lru_cache(maxsize=512)
def translate_to_user_lang(text: str, target_lang: str) -> str:
    try:
        text = str(text)
        target_lang = str(target_lang)

        if target_lang == "en":
            return text

        # For code-mixed Roman script — keep response in English
        # (user was typing Roman, so give Roman back not native script)
        original_query = text  # we'll check script below
        if is_codemixed(text, target_lang):
            return text  # return English — better than wrong-script output

        # For native script users — use NLLB-200
        tgt_lang = LANG_MAP.get(target_lang, "eng_Latn")
        inputs = tokenizer(text, return_tensors="pt")
        output = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang]
        )
        return tokenizer.decode(output[0], skip_special_tokens=True)

    except:
        return text

# from langdetect import detect
# from functools import lru_cache
# import re
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# MODEL_NAME = "facebook/nllb-200-distilled-600M"

# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
# SUPPORTED_LANGS = {"hi", "ta", "bn", "mr", "te", "ur", "en", "gu", "pa", "kn", "ml"}
# DIALECT_MAP = {
#     "kyaaa": "kya", "kia": "kya", "ka": "kya",
#     "rha": "raha", "rh": "raha",
#     "kr": "kar", "h": "hai",
#     "bhaiya": "bhai", "bhaii": "bhai",
#     "acha": "achha", "accha": "achha"
# }
# HINDI_MARKERS = {
#     "hai", "kya", "nahi", "aur", "mein", "se", "kar",
#     "ho", "tha", "bhi", "to", "mat", "karo", "yeh", "woh"
# }
# TAMIL_MARKERS = {
#     "vanakkam", "epdi", "inge", "enna", "sollu", "iruku",
#     "pongo", "nalla", "romba", "paaru", "theriyuma", "illai",
#     "seri", "avan", "aval", "yenna", "yeppo", "yengey"
# }
# BENGALI_MARKERS = {
#     "ki", "ache", "ami", "tumi", "kemon", "bolo", "jano",
#     "achho", "ektu", "dekho", "koro", "hobe", "niye", "bolchi",
#     "tomake", "amake", "kintu", "tahole", "thakbe"
# }
# TELUGU_MARKERS = {
#     "emi", "undi", "ante", "cheppu", "chusta", "vasta",
#     "ledu", "ayindi", "cheyyi", "ekkada", "enduku", "evaru",
#     "naaku", "meeru", "mee", "nenu", "okka", "anni"
# }
# KANNADA_MARKERS = {
#     "enu", "ide", "hellu", "illa", "beku", "hogona",
#     "eno", "yaako", "haege", "avru", "nimdu", "naanu",
#     "bekagide", "madtini", "bartini", "kelsa", "gottilla"
# }
# MALAYALAM_MARKERS = {
#     "anu", "evide", "ipo", "alle", "undo", "engane",
#     "enthanu", "paranju", "poyi", "varu", "cheyyu", "nokku",
#     "adipoli", "pakshe", "pinne", "athu", "ithanu", "sheriyanu"
# }
# MARATHI_MARKERS = {
#     "kay", "aahe", "nahi", "bara", "mala", "tula",
#     "aplya", "amhi", "tumhi", "kasa", "kiti", "hote",
#     "sangto", "bagha", "chala", "zala", "aahet", "naahi"
# }

# CODEMIX_LANG_MAP = {
#     "hindi": "hi", "tamil": "ta", "bengali": "bn",
#     "telugu": "te", "kannada": "kn", "malayalam": "ml", "marathi": "mr",
# }


# LANG_MAP = {
#     "en": "eng_Latn",
#     "hi": "hin_Deva",
#     "ta": "tam_Taml",
#     "bn": "ben_Beng",
#     "mr": "mar_Deva",
#     "te": "tel_Telu",
#     "ur": "urd_Arab",
#     "gu": "guj_Gujr",
#     "pa": "pan_Guru",
#     "kn": "kan_Knda",
#     "ml": "mal_Mlym"
# }


# def normalize_text(text):
#     text = text.lower()
#     text = re.sub(r'[^\w\s]', '', text)
#     words = text.split()
#     return " ".join([DIALECT_MAP.get(w, w) for w in words])


# def detect_language(text: str) -> str:
#     try:
#         text = normalize_text(text)
#         words = set(text.split())

#         scores = {
#             "hindi":     len(words & HINDI_MARKERS),
#             "tamil":     len(words & TAMIL_MARKERS),
#             "bengali":   len(words & BENGALI_MARKERS),
#             "telugu":    len(words & TELUGU_MARKERS),
#             "kannada":   len(words & KANNADA_MARKERS),
#             "malayalam": len(words & MALAYALAM_MARKERS),
#             "marathi":   len(words & MARATHI_MARKERS),
#         }

#         best_lang = max(scores, key=scores.get)
#         if scores[best_lang] >= 2:
#             return CODEMIX_LANG_MAP[best_lang]

#         lang = detect(text)
#         return lang if lang in SUPPORTED_LANGS else "en"

#     except:
#         return "en"
# # All 7 code-mixed language pair markers


# @lru_cache(maxsize=512)
# def translate_to_english(text: str) -> str:
#     try:
#         text = str(text)
#         text = normalize_text(text)
#         lang = detect_language(text)

#         if lang == "en":
#             return text

#         inputs = tokenizer(text, return_tensors="pt")

#         output = model.generate(
#             **inputs,
#             forced_bos_token_id=tokenizer.lang_code_to_id["eng_Latn"]
#         )

#         return tokenizer.decode(output[0], skip_special_tokens=True)

#     except:
#         return text


# @lru_cache(maxsize=512)
# def translate_to_user_lang(text: str, target_lang: str) -> str:
#     try:
#         text = str(text)
#         target_lang = str(target_lang)
#         if target_lang == "en":
#             return text

#         tgt_lang = LANG_MAP.get(target_lang, "eng_Latn")

#         inputs = tokenizer(text, return_tensors="pt")

#         output = model.generate(
#             **inputs,
#             forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang]
#         )

#         return tokenizer.decode(output[0], skip_special_tokens=True)

#     except:
#         return text

