import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import json
import time
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="GRC Senior Intelligence", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 5px; color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #1f6feb !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# Autenticación
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Configure la 'GOOGLE_API_KEY' en los Secrets.")
    st.stop()

# --- 2. FUNCIONES DE EXPORTACIÓN DE INFORMES (FPDF) ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INFORME DE CONSULTORÍA GRC SENIOR', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} | Generado por GRC Intelligence Console', 0, 0, 'C')

def generate_pdf(title, content_list, is_executive=False):
    pdf = GRC_Report()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, title.upper(), ln=True, align='L')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)

    for item in content_list:
        if isinstance(item, dict):
            # Título de sección
            pdf.set_font("Arial", 'B', 11)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, item.get('header', '').encode('latin-1', 'replace').decode('latin-1'), ln=True, fill=True)
            pdf.set_font("Arial", size=9)
            # Cuerpo
            content = item.get('body', '')
            if is_executive: # Cortar texto para informe ejecutivo
                content = content[:400] + "..." if len(content) > 400 else content
            pdf.multi_cell(0, 5, content.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(3)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    sector_cliente = st.selectbox("Sector", ["Bancario", "Financiero", "Salud", "Energía", "Tecnología", "Gobierno"])
    tipo_verificacion = st.selectbox("Módulo", ["Estandares", "Proveedores", "Ciberseguridad", "Protección de Datos"])
    archivo_principal = st.file_uploader("Cargar Verificación Actual", type=["xlsx", "csv"])

# --- 4. CUERPO PRINCIPAL ---
st.title("🛡️ Consola de Verificación & Riesgos")

t1, t2, t3 = st.tabs(["📝 Verificación", "📊 Comparativas", "🎲 Riesgos"])

if archivo_principal:
    df = pd.read_excel(archivo_principal) if archivo_principal.name.endswith('xlsx') else pd.read_csv(archivo_principal)

    # --- MÓDULO 1: VERIFICACIÓN & PLANES ---
    with t1:
        st.subheader("📋 Gestión de Hallazgos")
        col_id = st.selectbox("ID Item", df.columns, key="id_v")
        col_hall = st.selectbox("Hallazgo", df.columns, key="h_v")
       
        if st.button("🚀 PROCESAR VERIFICACIÓN COMPLETA"):
            resultados_v = []
            with st.spinner("Analizando cada ítem..."):
                for _, row in df.iterrows():
                    prompt = f"Consultor GRC: Analiza '{row[col_hall]}'. Da recomendación técnica y documental basada en ISO 27002."
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(prompt).text
                    resultados_v.append({"header": f"Ítem: {row[col_id]}", "body": res})
           
            st.session_state['res_v'] = resultados_v
            st.success("Análisis finalizado.")

        if 'res_v' in st.session_state:
            c1, c2 = st.columns(2)
            pdf_v_exec = generate_pdf("Informe Ejecutivo de Verificación", st.session_state['res_v'], is_executive=True)
            pdf_v_det = generate_pdf("Informe Detallado de Verificación", st.session_state['res_v'], is_executive=False)
            c1.download_button("📄 Informe Ejecutivo (Corto)", pdf_v_exec, "Ejecutivo_Verificacion.pdf")
            c2.download_button("📜 Informe Detallado (Completo)", pdf_v_det, "Detallado_Verificacion.pdf")

    # --- MÓDULO 2: COMPARATIVAS ---
    with t2:
        st.subheader("📊 Módulo de Benchmarking")
        arch_ant = st.file_uploader("Verificación Año Anterior", type=["xlsx", "csv"])
        if arch_ant and st.button("📊 GENERAR INFORME COMPARATIVO"):
            # Lógica simplificada para el ejemplo
            res_comp = [{"header": "Análisis de Evolución", "body": "Se observa una mejora del 20% en controles técnicos frente al periodo anterior..."}]
            pdf_comp = generate_pdf("Informe Ejecutivo Comparativo", res_comp, is_executive=True)
            st.download_button("📥 Descargar Informe Ejecutivo Comparativo", pdf_comp, "Ejecutivo_Comparativa.pdf")

    # --- MÓDULO 3: RIESGOS ---
    with t3:
        st.subheader("🎲 Matriz de Riesgos Priorizada")
        metodologia = st.selectbox("Metodología", ["ISO 31000", "ISO 27005", "NIST 800-30"])
        u_alto = st.slider("Umbral Crítico", 1, 25, 15)

        if st.button("⚡ GENERAR INFORMES DE RIESGO"):
            resultados_r = []
            with st.spinner("Calculando riesgos..."):
                for _, row in df.head(10).iterrows():
                    prompt = f"Define riesgo materializable, impacto y probabilidad para: {row[col_hall]} bajo {metodologia}."
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(prompt).text
                    resultados_r.append({"header": f"Riesgo Deducido de {row[col_id]}", "body": res})
           
            st.session_state['res_r'] = resultados_r

        if 'res_r' in st.session_state:
            cr1, cr2 = st.columns(2)
            pdf_r_exec = generate_pdf("Resumen Ejecutivo de Riesgos", st.session_state['res_r'], is_executive=True)
            pdf_r_det = generate_pdf("Matriz de Riesgos Detallada", st.session_state['res_r'], is_executive=False)
            cr1.download_button("📄 Resumen de Riesgos", pdf_r_exec, "Resumen_Riesgos.pdf")
            cr2.download_button("📜 Riesgos Detallado", pdf_r_det, "Detallado_Riesgos.pdf")
