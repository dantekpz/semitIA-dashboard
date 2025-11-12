# --- 1) Imports y configuración ---
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="SemitIA Dashboard", layout="wide")

# --- 2) Secrets (backend URL y token) ---
API_BASE = st.secrets.get("API_BASE", "http://localhost:8001")
API_TOKEN = st.secrets.get("API_TOKEN", None)

HEADERS = {"Content-Type": "application/json"}
if API_TOKEN:
    HEADERS["Authorization"] = f"Bearer {API_TOKEN}"

# --- 3) Sidebar (selector de modo) ---
st.sidebar.title("SemitIA")
mode = st.sidebar.radio("Modo", ["CSV", "Clasificación en vivo", "Estadísticas"], index=0)

# --- 4) Modo CSV: carga y visualización del dataset clasificado ---
if mode == "CSV":
    st.title("📊 SemitIA Dashboard – Análisis IHRA de Tuits")
    st.caption("Clasificación automática de antisemitismo (0–3) según IHRA")

    uploaded = st.file_uploader("📁 Subí tu CSV clasificado", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)

        # Validaciones suaves
        cols_requeridas = {"texto", "etiqueta_gpt", "subtipo_gpt", "confidence_gpt", "reason_gpt"}
        faltantes = cols_requeridas - set(df.columns)
        if faltantes:
            st.error(f"Faltan columnas en el CSV: {', '.join(sorted(faltantes))}")
        else:
            st.subheader("Datos generales")
            st.write(f"Tuits analizados: {len(df)}")

            # Distribución general (sin colores explícitos)
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
            st.write(f"Mostrando {len(filtrados)} tuits")
            st.dataframe(filtrados[["texto", "subtipo_gpt", "confidence_gpt", "reason_gpt"]])
    else:
        st.info("⬆️ Subí un CSV con tus clasificaciones (por ejemplo, `tuits_clasificados_final.csv`).")

# --- 5) Modo Clasificación en vivo: usa tu backend /api/classify ---
elif mode == "Clasificación en vivo":
    st.header("🔎 Clasificación IHRA en vivo")
    texto = st.text_area("Pegá un tuit o texto corto en español", height=140)

    col_a, col_b = st.columns([1, 3])
    with col_a:
        lanzar = st.button("Clasificar", type="primary")

    if lanzar:
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
                # Métricas
                col1, col2, col3 = st.columns(3)
                col1.metric("Nivel IHRA", data.get("label"))
                conf = data.get("confidence")
                col2.metric("Confianza", f"{conf*100:.1f}%" if isinstance(conf, (int, float)) else "—")
                col3.metric("Tiempo", f"{data.get('elapsed_ms', 0)} ms")

                # Detalle
                st.markdown(f"**Subtipo:** {data.get('subtype') or '—'}")
                st.markdown(f"**Reason:** {data.get('reason') or '—'}")
                st.caption(f"IHRA version: {data.get('ihra_version', '—')}")

# --- 6) Modo Estadísticas (placeholder a /api/stats) ---
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
                ax2 = df_series.set_index("date")[["0", "1", "2", "3"]].plot(figsize=(7, 4))
                ax2.set_ylabel("Cantidad")
                ax2.set_xlabel("Fecha")
                st.pyplot(plt.gcf())
        else:
            st.caption("Cuando el backend empiece a acumular datos, verás la serie temporal acá.")
