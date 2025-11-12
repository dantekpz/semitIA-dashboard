# --- 1) Imports y configuración ---
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="SemitIA – IHRA Dashboard",
    page_icon="🕊️",
    layout="centered"
)

# --- Fix visual: separa el contenido del header de Streamlit ---
st.markdown("""
    <style>
    /* Añade espacio arriba del body para que el header no tape el título */
    .block-container {
        padding-top: 6rem !important;
    }

    /* Header blanco y fijo */
    header[data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #0F172A !important;
        height: 3.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }

    /* Título con margen suave */
    h1 {
        margin-top: 0.5rem !important;
    }

    /* Corrige color de los íconos del header */
    [data-testid="stToolbar"] svg {
        fill: #0F172A !important;
        color: #0F172A !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2) Configuración API ---
API_BASE = st.secrets.get("API_BASE", "http://localhost:8001")
API_TOKEN = st.secrets.get("API_TOKEN", None)

HEADERS = {"Content-Type": "application/json"}
if API_TOKEN:
    HEADERS["Authorization"] = f"Bearer {API_TOKEN}"

# --- 3) Sidebar ---
st.sidebar.title("SemitIA")
mode = st.sidebar.radio(
    "Modo",
    ["CSV", "Clasificación en vivo", "Estadísticas"],
    index=0
)
st.sidebar.markdown("---")
st.sidebar.caption("Clasificación automática del discurso según IHRA (2016).")
st.sidebar.caption("© 2025 SemitIA – Demo educativa")

# --- 4) Modo CSV: carga y visualización ---
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

        if {"etiqueta_gpt"} <= set(df.columns):
            st.subheader("Distribución de clasificaciones (IHRA 0–3)")
            conteo = df["etiqueta_gpt"].value_counts().sort_index()
            fig, ax = plt.subplots()
            ax.bar(conteo.index.astype(str), conteo.values, color="#4F81BD")
            ax.set_xlabel("Categoría IHRA (0–3)")
            ax.set_ylabel("Cantidad de tuits")
            st.pyplot(fig)

            opcion = st.selectbox(
                "🔍 Filtrar por categoría (0–3):",
                sorted(df["etiqueta_gpt"].dropna().unique())
            )
            filtrados = df[df["etiqueta_gpt"] == opcion]
            st.write(f"Mostrando {len(filtrados)} tuits")
            st.dataframe(filtrados[["texto", "subtipo_gpt", "confidence_gpt", "reason_gpt"]])
        else:
            st.error("El CSV debe incluir una columna llamada 'etiqueta_gpt'.")

    else:
        st.info("⬆️ Subí un CSV con tus clasificaciones (por ejemplo, `tuits_clasificados_final.csv`).")

# --- 5) Modo Clasificación en vivo ---
elif mode == "Clasificación en vivo":
    st.header("🔎 Clasificación IHRA en vivo")
    texto = st.text_area("Pegá un tuit o texto corto en español", height=140)

    if st.button("Clasificar", type="primary"):
        if not texto.strip():
            st.warning("Pegá un texto primero.")
        else:
            with st.spinner("Clasificando..."):
                try:
                    r = requests.post(f"{API_BASE}/api/classify", headers=HEADERS, json={"text": texto}, timeout=30)
                except Exception as e:
                    st.error(f"No se pudo conectar al backend: {e}")
                    st.stop()

            if r.status_code != 200:
                st.error(f"Error {r.status_code}: {r.text}")
            else:
                data = r.json()
                col1, col2, col3 = st.columns(3)
                col1.metric("Nivel IHRA", data.get("label"))
                conf = data.get("confidence")
                col2.metric("Confianza", f"{conf*100:.1f}%" if isinstance(conf, (int, float)) else "—")
                col3.metric("Tiempo", f"{data.get('elapsed_ms', 0)} ms")

                st.markdown(f"**Subtipo:** {data.get('subtype') or '—'}")
                st.markdown(f"**Reason:** {data.get('reason') or '—'}")
                st.caption(f"IHRA version: {data.get('ihra_version', '—')}")

# --- 6) Modo Estadísticas ---
elif mode == "Estadísticas":
    st.header("📈 Estadísticas globales (v1)")
    rango = st.selectbox("Rango", ["7d", "30d", "90d"], index=1)

    try:
        resp = requests.get(f"{API_BASE}/api/stats", headers=HEADERS, params={"range": rango}, timeout=30)
    except Exception as e:
        st.error(f"No se pudo conectar al backend: {e}")
        st.stop()

    if resp.status_code != 200:
        st.error(f"No se pudo obtener stats: {resp.status_code} {resp.text}")
    else:
        stats = resp.json()
        counts = stats.get("counts", {})
        if counts:
            st.subheader("Conteo por nivel IHRA")
            df_counts = pd.DataFrame.from_dict(counts, orient="index").reset_index()
            df_counts.columns = ["label", "count"]
            df_counts = df_counts.sort_values("label")
            fig, ax = plt.subplots()
            ax.bar(df_counts["label"].astype(str), df_counts["count"], color="#4F81BD")
            ax.set_xlabel("Nivel IHRA")
            ax.set_ylabel("Cantidad")
            st.pyplot(fig)
        else:
            st.info("No hay datos de conteo aún.")
