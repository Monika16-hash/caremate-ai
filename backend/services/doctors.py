import re

SPEC_FIELDS = ("specialization", "speciality", "specialty")  # tolerate any spelling in Firestore
SPEC_PATTERNS = [
    ("Cardiologist", r"cardio|heart"), ("Dermatologist", r"dermat|skin"),
    ("Ophthalmologist", r"ophthal|eye"), ("Orthopedic", r"orthop|bone|joint"),
    ("Neurologist", r"neuro"), ("Psychiatrist", r"psychiat|mental"),
    ("ENT", r"\bent\b|otolaryng|ear.*nose"), ("Gastroenterologist", r"gastro"),
    ("Pulmonologist", r"pulmon|respirat|chest physician"), ("General Physician", r"general|physician|family"),
]

def _s(v): return str(v).strip() if v is not None else ""

def spec_key(s):
    """Canonical specialty so 'Cardiology', 'cardiologist ' and 'Cardiologist' all match."""
    s = _s(s).lower()
    for key, pat in SPEC_PATTERNS:
        if re.search(pat, s): return key
    return s

def spec_of(d):
    return next((_s(d[f]) for f in SPEC_FIELDS if _s(d.get(f))), "")

def public_doctor(doc_id, d):
    """Whitelist fields: JSON-safe (no Timestamps/None) and never leaks email or password_hash."""
    d = {str(k).strip().lower(): v for k, v in d.items()}  # tolerate "Specialization" / " name" keys
    av = d.get("availability")
    return {"id": doc_id, "name": _s(d.get("name")), "specialization": spec_of(d),
            "hospital": _s(d.get("hospital")), "location": _s(d.get("location")),
            "availability": [str(x) for x in av] if isinstance(av, list) else []}

def filter_doctors(raw, args):
    """raw: list of (doc_id, dict). args: q, specialty, location, hospital."""
    out = []
    for doc_id, d in raw:
        p = public_doctor(doc_id, d)
        want = _s(args.get("specialty"))
        if want and not (spec_key(want) == spec_key(p["specialization"]) or want.lower() in p["specialization"].lower()):
            continue
        if _s(args.get("q")).lower() not in p["name"].lower(): continue
        if _s(args.get("location")).lower() not in p["location"].lower(): continue
        if _s(args.get("hospital")).lower() not in p["hospital"].lower(): continue
        out.append(p)
    return out
