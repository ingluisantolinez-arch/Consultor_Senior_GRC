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
st.title
