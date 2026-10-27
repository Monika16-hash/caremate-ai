<img width="1142" height="2268" alt="image" src="https://github.com/user-attachments/assets/cb79d21d-b6f2-49ac-b9f3-ebef68874770" />
<img width="4032" height="1423" alt="image" src="https://github.com/user-attachments/assets/763ca636-3c5d-4c7c-8d61-9bf73b11d572" />

# CareMate AI
React + Tailwind + MUI icons (Vite) · Flask + JWT · Firestore · Gemini.

## Setup
```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values; put the Firebase service-account JSON at FIREBASE_CREDENTIALS
python app.py          # http://localhost:5000
# Frontend
cd frontend && npm install && cp .env.example .env && npm run dev
```
Image OCR needs the Tesseract binary (`sudo apt install tesseract-ocr`). WhatsApp needs `pip install twilio`.

## Firestore collections
- `patients`: name, email, phone, password_hash, attended, missed, last_visit
- `doctors`: name, email, password_hash, specialization, hospital, location, availability[]
- `appointments`: patient_id, doctor_id, date, slot, status (pending|approved|rejected|completed|missed), noshow_risk, reminded
- `medical_reports`: patient_id, filename, summary{key_findings, important_values, recommendations}
- `notifications`: patient_id, type, at · `chat_history`: patient_id, message, result · `analytics`: type, specialty, at

Firestore will prompt you to create composite indexes on first run of the booking and reminder queries; follow the link in the error.

## API (JSON; `Authorization: Bearer <jwt>` on everything except auth)
| Endpoint | Method | Request | Response |
|---|---|---|---|
| /api/auth/register | POST | role, name, email, password (+specialization, hospital, location for doctors) | token, role |
| /api/auth/login | POST | role, email, password | token, role |
| /api/doctors | GET | ?q &specialty &location &hospital | doctor[] |
| /api/appointments | POST (patient) | doctor_id, date, slot | id, status, noshow_risk |
| /api/appointments | GET | none | appointment[] |
| /api/appointments/:id | PATCH (doctor) | status | ok |
| /api/doctors/availability | PUT (doctor) | slots[] | ok |
| /api/ai/symptoms | POST (patient) | message | specialty, reason, urgent, disclaimer |
| /api/reports | POST (patient) | multipart `file` | key_findings, important_values, recommendations |
| /api/reports/:patient_id | GET | none | report[] |
| /api/admin/analytics | GET (admin) | none | appointments_per_day, top_specializations, no_show_rate, totals |
| /api/admin/:kind | GET (admin) | patients, doctors or appointments | row[] |

## Tests
`cd backend && pytest` · `cd frontend && npm test`

## Deploy
1. **Firebase**: create a project, enable Firestore, generate a service-account key.
2. **Render** (backend): Web Service, root `backend`, build `pip install -r requirements.txt`, start `gunicorn app:app`. Add env vars from `.env.example`; store the service-account JSON as a Secret File and point `FIREBASE_CREDENTIALS` to it. Set `FRONTEND_ORIGIN` to your Vercel URL.
3. **Vercel** (frontend): root `frontend`, framework Vite, env `VITE_API_URL=https://<render-app>.onrender.com/api`.
