import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
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
    st.error("⚠️ Configure la 'GOOGLE_API_KEY' en los Secrets.")
    st.stop()

# --- 2. MOTOR DE REPORTES (FPDF2) ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'REPORTE CORPORATIVO GRC - CONFIDENCIAL', 0, 1, 'R')

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
        pdf.set_fill_color(230, 235, 245)
        pdf.multi_cell(0, 8, txt=item.get('header', ''), fill=True)
        pdf.set_font("Helvetica", size=9)
        pdf.multi_cell(0, 5, txt=item.get('body', ''))
        pdf.ln(4)
    return pdf.output()

# --- 3. PANEL LATERAL & CARGA ---
with st.sidebar:
    st.header("⚙️ Configuración Senior")
    sector = st.selectbox("Sector Cliente", ["Bancario", "Salud", "Energía", "Tecnología", "Gobierno"])
    archivo = st.file_uploader("Cargar prueba1.xlsx", type=["xlsx", "csv"])

# --- 4. LÓGICA DE PROCESAMIENTO ---
if archivo:
    # Leemos sin encabezados primero para detectar la fila real de títulos
    df_raw = pd.read_excel(archivo, header=None) if archivo.name.endswith('xlsx') else pd.read_csv(archivo, header=None)
    
    # Buscamos la fila que contiene la palabra "Hallazgos" o "ID" (Típicamente fila 7 en tu archivo)
    fila_titulos = 0
    for i, row in df_raw.head(15).iterrows():
        if "Hallazgos" in row.values or "ID" in row.values:
            fila_titulos = i
            break
    
    # Recargamos el dataframe con la cabecera correcta
    df = pd.read_excel(archivo, skiprows=fila_titulos) if archivo.name.endswith('xlsx') else pd.read_csv(archivo, skiprows=fila_titulos)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Hallazgos"]) # Solo procesar filas que tengan hallazgos escritos

    st.title("🛡️ Consola GRC Elite")
    tab1, tab2 = st.tabs(["📝 Verificación de Hallazgos", "📥 Centro de Informes"])

    with tab1:
        st.subheader("📋 Análisis de Brechas (ISO 27001/2 / NIST)")
        
        # Detección automática de columnas críticas según tu archivo
        col_id = st.selectbox("Columna ID", df.columns, index=df.columns.get_loc("ID") if "ID" in df.columns else 0)
        col_lin = st.selectbox("Columna Lineamiento", df.columns, index=df.columns.get_loc("Lineamientos de Seguridad") if "Lineamientos de Seguridad" in df.columns else 0)
        col_h = st.selectbox("Columna Hallazgos", df.columns, index=df.columns.get_loc("Hallazgos") if "Hallazgos" in df.columns else 0)

        if st.button("🚀 EJECUTAR CONSULTORÍA DE NIVEL 3"):
            results_v = []
            with st.spinner("IA Analizando brechas técnicas y normativas..."):
                # Procesamos solo los primeros 10 para eficiencia
                for _, row in df.head(10).iterrows():
                    hallazgo = str(row[col_h])
                    lineamiento = str(row[col_lin])
                    id_item = str(row[col_id])

                    # PROMPT SENIOR: Compara lo que debería ser (Lineamiento) vs lo que es (Hallazgo)
                    prompt = f"""Actúa como un Auditor Senior de Ciberseguridad L3.
                    Sector: {sector}.
                    Lineamiento de Seguridad esperado: {lineamiento}
                    Hallazgo encontrado: {hallazgo}

                    Tarea:
                    1. Mapea la brecha específica contra controles ISO 27002:2022 o NIST SP 800-53.
                    2. Define la ACCIÓN TÉCNICA inmediata para remediar.
                    3. Define la BRECHA DOCUMENTAL (qué política o estándar falta).
                    Responde de forma ejecutiva y técnica."""

                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(prompt).text
                        results_v.append({"header": f"ITEM {id_item}: {lineamiento[:80]}...", "body": res})
                        st.markdown(f"**Análisis Item {id_item} finalizado.**")
                    except: continue
            
            st.session_state['v_data'] = results_v
            st.success("Análisis Senior Finalizado.")

    with tab2:
        st.subheader("📥 Exportación")
        if 'v_data' in st.session_state:
            pdf_data = exportar_informe(f"Informe GRC - Sector {sector}", st.session_state['v_data'])
            st.download_button("📥 Descargar Informe de Auditoría PDF", data=pdf_data, file_name="Consultoria_Senior_GRC.pdf", mime="application/pdf")
        else:
            st.info("Procese datos en la pestaña de Verificación para generar el informe.")

else:
    st.title("🛡️ Consola GRC Elite")
    st.info("👋 Por favor, carga tu archivo 'prueba1.xlsx' para detectar los lineamientos y hallazgos.")
