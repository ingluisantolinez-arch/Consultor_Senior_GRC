import streamlit as st
import google.generativeai as genai
import pandas as pd
from fpdf import FPDF
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

# Estilos CSS para mantener la estética
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
        self.cell(0, 10, f'Generado: {datetime.now().strftime("%d/%m/%Y")} | Página {self.page_no()}', 0, 0, 'C')

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
    archivo = st.file_uploader("Cargar prueba1.xlsx", type=["xlsx"])

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🛡️ Consola GRC Elite")

if archivo:
    # Lógica de detección de fila 7 (Títulos)
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

    with tab1:
        st.subheader("📋 Análisis de Hallazgos")
        # Ajuste nombres según tu archivo
        c_id = "ID" if "ID" in df.columns else df.columns[0]
        c_lin = "Lineamientos de Seguridad" if "Lineamientos de Seguridad" in df.columns else df.columns[1]
        
        if st.button("🚀 EJECUTAR CONSULTORÍA"):
            results_v = []
            with st.spinner("Procesando con Gemini..."):
                # Intentamos con el nombre estándar sin prefijos de versión
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    for _, row in df.head(10).iterrows():
                        prompt = f"Analiza como Auditor Senior GRC: Hallazgo: '{row['Hallazgos']}' vs Lineamiento: '{row[c_lin]}'. Indica Riesgo, Control ISO 27001 y Recomendación."
                        response = model.generate_content(prompt)
                        results_v.append({"header": f"ID {row[c_id]}: {row[c_lin][:50]}", "body": response.text})
                    st.session_state['v_data'] = results_v
                    st.success("Análisis finalizado.")
                except Exception as e:
                    st.error(f"Error con el modelo Flash. Intentando fallback a Pro...")
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        # ... repetimos bucle si es necesario ...
                    except:
                        st.error(f"Error crítico de API: {e}")

    with tab3:
        st.subheader("🎲 Matriz de Riesgos")
        if st.button("⚡ GENERAR RIESGOS"):
            results_r = []
            with st.spinner("Deduciendo niveles de riesgo..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    for _, row in df.head(8).iterrows():
                        p = f"Deduce Riesgo para: '{row['Hallazgos']}'. Responde SOLO JSON: id_riesgo, nombre_riesgo, prob(1-5), imp(1-5), sustento."
                        res = model.generate_content(p).text
                        clean = res.replace('```json', '').replace('```', '').strip()
                        js = json.loads(clean)
                        score = int(js['prob']) * int(js['imp'])
                        results_r.append({
                            "header": f"Riesgo: {js['nombre_riesgo']} (Score: {score})",
                            "body": f"Probabilidad: {js['prob']} | Impacto: {js['imp']}\nSustento: {js['sustento']}",
                            "score": score
                        })
                    st.session_state['r_data'] = sorted(results_r, key=lambda x: x.get('score', 0), reverse=True)
                    st.success("Matriz generada.")
                except Exception as e:
                    st.error(f"Error en matriz: {e}")

    with tab4:
        st.subheader("📥 Centro de Descarga")
        c1, c2 = st.columns(2)
        with c1:
            if 'v_data' in st.session_state:
                btn_data_v = generar_pdf("Informe de Verificación", st.session_state['v_data'])
                st.download_button("📄 PDF Auditoría", btn_data_v, "Auditoria.pdf", "application/pdf", key="v_pdf")
            else: st.info("Sin datos de Verificación.")
        with c2:
            if 'r_data' in st.session_state:
                btn_data_r = generar_pdf("Matriz de Riesgos", st.session_state['r_data'])
                st.download_button("🎲 PDF Riesgos", btn_data_r, "Riesgos.pdf", "application/pdf", key="r_pdf")
            else: st.info("Sin datos de Riesgos.")
else:
    st.info("👋 Sube tu archivo 'prueba1.xlsx' para activar los módulos.")
