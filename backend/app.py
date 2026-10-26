import os, io, html, datetime as dt
from functools import wraps
from dotenv import load_dotenv
load_dotenv()
import jwt, bcrypt
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import firebase_admin
from firebase_admin import credentials, firestore
from apscheduler.schedulers.background import BackgroundScheduler
from services.gemini import triage, summarize_report
from services.notify import send_email, send_whatsapp
from ml.noshow import predict_noshow
from services.doctors import filter_doctors

firebase_admin.initialize_app(credentials.Certificate(os.environ["FIREBASE_CREDENTIALS"]))
db = firestore.client()
app = Flask(__name__)
CORS(app, origins=[os.getenv("FRONTEND_ORIGIN", "*")])
limiter = Limiter(get_remote_address, app=app, default_limits=["200/hour"])
SECRET = os.environ["JWT_SECRET"]
COL = {"patient": "patients", "doctor": "doctors"}

def clean(v, n=300): return html.escape(str(v or "").strip())[:n]
def err(msg, code=400): return jsonify(error=msg), code

def auth(*roles):
    def deco(f):
        @wraps(f)
        def wrap(*a, **k):
            try:
                tok = request.headers.get("Authorization", "").split(" ")[1]
                g.user = jwt.decode(tok, SECRET, algorithms=["HS256"])
            except Exception:
                return err("Unauthorized", 401)
            if roles and g.user["role"] not in roles: return err("Forbidden", 403)
            return f(*a, **k)
        return wrap
    return deco

def make_token(uid, role):
    return jwt.encode({"sub": uid, "role": role, "exp": dt.datetime.utcnow() + dt.timedelta(hours=8)}, SECRET)

@app.post("/api/auth/register")
@limiter.limit("10/minute")
def register():
    d = request.get_json(force=True); role = d.get("role")
    if role not in COL: return err("Role must be patient or doctor")
    email, pw = clean(d.get("email")).lower(), d.get("password", "")
    if "@" not in email or len(pw) < 8: return err("Valid email and 8+ character password required")
    if list(db.collection(COL[role]).where("email", "==", email).limit(1).stream()): return err("Email already registered", 409)
    doc = {"name": clean(d.get("name")), "email": email, "phone": clean(d.get("phone"), 20),
           "password_hash": bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode(),
           "created_at": firestore.SERVER_TIMESTAMP}
    if role == "doctor":
        doc.update(specialization=clean(d.get("specialization")), hospital=clean(d.get("hospital")),
                   location=clean(d.get("location")), availability=d.get("availability", ["09:00", "10:00", "11:00", "14:00", "15:00"]))
    else:
        doc.update(attended=0, missed=0, last_visit=None)
    ref = db.collection(COL[role]).document(); ref.set(doc)
    return jsonify(token=make_token(ref.id, role), role=role), 201

@app.post("/api/auth/login")
@limiter.limit("10/minute")
def login():
    d = request.get_json(force=True); role = d.get("role"); email = clean(d.get("email")).lower(); pw = d.get("password", "")
    if role == "admin":
        if email == os.getenv("ADMIN_EMAIL", "").lower() and pw == os.getenv("ADMIN_PASSWORD"):
            return jsonify(token=make_token("admin", "admin"), role="admin")
        return err("Invalid credentials", 401)
    if role not in COL: return err("Invalid role")
    docs = list(db.collection(COL[role]).where("email", "==", email).limit(1).stream())
    if not docs or not bcrypt.checkpw(pw.encode(), docs[0].to_dict()["password_hash"].encode()):
        return err("Invalid credentials", 401)
    return jsonify(token=make_token(docs[0].id, role), role=role, name=docs[0].to_dict()["name"])

@app.get("/api/doctors")
@auth()
def doctors():
    args = {k: request.args.get(k, "") for k in ("q", "specialty", "location", "hospital")}
    raw = [(d.id, d.to_dict() or {}) for d in db.collection("doctors").stream()]
    found = filter_doctors(raw, args)
    print("Filters:", args, flush=True)
    print("Doctors in Firestore:", len(raw), flush=True)
    print("Doctors Found:", len(found), flush=True)
    print(found, flush=True)
    return jsonify(found)

@app.post("/api/appointments")
@auth("patient")
def book():
    d = request.get_json(force=True)
    doc_id, date, slot = clean(d.get("doctor_id")), clean(d.get("date"), 10), clean(d.get("slot"), 5)
    taken = db.collection("appointments").where("doctor_id", "==", doc_id).where("date", "==", date).where("slot", "==", slot).where("status", "in", ["pending", "approved"]).limit(1).stream()
    if list(taken): return err("Slot already booked", 409)
    p = db.collection("patients").document(g.user["sub"]).get().to_dict()
    total = p["attended"] + p["missed"]
    risk = predict_noshow(p["attended"] / total if total else 1.0, p["missed"], 30)
    ref = db.collection("appointments").document()
    ref.set({"patient_id": g.user["sub"], "doctor_id": doc_id, "date": date, "slot": slot, "status": "pending",
             "noshow_risk": risk, "reminded": False, "created_at": firestore.SERVER_TIMESTAMP})
    send_email(p["email"], "CareMate: appointment requested", f"Your appointment on {date} at {slot} is awaiting doctor approval.")
    return jsonify(id=ref.id, status="pending", noshow_risk=round(risk, 2)), 201

@app.get("/api/appointments")
@auth("patient", "doctor")
def my_appointments():
    field = "patient_id" if g.user["role"] == "patient" else "doctor_id"
    return jsonify([{**a.to_dict(), "id": a.id, "created_at": None} for a in db.collection("appointments").where(field, "==", g.user["sub"]).stream()])

@app.patch("/api/appointments/<aid>")
@auth("doctor")
def update_appointment(aid):
    status = request.get_json(force=True).get("status")
    ref = db.collection("appointments").document(aid); a = ref.get()
    if not a.exists or a.to_dict()["doctor_id"] != g.user["sub"]: return err("Not found", 404)
    if status not in ("approved", "rejected", "completed", "missed"): return err("Invalid status")
    ref.update({"status": status})
    if status in ("completed", "missed"):
        db.collection("patients").document(a.to_dict()["patient_id"]).update(
            {"attended" if status == "completed" else "missed": firestore.Increment(1), "last_visit": a.to_dict()["date"]})
    return jsonify(ok=True)

@app.put("/api/doctors/availability")
@auth("doctor")
def availability():
    db.collection("doctors").document(g.user["sub"]).update({"availability": [clean(s, 5) for s in request.get_json(force=True).get("slots", [])]})
    return jsonify(ok=True)

@app.post("/api/ai/symptoms")
@auth("patient")
@limiter.limit("20/hour")
def symptoms():
    text = clean(request.get_json(force=True).get("message"), 1000)
    if not text: return err("Describe your symptoms")
    res = triage(text)
    db.collection("chat_history").add({"patient_id": g.user["sub"], "message": text, "result": res, "at": firestore.SERVER_TIMESTAMP})
    db.collection("analytics").add({"type": "search", "specialty": res.get("specialty"), "at": firestore.SERVER_TIMESTAMP})
    return jsonify(res)


@app.post("/api/reports")
@auth("patient")
@limiter.limit("10/hour")
def upload_report():
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")): return err("Upload a PDF, JPG or PNG")
    data = f.read()
    if len(data) > 8_000_000: return err("File too large (8 MB max)")
    if f.filename.lower().endswith(".pdf"):
        from pypdf import PdfReader
        text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
    else:
        import pytesseract; from PIL import Image
        text = pytesseract.image_to_string(Image.open(io.BytesIO(data)))
    if not text.strip(): return err("No readable text found")
    summary = summarize_report(text)
    db.collection("medical_reports").add({"patient_id": g.user["sub"], "filename": clean(f.filename, 100), "summary": summary, "at": firestore.SERVER_TIMESTAMP})
    return jsonify(summary)

@app.get("/api/reports/<patient_id>")
@auth("doctor", "patient")
def reports(patient_id):
    if g.user["role"] == "patient" and g.user["sub"] != patient_id: return err("Forbidden", 403)
    return jsonify([{**r.to_dict(), "id": r.id, "at": None} for r in db.collection("medical_reports").where("patient_id", "==", patient_id).stream()])

@app.get("/api/admin/analytics")
@auth("admin")
def analytics():
    per_day, searches, done, missed = {}, {}, 0, 0
    for a in db.collection("appointments").stream():
        x = a.to_dict(); per_day[x["date"]] = per_day.get(x["date"], 0) + 1
        done += x["status"] == "completed"; missed += x["status"] == "missed"
    for s in db.collection("analytics").where("type", "==", "search").stream():
        k = s.to_dict().get("specialty") or "Unknown"; searches[k] = searches.get(k, 0) + 1
    return jsonify(appointments_per_day=per_day, top_specializations=searches,
                   no_show_rate=round(missed / (done + missed), 3) if done + missed else 0,
                   totals={c: len(list(db.collection(c).stream())) for c in ("patients", "doctors", "appointments")})
    


@app.get("/api/admin/<kind>")
@auth("admin")
def admin_list(kind):
    if kind not in ("patients", "doctors", "appointments"): return err("Not found", 404)
    return jsonify([{k: v for k, v in {**d.to_dict(), "id": d.id}.items() if k not in ("password_hash", "created_at")} for d in db.collection(kind).stream()])

def reminder_job():
    soon = (dt.datetime.now() + dt.timedelta(hours=24)).strftime("%Y-%m-%d")
    for a in db.collection("appointments").where("status", "==", "approved").where("reminded", "==", False).where("date", "==", soon).stream():
        x = a.to_dict(); p = db.collection("patients").document(x["patient_id"]).get().to_dict()
        msg = f"Reminder: your appointment is on {x['date']} at {x['slot']}."
        send_email(p["email"], "CareMate appointment reminder", msg)
        if x.get("noshow_risk", 0) > 0.7 and p.get("phone"): send_whatsapp(p["phone"], msg + " Please confirm or reschedule.")
        a.reference.update({"reminded": True})
        db.collection("notifications").add({"patient_id": x["patient_id"], "type": "reminder", "at": firestore.SERVER_TIMESTAMP})

if os.getenv("RUN_SCHEDULER", "1") == "1":
    _s = BackgroundScheduler(daemon=True); _s.add_job(reminder_job, "interval", hours=1); _s.start()
    
@app.get("/api/debug/doctors")
@auth()
def debug_doctors():
    if os.getenv("DEBUG_ENDPOINTS") != "1": return err("Not found", 404)
    docs = list(db.collection("doctors").stream())
    return jsonify(project=firebase_admin.get_app().project_id, count=len(docs),
        docs=[{"id": d.id, "field_types": {k: type(v).__name__ for k, v in (d.to_dict() or {}).items()},
               "specialization_repr": repr((d.to_dict() or {}).get("specialization"))} for d in docs])
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
