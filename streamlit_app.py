import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime
import math

# --- 1. SEGURIDAD Y CONFIGURACIÓN ---
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception:
    st.error("⚠️ Configura GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- 2. DICCIONARIOS AMPLIADOS ---
DICCIONARIOS = {
    "ESTADOS_LIC": ["Publicada", "Cerrada", "Desierta", "Adjudicada", "Revocada", "Suspendida", "Todos"],
    "REGIONES": [
        "Todas", "Arica y Parinacota", "Tarapacá", "Antofagasta", "Atacama", "Coquimbo", 
        "Valparaíso", "Metropolitana", "O'Higgins", "Maule", "Ñuble", "Biobío", 
        "Araucanía", "Los Ríos", "Los Lagos", "Aysén", "Magallanes"
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


# --- 3. DISEÑO DARK MODE MEJORADO ---
st.set_page_config(page_title="Asisteme Pro | Mercado Público", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0F172A; }
    h1, h2, h3, h4, span, p, label, .stMarkdown { color: #F8FAFC !important; }
    
    .card-vitrina { 
        border: 1px solid #334155; 
        padding: 18px; 
        border-radius: 15px; 
        background: #1E293B; 
        margin-bottom: 20px;
        height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .card-vitrina:hover { border-color: #10B981; transform: scale(1.01); transition: 0.2s; }

    .badge-estado {
        background: #064E3B; color: #34D399; padding: 2px 8px;
        border-radius: 10px; font-size: 10px; font-weight: bold;
    }
    .fecha-cierre { color: #F87171; font-size: 11px; font-weight: bold; }

    .stButton>button { 
        background-color: #10B981 !important; color: white !important;
        border-radius: 10px !important; font-weight: 600; width: 100%;
    }
    [data-testid="stSidebar"] { background-color: #111827; }
    </style>
""", unsafe_allow_html=True)

# --- 4. ONBOARDING ---
if 'perfil' not in st.session_state:
    st.title("🤝 Configura tu Perfil Comercial")
    with st.form("onboarding"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Nombre / Empresa")
            g = st.text_input("¿Qué vendes? (Rubro)")
            p = st.selectbox("Personalidad", ["Persona Natural", "Persona Jurídica"])
        with c2:
            exp = st.slider("Años en el rubro", 0, 40, 5)
            cert = st.multiselect("Sellos/Certificaciones", ["Sello Mujer", "Pyme", "Cooperativa", "Local"])
        if st.form_submit_button("Entrar al Panel"):
            if n and g:
                st.session_state.perfil = {"nom": n, "giro": g, "tipo": p, "exp": exp, "certs": cert}
                st.rerun()
    st.stop()

# --- 5. LÓGICA DE API ---
def call_api(path, params):
    ticket = "AA15FBCB-11BF-4385-BAEF-97C28C6052F2"
    url = f"https://api.mercadopublico.cl/servicios/v1/Publico/{path}?ticket={ticket}"
    try:
        r = requests.get(url, params=params, timeout=15)
        return r.json().get('Listado', []) if r.status_code == 200 else []
    except: return []

# --- 6. BUSCADOR AVANZADO ---
with st.sidebar:
    st.header("🔍 Filtros de Mercado")
    query = st.text_input("Palabra clave:", placeholder="ej: construcción")
    region_sel = st.selectbox("Región de ejecución:", DICCIONARIOS["REGIONES"])
    estado_sel = st.selectbox("Estado actual:", DICCIONARIOS["ESTADOS_LIC"])
    
    st.markdown("---")
    st.subheader("💰 Filtro Económico")
    monto_min = st.number_input("Monto Mínimo (CLP)", 0, 1000000000, 0)
    
    if st.button("🚀 Buscar Oportunidades"):
        hoy = datetime.now().strftime("%d%m%Y")
        p = {"fecha": hoy}
        if estado_sel != "Todos": p["estado"] = estado_sel.lower()
        
        with st.spinner("Conectando..."):
            data = call_api("licitaciones.json", p)
            if query:
                data = [l for l in data if query.lower() in l.get('Nombre', '').lower()]
            if region_sel != "Todas":
                data = [l for l in data if region_sel.lower() in l.get('NombreOrganismo', '').lower()]
            
            st.session_state.resultados = data
            st.session_state.pagina_actual = 1

# --- 7. VITRINA Y PAGINACIÓN ---
if 'resultados' in st.session_state and st.session_state.resultados:
    res = st.session_state.resultados
    it_pag = 12
    total_p = math.ceil(len(res) / it_pag)
    
    if 'pagina_actual' not in st.session_state: st.session_state.pagina_actual = 1

    c_head, c_nav = st.columns([3, 1])
    with c_head:
        st.subheader(f"💼 {len(res)} Licitaciones encontradas")
    with c_nav:
        # Selector de página con callback para refrescar
        pag_sel = st.selectbox("Ir a página:", range(1, total_p + 1), index=st.session_state.pagina_actual-1)
        if pag_sel != st.session_state.pagina_actual:
            st.session_state.pagina_actual = pag_sel
            st.rerun()

    inicio = (st.session_state.pagina_actual - 1) * it_pag
    bloque = res[inicio : inicio + it_pag]

    # Render de Vitrina 3x4
    for i in range(0, len(bloque), 3):
        cols = st.columns(3)
        for j, lic in enumerate(bloque[i:i+3]):
            with cols[j]:
                nombre = lic.get('Nombre', 'Sin nombre')[:70]
                org = lic.get('NombreOrganismo', 'Organismo no detectado')
                codigo = lic.get('CodigoExterno', 'N/A')
                est = lic.get('Estado', 'Revisar')
                
                st.markdown(f"""
                <div class="card-vitrina">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="badge-estado">{est}</span>
                            <span class="fecha-cierre">ID: {codigo}</span>
                        </div>
                        <h4 style="margin:12px 0; font-size:15px; color:#F1F5F9;">{nombre}...</h4>
                        <p style="font-size:12px; color:#94A3B8;">🏢 <b>{org}</b></p>
                    </div>
                    <div style="border-top:1px solid #334155; padding-top:10px;">
                        <p style="font-size:11px; margin:0; color:#CBD5E1;">📍 {region_sel if region_sel != "Todas" else "Chile (Ver bases)"}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔍 Ver Análisis IA", key=f"btn_{codigo}"):
                    st.session_state.focus = lic

# --- 8. CONSULTORÍA AI LATERAL ---
if 'focus' in st.session_state:
    with st.sidebar:
        st.markdown("---")
        st.success(f"Analizando: {st.session_state.focus['CodigoExterno']}")
        with st.status("Consultando Gemini..."):
            prompt = f"""
            Analiza esta licitación para mi perfil:
            MI PERFIL: {st.session_state.perfil}
            LICITACIÓN: {st.session_state.focus}
            
            Dime de forma directa:
            1. ¿Es factible para mí?
            2. Documentos de {st.session_state.perfil['tipo']} críticos.
            3. Estrategia para ganar.
            """
            st.markdown(model.generate_content(prompt).text)
        if st.button("Cerrar Análisis"):
            del st.session_state.focus
            st.rerun()
