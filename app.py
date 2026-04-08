import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .report-card { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 15px; }
    .main { background-color: #0d1117; color: #c9d1d9; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar llaves de API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Error: Configure la 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 2. MOTOR DE REPORTES (FPDF2) ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 10, 'REPORTE CORPORATIVO DE CIBERSEGURIDAD Y GRC', 0, 1, 'R')
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf(titulo, datos):
    pdf = GRC_Report()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 15, titulo.upper(), ln=True)
    pdf.ln(5)
    for item in datos:
        pdf.set_font("Helvetica", 'B', 11)
        pdf.set_fill_color(230, 235, 245)
        pdf.multi_cell(0, 8, txt=item.get('header', ''), fill=True)
        pdf.set_font("Helvetica", size=9)
        pdf.multi_cell(0, 5, txt=item.get('body', ''))
        pdf.ln(4)
    return bytes(pdf.output())

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración Senior")
    sector_input = st.selectbox("Sector Cliente", ["Bancario", "Salud", "Energía", "Tecnología", "Gobierno"])
    archivo = st.file_uploader("Cargar Archivo Base (Excel)", type=["xlsx"])

# --- 4. INTERFAZ Y LÓGICA ---
st.title("🛡️ Consola GRC Elite: Verificación & Riesgos")

if archivo:
    # Detección de fila de títulos (Buscamos la fila 7 donde están tus datos)
    df_raw = pd.read_excel(archivo, header=None)
    fila_inicio = 0
    for i, row in df_raw.head(20).iterrows():
        if "Hallazgos" in row.values or "ID" in row.values:
            fila_inicio = i
            break
    
    df = pd.read_excel(archivo, skiprows=fila_inicio)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Hallazgos"])

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Verificación", "📊 Benchmarking", "🎲 Riesgos", "📥 INFORMES"])

    # --- TAB 1: VERIFICACIÓN ---
    with tab1:
        st.subheader("📋 Gestión de Hallazgos")
        col_id = "ID" if "ID" in df.columns else df.columns[0]
        col_lin = "Lineamientos de Seguridad" if "Lineamientos de Seguridad" in df.columns else df.columns[1]
        
        if st.button("🚀 PROCESAR ANÁLISIS"):
            results_v = []
            with st.spinner("IA Analizando hallazgos..."):
                # Especificamos el modelo con el nombre técnico completo
                try:
                    model = genai.GenerativeModel('models/gemini-1.5-flash') 
                    for _, row in df.head(10).iterrows():
                        prompt = f"Como Auditor Senior, analiza el hallazgo: {row['Hallazgos']} contra el lineamiento: {row[col_lin]}. Define Riesgo e ISO 27001."
                        response = model.generate_content(prompt)
                        results_v.append({"header": f"ID {row[col_id]}", "body": response.text})
                    st.session_state['v_data'] = results_v
                    st.success("Análisis completado exitosamente.")
                except Exception as e:
                    st.error(f"Error de conexión con la IA: {e}")
                    st.info("Nota: Verifique que el modelo 'gemini-1.5-flash' esté disponible en su región.")

    # --- TAB 3: RIESGOS ---
    with tab3:
        st.subheader("🎲 Matriz de Riesgos")
        if st.button("⚡ GENERAR MATRIZ"):
            results_r = []
            with st.spinner("Deduciendo matriz de riesgos..."):
                try:
                    model = genai.GenerativeModel('models/gemini-1.5-flash')
                    for _, row in df.head(8).iterrows():
                        p = f"Deduce Riesgo para: '{row['Hallazgos']}'. Responde JSON: id_riesgo, nombre_riesgo, prob(1-5), imp(1-5), sustento."
                        raw_res = model.generate_content(p).text
                        clean_json = raw_res.replace('```json', '').replace('```', '').strip()
                        resp = json.loads(clean_json)
                        score = int(resp['prob']) * int(resp['imp'])
                        results_r.append({
                            "header": f"Riesgo: {resp['nombre_riesgo']} (Score: {score})",
                            "body": f"Probabilidad: {resp['prob']} | Impacto: {resp['imp']}\nSustento: {resp['sustento']}",
                            "score": score
                        })
                    st.session_state['r_data'] = sorted(results_r, key=lambda x: x.get('score', 0), reverse=True)
                    st.success("Matriz generada.")
                except Exception as e:
                    st.error(f"Error al generar riesgos: {e}")

    # --- TAB 4: INFORMES ---
    with tab4:
        st.subheader("📥 Centro de Descarga")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            if 'v_data' in st.session_state:
                pdf_v = generar_pdf("Informe de Verificación", st.session_state['v_data'])
                st.download_button("📄 Bajar Informe Auditoría", pdf_v, "Auditoria.pdf", "application/pdf", key="btn_v")
            else: st.warning("Procesa la Verificación primero.")
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            if 'r_data' in st.session_state:
                pdf_r = generar_pdf("Matriz de Riesgos", st.session_state['r_data'])
                st.download_button("🎲 Bajar Matriz de Riesgos", pdf_r, "Riesgos.pdf", "application/pdf", key="btn_r")
            else: st.warning("Procesa los Riesgos primero.")
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👋 Por favor, carga el archivo Excel en el panel lateral.")
