# ============================================
# SemitIA – IHRA Dashboard (Streamlit frontend)
# Minimal, claro y con FIX definitivo de íconos del header
# ============================================

import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="SemitIA – IHRA Dashboard", page_icon="🕊️", layout="centered")

# ===== CSS unificado y FIX de íconos =====
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
  background-color: #FFFFFF !important;
  color: #0F172A !important;
}

/* HEADER */
header[data-testid="stHeader"], .stApp header {
  background-color: #FFFFFF !important;
  color: #0F172A !important;
  border-bottom: 1px solid #E5E7EB !important;
}

/* FIX definitivo de íconos oscuros */
[data-testid="stToolbar"], header [data-testid="stToolbar"], .stApp header [data-testid="stToolbar"] {
  color: #0F172A !important;
  opacity: 1 !important;
  filter: none !important;
  mix-blend-mode: normal !important;
}
header[data-testid="stHeader"] svg,
header[data-testid="stHeader"] svg *,
[data-testid="stToolbar"] svg,
[data-testid="stToolbar"] svg *,
.stApp header svg,
.stApp header svg * {
  fill: #0F172A !important;
  stroke: #0F172A !important;
  color: #0F172A !important;
  opacity: 1 !important;
  visibility: visible !important;
  display: inline-block !important;
  filter: none !important;
  mix-blend-mode: normal !important;
  width: 1em !important; height: 1em !important;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
  background-color: #F7F9FC !important;
  color: #0F172A !important;
}
[data-testid="stSidebar"] * {
  color: #0F172A !important;
}

/* BOTONES */
.stButton > button, .stDownloadButton > button {
  background: #0F172A !important;
  color: #FFFFFF !important;
  border: 1px solid #0F172A !important;
  border-radius: 10px !important;
  padding: 10px 16px !important;
  font-weight: 600 !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: #15223B !important;
}

/* FILE UPLOADER */
[data-testid="stFileUploaderDropzone"] {
  background: #FFFFFF !important;
  border: 2px dashed #CBD5E1 !important;
  color: #0F172A !important;
  border-radius: 14px !important;
}
[data-testid="stFileUploaderDropzone"] * { color: #0F172A !important; }
[data-testid="stFileUploaderDropzone"] svg,
[data-testid="stFileUploaderDropzone"] svg * {
  fill: #0F172A !important; stroke: #0F172A !important;
}
[data-testid="stFileUploaderDropzone"] button {
  background: #0F172A !important;
  color: #FFFFFF !important;
  border: 1px solid #0F172A !important;
  border-radius: 10px !important;
  padding: 8px 14px !important;
  font-weight: 600 !important;
}

/* CARDS */
.badge {display:inline-block;padding:4px 10px;border-radius:999px;font-size:12px;border:1px solid #e5e7eb;background:#f8fafc}
.badge-0 {background:#e6f7ff;border-color:#b3e5fc}
.badge-1 {background:#fffbe6;border-color:#ffec99}
.badge-2 {background:#fff1f0;border-color:#ffc9c9}
.badge-3 {background:#ffe7ba;border-color:#ffd8a8}
.card {border:1px solid #eaecef;border-radius:16px;padding:14px;background:#ffffff}
.caption {color:#64748b;font-size:12px}
.footer {margin-top:30px;color:#94a3b8;font-size:12px;text-align:center}

.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ===== Variables de entorno (secrets) =====
API_BASE = st.secrets.get("API_BASE")
API_ENDPOINT = st.secrets.get("API_ENDPOINT")
API_TOKEN = st.secrets.get("API_TOKEN")

def get_headers():
    h = {"Content-Type": "application/json"}
    if API_TOKEN:
        h["Authorization"] = API_TOKEN if API_TOKEN.lower().startswith("bearer ") else f"Bearer {API_TOKEN}"
    return h

def get_classify_url():
    if API_ENDPOINT:
        return API_ENDPOINT
    if API_BASE:
        return f"{API_BASE}/api/classify"
    return None

def get_stats_url():
    return f"{API_BASE}/api/stats" if API_BASE else None

# ===== Portada =====
st.markdown("## 🕊️ SemitIA")
st.markdown("Clasificación **IHRA (0–3)** con explicación y confianza para entender y prevenir el antisemitismo online.")

col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Demo en vivo"):
        st.session_state["_mode"] = "Clasificación en vivo"
with col2:
    if st.button("📂 Subir CSV"):
        st.session_state["_mode"] = "CSV"

default_mode = st.session_state.get("_mode", "CSV")

# ===== Sidebar =====
st.sidebar.title("SemitIA")
mode = st.sidebar.radio("Modo", ["CSV", "Clasificación en vivo", "Estadísticas"],
                        index=["CSV","Clasificación en vivo","Estadísticas"].index(default_mode))
with st.sidebar.expander("Acerca de"):
    st.markdown("Clasificación automática del discurso sobre judíos/Israel según la definición IHRA (2016).")
    st.markdown('<span class="caption">Demo educativa. No reemplaza moderación humana.</span>', unsafe_allow_html=True)

# ===== CSV =====
if mode == "CSV":
    st.markdown("### 📊 Análisis IHRA de Tuits (CSV)")
    uploaded = st.file_uploader("Arrastrá o elegí un archivo CSV", type=["csv"])

    if uploaded:
        df = pd.read_csv(uploaded)
        cols = {"texto", "etiqueta_gpt", "subtipo_gpt", "confidence_gpt", "reason_gpt"}
        faltantes = cols - set(df.columns)
        if faltantes:
            st.error(f"Faltan columnas: {', '.join(sorted(faltantes))}")
            st.stop()

        st.download_button("💾 Descargar CSV enriquecido",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="semitia_clasificado.csv", mime="text/csv")

        st.write(f"Tuits analizados: **{len(df)}**")
        conteo = df["etiqueta_gpt"].value_counts().sort_index()
        fig, ax = plt.subplots()
        ax.bar(conteo.index.astype(str), conteo.values)
        st.pyplot(fig)

        opcion = st.selectbox("Filtrar por categoría (0–3):", sorted(df["etiqueta_gpt"].dropna().unique()))
        st.dataframe(df[df["etiqueta_gpt"] == opcion][["texto", "subtipo_gpt", "confidence_gpt", "reason_gpt"]])
    else:
        st.info("⬆️ Subí un CSV con tus clasificaciones.")

# ===== Clasificación en vivo =====
elif mode == "Clasificación en vivo":
    st.markdown("### 🔎 Clasificación IHRA en vivo")
    ejemplos = {
        "0 · Neutro": "Hoy se recuerda el Holocausto.",
        "1 · Crítica política": "El gobierno de Israel actúa de forma desproporcionada.",
        "2 · Implícito": "Israel controla los medios y nadie lo dice.",
        "3 · Explícito": "El Holocausto nunca existió."
    }
    ej = st.selectbox("Elegí un ejemplo (opcional)", list(ejemplos.keys()), index=None)
    if ej:
        st.session_state["_texto_demo"] = ejemplos[ej]

    texto = st.text_area("Pegá un tuit o texto corto en español", height=140, value=st.session_state.get("_texto_demo",""))
    timeout_s = st.slider("⏱️ Timeout (segundos)", 5, 60, 20)

    if st.button("Clasificar"):
        url = get_classify_url()
        if not url:
            st.error("No hay URL configurada.")
            st.stop()
        if not texto.strip():
            st.warning("Pegá un texto primero.")
            st.stop()
        try:
            t0 = time.time()
            with st.spinner("Clasificando..."):
                r = requests.post(url, headers=get_headers(), json={"text": texto}, timeout=timeout_s)
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

        elapsed = int((time.time() - t0) * 1000)
        if r.status_code != 200:
            st.error(f"Error {r.status_code}: {r.text}")
        else:
            data = r.json()
            nivel = data.get("label")
            sub = data.get("subtype") or "—"
            conf = data.get("confidence")
            rsn = data.get("reason") or "—"
            st.markdown(f"""
            <div class="card">
              <div class="badge badge-{nivel}">Nivel IHRA: {nivel}</div>
              <div><b>Subtipo:</b> {sub}</div>
              <div><b>Confianza:</b> {f"{conf*100:.1f}%" if isinstance(conf,(int,float)) else "—"}</div>
              <div><b>Reason:</b> {rsn}</div>
            </div>
            """, unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Nivel IHRA", nivel if nivel is not None else "—")
            c2.metric("Confianza", f"{conf*100:.1f}%" if isinstance(conf,(int,float)) else "—")
            c3.metric("Tiempo", f"{elapsed} ms")

# ===== Estadísticas =====
elif mode == "Estadísticas":
    st.markdown("### 📈 Estadísticas globales")
    url_stats = get_stats_url()
    if not url_stats:
        st.info("Configura API_BASE en Secrets para habilitar /api/stats.")
        st.stop()

    rango = st.selectbox("Rango", ["7d", "30d", "90d"], index=1)
    try:
        resp = requests.get(url_stats, headers=get_headers(), params={"range": rango}, timeout=30)
    except Exception as e:
        st.error(f"No se pudo conectar: {e}")
        st.stop()

    if resp.status_code != 200:
        st.error(f"Error: {resp.status_code}")
        st.stop()

    stats = resp.json()
    counts = stats.get("counts", {})
    if counts:
        st.subheader("Conteo por nivel IHRA")
        df_counts = pd.DataFrame.from_dict(counts, orient="index").reset_index()
        df_counts.columns = ["label", "count"]
        fig, ax = plt.subplots()
        ax.bar(df_counts["label"].astype(str), df_counts["count"])
        st.pyplot(fig)
    else:
        st.info("No hay datos aún.")
""", unsafe_allow_html=True)
