import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import json
import time
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
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
    st.error("⚠️ Error: Configure la API Key en los Secrets de Streamlit.")
    st.stop()

# --- 2. MOTOR DE REPORTES CENTRALIZADO ---
# Usamos FPDF (fpdf2 en requirements) para mejor compatibilidad
class GRC_Report(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 10, 'REPORTE CORPORATIVO DE CIBERSEGURIDAD Y GRC', 0, 1, 'R')

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Generado el {datetime.now().strftime("%d/%m/%Y")} | Página {self.page_no()}', 0, 0, 'C')

def exportar_informe(titulo, datos, es_ejecutivo=False):
    pdf = GRC_Report()
    pdf.add_page()
    
    # Título Principal
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 15, titulo.upper(), ln=True)
    
    # Metadatos
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, f"Sector: {st.session_state.get('sector', 'N/A')}", ln=True)
    pdf.cell(0, 5, f"Tipo: {st.session_state.get('tipo', 'N/A')}", ln=True)
    pdf.ln(10)

    for item in datos:
        # Encabezado de Sección
        pdf.set_font("Helvetica", 'B', 11)
        pdf.set_fill_color(230, 235, 245)
        # multi_cell con fpdf2 maneja mejor los saltos
        pdf.multi_cell(0, 8, txt=item.get('header', ''), fill=True)
        
        # Cuerpo de la sección
        pdf.set_font("Helvetica", size=9)
        cuerpo = item.get('body', '')
        
        if es_ejecutivo and len(cuerpo) > 400:
            cuerpo = cuerpo[:400] + "\n\n[Resumen Ejecutivo: Consulte el informe detallado para el análisis técnico completo]"
        
        pdf.multi_cell(0, 5, txt=cuerpo)
        pdf.ln(4)
    
    # EL CAMBIO CLAVE: fpdf2 devuelve bytes directamente con .output()
    return pdf.output()

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración Senior")
    st.session_state['sector'] = st.selectbox("Sector Cliente", ["Bancario", "Salud", "Energía", "Tecnología", "Gobierno"])
    st.session_state['tipo'] = st.selectbox("Módulo de Verificación", [
        "Verificación de Estándares", "Verificación de Proveedores",
        "Verificación Cumplimiento Seguridad", "Verificación Protección de Datos"
    ])
    archivo = st.file_uploader("Cargar Archivo Base", type=["xlsx", "csv"])

# --- 4. INTERFAZ DE MÓDULOS ---
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

    # --- TAB 1: VERIFICACIÓN ---
    with tab1:
        st.subheader("📋 Gestión de Hallazgos")
        # Aseguramos que las columnas existan
        cols_disponibles = df.columns.tolist()
        col_id = st.selectbox("ID Item", cols_disponibles)
        col_h = st.selectbox("Hallazgo", cols_disponibles)
        
        if st.button("🚀 PROCESAR ANÁLISIS DE VERIFICACIÓN"):
            results_v = []
            with st.spinner("Analizando bajo ISO 27002, NIST y COBIT..."):
                # Limitamos a 5 para evitar Timeouts o cuotas de API
                for _, row in df.head(5).iterrows():
                    p = f"Analiza '{row[col_h]}'. Cita Cláusulas ISO 27002. Identifica BRECHA DOCUMENTAL y Acción Técnica."
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(p).text
                    results_v.append({"header": f"Item {row[col_id]}", "body": res})
            st.session_state['v_data'] = results_v
            st.success("Análisis de Verificación listo.")

    # --- TAB 3: RIESGOS ---
    with tab3:
        st.subheader("🎲 Riesgos ISO 31000 / 27005")
        metodo = st.selectbox("Metodología", ["ISO 31000", "ISO 27005", "NIST 800-30"])
        
        if st.button("⚡ GENERAR MATRIZ DE RIESGOS"):
            results_r = []
            with st.spinner(f"Deduciendo riesgos bajo {metodo}..."):
                for _, row in df.head(5).iterrows():
                    p = f"Deduce Riesgo bajo {metodo} para: '{row[col_h]}'. Responde JSON puro (sin markdown) con: id_riesgo, nombre_riesgo, prob(1-5), imp(1-5), brecha_doc, sustento."
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    try:
                        raw_res = model.generate_content(p).text
                        # Limpieza de JSON
                        clean_json = raw_res.replace('```json', '').replace('```', '').strip()
                        resp = json.loads(clean_json)
                        score = int(resp['prob']) * int(resp['imp'])
                        nivel = "CRÍTICO" if score >= 15 else "MEDIO/BAJO"
                        results_r.append({
                            "header": f"{nivel}: {resp['nombre_riesgo']} ({resp['id_riesgo']})",
                            "body": f"Probabilidad: {resp['prob']} | Impacto: {resp['imp']} | Inherente: {score}\nSustento: {resp['sustento']}\nBrecha Documental: {resp['brecha_doc']}",
                            "score": score
                        })
                    except Exception as e:
                        st.error(f"Error procesando fila: {e}")
            st.session_state['r_data'] = sorted(results_r, key=lambda x: x.get('score', 0), reverse=True)
            st.success("Matriz de Riesgos lista.")

    # --- TAB 4: INFORMES ---
    with tab4:
        st.subheader("📥 Centro de Descarga de Informes GRC")
        
        col_inf1, col_inf2 = st.columns(2)
        
        with col_inf1:
            st.markdown("### 📋 Informes de Verificación")
            if 'v_data' in st.session_state:
                pdf_v_exec = exportar_informe("Ejecutivo de Verificación", st.session_state['v_data'], True)
                st.download_button("📄 Descargar Ejecutivo", data=pdf_v_exec, file_name="Ejecutivo_Verificacion.pdf", mime="application/pdf")
            else:
                st.warning("Procese Verificación primero.")

        with col_inf2:
            st.markdown("### 🎲 Informes de Riesgos")
            if 'r_data' in st.session_state:
                pdf_r_det = exportar_informe("Matriz de Riesgos Detallada", st.session_state['r_data'], False)
                st.download_button("📜 Descargar Matriz", data=pdf_r_det, file_name="Matriz_Riesgos.pdf", mime="application/pdf")
            else:
                st.warning("Procese Riesgos primero.")

else:
    st.info("👋 Por favor, cargue el archivo en el panel lateral.")
