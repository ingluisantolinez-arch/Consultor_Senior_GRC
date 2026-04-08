import streamlit as st
import google.generativeai as genai
import pandas as pd
from fpdf import FPDF
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Configure la API Key en los Secrets.")
    st.stop()

# --- 2. MOTOR DE REPORTES (SINTAXIS FPDF2) ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'REPORTE CORPORATIVO GRC - NIVEL SENIOR', 0, 1, 'R')

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Generado el {datetime.now().strftime("%d/%m/%Y")} | Página {self.page_no()}', 0, 0, 'C')

def exportar_informe(titulo, datos):
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
    
    # IMPORTANTE: Convertimos explícitamente a bytes para evitar el error de Streamlit
    return bytes(pdf.output())

# --- 3. PROCESAMIENTO DE ARCHIVO ---
archivo = st.sidebar.file_uploader("Cargar prueba1.xlsx", type=["xlsx", "csv"])

if archivo:
    # 1. Detectar cabecera real (Típicamente fila 7 en tu archivo)
    df_raw = pd.read_excel(archivo, header=None) if archivo.name.endswith('xlsx') else pd.read_csv(archivo, header=None)
    
    fila_titulos = 0
    for i, row in df_raw.head(15).iterrows():
        # Buscamos la fila donde aparece la palabra "Hallazgos"
        if "Hallazgos" in row.values:
            fila_titulos = i
            break
    
    # 2. Cargar datos limpios
    df = pd.read_excel(archivo, skiprows=fila_titulos) if archivo.name.endswith('xlsx') else pd.read_csv(archivo, skiprows=fila_titulos)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Limpiamos filas que no tengan hallazgos reales
    df = df.dropna(subset=["Hallazgos"])

    st.title("🛡️ Consola GRC Elite")
    tab1, tab2 = st.tabs(["📝 Verificación", "📥 Centro de Informes"])

    with tab1:
        st.subheader("📋 Análisis Senior de Hallazgos")
        
        # Mapeo de columnas según tu Excel
        col_id = "ID" if "ID" in df.columns else df.columns[0]
        col_lin = "Lineamientos de Seguridad" if "Lineamientos de Seguridad" in df.columns else df.columns[1]
        col_h = "Hallazgos"
        
        if st.button("🚀 EJECUTAR CONSULTORÍA L3"):
            results_v = []
            with st.spinner("Analizando brechas..."):
                for _, row in df.head(10).iterrows():
                    hallazgo = str(row[col_h])
                    lineamiento = str(row[col_lin])
                    id_item = str(row[col_id])

                    prompt = f"""Actúa como Auditor Senior GRC.
                    Control: {lineamiento}
                    Situación Encontrada: {hallazgo}
                    
                    Analiza y define:
                    1. Riesgo asociado.
                    2. Recomendación técnica (ISO 27001).
                    3. Brecha documental detectada."""

                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(prompt).text
                        results_v.append({"header": f"ID {id_item}: {lineamiento[:50]}...", "body": res})
                    except: continue
            
            st.session_state['v_data'] = results_v
            st.success("Análisis completado.")

    with tab2:
        if 'v_data' in st.session_state:
            # Generamos los bytes del PDF
            pdf_bytes = exportar_informe("Informe de Verificación GRC", st.session_state['v_data'])
            
            st.download_button(
                label="📥 Descargar Informe PDF",
                data=pdf_bytes,
                file_name=f"Informe_GRC_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("Primero ejecute el análisis en la pestaña de Verificación.")
else:
    st.info("👋 Por favor, carga el archivo 'prueba1.xlsx' para iniciar.")
