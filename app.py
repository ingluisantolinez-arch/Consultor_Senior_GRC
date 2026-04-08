import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import json
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

# Estilo Premium
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 5px; color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #1f6feb !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# Autenticación
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Error: Configure la 'GOOGLE_API_KEY' en los Secrets.")
    st.stop()

# --- 2. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Entorno de Consultoría")
    sector_cliente = st.selectbox("Sector del Cliente",
        ["Bancario", "Financiero", "Salud", "Energía", "Educativo", "Industrial", "Tecnología", "Gobierno"])
   
    tipo_verificacion = st.selectbox("Módulo de Verificación", [
        "Verificación de Estándares", "Verificación de Proveedores",
        "Verificación Cumplimiento Seguridad y Ciberseguridad",
        "Verificación de Seguridad", "Verificación de Ciberseguridad",
        "Verificación Cumplimiento Protección de Datos"
    ])
   
    st.markdown("---")
    archivo_principal = st.file_uploader("Cargar Archivo de Verificación", type=["xlsx", "csv"])

# --- 3. CUERPO PRINCIPAL ---
st.title(f"🛡️ Consola Senior GRC: Gestión Integral de Riesgos")

t1, t2, t3 = st.tabs(["📝 Verificación & Planes de Acción", "📊 Benchmarking", "🎲 Gestión de Riesgos Multimetodología"])

if archivo_principal:
    df = pd.read_excel(archivo_principal) if archivo_principal.name.endswith('xlsx') else pd.read_csv(archivo_principal)

    with t1:
        st.subheader("📋 Plan de Acción y Análisis de Brecha")
        c1, c2, c3 = st.columns(3)
        with c1: col_id_c = st.selectbox("ID Control", df.columns)
        with c2: col_hall = st.selectbox("Columna Hallazgo", df.columns)
        with c3: col_calif = st.selectbox("Columna Calificación", df.columns)

        if st.button("🚀 GENERAR PLANES DE ACCIÓN"):
            with st.spinner("🧠 Analizando brechas bajo estándares internacionales..."):
                for idx, row in df.head(5).iterrows():
                    prompt_audit = f"""
                    Actúa como Consultor Senior GRC. Sector: {sector_cliente}.
                    HALLAZGO: {row[col_hall]}
                   
                    TAREA:
                    1. CLÁUSULAS: Cita ISO 27002, NIST 800-53 y COBIT 2019.
                    2. ANÁLISIS DE BRECHA DOCUMENTAL: Basado en ISO 31000, identifica qué política o marco de gobierno falta.
                    3. RECOMENDACIÓN TÉCNICA: Pasos de remediación técnica precisos.
                    4. RECOMENDACIÓN DOCUMENTAL: Nombre del documento requerido para cerrar la brecha.
                    """
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(prompt_audit)
                    with st.expander(f"📍 {row[col_id_c]} - Análisis"):
                        st.markdown(res.text)

    # --- TAB 3: MATRIZ DE RIESGOS (DISEÑO MULTIMETODOLOGÍA INCLUYENDO 31000) ---
    with t3:
        st.subheader("🎲 Matriz de Riesgos Adaptativa")
       
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            metodologia = st.selectbox("Metodología de Riesgo", [
                "ISO 31000:2018 (Gestión de Riesgos Empresariales)",
                "ISO/IEC 27005:2022 (Riesgos TI/Seguridad)",
                "NIST SP 800-30 Rev 1",
                "MAGERIT v3"
            ])
        with c_m2:
            esc_max = st.number_input("Escala de Valoración (Ej: 5)", 3, 10, 5)

        with st.expander("⚙️ Parametrización del Mapa de Calor"):
            cp1, cp2 = st.columns(2)
            z_amarilla = cp1.slider("Zona de Riesgo Medio (Amarillo)", 1, esc_max**2, int((esc_max**2)*0.3))
            z_roja = cp2.slider("Zona de Riesgo Alto (Rojo)", 1, esc_max**2, int((esc_max**2)*0.6))

        if st.button("⚡ DEDUCIR RIESGOS BAJO " + metodologia):
            with st.spinner(f"🧠 Analizando escenarios bajo {metodologia}..."):
                lista_riesgos = []
                for idx, row in df.head(8).iterrows():
                    p_riesgo = f"""
                    Basado en el hallazgo: '{row[col_hall]}'.
                    Deduce el RIESGO materializable usando la metodología {metodologia}.
                   
                    RESPONDE ÚNICAMENTE EN JSON:
                    {{
                        "id_riesgo": "R-{idx+1:03}",
                        "riesgo_nombre": "Breve y técnico",
                        "probabilidad": 1 a {esc_max},
                        "impacto": 1 a {esc_max},
                        "sustento_metodologico": "Análisis según {metodologia}",
                        "brecha_documental": "Qué documento de gobierno falta",
                        "controles_iso27002": "Cláusulas de mitigación"
                    }}
                    """
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        resp = model.generate_content(p_riesgo)
                        clean_json = resp.text.replace('```json', '').replace('```', '').strip()
                        item = json.loads(clean_json)
                        item['inherente'] = item['probabilidad'] * item['impacto']
                        lista_riesgos.append(item)
                    except: pass

                if lista_riesgos:
                    df_r = pd.DataFrame(lista_riesgos)
                    st.table(df_r[['id_riesgo', 'riesgo_nombre', 'probabilidad', 'impacto', 'inherente', 'brecha_documental', 'controles_iso27002']])

                    # Mapa de Calor
                    grid = [[(i*j) for i in range(1, esc_max+1)] for j in range(1, esc_max+1)]
                    fig_h = go.Figure(data=go.Heatmap(
                        z=grid, x=list(range(1, esc_max+1)), y=list(range(1, esc_max+1)),
                        colorscale=[[0, 'green'], [z_amarilla/(esc_max**2), 'yellow'], [z_roja/(esc_max**2), 'red'], [1, 'darkred']],
                        showscale=False
                    ))
                    fig_h.add_trace(go.Scatter(x=df_r['probabilidad'], y=df_r['impacto'], mode='markers+text', text=df_r['id_riesgo'], marker=dict(size=14, color='white', symbol='diamond')))
                    st.plotly_chart(fig_h, use_container_width=True)
