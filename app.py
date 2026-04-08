import streamlit as st
import google.generativeai as genai
import pandas as pd
from fpdf import FPDF
import json
import re
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Error: Configure la API Key en los Secrets.")
    st.stop()

# --- 2. MOTOR DE REPORTES CORREGIDO ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(128)
        self.cell(0, 10, 'REPORTE CORPORATIVO GRC - NIVEL SENIOR', 0, 1, 'R')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def limpiar_para_pdf(texto):
    """Limpia caracteres de Markdown y asegura compatibilidad Latin-1"""
    if not texto:
        return ""
    # Eliminar negritas y otros símbolos de Markdown
    texto = texto.replace('**', '').replace('*', '').replace('`', '').replace('#', '')
    # Reemplazar caracteres especiales comunes que rompen FPDF
    replacements = {
        '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2022': '.', '\u2026': '...'
    }
    for char, replacement in replacements.items():
        texto = texto.replace(char, replacement)
    # Forzar a latin-1 ignorando lo que no se pueda convertir
    return texto.encode('latin-1', 'replace').decode('latin-1')

def generar_pdf(titulo, datos):
    pdf = GRC_Report()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # Título Principal
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(31, 111, 235) 
    pdf.cell(0, 15, limpiar_para_pdf(titulo.upper()), ln=True)
    pdf.ln(5)

    # Ancho efectivo (Total - márgenes)
    effective_width = pdf.w - 2 * pdf.l_margin

    for item in datos:
        # Encabezado Gris
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0)
        header_txt = limpiar_para_pdf(item.get('header', 'Análisis'))
        pdf.multi_cell(effective_width, 8, txt=header_txt, fill=True, border='B')
        
        # Cuerpo
        pdf.set_font("Arial", size=9)
        body_txt = limpiar_para_pdf(item.get('body', ''))
        pdf.multi_cell(effective_width, 6, txt=body_txt)
        pdf.ln(5)
    
    return bytes(pdf.output())

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    archivo = st.file_uploader("Cargar prueba1.xlsx", type=["xlsx"])

# --- 4. FUNCIÓN IA ---
def llamar_ia(prompt):
    for m in ['gemini-1.5-flash', 'gemini-1.5-pro']:
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
    df = df.dropna(subset=["Hallazgos"])

    tab1, tab3, tab4 = st.tabs(["📝 Verificación", "🎲 Riesgos", "📥 INFORMES"])

    with tab1:
        st.subheader("📋 Gestión de Hallazgos")
        c_lin = "Lineamientos de Seguridad" if "Lineamientos de Seguridad" in df.columns else df.columns[1]
        
        if st.button("🚀 EJECUTAR ANÁLISIS"):
            results_v = []
            with st.spinner("Analizando..."):
                for _, row in df.head(10).iterrows():
                    p = f"Analiza como Auditor GRC: Hallazgo: '{row['Hallazgos']}' vs Lineamiento: '{row[c_lin]}'. Indica Riesgo y Recomendación."
                    res = llamar_ia(p)
                    results_v.append({"header": f"ID: {row[c_lin][:60]}", "body": res})
            st.session_state['v_data'] = results_v
            st.success("Análisis listo.")

    with tab4:
        st.subheader("📥 Centro de Descarga")
        if 'v_data' in st.session_state:
            try:
                # Generamos el PDF al momento del clic para asegurar datos frescos
                pdf_bytes = generar_pdf("Informe de Auditoría GRC", st.session_state['v_data'])
                st.download_button(
                    label="📄 Descargar Informe PDF",
                    data=pdf_bytes,
                    file_name="Reporte_GRC.pdf",
                    mime="application/pdf",
                    key="btn_descarga_final"
                )
            except Exception as e:
                st.error(f"Error generando el documento: {e}")
        else:
            st.info("Primero procese los datos en la pestaña de Verificación.")
else:
    st.info("👋 Por favor, carga tu archivo para comenzar.")
