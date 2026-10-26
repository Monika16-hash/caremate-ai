import os, json, re, logging
from google import genai
from google.genai import types

log = logging.getLogger("caremate.gemini")
MODELS = [m.strip() for m in os.getenv("GEMINI_MODEL", "gemini-3.5-flash,gemini-3.1-flash-lite").split(",") if m.strip()]
DISCLAIMER = "AI recommendation only. Not a medical diagnosis."
SPECIALTIES = ["Cardiologist", "Dermatologist", "Ophthalmologist", "Orthopedic", "Neurologist",
               "Psychiatrist", "ENT", "Gastroenterologist", "Pulmonologist", "General Physician"]

KEYWORDS = {
    "Cardiologist": ["chest pain", "palpitation", "heart", "chest tightness", "dizz"],
    "Dermatologist": ["rash", "itch", "skin", "acne", "eczema", "hives"],
    "Ophthalmologist": ["eye", "vision", "blurred", "sight"],
    "Orthopedic": ["joint", "fracture", "bone", "knee", "back pain", "sprain"],
    "Psychiatrist": ["anxiety", "depress", "panic", "stress", "mood", "suicid"],
    "Neurologist": ["migraine", "seizure", "numbness", "headache"],
    "ENT": ["ear", "throat", "sinus", "nose", "hearing"],
    "Gastroenterologist": ["stomach", "abdominal", "nausea", "vomit", "acid", "diarrhea"],
    "Pulmonologist": ["cough", "breath", "asthma", "wheez"],
}
URGENT = ["chest pain", "suicid", "can't breathe", "cannot breathe", "fainted", "stroke"]

def keyword_triage(text: str) -> dict:
    t = text.lower()
    scores = {s: sum(k in t for k in kws) for s, kws in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return {"specialty": best if scores[best] else "General Physician",
            "reason": "Matched from the symptoms you described.",
            "urgent": any(u in t for u in URGENT)}

_CLIENT = None

def _client():
    global _CLIENT

    if _CLIENT is None:
        _CLIENT = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

    return _CLIENT

def _generate(prompt: str):
    """Try each model in MODELS in order; raise the last error if all fail."""
    last = None
    for m in MODELS:
        try:
            return _client().models.generate_content(
                model=m, contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0))
        except Exception as e:
            log.warning("Gemini model %s failed: %s", m, e)
            print(f"Gemini model {m} failed: {e}", flush=True)
            last = e
    raise last

def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    return json.loads(m.group(0)) if m else {}

def triage(symptoms: str) -> dict:
    prompt = (f"You are a triage assistant. Pick the single most appropriate specialty from {SPECIALTIES} "
              'for these symptoms. Reply ONLY with JSON: {"specialty": "...", "reason": "one short sentence", '
              f'"urgent": true|false}}. Symptoms: {symptoms}')
    source, error = "ai", None
    try:
        data = _parse(_generate(prompt).text)
        if data.get("specialty") not in SPECIALTIES:
            raise ValueError(f"Unexpected specialty: {data.get('specialty')!r}")
    except Exception as e:
        log.exception("Gemini triage failed, using keyword fallback")
        data, source, error = keyword_triage(symptoms), "keywords", str(e)[:200]
    data.setdefault("reason", ""); data.setdefault("urgent", False)
    return {**data, "source": source, "error": error, "disclaimer": DISCLAIMER}

def summarize_report(text: str) -> dict:
    prompt = ('Summarize this medical report in plain language. Reply ONLY JSON: '
              '{"key_findings":[],"important_values":[],"recommendations":[]}. ' f"Report: {text[:12000]}")
    return _parse(_generate(prompt).text)