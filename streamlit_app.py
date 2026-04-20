import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime

# --- 1. SEGURIDAD Y CONFIGURACIÓN ---
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("⚠️ Configura GEMINI_API_KEY y MP_TICKET en los Secrets de Streamlit.")
    st.stop()

# --- 2. DICCIONARIOS TÉCNICOS CORREGIDOS ---
DICCIONARIOS = {
    "ESTADOS_LIC": ["Publicada", "Cerrada", "Desierta", "Adjudicada", "Revocada", "Suspendida", "Todos"],
    
    "TIPOS_LIC": {
        "L1": "Licitación Pública Menor a 100 UTM",
        "LE": "Licitación Pública Entre 100 y 1000 UTM",
        "LP": "Licitación Pública Mayor 1000 UTM",
        "LS": "Licitación Pública Servicios personales especializados",
        "A1": "Licitación Privada (Pública previa sin oferentes)",
        "B1": "Licitación Privada por otras causales",
        "J1": "Licitación Privada por Servicios Confidenciales",
        "F1": "Licitación Privada (Extranjeros)",
        "E1": "Licitación Privada por Remanente",
        "CO": "Licitación Privada 100-1000 UTM",
        "B2": "Licitación Privada Mayor a 1000 UTM",
        "A2": "Trato Directo (Privada previa desierta)",
        "D1": "Trato Directo por Proveedor Único",
        "E2": "Licitación Privada Menor a 100 UTM",
        "C2": "Trato Directo (Cotización)",
        "C1": "Compra Directa (Orden de compra)",
        "F2": "Trato Directo (Cotización)",
        "F3": "Compra Directa (Orden de compra)",
        "G2": "Directo (Cotización)",
        "G1": "Compra Directa (Orden de compra)",
        "R1": "Orden de Compra menor a 3 UTM",
        "CA": "Orden de Compra sin Resolución",
        "SE": "OC desde adquisición sin emisión automática"
    },

    "MODALIDADES_PAGO": {
        "1": "Pago a 30 días", "2": "Pago a 30, 60 y 90 días", "3": "Pago al día",
        "4": "Pago Anual", "5": "Pago a 60 días", "6": "Pagos Mensuales",
        "7": "Pago Contra Entrega Conforme", "8": "Pago Bimensual",
        "9": "Pago Por Estado de Avance", "10": "Pago Trimestral"
    },

    "UNIDADES_TIEMPO": {
        "1": "Horas", "2": "Días", "3": "Semanas", "4": "Meses", "5": "Años"
    }
}

# --- 3. DISEÑO DE INTERFAZ (AZUL MARINO OSCURO) ---
st.set_page_config(page_title="Asisteme", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0F172A; }
    h1, h2, h3, h4, span, p, label, .stMarkdown { color: #F8FAFC !important; }
    .stWidget label p { color: #CBD5E1 !important; }

    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
    }

    .card { 
        border: 1px solid #334155; 
        padding: 20px; 
        border-radius: 12px; 
        background: #1E293B; 
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    .stButton>button { 
        background-color: #10B981 !important; 
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 12px !important;
        border: none !important;
        width: 100%;
    }
    .stButton>button:hover { background-color: #059669 !important; }
    
    .badge {
        background-color: #334155;
        color: #38BDF8;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #38BDF8;
    }

    [data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. ONBOARDING ---
if 'perfil' not in st.session_state:
    st.title("🤝 Bienvenido a Asisteme")
    with st.form("onboarding_completo"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("1. Razón Social o Nombre Completo")
            g = st.text_input("2. Giro o Rubro")
            p = st.selectbox("3. Tipo de Personería", ["Persona Natural", "Persona Jurídica"])
            t = st.selectbox("4. Tamaño / Segmento", ["Micro/Pyme", "Mediana", "Grande", "Independiente"])
            exp = st.slider("5. Años de experiencia", 0, 40, 1)
        with c2:
            reg = st.selectbox("6. Región principal", ["Metropolitana", "Valparaíso", "Biobío", "Otras"])
            cap = st.selectbox("7. Capacidad de Monto", ["Hasta 10M", "10M - 50M", "50M - 200M", "Sin límite"])
            certs = st.multiselect("8. Atributos especiales", ["Sello Mujer", "Cooperativa", "Proveedor Local", "Certificación ISO"])
            dolor = st.text_area("9. Mayor dificultad al postular")
            interes = st.text_input("10. Palabras clave (ej: Aseo)")

        if st.form_submit_button("Guardar y Comenzar"):
            if n and g:
                st.session_state.perfil = {"nom": n, "giro": g, "tipo": p, "tam": t, "exp": exp, "reg": reg, "cap": cap, "certs": certs, "dolor": dolor, "keywords": interes}
                st.rerun()
            else:
                st.error("Nombre y Giro son obligatorios.")
    st.stop()

# --- 5. LÓGICA DE API ---
def call_api(path, params):
    url = f"https://api.mercadopublico.cl/servicios/v1/Publico/{path}&ticket=AA15FBCB-11BF-4385-BAEF-97C28C6052F2"
    try:
        r = requests.get(url, params=params, timeout=15)
        return r.json().get('Listado', [])
    except: return []

# --- 6. DASHBOARD PRINCIPAL ---
st.title("🏢 Panel Asisteme")
st.caption(f"Perfil: **{st.session_state.perfil['nom']}** ({st.session_state.perfil['tipo']})")

with st.sidebar:
    st.header("🔍 Buscador")
    modo = st.selectbox("Filtrar por:", ["Hoy", "Por Estado", "Por Código", "Por Organismo"])
    if modo == "Por Estado":
        criterio = st.selectbox("Seleccione un estado:", DICCIONARIOS["ESTADOS_LIC"])
    else:
        criterio = st.text_input("Ingrese ID o Código")

    if st.button("Consultar Mercado"):
        hoy = datetime.now().strftime("%d%m%Y")
        p = {"fecha": hoy}
        if modo == "Por Estado": p["estado"] = criterio.lower() if criterio != "Todos" else "todos"
        elif modo == "Por Código": p = {"codigo": criterio}
        elif modo == "Por Organismo": p["CodigoOrganismo"] = criterio
        
        with st.spinner("Cargando..."):
            st.session_state.resultados = call_api("licitaciones.json", p)

# --- 7. RESULTADOS Y CONSULTORÍA AI ---
c_lista, c_analisis = st.columns([1, 1.2])

with c_lista:
    if 'resultados' in st.session_state:
        st.subheader(f"🔍 Disponibles: {len(st.session_state.resultados)}")
        for lic in st.session_state.resultados[:12]:
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <span class="badge">{lic.get('Estado', 'Ver')}</span>
                    <h4 style="margin:10px 0;">{lic['Nombre']}</h4>
                    <p style="font-size:13px; color:#94A3B8 !important;">ID: {lic['CodigoExterno']}<br><b>{lic['NombreOrganismo']}</b></p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Analizar Viabilidad", key=lic['CodigoExterno']):
                    st.session_state.focus = lic

with c_analisis:
    if 'focus' in st.session_state:
        item = st.session_state.focus
        st.subheader("Análisis Estratégico")
        with st.status("Analizando perfil y normativa...", expanded=True):
            doc_extra = "Documentos de identidad y carpeta tributaria" if st.session_state.perfil['tipo'] == "Persona Natural" else "Escrituras y poderes legales"
            prompt = f"Actúa como consultor experto. PERFIL: {st.session_state.perfil} LICITACIÓN: {item}. Responde factibilidad, documentos ({doc_extra}), estrategia para '{st.session_state.perfil['dolor']}' y probabilidad de éxito."
            st.markdown(model.generate_content(prompt).text)
            
        if st.button("Cerrar Análisis"):
            del st.session_state.focus
            st.rerun()
