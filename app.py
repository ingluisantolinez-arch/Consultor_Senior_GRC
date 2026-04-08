import streamlit as st
import google.generativeai as genai
import pandas as pd
from fpdf import FPDF
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .report-card { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 15px; }
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    </style>
    """, unsafe_allow_html=True)

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
    pdf.set_text_color(31, 111, 235) 
    pdf.cell(0, 15, titulo.upper(), ln=True)
    pdf.ln(5)
    for item in datos:
        pdf.set_font("Helvetica", 'B', 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.multi_cell(0, 8, txt=item.get('header', ''), fill=True)
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, txt=item.get('body', ''))
        pdf.ln(4)
    return bytes(pdf.output())

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración Senior")
    sector = st.selectbox("Sector Cliente", ["Bancario", "Salud", "Energía", "Tecnología", "Gobierno"])
    archivo = st.file_uploader("Cargar Archivo Base (Excel)", type=["xlsx"])

# --- 4. FUNCIÓN DE APOYO PARA IA ---
def llamar_ia(prompt):
    modelos = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content(prompt)
            return response.text
        except:
            continue
    return "Error: No se pudo conectar con la IA."

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🛡️ Consola GRC Elite: Verificación & Riesgos")

if archivo:
    # Detección de fila de títulos (Fila 7 según tu archivo)
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

    with tab1:
        st.subheader("📋 Gestión de Hallazgos e ISO 27001")
        c_id = "ID" if "ID" in df.columns else df.columns[0]
        c_lin = "Lineamientos de Seguridad" if "Lineamientos de Seguridad" in df.columns else df.columns[1]
        
        if st.button("🚀 PROCESAR ANÁLISIS DE CONSULTORÍA"):
            results_v = []
            with st.spinner("Analizando brechas con IA..."):
                for _, row in df.head(10).iterrows():
                    # Línea corregida para evitar el SyntaxError
                    p = f"Actúa como Auditor GRC Senior. Analiza el hallazgo: '{row['Hallazgos']}' basado en el lineamiento: '{row[c_lin]}'. Indica Riesgo, Control ISO 27001 y Recomendación técnica."
                    res_text = llamar_ia(p)
                    results_v.append({"header": f"ID {row[c_id]}: {row[c_lin][:60]}...", "body": res_text})
                st.session_state['v_data'] = results_v
                st.success("Análisis completado.")

    with tab3:
        st.subheader("🎲 Matriz de Riesgos Técnica")
        if st.button("⚡ GENERAR MATRIZ DE RIESGOS"):
            results_r = []
            with st.spinner("Deduciendo riesgos..."):
                for _, row in df.head(8).iterrows():
                    p_riesgo = f"Deduce Riesgo para: '{row['Hallazgos']}'. Responde SOLO JSON con: id_riesgo, nombre_riesgo, prob(1-5), imp(1-5), sustento."
                    res_json = llamar_ia(p_riesgo)
                    try:
                        clean = res_json.replace('```json', '').replace('```', '').strip()
                        js = json.loads(clean)
                        score = int(js['prob']) * int(js['imp'])
                        results_r.append({
                            "header": f"Riesgo: {js['nombre_riesgo']} (Score: {score})",
                            "body": f"Probabilidad: {js['prob']} | Impacto: {js['imp']}\nSustento: {js['sustento']}",
                            "score": score
                        })
                    except: continue
                st.session_state['r_data'] = sorted(results_r, key=lambda x: x.get('score', 0), reverse=True)
                st.success("Matriz generada.")

    with tab4:
        st.subheader("📥 Centro de Exportación de Informes")
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            if 'v_data' in st.session_state:
                pdf_v = generar_pdf("Informe de Verificación GRC", st.session_state['v_data'])
                st.download_button("📄 Descargar PDF Auditoría", pdf_v, "Auditoria_GRC.pdf", "application/pdf", key="dl_v")
            else: st.warning("Procesa la Verificación en la Tab 1.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            if 'r_data' in st.session_state:
                pdf_r = generar_pdf("Matriz de Riesgos Corporativos", st.session_state['r_data'])
                st.download_button("🎲 Descargar PDF Riesgos", pdf_r, "Matriz_Riesgos.pdf", "application/pdf", key="dl_r")
            else: st.warning("Genera la Matriz en la Tab 3.")
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👋 Bienvenida. Por favor, carga tu archivo Excel en el panel izquierdo para comenzar.")
