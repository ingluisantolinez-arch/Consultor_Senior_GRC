import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import json
import time
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .report-card { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 15px; }
    .main { background-color: #0d1117; color: #c9d1d9; }
    </style>
    """, unsafe_allow_html=True)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Error: Configure la API Key.")
    st.stop()

# --- 2. MOTOR DE REPORTES CENTRALIZADO ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'REPORTE CORPORATIVO DE CIBERSEGURIDAD Y GRC', 0, 1, 'R')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generado el {datetime.now().strftime("%d/%m/%Y")} | Página {self.page_no()}', 0, 0, 'C')

def exportar_informe(titulo, datos, es_ejecutivo=False):
    pdf = GRC_Report()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, titulo.upper(), ln=True)
    pdf.set_font("Arial", size=9)
    pdf.cell(0, 5, f"Sector: {st.session_state.get('sector', 'N/A')}", ln=True)
    pdf.cell(0, 5, f"Tipo: {st.session_state.get('tipo', 'N/A')}", ln=True)
    pdf.ln(10)

    for item in datos:
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(230, 235, 245)
        pdf.cell(0, 8, item.get('header', '').encode('latin-1', 'replace').decode('latin-1'), ln=True, fill=True)
        pdf.set_font("Arial", size=9)
       
        cuerpo = item.get('body', '')
        if es_ejecutivo and len(cuerpo) > 400:
            cuerpo = cuerpo[:400] + "\n\n[Resumen Ejecutivo: Consulte el informe detallado para el análisis técnico completo]"
       
        pdf.multi_cell(0, 5, cuerpo.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(4)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración Senior")
    st.session_state['sector'] = st.selectbox("Sector Cliente", ["Bancario", "Salud", "Energía", "Tecnología", "Gobierno"])
    st.session_state['tipo'] = st.selectbox("Módulo de Verificación", [
        "Verificación de Estándares", "Verificación de Proveedores",
        "Verificación Cumplimiento Seguridad", "Verificación Protección de Datos"
    ])
    archivo = st.file_uploader("Cargar Archivo Base", type=["xlsx", "csv"])

# --- 4. INTERFAZ DE MÓDULOS ---
st.title("🛡️ Consola GRC Elite: Verificación & Riesgos")

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Verificación & Acción",
    "📊 Benchmarking",
    "🎲 Matriz de Riesgos",
    "📥 CENTRO DE INFORMES"
])

if archivo:
    df = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # --- TAB 1: VERIFICACIÓN ---
    with tab1:
        st.subheader("📋 Gestión de Hallazgos")
        col_id = st.selectbox("ID Item", df.columns)
        col_h = st.selectbox("Hallazgo", df.columns)
       
        if st.button("🚀 PROCESAR ANÁLISIS DE VERIFICACIÓN"):
            results_v = []
            with st.spinner("Analizando bajo ISO 27002, NIST y COBIT..."):
                for _, row in df.head(10).iterrows():
                    p = f"Analiza '{row[col_h]}'. Cita Cláusulas ISO 27002. Identifica BRECHA DOCUMENTAL y Acción Técnica."
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(p).text
                    results_v.append({"header": f"Item {row[col_id]}", "body": res})
            st.session_state['v_data'] = results_v
            st.success("Análisis de Verificación listo para exportar.")

    # --- TAB 3: RIESGOS ---
    with tab3:
        st.subheader("🎲 Riesgos ISO 31000 / 27005")
        metodo = st.selectbox("Metodología", ["ISO 31000", "ISO 27005", "NIST 800-30"])
       
        if st.button("⚡ GENERAR MATRIZ DE RIESGOS"):
            results_r = []
            with st.spinner(f"Deduciendo riesgos bajo {metodo}..."):
                for _, row in df.head(8).iterrows():
                    p = f"Deduce Riesgo bajo {metodo} para: '{row[col_h]}'. Responde JSON con: id_riesgo, nombre_riesgo, prob(1-5), imp(1-5), brecha_doc, sustento."
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    try:
                        resp = json.loads(model.generate_content(p).text.replace('```json', '').replace('```', '').strip())
                        score = resp['prob'] * resp['imp']
                        nivel = "CRÍTICO" if score >= 15 else "MEDIO/BAJO"
                        results_r.append({
                            "header": f"{nivel}: {resp['nombre_riesgo']} ({resp['id_riesgo']})",
                            "body": f"Probabilidad: {resp['prob']} | Impacto: {resp['imp']} | Inherente: {score}\nSustento: {resp['sustento']}\nBrecha Documental: {resp['brecha_doc']}",
                            "score": score
                        })
                    except: pass
            # Priorización
            st.session_state['r_data'] = sorted(results_r, key=lambda x: x.get('score', 0), reverse=True)
            st.success("Matriz de Riesgos lista para exportar.")

    # --- TAB 4: NUEVO MÓDULO DE INFORMES CENTRALIZADO ---
    with tab4:
        st.subheader("📥 Centro de Descarga de Informes GRC")
        st.write("Seleccione los informes procesados que desea exportar en formato PDF de alta categoría.")
       
        col_inf1, col_inf2 = st.columns(2)
       
        with col_inf1:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown("### 📋 Informes de Verificación")
            if 'v_data' in st.session_state:
                st.download_button("📄 Informe Ejecutivo (Resumido)", exportar_informe("Ejecutivo de Verificación", st.session_state['v_data'], True), "Ejecutivo_Verificacion.pdf")
                st.download_button("📜 Informe Detallado (Técnico)", exportar_informe("Detallado de Verificación", st.session_state['v_data'], False), "Detallado_Verificacion.pdf")
            else:
                st.warning("Procese la pestaña de Verificación primero.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_inf2:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown("### 🎲 Informes de Riesgos")
            if 'r_data' in st.session_state:
                st.download_button("📄 Resumen de Riesgos (Priorizado)", exportar_informe("Ejecutivo de Riesgos", st.session_state['r_data'], True), "Ejecutivo_Riesgos.pdf")
                st.download_button("📜 Matriz de Riesgos Detallada", exportar_informe("Detallado de Riesgos", st.session_state['r_data'], False), "Detallado_Riesgos.pdf")
            else:
                st.warning("Procese la pestaña de Riesgos primero.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Informes Comparativos (Benchmarking)")
        st.download_button("📥 Informe de Evolución Histórica", exportar_informe("Comparativa de Verificaciones", [{"header": "Análisis", "body": "Se observa una evolución constante..."}], True), "Ejecutivo_Comparativo.pdf")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👋 Por favor, cargue el archivo de Verificación en el panel lateral.")

