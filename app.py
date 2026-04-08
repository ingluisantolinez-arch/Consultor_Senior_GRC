import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import json
import time
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GRC Senior Specialist L3", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .report-card { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 15px; }
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 5px; color: #8b949e; }
    </style>
    """, unsafe_allow_html=True)

# Autenticación
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Configure la 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 2. MOTOR DE REPORTES (COMPATIBLE CON FPDF2) ---
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'REPORTE CORPORATIVO DE CIBERSEGURIDAD Y GRC - NIVEL SENIOR', 0, 1, 'R')

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Generado el {datetime.now().strftime("%d/%m/%Y")} | Página {self.page_no()}', 0, 0, 'C')

def exportar_informe(titulo, datos, es_ejecutivo=False):
    pdf = GRC_Report()
    pdf.add_page()
    
    # Título Principal
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(31, 111, 235) # Azul corporativo
    pdf.cell(0, 15, titulo.upper(), ln=True)
    
    # Metadatos
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, f"Sector: {st.session_state.get('sector', 'N/A')}", ln=True)
    pdf.cell(0, 5, f"Módulo: {st.session_state.get('tipo', 'N/A')}", ln=True)
    pdf.ln(10)

    for item in datos:
        # Encabezado de Sección
        pdf.set_font("Helvetica", 'B', 11)
        pdf.set_fill_color(230, 235, 245)
        pdf.multi_cell(0, 8, txt=item.get('header', ''), fill=True)
        
        # Cuerpo
        pdf.set_font("Helvetica", size=9)
        cuerpo = item.get('body', '')
        if es_ejecutivo and len(cuerpo) > 500:
            cuerpo = cuerpo[:500] + "\n\n[Nota: Ver informe detallado para el análisis técnico completo]"
        
        pdf.multi_cell(0, 5, txt=cuerpo)
        pdf.ln(4)
    
    return pdf.output() # Retorna bytes directamente (fpdf2)

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración Senior")
    st.session_state['sector'] = st.selectbox("Sector Cliente", ["Bancario", "Salud", "Energía", "Tecnología", "Gobierno"])
    st.session_state['tipo'] = st.selectbox("Módulo de Verificación", [
        "Verificación de Estándares", "Verificación de Proveedores",
        "Verificación Cumplimiento Seguridad", "Verificación Protección de Datos"
    ])
    archivo = st.file_uploader("Cargar Archivo de Auditoría/Riesgos", type=["xlsx", "csv"])

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🛡️ Consola GRC Elite: Verificación & Riesgos")

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Verificación & Acción", 
    "📊 Benchmarking", 
    "🎲 Matriz de Riesgos", 
    "📥 CENTRO DE INFORMES"
])

if archivo:
    df = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # TAB 1: VERIFICACIÓN
    with tab1:
        st.subheader("📋 Gestión de Hallazgos y Acciones")
        cols = df.columns.tolist()
        col_id = st.selectbox("Seleccione ID/Referencia", cols)
        col_h = st.selectbox("Seleccione Columna de Hallazgo", cols)
        
        if st.button("🚀 PROCESAR ANÁLISIS DE VERIFICACIÓN"):
            results_v = []
            with st.spinner("Analizando bajo ISO 27002, NIST y COBIT..."):
                # Limitamos a los primeros 10 para control de cuota
                for _, row in df.head(10).iterrows():
                    p = f"Analiza: '{row[col_h]}'. Cita Cláusulas ISO 27002:2022. Identifica BRECHA DOCUMENTAL y Acción Técnica sugerida."
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    try:
                        res = model.generate_content(p).text
                        results_v.append({"header": f"Item {row[col_id]}", "body": res})
                    except: continue
            st.session_state['v_data'] = results_v
            st.success("Análisis completado exitosamente.")

    # TAB 3: RIESGOS
    with tab3:
        st.subheader("🎲 Análisis de Riesgos ISO 27005")
        if st.button("⚡ GENERAR MATRIZ DE RIESGOS"):
            results_r = []
            with st.spinner("Deduciendo riesgos técnicos..."):
                for _, row in df.head(8).iterrows():
                    p = f"Deduce Riesgo para: '{row[col_h]}'. Responde SOLO JSON con: id_riesgo, nombre_riesgo, prob(1-5), imp(1-5), brecha_doc, sustento."
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    try:
                        raw = model.generate_content(p).text
                        clean_json = raw.replace('```json', '').replace('```', '').strip()
                        resp = json.loads(clean_json)
                        score = int(resp['prob']) * int(resp['imp'])
                        nivel = "CRÍTICO" if score >= 15 else "MEDIO" if score >= 8 else "BAJO"
                        results_r.append({
                            "header": f"{nivel}: {resp['nombre_riesgo']} (Score: {score})",
                            "body": f"Probabilidad: {resp['prob']} | Impacto: {resp['imp']}\nBrecha: {resp['brecha_doc']}\nAnálisis: {resp['sustento']}",
                            "score": score
                        })
                    except: continue
            st.session_state['r_data'] = sorted(results_r, key=lambda x: x.get('score', 0), reverse=True)
            st.success("Matriz de Riesgos generada.")

    # TAB 4: CENTRO DE INFORMES
    with tab4:
        st.subheader("📥 Exportación de Entregables")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown("### 📋 Verificación")
            if 'v_data' in st.session_state:
                pdf_v = exportar_informe("Informe de Verificación GRC", st.session_state['v_data'], False)
                st.download_button("📥 Bajar Informe Técnico", data=pdf_v, file_name="Auditoria_Tecnica.pdf", mime="application/pdf")
            else: st.warning("Sin datos procesados.")
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown("### 🎲 Riesgos")
            if 'r_data' in st.session_state:
                pdf_r = exportar_informe("Matriz de Riesgos Corporativos", st.session_state['r_data'], False)
                st.download_button("📥 Bajar Matriz de Riesgos", data=pdf_r, file_name="Matriz_Riesgos.pdf", mime="application/pdf")
            else: st.warning("Sin datos procesados.")
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👋 Bienvenida a la consola GRC. Cargue un archivo para comenzar.")
