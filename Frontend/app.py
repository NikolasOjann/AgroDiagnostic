# app.py (VERSI FRONTEND MURNI - DECOUPLED)
import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import os

# Konfigurasi URL Backend (Bisa diatur via Environment Variables di Docker nanti)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ============================================================
# PAGE CONFIGURATION & CSS (TETAP DIPERTAHANKAN KARENA INI RANAH UI)
# ============================================================
st.set_page_config(page_title="Admin Dashboard - Diagnosis Cabai", page_icon="🌶️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background: #f1f5f9; }
    /* (Mempersingkat CSS di tampilan agar rapi, pastikan Anda menggunakan CSS lengkap Anda sebelumnya jika ada yang terpotong) */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); padding-top: 1.5rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] { color: #e2e8f0; }
    .sidebar-logo { text-align: center; padding: 0 1rem 1.5rem 1rem; margin-bottom: 1.5rem; border-bottom: 1px solid #334155; }
    .sidebar-logo-icon { font-size: 3rem; margin-bottom: 0.5rem; }
    .sidebar-logo-text { font-size: 1.2rem; font-weight: 700; background: linear-gradient(135deg, #a5d6a5, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; }
    .sidebar-section { padding: 0 1rem; margin-bottom: 1.5rem; }
    .sidebar-section-title { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin-bottom: 0.75rem; font-weight: 600; }
    .status-indicator { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; background: rgba(255,255,255,0.05); border-radius: 12px; margin: 1rem; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    .status-text { font-size: 0.7rem; color: #cbd5e1; }
    .status-version { font-size: 0.6rem; color: #64748b; margin-left: auto; }
    .sidebar-stats { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 1rem; margin: 1rem; }
    .sidebar-stat-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #334155; }
    .sidebar-stat-label { font-size: 0.7rem; color: #94a3b8; }
    .sidebar-stat-value { font-size: 0.8rem; font-weight: 600; color: #a5d6a5; }
    .sidebar-footer { position: absolute; bottom: 1rem; left: 0; right: 0; text-align: center; padding: 1rem; font-size: 0.6rem; color: #64748b; border-top: 1px solid #334155; margin: 0 1rem; }
    .main-content { padding: 1.5rem 2rem; }
    .page-header { margin-bottom: 1.5rem; }
    .page-title { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-bottom: 0.25rem; }
    .page-subtitle { font-size: 0.8rem; color: #64748b; }
    .stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    .stat-card { background: white; border-radius: 20px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; transition: all 0.2s; }
    .stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
    .stat-title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 0.5rem; }
    .stat-value { font-size: 1.8rem; font-weight: 700; color: #1e293b; }
    .stat-unit { font-size: 0.8rem; font-weight: 400; color: #94a3b8; }
    .stat-change { font-size: 0.7rem; margin-top: 0.5rem; color: #22c55e; }
    .card { background: white; border-radius: 20px; padding: 1.25rem; margin-bottom: 1.25rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
    .card-title { font-size: 1rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; display: flex; align-items: center; gap: 0.5rem; }
    .param-row { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid #f1f5f9; }
    .param-label { display: flex; align-items: center; gap: 0.75rem; font-size: 0.85rem; font-weight: 500; color: #334155; min-width: 160px; }
    .param-icon { font-size: 1.2rem; }
    .param-value { font-weight: 600; color: #1e293b; min-width: 60px; text-align: right; }
    .param-bar { width: 200px; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
    .param-bar-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
    .fill-good { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .fill-warning { background: linear-gradient(90deg, #f59e0b, #d97706); }
    .fill-bad { background: linear-gradient(90deg, #ef4444, #dc2626); }
    .score-indicator { text-align: center; padding: 1rem; }
    .score-circle { width: 130px; height: 130px; border-radius: 50%; margin: 0 auto; display: flex; flex-direction: column; align-items: center; justify-content: center; background: white; box-shadow: 0 8px 25px rgba(0,0,0,0.1); border: 3px solid #e2e8f0; }
    .score-number { font-size: 2.5rem; font-weight: 800; }
    .score-label { font-size: 0.6rem; color: #64748b; }
    .badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.35rem 0.9rem; border-radius: 30px; font-size: 0.7rem; font-weight: 600; }
    .badge-success { background: #dcfce7; color: #16a34a; }
    .badge-warning { background: #fef3c7; color: #d97706; }
    .badge-danger { background: #fee2e2; color: #dc2626; }
    .diagnosis-item { padding: 0.85rem; margin-bottom: 0.75rem; border-radius: 14px; background: #f8fafc; border-left: 4px solid; transition: all 0.2s; }
    .diagnosis-critical { border-left-color: #ef4444; background: #fef2f2; }
    .diagnosis-warning { border-left-color: #f59e0b; background: #fffbeb; }
    .diagnosis-title { font-weight: 700; font-size: 0.85rem; margin-bottom: 0.35rem; }
    .diagnosis-message { font-size: 0.75rem; color: #475569; margin-bottom: 0.35rem; }
    .diagnosis-action { font-size: 0.7rem; color: #2e7d32; margin-top: 0.35rem; padding-top: 0.35rem; border-top: 1px dashed #e2e8f0; }
    .data-table-container { overflow-x: auto; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPER FUNCTIONS UNTUK UI
# ============================================================
def get_progress_class(value, optimal_min, optimal_max):
    if optimal_min <= value <= optimal_max: return "fill-good"
    elif value < optimal_min and value > optimal_min - 15: return "fill-warning"
    elif value > optimal_max and value < optimal_max + 15: return "fill-warning"
    else: return "fill-bad"

def get_progress_width(value, optimal_min, optimal_max, max_val=100):
    if value < optimal_min: return (value / optimal_min) * 100
    elif value > optimal_max: return max(0, 100 - ((value - optimal_max) / (max_val - optimal_max) * 50))
    else: return 100

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🌶️🌿</div>
        <div class="sidebar-logo-text">AgroDiagnostic</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section"><div class="sidebar-section-title">SYSTEM STATUS</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot"></div>
        <div class="status-text">API Connected</div>
        <div class="status-version">Online</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    if 's_in' not in st.session_state:
        st.session_state.update({'s_in': 28.0, 'k_in': 70, 'p_in': 6.5, 't_in': 65, 'c_in': 75, 'u_in': 45})
    
    st.markdown('<div class="sidebar-section"><div class="sidebar-section-title">QUICK STATS</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sidebar-stats">
        <div class="sidebar-stat-item"><span class="sidebar-stat-label">Parameters Active</span><span class="sidebar-stat-value">6/6</span></div>
        <div class="sidebar-stat-item"><span class="sidebar-stat-label">AI Engine</span><span class="sidebar-stat-value">Cloud Backend</span></div>
        <div class="sidebar-stat-item"><span class="sidebar-stat-label">Session ID</span><span class="sidebar-stat-value">#CHL-{datetime.now().strftime('%d%m')}</span></div>
    </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-footer">Kelompok 3<br>Powered by Cloud Microservices</div>', unsafe_allow_html=True)

# ============================================================
# MAIN CONTENT
# ============================================================
st.markdown('<div class="main-content">', unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <div class="page-title">Dashboard Diagnosis Cabai</div>
    <div class="page-subtitle">Monitoring kualitas tanaman berbasis AI & Microservices | Real-time analysis</div>
</div>
""", unsafe_allow_html=True)

# Input parameters
col1, col2, col3 = st.columns(3)
with col1:
    s_in = st.slider("🌡️ Suhu Lingkungan", 0.0, 50.0, 28.0, 0.5, format="%.1f °C")
    t_in = st.slider("💧 Kelembaban Tanah", 0, 100, 65, format="%d %%")
with col2:
    k_in = st.slider("💨 Kelembaban Udara", 0, 100, 70, format="%d %%")
    p_in = st.slider("🧪 pH Tanah", 0.0, 14.0, 6.5, 0.1, format="%.1f")
with col3:
    c_in = st.slider("☀️ Intensitas Cahaya", 0, 100, 75, format="%d %%")
    u_in = st.slider("🌱 Umur Tanaman", 0, 120, 45, format="%d hari")

# ============================================================
# MENGIRIM DATA KE BACKEND FASTAPI
# ============================================================
skor = 50
diagnoses = []
payload = {
    "suhu": s_in, "kelembaban": k_in, "ph": p_in, 
    "tanah": t_in, "cahaya": c_in, "umur": u_in
}

try:
    # Ini akan memanggil backend API Anda
    res = requests.post(f"{BACKEND_URL}/predict-fuzzy", json=payload)
    if res.status_code == 200:
        data = res.json()
        skor = data.get("skor", 50)
        diagnoses = data.get("diagnoses", [])
except Exception as e:
    # Fallback jika backend mati
    diagnoses = [{'type': 'critical', 'title': '🔌 API Terputus', 'message': 'Gagal menghubungi Backend FastAPI.', 'saran': 'Pastikan container Backend berjalan.'}]

# Determine phase
if u_in < 30: phase, phase_detail = "🌱 Fase Bibit", "0-30 hari"
elif u_in < 60: phase, phase_detail = "🌿 Fase Vegetatif", "30-60 hari"
else: phase, phase_detail = "🍎 Fase Produktif", "60-120 hari"

# Stats Cards
if skor <= 45: status_text, status_color, status_icon = "Kritis", "badge-danger", "🔴"
elif skor <= 75: status_text, status_color, status_icon = "Perlu Perhatian", "badge-warning", "🟡"
else: status_text, status_color, status_icon = "Optimal", "badge-success", "🟢"

st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card"><div class="stat-title">SKOR KUALITAS</div><div class="stat-value">{skor:.1f}<span class="stat-unit">/100</span></div><div class="stat-change">Fuzzy Inference Result</div></div>
    <div class="stat-card"><div class="stat-title">STATUS</div><div class="stat-value" style="font-size: 1rem;"><span class="badge {status_color}">{status_icon} {status_text}</span></div><div class="stat-change">Last updated: {datetime.now().strftime('%H:%M:%S')}</div></div>
    <div class="stat-card"><div class="stat-title">FASE TANAMAN</div><div class="stat-value" style="font-size: 1.1rem;">{phase}</div><div class="stat-change">{phase_detail}</div></div>
    <div class="stat-card"><div class="stat-title">PARAMETER</div><div class="stat-value" style="font-size: 1.1rem;">6 Aktif</div><div class="stat-change">API Synced</div></div>
</div>
""", unsafe_allow_html=True)

# Main content split
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<div class="card"><div class="card-title"><span>📊</span> Parameter Monitoring</div>', unsafe_allow_html=True)
    params = [
        {"name": "Suhu Lingkungan", "icon": "🌡️", "value": f"{s_in:.1f}°C", "optimal_min": 25, "optimal_max": 30, "current": s_in, "max_val": 50},
        {"name": "Kelembaban Udara", "icon": "💨", "value": f"{k_in}%", "optimal_min": 60, "optimal_max": 80, "current": k_in, "max_val": 100},
        {"name": "pH Tanah", "icon": "🧪", "value": f"{p_in:.1f}", "optimal_min": 6.2, "optimal_max": 6.8, "current": p_in, "max_val": 14},
        {"name": "Kelembaban Tanah", "icon": "💧", "value": f"{t_in}%", "optimal_min": 60, "optimal_max": 80, "current": t_in, "max_val": 100},
        {"name": "Intensitas Cahaya", "icon": "☀️", "value": f"{c_in}%", "optimal_min": 70, "optimal_max": 90, "current": c_in, "max_val": 100},
    ]
    for p in params:
        p_w = get_progress_width(p['current'], p['optimal_min'], p['optimal_max'], p['max_val'])
        p_c = get_progress_class(p['current'], p['optimal_min'], p['optimal_max'])
        st.markdown(f"""
        <div class="param-row"><div class="param-label"><span class="param-icon">{p['icon']}</span><span>{p['name']}</span></div>
        <div style="display: flex; align-items: center; gap: 1rem;"><div class="param-bar"><div class="param-bar-fill {p_c}" style="width: {p_w}%;"></div></div><div class="param-value">{p['value']}</div></div></div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    if skor <= 45: score_color, bg_gradient = "#dc2626", "linear-gradient(135deg, #fef2f2, #fee2e2)"
    elif skor <= 75: score_color, bg_gradient = "#d97706", "linear-gradient(135deg, #fffbeb, #fef3c7)"
    else: score_color, bg_gradient = "#16a34a", "linear-gradient(135deg, #f0fdf4, #dcfce7)"
    
    st.markdown(f"""
    <div class="card"><div class="card-title"><span>🎯</span> Quality Score</div>
    <div class="score-indicator"><div class="score-circle" style="background: {bg_gradient};"><div class="score-number" style="color: {score_color};">{skor:.1f}</div><div class="score-label">/ 100</div></div></div>
    """, unsafe_allow_html=True)
    
    summary = "✨ Optimal" if skor >= 75 else "📋 Perlu Perbaikan" if skor >= 45 else "⚠️ Kritis!"
    st.markdown(f'<div style="text-align: center; margin-top: 1rem; padding: 0.75rem; background: #f8fafc; border-radius: 12px;"><span style="font-size: 0.8rem; color: #475569;">{summary}</span></div></div>', unsafe_allow_html=True)

# Diagnosis Section
st.markdown('<div class="card"><div class="card-title"><span>🔍</span> Diagnosis & Rekomendasi</div>', unsafe_allow_html=True)
if diagnoses:
    for diag in diagnoses:
        css_class = "diagnosis-critical" if diag['type'] == 'critical' else "diagnosis-warning"
        st.markdown(f"""
        <div class="diagnosis-item {css_class}">
            <div class="diagnosis-title">{diag['title']}</div>
            <div class="diagnosis-message">{diag['message']}</div>
            <div class="diagnosis-action">💡 Tindakan: {diag['saran']}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="diagnosis-item" style="border-left-color: #22c55e; background: #f0fdf4;">
        <div class="diagnosis-title">✅ Analisis API: Semua Parameter Optimal</div>
        <div class="diagnosis-message">Tanaman cabai dalam kondisi sehat dan optimal</div>
        <div class="diagnosis-action">💡 Lanjutkan perawatan yang sudah dilakukan</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# NLP GEJALA (VIA API)
# ============================================================
st.markdown("---")
col_nlp, col_upload = st.columns(2)

with col_nlp:
    st.subheader("📝 Analisis Gejala NLP")
    gejala_text = st.text_area("Masukkan gejala tanaman", placeholder="Contoh: daun menguning dan tanaman layu")
    if st.button("Analisis Gejala"):
        try:
            res_nlp = requests.post(f"{BACKEND_URL}/analyze-nlp", json={"teks": gejala_text})
            hasil_nlp = res_nlp.json().get("hasil", [])
            
            if hasil_nlp:
                for item in hasil_nlp:
                    st.success(f"Gejala Terdeteksi : {item['gejala'].title()}")
                    st.write(f"**Diagnosis :** {item['masalah']}")
                    st.write(f"**Solusi :** {item['solusi']}")
                    st.divider()
            else:
                st.warning("Gejala tidak dikenali oleh mesin Sastrawi di Backend.")
        except:
            st.error("Gagal memanggil API NLP di Backend.")

# ============================================================
# MULTI-CLOUD STORAGE UPLOAD (SYARAT 10%)
# ============================================================
with col_upload:
    st.subheader("☁️ Diagnosis Visual (Multi-Cloud)")
    st.info("Upload foto daun akan dikirim ke GCP Cloud Storage melalui Backend AWS.")
    uploaded_file = st.file_uploader("Upload Foto Daun", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        if st.button("Kirim ke Cloud Storage"):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                res_upload = requests.post(f"{BACKEND_URL}/upload-image", files=files)
                if res_upload.status_code == 200:
                    url_gambar = res_upload.json().get("url")
                    st.success("File berhasil disimpan di Bucket terpisah!")
                    st.write(f"🔗 URL: {url_gambar}")
                else:
                    st.error("Gagal mengunggah ke Storage.")
            except:
                st.error("Gagal memanggil API Upload.")

# ============================================================
# CHATBOT GEMINI AI (VIA API)
# ============================================================
st.markdown("---")
st.subheader("🤖 Chatbot Konsultan AI (Gemini)")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

pertanyaan = st.chat_input("Tanyakan sesuatu tentang tanaman cabai...")

if pertanyaan:
    st.session_state.chat_history.append(("user", pertanyaan))
    
    # Panggil Backend API Chat
    try:
        res_chat = requests.post(f"{BACKEND_URL}/chat", json={"pesan": pertanyaan})
        jawaban = res_chat.json().get("jawaban", "Maaf, tidak ada respon.")
    except:
        jawaban = "Maaf, sistem AI sedang offline. Pastikan backend menyala."
        
    st.session_state.chat_history.append(("assistant", jawaban))

for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(msg)

st.markdown('</div>', unsafe_allow_html=True)