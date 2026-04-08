import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import time
import io

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GRC Senior Intelligence Console", layout="wide", page_icon="🛡️")

# Estilo Premium Dark
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] { background-color: #1f6feb ! suppressed; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTENTICACIÓN ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Configura la 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 3. INTERFAZ PRINCIPAL ---
st.title("🛡️ Consola de Consultoría GRC Nivel 3")
st.caption("Frameworks: ISO 27001/2/5 | NIST SP 800-53 | COBIT 2019 | Ley 1581")

tab1, tab2, tab3 = st.tabs([
    "🔍 Auditoría & Consultoría IA",
    "📊 Benchmarking Comparativo",
    "🎲 Matriz de Riesgos ISO 27005"
])

# --- MÓDULO 1: AUDITORÍA & CONSULTORÍA ---
with tab1:
    with st.sidebar:
        st.header("🏢 Configuración")
        sector = st.selectbox("Sector del Cliente", ["Bancario", "Salud", "Educación", "Energía", "Industrial", "Tecnología", "Gobierno"])
        archivo_audit = st.file_uploader("Cargar Matriz de Auditoría", type=["xlsx", "csv"], key="audit_up")

    if archivo_audit:
        df_a = pd.read_excel(archivo_audit) if archivo_audit.name.endswith('xlsx') else pd.read_csv(archivo_audit)
        st.subheader("📊 Dashboard de Cumplimiento Actual")
       
        c1, c2 = st.columns(2)
        with c1: col_h = st.selectbox("Columna: Hallazgo", df_a.columns)
        with c2: col_c = st.selectbox("Columna: Calificación", df_a.columns)
       
        fig_pie = px.pie(df_a, names=col_c, hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_pie, use_container_width=True)

        if st.button("🚀 EJECUTAR CONSULTORÍA SENIOR"):
            with st.spinner("🧠 Mapeando contra ISO, NIST y COBIT..."):
                for idx, row in df_a.head(10).iterrows():
                    prompt = f"""Actúa como Consultor GRC L3. Sector: {sector}.
                    Hallazgo: {row[col_h]} | Calificación: {row[col_c]}.
                    Mapea contra ISO 27001, NIST 800-53 y COBIT 2019. Da recomendaciones técnicas y documentales."""
                   
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt)
                    with st.expander(f"📌 Análisis Fila {idx+1}"):
                        st.markdown(response.text)
                    time.sleep(1)
    else:
        st.info("Sube un archivo para iniciar el análisis de auditoría.")

# --- MÓDULO 2: BENCHMARKING ---
with tab2:
    st.subheader("📊 Comparativa Interanual (Benchmarking)")
    col_a, col_b = st.columns(2)
    arch_v = col_a.file_uploader("Matriz Año Anterior", type=["xlsx", "csv"])
    arch_n = col_b.file_uploader("Matriz Año Actual", type=["xlsx", "csv"])

    if arch_v and arch_n:
        df_v = pd.read_excel(arch_v) if arch_v.name.endswith('xlsx') else pd.read_csv(arch_v)
        df_n = pd.read_excel(arch_n) if arch_n.name.endswith('xlsx') else pd.read_csv(arch_n)
       
        col_comp = st.selectbox("Columna de Calificación a comparar", df_v.columns, key="comp_col")
       
        v1 = df_v[col_comp].value_counts()
        v2 = df_n[col_comp].value_counts()
       
        fig_bench = go.Figure(data=[
            go.Bar(name='Anterior', x=v1.index, y=v1.values, marker_color='#30363d'),
            go.Bar(name='Actual', x=v2.index, y=v2.values, marker_color='#1f6feb')
        ])
        st.plotly_chart(fig_bench, use_container_width=True)

# --- MÓDULO 3: MATRIZ DE RIESGOS ISO 27005 ---
with tab3:
    st.subheader("🎲 Gestión de Riesgos Personalizada (ISO 27005 & 27002)")
   
    with st.expander("⚙️ Parametrización de Escalas"):
        c_p1, c_p2 = st.columns(2)
        escala_max = c_p1.number_input("Escala Máxima (3, 5 o 10)", 3, 10, 5)
        umbral = c_p2.slider("Umbral de Riesgo No Aceptable", 1, escala_max**2, int((escala_max**2)*0.6))

    archivo_r = st.file_uploader("Cargar Inventario de Riesgos", type=["xlsx", "csv"], key="risk_up")

    if archivo_r:
        df_r = pd.read_excel(archivo_r) if archivo_r.name.endswith('xlsx') else pd.read_csv(archivo_r)
       
        cols_r = st.columns(3)
        col_rd = cols_r[0].selectbox("Columna: Descripción", df_r.columns)
        col_rp = cols_r[1].selectbox("Columna: Probabilidad", df_r.columns)
        col_ri = cols_r[2].selectbox("Columna: Impacto", df_r.columns)

        df_r['Riesgo_T'] = df_r[col_rp] * df_r[col_ri]

        # Mapa de Calor ISO 27005
        fig_h = go.Figure(data=go.Heatmap(
            z=[[i*j for i in range(1, escala_max+1)] for j in range(1, escala_max+1)],
            x=[str(i) for i in range(1, escala_max+1)],
            y=[str(i) for i in range(1, escala_max+1)],
            colorscale='RdYlGn', reverseScale=True, showscale=False, opacity=0.3
        ))
        fig_h.add_trace(go.Scatter(x=df_r[col_rp], y=df_r[col_ri], mode='markers',
                                   marker=dict(size=15, color='black', symbol='diamond')))
        st.plotly_chart(fig_h, use_container_width=True)

        if st.button("🚀 ANALIZAR TRATAMIENTO (ISO 27002)"):
            with st.spinner("🧠 Consultor analizando bajo ISO 27005/27002..."):
                top_riesgos = df_r.sort_values(by='Riesgo_T', ascending=False).head(5)
                reporte_r = ""
               
                for _, row in top_riesgos.iterrows():
                    p_r = f"""Actúa como Gestor de Riesgos ISO 27005.
                    Riesgo: {row[col_rd]} | Valor: {row['Riesgo_T']}.
                    1. Opción de Tratamiento (ISO 27005).
                    2. Controles de Mitigación (ISO 27002:2022).
                    3. Mapeo NIST y COBIT.
                    4. Proyección de Riesgo Residual."""
                   
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(p_r)
                    st.markdown(f"### 🔥 Análisis: {row[col_rd]}")
                    st.write(res.text)
                    reporte_r += res.text + "\n\n"

                # Generador de PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 8, reporte_r.encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 Descargar Plan de Tratamiento PDF",
                                   data=pdf.output(dest='S').encode('latin-1'),
                                   file_name="Plan_ISO_27005.pdf")
