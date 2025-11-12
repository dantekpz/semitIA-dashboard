# ============================================
# SemitIA – IHRA Dashboard (Streamlit frontend)
# Limpio, sin modo noche y con estilos seguros
# ============================================

# --- Imports & Config ---
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="SemitIA – IHRA Dashboard", page_icon="🕊️", layout="centered")

# --- CSS claro, seguro y minimalista (no rompe iconos/menus) ---
st.markdown("""
<style>
/* Fondo principal y contenedor */
html, body, [data-testid="stAppViewContainer"] {
  background-color: #FFFFFF !important;
  color: #0F172A !important;
}

/* Header (toolbar) claro con iconos visibles */
header[data-testid="stHeader"], .stApp header {
  background-color: #FFFFFF !important;
  color: #0F172A !important;
  border-bottom: 1px solid #E5E7EB !important;
}
header[data-testid="stHeader"] *, .stApp header * {
  color: #0F172A !important;
}
header[data-testid="stHeader"] svg, .stApp header svg {
  fill: #0F172A !important;
  stroke: #0F172A !important;
}

/* Sidebar claro + texto/iconos visibles */
[data-testid="stSidebar"] {
  background-color: #F7F9FC !important;
  color: #0F172A !important;
}
[data-testid="stSidebar"] * {
  color: #0F172A !important;
}
[data-testid="stSidebar"] svg {
  fill: #0F172A !important;
  stroke: #0F172A !important;
}

/* Helpers visuales (no tocan layout base) */
.badge {display:inline-block;padding:4px 10px;border-radius:999px;font-size:12px;border:1px solid #e5e7eb;background:#f8fafc}
.badge-0 {background:#e6f7ff;border-color:#b3e5fc}
.badge-1 {background:#fffbe6;border-color:#ffec99}
.badge-2 {background:#fff1f0;border-color:#ffc9c9}
.badge-3 {background:#ffe7ba;border-color:#ffd8a8}
.card {border:1px solid #eaecef;border-radius:16px;padding:14px;background:#ffffff}
.caption {color:#64748b;font-size:12px}
.footer {margin-top:30px;color:#94a3b8;font-size:12px;text-align:center}

/* Botones tipo CTA (HTML) */
.cta-btn {
  display:inline-block; padding:10px 14px; border-radius:10px;
  border:1px solid #2F6FED; background:#2F6FED; color:#fff; text-decoration:none;
  font-weight:600;
}
.cta-btn.secondary {
  background:#fff; color:#2F6FED; border:1px solid #2F6FED;
}
</style>
""", unsafe_allow_html=True)

# --- Secrets (backend URL / token) ---
API_BASE = st.secrets.get("API_BASE")          # ej: https://tu-backend.app
API_ENDPOINT = st.secrets.get("API_ENDPOINT")  # opcional: https://tu-backend.app/classify
API_TOKEN = st.secrets.get("API_TOKEN")        # SOLO el token (sin "Bearer ")

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

# --- Hero (portada simple y prolija) ---
with st.container():
    st.markdown("### 🕊️ SemitIA")
    st.markdown("**IA para entender y prevenir el antisemitismo online** · Clasificación IHRA (0–3) con explicación y confianza.")
    c1, c2, c3 = st.columns([1,1,6])
    with c1:
        if st.button("▶️ Demo en vivo", type="primary"):
            st.session_state["_mode"] = "Clasificación en vivo"
    with c2:
        if st.button("📂 Subir CSV"):
            st.session_state["_mode"] = "CSV"

default_mode = st.session_state.get("_mode", "CSV")

# --- Sidebar (selector de modo + about) ---
st.sidebar.title("SemitIA")
mode = st.sidebar.radio(
    "Modo", ["CSV", "Clasificación en vivo", "Estadísticas"],
    index=["CSV","Clasificación en vivo","Estadísticas"].index(default_mode)
)
with st.sidebar.expander("Acerca de"):
    st.markdown("Clasificación automática del discurso sobre judíos/Israel según definición IHRA (2016).")
    st.markdown('<span class="caption">Demo educativa. No reemplaza moderación humana.</span>', unsafe_allow_html=True)

# =========================
#        MODO CSV
# =========================
if mode == "CSV":
    st.markdown("## 📊 Análisis IHRA de Tuits (CSV)")
    st.caption("Subí un CSV con columnas: `texto, etiqueta_gpt, subtipo_gpt, confidence_gpt, reason_gpt`.")

    uploaded = st.file_uploader("📁 Subí tu CSV clasificado", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)

        # Validación de columnas
        cols_requeridas = {"texto", "etiqueta_gpt", "subtipo_gpt", "confidence_gpt", "reason_gpt"}
        faltantes = cols_requeridas - set(df.columns)
        if faltantes:
            st.error(f"Faltan columnas en el CSV: {', '.join(sorted(faltantes))}")
            st.stop()

        # Botón de descarga
        st.download_button(
            "💾 Descargar CSV enriquecido",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="semitia_clasificado.csv",
            mime="text/csv"
        )

        # Datos generales
        st.subheader("Datos generales")
        st.write(f"Tuits analizados: **{len(df)}**")

        # Distribución general
        st.subheader("Distribución de clasificaciones (IHRA 0–3)")
        conteo = df["etiqueta_gpt"].value_counts().sort_index()
        fig, ax = plt.subplots()
        ax.bar(conteo.index.astype(str), conteo.values)
        ax.set_xlabel("Categoría IHRA (0–3)")
        ax.set_ylabel("Cantidad de tuits")
        st.pyplot(fig)

        # Filtro por categoría
        opciones = sorted(df["etiqueta_gpt"].dropna().unique())
        opcion = st.selectbox("🔍 Filtrar por categoría (0–3):", opciones)
        filtrados = df[df["etiqueta_gpt"] == opcion]
        st.write(f"Mostrando **{len(filtrados)}** tuits")
        st.dataframe(filtrados[["texto", "subtipo_gpt", "confidence_gpt", "reason_gpt"]], use_container_width=True)
    else:
        st.info("⬆️ Subí un CSV con tus clasificaciones.")

# ===============================
#   MODO CLASIFICACIÓN EN VIVO
# ===============================
elif mode == "Clasificación en vivo":
    st.markdown("## 🔎 Clasificación IHRA en vivo")

    # Diagnóstico de conexión
    with st.expander("⚙️ Diagnóstico"):
        st.write("API_ENDPOINT:", API_ENDPOINT or "—")
        st.write("API_BASE:", API_BASE or "—")
        st.write("URL destino:", get_classify_url() or "❌ no configurada")

    # Ejemplos
    ejemplos = {
        "0 · Neutro": "Hoy se recuerda el Holocausto.",
        "1 · Crítica política": "El gobierno de Israel actúa de forma desproporcionada.",
        "2 · Implícito": "Israel controla los medios y nadie lo dice.",
        "3 · Explícito": "El Holocausto nunca existió."
    }
    ej = st.selectbox("Elegí un ejemplo (opcional)", list(ejemplos.keys()), index=None, placeholder="Elegí un ejemplo…")
    if ej:
        st.session_state["_texto_demo"] = ejemplos[ej]

    texto = st.text_area("Pegá un tuit o texto corto en español", height=140, value=st.session_state.get("_texto_demo",""))
    timeout_s = st.slider("⏱️ Timeout (segundos)", 5, 60, 20)

    if st.button("Clasificar", type="primary"):
        url = get_classify_url()
        if not url:
            st.error("No hay URL configurada. Definí `API_ENDPOINT` o `API_BASE` en Secrets.")
            st.stop()
        if not texto.strip():
            st.warning("Pegá un texto primero.")
            st.stop()

        try:
            t0 = time.time()
            with st.spinner("Clasificando..."):
                r = requests.post(url, headers=get_headers(), json={"text": texto}, timeout=timeout_s)
        except requests.exceptions.ReadTimeout:
            st.error(f"Timeout: el backend tardó más de {timeout_s}s en responder.")
            st.stop()
        except Exception as e:
            st.error(f"No se pudo conectar al backend: {e}")
            st.stop()

        elapsed = int((time.time() - t0) * 1000)
        if r.status_code != 200:
            st.error(f"Error {r.status_code}: {r.text[:500]}")
        else:
            data = r.json()
            nivel = data.get("label")
            sub = data.get("subtype") or "—"
            rsn = data.get("reason") or "—"
            conf = data.get("confidence")

            st.markdown(f"""
            <div class="card">
              <div class="badge badge-{nivel}">Nivel IHRA: {nivel}</div>
              <div style="margin-top:8px"><b>Subtipo:</b> {sub}</div>
              <div><b>Confianza:</b> {f"{conf*100:.1f}%" if isinstance(conf,(int,float)) else "—"}</div>
              <div><b>Reason:</b> {rsn}</div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Nivel IHRA", nivel if nivel is not None else "—")
            c2.metric("Confianza", f"{conf*100:.1f}%" if isinstance(conf,(int,float)) else "—")
            c3.metric("Tiempo", f"{data.get('elapsed_ms', elapsed)} ms")
            st.caption(f"IHRA version: {data.get('ihra_version','—')}")

# =========================
#         ESTADÍSTICAS
# =========================
elif mode == "Estadísticas":
    st.markdown("## 📈 Estadísticas globales (v1)")
    url_stats = get_stats_url()
    if not url_stats:
        st.info("Configura API_BASE en Secrets para habilitar /api/stats.")
        st.stop()

    rango = st.selectbox("Rango", ["7d", "30d", "90d"], index=1)
    try:
        resp = requests.get(url_stats, headers=get_headers(), params={"range": rango}, timeout=30)
    except Exception as e:
        st.error(f"No se pudo conectar al backend: {e}")
        st.stop()

    if resp.status_code != 200:
        st.error(f"No se pudo obtener stats: {resp.status_code} {resp.text}")
        st.stop()

    stats = resp.json()
    counts = stats.get("counts", {})
    if counts:
        st.subheader("Conteo por nivel IHRA")
        df_counts = pd.DataFrame.from_dict(counts, orient="index").reset_index()
        df_counts.columns = ["label", "count"]
        df_counts = df_counts.sort_values("label")
        fig, ax = plt.subplots()
        ax.bar(df_counts["label"].astype(str), df_counts["count"])
        ax.set_xlabel("Nivel IHRA")
        ax.set_ylabel("Cantidad")
        st.pyplot(fig)
    else:
        st.info("No hay datos de conteo aún.")

    series = stats.get("series", [])
    if series:
        st.subheader("Evolución temporal")
        df_series = pd.DataFrame(series)
        if "date" in df_series.columns:
            df_series = df_series.sort_values("date")
            ax2 = df_series.set_index("date")[["0","1","2","3"]].plot(figsize=(7,4))
            ax2.set_ylabel("Cantidad")
            ax2.set_xlabel("Fecha")
            st.pyplot(plt.gcf())
    else:
        st.caption("Cuando el backend empiece a acumular datos, verás la serie temporal acá.")
