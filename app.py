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
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    </style>
    """, unsafe_allow_html=True)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Error: Configure la 'GOOGLE_API_KEY' en los Secrets.")
    st.stop()

# --- 2. MOTOR DE REPORTES ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 10, 'REPORTE CORPORATIVO GRC - NIVEL SENIOR', 0, 1, 'R')
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
    st.header("⚙️ Configuración")
    sector = st.selectbox("Sector", ["Bancario", "Salud", "Energía", "Tecnología", "Gobierno"])
    archivo = st.file_uploader("Cargar Excel (prueba1.xlsx)", type=["xlsx"])

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🛡️ Consola GRC Elite")

if archivo:
    # Lógica para detectar la fila de títulos (Fila 7 según tu archivo)
    df_raw = pd.read_excel(archivo, header=None)
    fila_inicio = 0
    for i, row in df_raw.head(15).iterrows():
        if "Hallazgos" in row.values or "ID" in row.values:
            fila_inicio = i
            break
    
    df = pd.read_excel(archivo, skiprows=fila_inicio)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Hallazgos"])

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Verificación", "📊 Benchmarking", "🎲 Riesgos", "📥 INFORMES"])

    # Función para intentar llamar a diferentes modelos si uno falla
    def llamar_ia(prompt):
        # Lista de modelos por orden de preferencia
        modelos_intentar = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
        for nombre_modelo in modelos_intentar:
            try:
                model = genai.GenerativeModel(nombre_modelo)
                response = model.generate_content(prompt)
                return response.text
            except Exception:
                continue
        return "Error: No se pudo conectar con ningún modelo de Gemini disponible."

    with tab1:
        st.subheader("📋 Análisis de Hallazgos")
        c_id = "ID" if "ID" in df.columns else df.columns[0]
        c_lin = "Lineamientos de Seguridad" if "Lineamientos de Seguridad" in df.columns else df.columns[1]
        
        if st.button("🚀 EJECUTAR CONSULTORÍA"):
            results_v = []
            with st.spinner("Procesando hallazgos con IA..."):
                # Procesamos los hallazgos
                for _, row in df.head(10).iterrows():
                    p = f"Analiza como Auditor Senior GRC: Hallazgo: '{row['Hallazgos']}' vs Lineamiento: '{row[c_lin]}'. Indica Riesgo, Control ISO 2
