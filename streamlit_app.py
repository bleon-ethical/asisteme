import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime

# --- 1. SEGURIDAD Y CONFIGURACIÓN ---
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    MP_TICKET = st.secrets["MP_TICKET"]
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("Configura GEMINI_API_KEY y MP_TICKET en los Secrets de Streamlit.")
    st.stop()

# --- 2. DICCIONARIOS TÉCNICOS (SIN NÚMEROS EN ESTADOS) ---
DICCIONARIOS = {
    "ESTADOS_LIC": [
        "Publicada", "Cerrada", "Desierta", "Adjudicada", 
        "Revocada", "Suspendida", "Todos"
    ],
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
    "PAGOS": {
        "1": "Pago a 30 días", "2": "Pago a 30, 60 y 90 días", "3": "Pago al día",
        "4": "Pago Anual", "5": "Pago a 60 días", "6": "Pagos Mensuales",
        "7": "Pago Contra Entrega Conforme", "8": "Pago Bimensual",
        "9": "Pago Por Estado de Avance", "10": "Pago Trimestral"
    },
    "MONEDAS": {
        "CLP": "Peso Chileno", "CLF": "UF", "USD": "Dólar", "UTM": "UTM", "EUR": "Euro"
    }
}

# --- 3. ESTILOS DE INTERFAZ ---
st.set_page_config(page_title="Asisteme AI v2", layout="wide", page_icon="🏢")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .card { border: 1px solid #EEE; padding: 20px; border-radius: 12px; background: #F9F9F9; margin-bottom: 10px; }
    .badge { background: #E8F5E9; color: #2E7D32; padding: 4px 10px; border-radius: 15px; font-size: 11px; font-weight: bold; }
    .stButton>button { background-color: #90EE90 !important; font-weight: bold !important; border-radius: 8px !important; border: none !important; width: 100%;}
    </style>
""", unsafe_allow_html=True)

# --- 4. PERFIL DE USUARIO ---
if 'perfil' not in st.session_state:
    st.title("🤝 Bienvenido a Asisteme")
    with st.form("onboarding"):
        st.subheader("Configura tu Perfil")
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Razón Social")
            g = st.text_input("Giro Comercial")
            p = st.selectbox("Personería", ["Persona Jurídica", "Persona Natural"])
        with c2:
            t = st.selectbox("Tamaño", ["Micro/Pyme", "Mediana", "Grande"])
            e = st.slider("Años Exp", 0, 30, 1)
        if st.form_submit_button("Guardar y Entrar"):
            st.session_state.perfil = {"nom": n, "giro": g, "tipo": p, "tam": t, "exp": e}
            st.rerun()
    st.stop()

# --- 5. FUNCIONES API ---
def call_api(path, params):
    url = f"https://api.mercadopublico.cl/servicios/v1/Publico/{path}"
    params["ticket"] = MP_TICKET
    try:
        r = requests.get(url, params=params, timeout=15)
        return r.json().get('Listado', [])
    except: return []

# --- 6. SIDEBAR Y BUSCADOR ---
st.title("Asisteme")
with st.sidebar:
    st.header("🔍 Consultas")
    
    with st.expander("Buscar IDs (Org/RUT)"):
        opcion_id = st.radio("Tipo:", ["RUT Proveedor", "Nombre Organismo"])
        valor_id = st.text_input("Dato a buscar")
        if st.button("Buscar ID"):
            path = "Empresas/BuscarProveedor" if opcion_id == "RUT Proveedor" else "Empresas/BuscarComprador"
            p = {"rutempresaproveedor": valor_id} if opcion_id == "RUT Proveedor" else {}
            res = call_api(path, p)
            if opcion_id == "Nombre Organismo":
                res = [o for o in res if valor_id.lower() in o['NombreEmpresa'].lower()]
            for i in res[:5]: st.code(f"ID: {i['CodigoEmpresa']}\n{i['NombreEmpresa']}")

    st.divider()
    modo = st.selectbox("Filtrar Licitaciones por:", ["Hoy", "Por Estado", "Por Código", "Por Organismo"])
    criterio = ""
    if modo == "Por Estado":
        criterio = st.selectbox("Estado:", DICCIONARIOS["ESTADOS_LIC"])
    else:
        criterio = st.text_input("ID o Código")

    if st.button("Consultar Licitaciones"):
        hoy = datetime.now().strftime("%d%m%Y")
        if modo == "Hoy": p = {"fecha": hoy}
        elif modo == "Por Estado": p = {"fecha": hoy, "estado": criterio.lower() if criterio != "Todos" else "todos"}
        elif modo == "Por Código": p = {"codigo": criterio}
        else: p = {"fecha": hoy, "CodigoOrganismo": criterio}
        
        st.session_state.resultados = call_api("licitaciones.json", p)

# --- 7. RESULTADOS Y ANÁLISIS ---
col1, col2 = st.columns([1, 1])

with col1:
    if 'resultados' in st.session_state:
        st.subheader(f"Resultados ({len(st.session_state.resultados)})")
        for l in st.session_state.resultados[:15]:
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <span class="badge">{l.get('Estado', 'Ver Detalle')}</span>
                    <h4 style="margin:8px 0;">{l['Nombre']}</h4>
                    <p style="font-size:12px; color:#555;">ID: {l['CodigoExterno']} | {l['NombreOrganismo']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Analizar con AI", key=f"ai_{l['CodigoExterno']}"):
                    st.session_state.focus = l

with col2:
    if 'focus' in st.session_state:
        lic = st.session_state.focus
        st.subheader("Consultoría Estratégica")
        with st.status("Asisteme AI analizando viabilidad...", expanded=True):
            tipo_txt = DICCIONARIOS["TIPOS_LIC"].get(lic.get('CodigoTipo'), "Pública")
            
            prompt = f"""
            Analiza como experto en licitaciones publicas chilenas para: {st.session_state.perfil}
            Licitación: {lic['Nombre']}
            Organismo: {lic['NombreOrganismo']}
            Tipo: {tipo_txt}
            
            Responde:
            1. ¿Es viable por rubro y tamaño?
            2. ¿Qué riesgos ves en esta licitación {tipo_txt}?
            3. Una recomendación directa para ganar.
            """
            st.markdown(model.generate_content(prompt).text)
