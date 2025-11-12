import streamlit as st
import streamlit as st, requests, pandas as pd, matplotlib.pyplot as plt

# 🔒 Leemos las variables seguras desde Streamlit Secrets
API_BASE = st.secrets.get("API_BASE", "http://localhost:8001")
API_TOKEN = st.secrets.get("API_TOKEN", None)

# Encabezados HTTP para la API
HEADERS = {"Content-Type": "application/json"}
if API_TOKEN:
    HEADERS["Authorization"] = f"Bearer {API_TOKEN}"
import pandas as pd
import matplotlib.pyplot as plt

# --- Cargar dataset ---
st.title("📊 SemitIA Dashboard – Análisis IHRA de Tuits")
st.caption("Clasificación automática de antisemitismo (0–3) según IHRA")

uploaded = st.file_uploader("📁 Subí tu CSV clasificado", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)

    # --- Mostrar datos ---
    st.subheader("Datos generales")
    st.write(f"Tuits analizados: {len(df)}")

    # --- Distribución general ---
    conteo = df["etiqueta_gpt"].value_counts().sort_index()
    fig, ax = plt.subplots()
    ax.bar(conteo.index, conteo.values, color="skyblue")
    ax.set_xlabel("Categoría IHRA (0–3)")
    ax.set_ylabel("Cantidad de tuits")
    ax.set_title("Distribución general de clasificaciones")
    st.pyplot(fig)

    # --- Filtro ---
    opcion = st.selectbox("🔍 Filtrar por categoría (0–3):", sorted(df["etiqueta_gpt"].dropna().unique()))
    filtrados = df[df["etiqueta_gpt"] == opcion]
    st.write(f"Mostrando {len(filtrados)} tuits")

    st.dataframe(filtrados[["texto", "subtipo_gpt", "confidence_gpt", "reason_gpt"]])

else:
    st.info("⬆️ Subí un CSV con tus clasificaciones (por ejemplo, `tuits_clasificados_final.csv`).")
