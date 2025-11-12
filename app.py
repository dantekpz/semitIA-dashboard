# ============================================
# SemitIA – IHRA Dashboard (Streamlit frontend)
# ============================================

# --- Imports & Config ---
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="SemitIA – IHRA Dashboard", page_icon="🕊️", layout="centered")

# --- CSS base (header + centro blancos unificados) ---
st.markdown("""
<style>
/* === Estilo limpio y claro === */

/* Fondo principal */
html, body, [data-testid="stAppViewContainer"] {
  background-color: #FFFFFF !important;
  color: #0F172A !important;
}

/* Header blanco con línea sutil */
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

/* Sidebar claro */
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

/* Tarjetas y detalles */
.badge {display:inline-block;padding:4px 10px;border-radius:999px;font-size:12px;border:1px solid #e5e7eb;background:#f8fafc}
.badge-0 {background:#e6f7ff;border-color:#b3e5fc}
.badge-1 {background:#fffbe6;border-color:#ffec99}
.badge-2 {background:#fff1f0;border-color:#ffc9c9}
.badge-3 {background:#ffe7ba;border-color:#ffd8a8}
.card {border:1px solid #eaecef;border-radius:16px;padding:14px;background:#ffffff}
.caption {color:#64748b;font-size:12px}
.footer {margin-top:30px;color:#94a3b8;font-size:12px;text-align:center}
.hero {padding:18px 20px;border-radius:18px;background:#F7F9FC;border:1px solid #eaecef}
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

# --- Sidebar: brand + night mode + info + selector ---
st.sidebar.title("SemitIA")
dark = st.sidebar.toggle("🌙 Modo noche", value=False)

# Modo noche (incluye header y centro oscuros)
if dark:
    st.markdown("""
    <style>
    /* Centro y texto */
    [data-testid="stAppViewContainer"] { background:#0B1220 !important; color:#E5E7EB !important; }
    /* Sidebar */
    [data-testid="stSidebar"] { background:#0F172A !important; color:#E5E7EB !important; }
    /* Header (toolbar) */
    header[data-testid="stHeader"], .stApp header {
      background:#0B1220 !important;
      color:#E5E7EB !important;
      border-bottom: 1px solid #1F2937 !important;
    }
    .card { background:#0F172A !important; border-color:#1F2937 !important; }
    .badge { background:#111827 !important; border-color:#374151 !important; color:#E5E7EB !important; }
    .caption, .footer { color:#9CA3AF !important; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar.expander("Acerca de SemitIA"):
    st.markdown("Clasificación automática del discurso sobre judíos/Israel según la definición IHRA (2016).")
    st.markdown('<span class="caption">Demo para evaluación y fines educativos. No reemplaza moderación humana.</span>', unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2025 SemitIA · IHRA-based classification · Demo</div>', unsafe_allow_html=True)

# --- Hero (portada) ---
with st.container():
    col1, col2 = st.columns([3, 1], vertical_alignment="center")
    with col1:
        st.markdown("""
        # 🕊️ SemitIA
        **IA para entender y prevenir el antisemitismo online**  
        Clasificación automática según criterios **IHRA (0–3)**, con explicación y confianza.
        """)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️ Probar demo en vivo", type="primary"):
                st.session_state["_mode"] = "Clasificación en vivo"
        with c2:
            if st.button("📂 Subir CSV"):
                st.session_state["_mode"] = "CSV"
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:10px;border-radius:16px;background:#F7F9FC;border:1px solid #eaecef">
            <div style="font-size:40px">📊</div>
            <div style="margin-top:6px">IHRA 0–3</div>
        </div>
        """, unsafe_allow_html=True)

default_mode = st.session_state.get("_mode", "CSV")

mode = st.sidebar.radio(
    "Modo", ["CSV", "Clasificación en vivo", "Estadísticas"],
    index=["CSV","Clasificación en vivo","Estadísticas"].index(default_mode)
)

# =========================
#        MODO CSV
# =========================
if mode == "CSV":
    st.title("📊 SemitIA Dashboard – Análisis IHRA de Tuits")
    st.caption("Clasificación automática de antisemitismo (0–3) según IHRA")

    uploaded = st.file_uploader("📁 Subí tu CSV clasificado", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)

        st.download_button(
            "💾 Descargar CSV enriquecido",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="semitia_clasificado.csv",
            mime="text/csv"
        )

        cols_requeridas = {"texto", "etiqueta_gpt", "subtipo_gpt", "confidence_gpt", "reason_gpt"}
        faltantes = cols_requeridas - set(df.columns)
        if faltantes:
            st.error(f"Faltan columnas en el CSV: {', '.join(sorted(faltantes))}")
            st.stop()

        st.subheader("Datos generales")
        st.write(f"Tuits analizados: {len(df)}")

        st.subheader("Distribución de clasificaciones (IHRA 0–3)")
        conteo = df["etiqueta_gpt"].value_counts().sort_index()
        fig, ax = plt.subplots()
        ax.bar(conteo.index.astype(str), conteo.values)
        ax.set_xlabel("Categoría IHRA (0–3)")
        ax.set_ylabel("Cantidad de tuits")
        st.pyplot(fig)

        opciones = sorted(df["etiqueta_gpt"].dropna().unique())
        opcion = st.selectbox("🔍 Filtrar por categoría (0–3):", opciones)
        filtrados = df[df["etiqueta_gpt"] == opcion]
        st.write(f"Mostrando {len(filtrados)} tuits")
        st.dataframe(filtrados[["texto", "subtipo_gpt", "confidence_gpt", "reason_gpt"]])
    else:
        st.info("⬆️ Subí un CSV con tus clasificaciones (por ejemplo, `tuits_clasificados_final.csv`).")

# ===============================
#   MODO CLASIFICACIÓN EN VIVO
# ===============================
elif mode == "Clasificación en vivo":
    st.header("🔎 Clasificación IHRA en vivo")

    with st.expander("⚙️ Diagnóstico de conexión"):
        st.write("API_ENDPOINT:", API_ENDPOINT or "—")
        st.write("API_BASE:", API_BASE or "—")
        st.write("URL destino:", get_classify_url() or "❌ no configurada")

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
    timeout_s = st.slider("⏱️ Timeout de la solicitud (segundos)", 5, 60, 20)

    col_a, col_b = st.columns([1, 3])
    with col_a:
        lanzar = st.button("Clasificar", type="primary")

    if lanzar:
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

            col1, col2, col3 = st.columns(3)
            col1.metric("Nivel IHRA", nivel if nivel is not None else "—")
            col2.metric("Confianza", f"{conf*100:.1f}%" if isinstance(conf,(int,float)) else "—")
            col3.metric("Tiempo", f"{data.get('elapsed_ms', elapsed)} ms")
            st.caption(f"IHRA version: {data.get('ihra_version','—')}")

# =========================
#         ESTADÍSTICAS
# =========================
elif mode == "Estadísticas":
    st.header("📈 Estadísticas globales (v1)")
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
