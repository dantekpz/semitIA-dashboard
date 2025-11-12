import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="SemitIA – IHRA Dashboard", page_icon="🕊️", layout="centered")

# === Cargar CSS externo (evita errores de triple quotes) ===
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
 # --- Fix: margen superior para evitar que el header blanco tape el título ---
# --- Fix visual: separa el contenido del header de Streamlit ---
if True:  # evita errores de indentación accidental
    st.markdown("""
        <style>
        /* Añade espacio arriba del body para que el header no tape el título */
        .block-container {
            padding-top: 6rem !important;  /* subí este valor si sigue muy arriba */
        }

        /* Mantén el header fijo y blanco */
        header[data-testid="stHeader"] {
            background-color: #ffffff !important;
            color: #0F172A !important;
            height: 3.5rem;  /* asegura tamaño estable */
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        }

        /* Corrige también el espaciado del título principal */
        h1 {
            margin-top: 0.5rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
else:
    st.warning("No se encontró styles.css (se verá el estilo por defecto).")

# === Secrets / Endpoints ===
API_BASE = st.secrets.get("API_BASE")          # ej: https://tu-backend.app
API_ENDPOINT = st.secrets.get("API_ENDPOINT")  # opcional: https://tu-backend.app/classify
API_TOKEN = st.secrets.get("API_TOKEN")        # SOLO el token (sin 'Bearer ')

def get_headers():
    h = {"Content-Type": "application/json"}
    if API_TOKEN:
        h["Authorization"] = API_TOKEN if API_TOKEN.lower().startswith("bearer ") else f"Bearer {API_TOKEN}"
    return h

def get_classify_url():
    if API_ENDPOINT: return API_ENDPOINT
    if API_BASE:     return f"{API_BASE}/api/classify"
    return None

def get_stats_url():
    return f"{API_BASE}/api/stats" if API_BASE else None

# === Hero (minimal) ===
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

# === Sidebar ===
st.sidebar.title("SemitIA")
mode = st.sidebar.radio("Modo", ["CSV", "Clasificación en vivo", "Estadísticas"],
                        index=["CSV","Clasificación en vivo","Estadísticas"].index(default_mode))
with st.sidebar.expander("Acerca de"):
    st.markdown("Clasificación automática del discurso sobre judíos/Israel según la definición IHRA (2016).")
    st.markdown('<span class="caption">Demo educativa. No reemplaza moderación humana.</span>', unsafe_allow_html=True)

# =========================
#        MODO CSV
# =========================
if mode == "CSV":
    st.markdown("### 📊 Análisis IHRA de Tuits (CSV)")
    uploaded = st.file_uploader("Arrastrá o elegí un archivo CSV", type=["csv"])

    if uploaded:
        df = pd.read_csv(uploaded)

        # Validación de columnas esperadas
        required = {"texto", "etiqueta_gpt", "subtipo_gpt", "confidence_gpt", "reason_gpt"}
        missing = required - set(df.columns)
        if missing:
            st.error(f"Faltan columnas: {', '.join(sorted(missing))}")
            st.stop()

        # Descarga
        st.download_button(
            "💾 Descargar CSV enriquecido",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="semitia_clasificado.csv",
            mime="text/csv",
        )

        # Datos generales
        st.subheader("Datos generales")
        st.write(f"Tuits analizados: **{len(df)}**")

        # Distribución
        st.subheader("Distribución de clasificaciones (IHRA 0–3)")
        conteo = df["etiqueta_gpt"].value_counts().sort_index()
        fig, ax = plt.subplots()
        ax.bar(conteo.index.astype(str), conteo.values)
        ax.set_xlabel("Categoría IHRA (0–3)")
        ax.set_ylabel("Cantidad de tuits")
        st.pyplot(fig)

        # Filtro simple
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
    st.markdown("### 🔎 Clasificación IHRA en vivo")

    with st.expander("⚙️ Diagnóstico"):
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
    timeout_s = st.slider("⏱️ Timeout (segundos)", 5, 60, 20)

    if st.button("Clasificar"):
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
            st.error(f"Timeout: el backend tardó más de {timeout_s}s.")
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

            st.markdown(
                f"""
                <div class="card">
                  <div class="badge badge-{nivel}">Nivel IHRA: {nivel}</div>
                  <div style="margin-top:8px"><b>Subtipo:</b> {sub}</div>
                  <div><b>Confianza:</b> {f"{conf*100:.1f}%" if isinstance(conf,(int,float)) else "—"}</div>
                  <div><b>Reason:</b> {rsn}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Nivel IHRA", nivel if nivel is not None else "—")
            c2.metric("Confianza", f"{conf*100:.1f}%" if isinstance(conf,(int,float)) else "—")
            c3.metric("Tiempo", f"{data.get('elapsed_ms', elapsed)} ms")

# =========================
#         ESTADÍSTICAS
# =========================
elif mode == "Estadísticas":
    st.markdown("### 📈 Estadísticas globales (v1)")
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
