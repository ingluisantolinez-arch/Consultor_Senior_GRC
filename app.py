import streamlit as st
import google.generativeai as genai
import pandas as pd
from fpdf import FPDF
import json
import re
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .report-card { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 15px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    </style>
    """, unsafe_allow_html=True)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Error: Configure la API Key en los Secrets.")
    st.stop()

# --- 2. MOTOR DE REPORTES CORREGIDO ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 10, 'REPORTE CORPORATIVO GRC - NIVEL SENIOR', 0, 1, 'R')
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def limpiar_texto(texto):
    # Elimina asteriscos de negrita de Markdown y caracteres no-latin1 que rompen FPDF
    texto = texto.replace('**', '').replace('*', '')
    return texto.encode('latin-1', 'replace').decode('latin-1')

def generar_pdf(titulo, datos):
    pdf = GRC_Report()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Título
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(31, 111, 235) 
    pdf.cell(0, 15, limpiar_texto(titulo.upper()), ln=True)
    pdf.ln(5)

    for item in datos:
        # Encabezado de sección
        pdf.set_font("Helvetica", 'B', 11)
        pdf.set_fill_color(240, 240, 240)
        header_text = limpiar_texto(item.get('header', 'Sin Título'))
        pdf.multi_cell(0, 8, txt=header_text, fill=True)
        
        # Cuerpo del análisis
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(0, 0, 0)
        body_text = limpiar_texto(item.get('body', ''))
        # Usamos multi_cell con un ancho fijo (w=0 significa hasta el margen derecho)
        pdf.multi_cell(0, 5, txt=body_text)
        pdf.ln(4)
    
    return bytes(pdf.output())

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    sector = st.selectbox("Sector", ["Bancario", "Salud", "Energía", "Tecnología", "Gobierno"])
    archivo = st.file_uploader("Cargar prueba1.xlsx", type=["xlsx"])

# --- 4. FUNCIÓN IA MULTI-MODELO ---
def llamar_ia(prompt):
    for m in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content(prompt)
            return response.text
        except: continue
    return "Error de conexión con la IA."

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🛡️ Consola GRC Elite")

if archivo:
    # Detección de fila de títulos (Fila 7)
    df_raw = pd.read_excel(archivo, header=None)
    fila_inicio = 0
    for i, row in df_raw.head(20).iterrows():
        if "Hallazgos" in row.values:
            fila_inicio = i
            break
    
    df = pd.read_excel(archivo, skiprows=fila_inicio)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Hallazgos"])

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Verificación", "📊 Benchmarking", "🎲 Riesgos", "📥 INFORMES"])

    with tab1:
        st.subheader("📋 Análisis de Hallazgos")
        c_lin = "Lineamientos de Seguridad" if "Lineamientos de Seguridad" in df.columns else df.columns[1]
        c_id = "ID" if "ID" in df.columns else "ID"
        
        if st.button("🚀 PROCESAR CONSULTORÍA"):
            results_v = []
            with st.spinner("IA Analizando..."):
                for _, row in df.head(10).iterrows():
                    p = f"Analiza como Auditor GRC: Hallazgo: '{row['Hallazgos']}' vs Lineamiento: '{row[c_lin]}'. Indica Riesgo, Control ISO 27001 y Recomendación."
                    res = llamar_ia(p)
                    results_v.append({"header": f"ID {row.get(c_id, 'N/A')}: {row[c_lin][:50]}", "body": res})
            st.session_state['v_data'] = results_v
            st.success("Análisis terminado.")

    with tab3:
        st.subheader("🎲 Matriz de Riesgos")
        if st.button("⚡ GENERAR RIESGOS"):
            results_r = []
            with st.spinner("Calculando riesgos..."):
                for _, row in df.head(8).iterrows():
                    p = f"Deduce Riesgo para: '{row['Hallazgos']}'. Responde SOLO JSON: id_riesgo, nombre_riesgo, prob(1-5), imp(1-5), sustento."
                    res_raw = llamar_ia(p)
                    try:
                        clean = re.sub(r'```json|```', '', res_raw).strip()
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
        st.subheader("📥 Exportación")
        c1, c2 = st.columns(2)
        with c1:
            if 'v_data' in st.session_state:
                pdf_v = generar_pdf("Informe de Verificación", st.session_state['v_data'])
                st.download_button("📄 PDF Auditoría", pdf_v, "Auditoria.pdf", "application/pdf", key="v_pdf")
        with c2:
            if 'r_data' in st.session_state:
                pdf_r = generar_pdf("Matriz de Riesgos", st.session_state['r_data'])
                st.download_button("🎲 PDF Riesgos", pdf_r, "Riesgos.pdf", "application/pdf", key="r_pdf")
else:
    st.info("👋 Sube tu archivo para comenzar.")
