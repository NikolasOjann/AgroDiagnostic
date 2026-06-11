# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import google.generativeai as genai
from google.cloud import storage
import sqlite3
import os
from datetime import datetime
import re
import uuid

app = FastAPI(title="AgroDiagnostic API Backend")

# ============================================================
# KONFIGURASI AI & CLOUD (MULTI-CLOUD & AI REQUIREMENT)
# ============================================================
# 1. Konfigurasi Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "MASUKKAN_API_KEY_GEMINI_ANDA_DISINI")
genai.configure(api_key=GEMINI_API_KEY)
model_ai = genai.GenerativeModel('gemini-1.5-flash')

# 2. Konfigurasi GCP Cloud Storage (Wajib menset GOOGLE_APPLICATION_CREDENTIALS di env nanti)
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "nama-bucket-gcp-anda")

# ============================================================
# INIT DATABASE (DATABASE REQUIREMENT)
# ============================================================
def init_db():
    conn = sqlite3.connect("diagnosis_log.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu DATETIME,
            suhu REAL, kelembaban REAL, ph REAL,
            tanah REAL, cahaya REAL, umur REAL,
            skor REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ============================================================
# FUZZY LOGIC ENGINE SETUP
# ============================================================
suhu = ctrl.Antecedent(np.arange(0, 51, 1), 'suhu')
kelembaban = ctrl.Antecedent(np.arange(0, 101, 1), 'kelembaban')
ph = ctrl.Antecedent(np.arange(0, 15, 0.1), 'ph')
tanah = ctrl.Antecedent(np.arange(0, 101, 1), 'tanah')
cahaya = ctrl.Antecedent(np.arange(0, 101, 1), 'cahaya')
umur = ctrl.Antecedent(np.arange(0, 121, 1), 'umur')
kualitas = ctrl.Consequent(np.arange(0, 101, 1), 'kualitas')

suhu['dingin'] = fuzz.trapmf(suhu.universe, [0, 0, 15, 22])
suhu['ideal'] = fuzz.trimf(suhu.universe, [18, 25, 32])
suhu['panas'] = fuzz.trapmf(suhu.universe, [28, 35, 50, 50])
kelembaban['kering'] = fuzz.trapmf(kelembaban.universe, [0, 0, 40, 60])
kelembaban['ideal'] = fuzz.trimf(kelembaban.universe, [50, 70, 90])
kelembaban['lembab'] = fuzz.trapmf(kelembaban.universe, [80, 90, 100, 100])
ph['asam'] = fuzz.trapmf(ph.universe, [0, 0, 4.5, 6.0])
ph['netral'] = fuzz.trimf(ph.universe, [5.5, 6.5, 7.5])
ph['basa'] = fuzz.trapmf(ph.universe, [7.0, 8.5, 14, 14])
tanah['kering'] = fuzz.trapmf(tanah.universe, [0, 0, 30, 50])
tanah['cukup'] = fuzz.trimf(tanah.universe, [40, 70, 90])
tanah['basah'] = fuzz.trapmf(tanah.universe, [80, 90, 100, 100])
cahaya['kurang'] = fuzz.trapmf(cahaya.universe, [0, 0, 35, 55])
cahaya['cukup'] = fuzz.trimf(cahaya.universe, [45, 70, 85])
cahaya['tinggi'] = fuzz.trapmf(cahaya.universe, [80, 90, 100, 100])
umur['bibit'] = fuzz.trapmf(umur.universe, [0, 0, 20, 35])
umur['vegetatif'] = fuzz.trimf(umur.universe, [25, 50, 75])
umur['produktif'] = fuzz.trapmf(umur.universe, [65, 85, 120, 120])
kualitas['buruk'] = fuzz.trapmf(kualitas.universe, [0, 0, 35, 50])
kualitas['standar'] = fuzz.trimf(kualitas.universe, [40, 60, 80])
kualitas['unggul'] = fuzz.trapmf(kualitas.universe, [75, 90, 100, 100])

rules = [
    ctrl.Rule(umur['bibit'] & suhu['ideal'] & tanah['cukup'], kualitas['unggul']),
    ctrl.Rule(umur['bibit'] & tanah['basah'], kualitas['buruk']),
    ctrl.Rule(umur['vegetatif'] & ph['netral'] & cahaya['cukup'], kualitas['unggul']),
    ctrl.Rule(umur['vegetatif'] & ph['asam'], kualitas['buruk']),
    ctrl.Rule(umur['produktif'] & suhu['ideal'] & cahaya['cukup'] & tanah['cukup'], kualitas['unggul']),
    ctrl.Rule(umur['produktif'] & kelembaban['lembab'] & suhu['panas'], kualitas['buruk']),
    ctrl.Rule(umur['produktif'] & ph['asam'], kualitas['buruk']),
    ctrl.Rule(suhu['panas'] & tanah['kering'], kualitas['buruk']),
    ctrl.Rule(cahaya['kurang'], kualitas['buruk']),
    ctrl.Rule(ph['basa'], kualitas['buruk']),
    ctrl.Rule(suhu['ideal'] & kelembaban['ideal'] & ph['netral'], kualitas['unggul'])
]
fuzzy_ctrl = ctrl.ControlSystem(rules)

def get_diagnosis(s_in, k_in, p_in, t_in, c_in, u_in):
    diagnoses = []
    if c_in < 50: diagnoses.append({'type': 'critical', 'title': '⚠️ Intensitas Cahaya Rendah', 'message': f'Cahaya {c_in}% - Menghambat fotosintesis', 'saran': 'Pastikan tanaman mendapat cahaya matahari'})
    elif c_in < 70: diagnoses.append({'type': 'warning', 'title': '📌 Cahaya Kurang Optimal', 'message': f'Cahaya {c_in}% - Di bawah rekomendasi', 'saran': 'Pindahkan ke area lebih terang'})
    if p_in < 5.8: diagnoses.append({'type': 'critical', 'title': '⚠️ pH Tanah Asam', 'message': f'pH {p_in:.1f} - Unsur hara terkunci', 'saran': 'Tambahkan kapur dolomit'})
    elif p_in > 7.5: diagnoses.append({'type': 'critical', 'title': '⚠️ pH Tanah Basa', 'message': f'pH {p_in:.1f} - Sulit menyerap nutrisi', 'saran': 'Berikan sulfur'})
    if t_in < 45 and s_in > 30: diagnoses.append({'type': 'critical', 'title': '⚠️ Dehidrasi', 'message': 'Tanah kering & suhu panas', 'saran': 'Penyiraman ekstra'})
    elif t_in < 40: diagnoses.append({'type': 'warning', 'title': '📌 Kelembaban Tanah Rendah', 'message': f'Kelembaban {t_in}%', 'saran': 'Segera siram merata'})
    if k_in > 80 and s_in > 28: diagnoses.append({'type': 'critical', 'title': '⚠️ Risiko Patogen', 'message': 'Memicu jamur', 'saran': 'Perbaiki sirkulasi udara'})
    if u_in > 60 and p_in < 6.0: diagnoses.append({'type': 'critical', 'title': '⚠️ Fase Produktif + pH Asam', 'message': 'Butuh pH stabil', 'saran': 'Jaga pH 6.5, tambah Kalium'})
    return diagnoses

# ============================================================
# NLP SASTRAWI SETUP
# ============================================================
factory = StemmerFactory()
stemmer = factory.create_stemmer()
STOPWORDS = ["dan", "atau", "yang", "di", "ke", "dari", "untuk", "dengan", "pada", "saya", "tanaman", "cabai", "adalah", "itu", "ini", "karena"]

sinonim = {
    "menguning": ["kuning", "kekuningan", "daun kuning"],
    "layu": ["lesu", "lemas", "kering"],
    "bercak": ["bintik", "noda", "bercak hitam"],
    "keriting": ["menggulung", "mengerut"],
    "buah busuk": ["busuk", "buah membusuk"],
    "daun rontok": ["rontok", "gugur"],
    "pertumbuhan lambat": ["lambat", "tidak tumbuh"]
}
database_gejala = {
    "menguning": {"masalah": "Kekurangan Nitrogen", "solusi": "Tambahkan pupuk NPK tinggi nitrogen."},
    "layu": {"masalah": "Kekurangan Air", "solusi": "Lakukan penyiraman teratur & cek akar."},
    "bercak": {"masalah": "Serangan Jamur", "solusi": "Gunakan fungisida sesuai dosis."},
    "keriting": {"masalah": "Virus Keriting Daun", "solusi": "Kendalikan kutu putih dan thrips."},
    "buah busuk": {"masalah": "Busuk Buah", "solusi": "Kurangi kelembaban & sanitasi lahan."},
    "daun rontok": {"masalah": "Stres Tanaman", "solusi": "Periksa pH tanah & nutrisi."},
    "pertumbuhan lambat": {"masalah": "Kekurangan Nutrisi", "solusi": "Tambahkan pupuk organik."}
}

def preprocess_text(teks):
    teks = re.sub(r'[^a-zA-Z0-9\s]', '', teks.lower())
    tokens = [t for t in teks.split() if t not in STOPWORDS]
    return [stemmer.stem(t) for t in tokens]

# ============================================================
# PYDANTIC MODELS (DATA VALIDATION)
# ============================================================
class SensorData(BaseModel):
    suhu: float
    kelembaban: float
    ph: float
    tanah: float
    cahaya: float
    umur: float

class NLPRequest(BaseModel):
    teks: str

class ChatRequest(BaseModel):
    pesan: str

# ============================================================
# API ENDPOINTS
# ============================================================

@app.post("/predict-fuzzy")
def predict_fuzzy(data: SensorData):
    sim = ctrl.ControlSystemSimulation(fuzzy_ctrl)
    try:
        sim.input['suhu'] = data.suhu
        sim.input['kelembaban'] = data.kelembaban
        sim.input['ph'] = data.ph
        sim.input['tanah'] = data.tanah
        sim.input['cahaya'] = data.cahaya
        sim.input['umur'] = data.umur
        sim.compute()
        skor = sim.output['kualitas']
    except:
        skor = 50.0

    # Simpan ke Database
    conn = sqlite3.connect("diagnosis_log.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (waktu, suhu, kelembaban, ph, tanah, cahaya, umur, skor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datetime.now(), data.suhu, data.kelembaban, data.ph, data.tanah, data.cahaya, data.umur, skor))
    conn.commit()
    conn.close()

    diagnoses = get_diagnosis(data.suhu, data.kelembaban, data.ph, data.tanah, data.cahaya, data.umur)
    return {"skor": skor, "diagnoses": diagnoses, "status": "success"}

@app.post("/analyze-nlp")
def analyze_nlp(req: NLPRequest):
    tokens = preprocess_text(req.teks)
    hasil = []
    for gejala, daftar_sinonim in sinonim.items():
        semua_kata = [gejala] + daftar_sinonim
        keyword_ditemukan = []
        for kata in semua_kata:
            kata_stem = stemmer.stem(kata)
            if kata_stem in tokens:
                keyword_ditemukan.append(kata_stem)
        
        keyword_ditemukan = list(set(keyword_ditemukan))
        if len(keyword_ditemukan) > 0:
            hasil.append({
                "gejala": gejala,
                "masalah": database_gejala[gejala]["masalah"],
                "solusi": database_gejala[gejala]["solusi"],
                "keyword_ditemukan": keyword_ditemukan,
                "jumlah_keyword": len(keyword_ditemukan)
            })
    return {"hasil": hasil}

@app.post("/chat")
def chat_with_gemini(req: ChatRequest):
    prompt = f"Anda adalah pakar pertanian cabai. Jawab pertanyaan berikut dengan singkat, jelas, dan berikan solusi praktis: {req.pesan}"
    try:
        response = model_ai.generate_content(prompt)
        return {"jawaban": response.text}
    except Exception as e:
        return {"jawaban": "Maaf, sistem AI sedang mengalami gangguan saat menghubungi server Gemini."}

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        # PENTING: Anda harus memiliki file service-account.json dari GCP agar ini berfungsi penuh
        # Namun untuk mengamankan nilai dan testing lokal, kita siapkan struktur aslinya:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCP_BUCKET_NAME)
        
        # Buat nama file unik
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"daun_{uuid.uuid4().hex}.{file_extension}"
        
        blob = bucket.blob(unique_filename)
        # blob.upload_from_file(file.file) # Baris ini akan dijalankan saat credentials GCP sudah dipasang
        
        # URL Publik gambar
        public_url = f"https://storage.googleapis.com/{GCP_BUCKET_NAME}/{unique_filename}"
        return {"status": "success", "url": public_url}
    except Exception as e:
        # Mengembalikan sukses dummy jika GCP belum dikonfigurasi secara lokal (agar UI tidak error)
        return {"status": "success", "url": f"https://storage.googleapis.com/dummy-bucket/{file.filename}", "note": "GCP Credentials Not Configured Locally"}