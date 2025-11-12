# === SemitIA – IHRA Dashboard (Streamlit) ===
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ---------------------------
# 1) Config básica y estilos
# ---------------------------
st.set_page_config(page_title="SemitIA – IHRA Dashboard", page_icon="🕊️", layout="centered")

# Header blanco + margen superior para que no tape el título + íconos oscuros
st.markdown("""
    <style>
    .block-container { padding-top: 6rem !important; padding-left: 3rem !important; padding-right: 3rem !important; }
    header[data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #0F172A !important;
        height: 3.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    [data-testid="stToolbar"] svg {
        fill: #0F172A !important;
        color: #0F172A !important;
    }
    h1, h2, h3, h4 { font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# 2) Config API (secrets)
# ---------------------------
API_BASE = st.secrets.get("API_BASE")          # ej: https://tu-backend.app (sin barra final)
API_ENDPOINT = st.secrets.get("API_ENDPOINT")  # ej: https://tu-backend.app/api/classify (completo)
API_TOKEN = st.secrets.get("API_TOKEN")        # SOLO el token (sin 'Bearer ')

def get_headers():
    h = {"Content-Type": "application/json"}
    if API_TOKEN:
        h["Authorization"] = API_TOKEN if API_TOKEN.lower().startswith("bearer ") else f"Bearer {API_TOKEN}"
    return h

# ---------------------------
# 3) Helpers de URL + fallback
# ---------------------------
def _normalize_base(u: str | None) -> str | None:
    if not u:
        return u
    return u[:-1] if u.endswith("/") else u

def get_classify_candidates():
    """ Devuelve rutas candidatas para POST /classify, probando ambas variantes comunes. """
    cands = []
    if API_ENDPOINT:  # si definiste el endpoint completo, probalo tal cual
        cands.append(API_ENDPOINT)

    if API_BASE:
        b = _normalize_base(API_BASE)
        cands.append(f"{b}/api/classify")
        cands.append(f"{b}/classify")

    # deduplicar preservando orden
    out, seen = [], set()
    for c in cands:
        if c and c not in seen:
            out.append(c); seen.add(c)
    return out

def post_classify_with_fallback(payload: dict, headers: dict, timeout: int = 20):
    """
    Intenta POST contra las rutas candidatas hasta obtener 200.
    Si 404, prueba la siguiente. Si 401/403, muestra error de auth.
    Devuelve (data_json, url_usada, elapsed_ms) o levanta RuntimeError.
    """
    last_err = None
    for url in get_classify_candidates():
        t0 = time.time()
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            elapsed = int((time.time() - t0) * 1000)
        except Exception as e:
            last_err = e
            continue

        if r.status_code == 200:
            return r.json(), url, elapsed
        elif r.status_code in (401, 403):
            st.error(f"Auth error {r.status_code} en {url}. Revisá API_TOKEN/Authorization.")
            return None, url, elapsed
        elif r.status_code == 404:
            last_err = f"404 en {url}"
            continue
        else:
            last_err = f"{r.status_code}: {r.text[:300]} en {url}"
            continue

    raise RuntimeError(f"No se pudo clasificar. Último error: {last_err}")

# ---------------------------
# 4) Sidebar
# ---------------------------
st.sidebar.title("SemitIA")
mode = st.sidebar.radio("Modo", ["CSV", "Clasificación en vivo", "Estadísticas"], index=0)
st.sidebar.markdown("---")
st.sidebar.caption("Clasificación automática del discurso según IHRA (2016).")
st.sidebar.caption("© 2025 SemitIA – Demo educativa")

# ---------------------------
# 5) CSV – carga y análisis
# ---------------------------
if mode == "CSV":
    st.markdown("""
    <div style="text-align:center; margin-bottom: 1.5rem;">
        <h1 style="font-size: 2.2rem; margin-bottom: 0.3rem; color:#0F172A;">
            🕊️ SemitIA
        </h1>
        <h4 style="font-weight:400; color:#475569; margin-top:0;">
            Dashboard de análisis IHRA de antisemitismo (0–3)
        </h4>
    </div>
    """, unsafe_allow_html=True)

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
            ax.bar(conteo.index.astype(str), conteo.values)
            ax.set_xlabel("Categoría IHRA (0–3)")
            ax.set_ylabel("Cantidad de tuits")
            st.pyplot(fig)

            opcion = st.selectbox(
                "🔍 Filtrar por categoría (0–3):",
                sorted(df["etiqueta_gpt"].dropna().unique())
            )
            filtrados = df[df["etiqueta_gpt"] == opcion]
            st.write(f"Mostrando {len(filtrados)} tuits")
            st.dataframe(filtrados[["texto", "subtipo_gpt", "confidence_gpt", "reason_gpt"]], use_container_width=True)
        else:
            st.error("El CSV debe incluir una columna llamada 'etiqueta_gpt'.")
    else:
        st.info("⬆️ Subí un CSV con tus clasificaciones (por ejemplo, `tuits_clasificados_final.csv`).")

# ---------------------------
# 6) Clasificación en vivo
# ---------------------------
elif mode == "Clasificación en vivo":
    st.markdown("""
    <div style="text-align:center; margin-bottom: 1.5rem;">
        <h1 style="font-size: 2.2rem; margin-bottom: 0.3rem; color:#0F172A;">
            🕊️ SemitIA
        </h1>
        <h4 style="font-weight:400; color:#475569; margin-top:0;">
            Clasificación IHRA en tiempo real
        </h4>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔎 Diagnóstico de rutas"):
        st.write("API_ENDPOINT:", API_ENDPOINT or "—")
        st.write("API_BASE:", API_BASE or "—")
        st.write("Candidatos:", get_classify_candidates())

    texto = st.text_area("Pegá un tuit o texto corto en español", height=140)
    timeout_s = st.slider("⏱️ Timeout (segundos)", 5, 60, 20, help="Tiempo máximo de espera del backend")

    if st.button("Clasificar", type="primary"):
        if not texto.strip():
            st.warning("Pegá un texto primero.")
            st.stop()

        try:
            with st.spinner("Clasificando..."):
                data, url_usada, elapsed = post_classify_with_fallback(
                    payload={"text": texto},
                    headers=get_headers(),
                    timeout=timeout_s
                )
        except Exception as e:
            st.error(f"No se pudo clasificar: {e}")
            st.stop()

        if data is None:
            st.stop()

        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Nivel IHRA", data.get("label"))
        conf = data.get("confidence")
        col2.metric("Confianza", f"{conf*100:.1f}%" if isinstance(conf, (int, float)) else "—")
        col3.metric("Tiempo", f"{data.get('elapsed_ms', elapsed)} ms")

        # Detalle
        st.markdown(f"**Subtipo:** {data.get('subtype') or '—'}")
        st.markdown(f"**Reason:** {data.get('reason') or '—'}")
        st.caption(f"Endpoint usado: {url_usada}")

# ---------------------------
# 7) Estadísticas (v1)
# ---------------------------
elif mode == "Estadísticas":
    st.markdown("""
    <div style="text-align:center; margin-bottom: 1.5rem;">
        <h1 style="font-size: 2.2rem; margin-bottom: 0.3rem; color:#0F172A;">
            🕊️ SemitIA
        </h1>
        <h4 style="font-weight:400; color:#475569; margin-top:0;">
            Estadísticas globales de antisemitismo (v1)
        </h4>
    </div>
    """, unsafe_allow_html=True)

    rango = st.selectbox("Rango", ["7d", "30d", "90d"], index=1)
    if not API_BASE:
        st.info("Configura API_BASE en Secrets para habilitar /api/stats.")
        st.stop()

    try:
        resp = requests.get(f"{_normalize_base(API_BASE)}/api/stats", headers=get_headers(), params={"range": rango}, timeout=30)
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
