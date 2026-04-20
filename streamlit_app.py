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
    st.error("⚠️ Configura GEMINI_API_KEY y MP_TICKET en los Secrets de Streamlit.")
    st.stop()

# --- 2. DICCIONARIOS TÉCNICOS (ESTADOS COMO TEXTO) ---
DICCIONARIOS = {
    # --- MAPEADO COMPLETO DE TIPOLOGÍAS (23 TIPOS) ---
TIPOS_LIC = {
    "L1": "Licitación Pública Menor a 100 UTM",
    "LE": "Licitación Pública Entre 100 y 1000 UTM",
    "LP": "Licitación Pública Mayor 1000 UTM",
    "LS": "Licitación Pública Servicios personales especializados",
    "A1": "Licitación Privada (Pública previa sin oferentes)",
    "B1": "Licitación Privada por otras causales (excluidas Ley Compras)",
    "J1": "Licitación Privada por Servicios de Naturaleza Confidencial",
    "F1": "Licitación Privada por Convenios con Personas Jurídicas Extranjeras",
    "E1": "Licitación Privada por Remanente de Contrato anterior",
    "CO": "Licitación Privada entre 100 y 1000 UTM",
    "B2": "Licitación Privada Mayor a 1000 UTM",
    "A2": "Trato Directo (Licitación Privada previa desierta)",
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
}

}

# --- MODALIDADES DE PAGO (10 TIPOS) ---
MODALIDADES_PAGO = {
    "1": "Pago a 30 días",
    "2": "Pago a 30, 60 y 90 días",
    "3": "Pago al día",
    "4": "Pago Anual",
    "5": "Pago a 60 días",
    "6": "Pagos Mensuales",
    "7": "Pago Contra Entrega Conforme",
    "8": "Pago Bimensual",
    "9": "Pago Por Estado de Avance",
    "10": "Pago Trimestral"
}

# --- UNIDADES DE TIEMPO (EVALUACIÓN Y CONTRATO) ---
UNIDADES_TIEMPO = {
    "1": "Horas",
    "2": "Días",
    "3": "Semanas",
    "4": "Meses",
    "5": "Años"
}

# --- 3. DISEÑO DE INTERFAZ (AZUL MARINO OSCURO) ---
st.set_page_config(page_title="Asisteme Pro | Dark Edition", layout="wide")

st.markdown("""
    <style>
    /* Fondo Azul Marino Oscuro */
    .stApp { 
        background-color: #0F172A; 
    }
    
    /* Textos Principales en Blanco/Gris Claro para contraste */
    h1, h2, h3, h4, span, p, label, .stMarkdown { 
        color: #F8FAFC !important; 
    }
    
    /* Ajuste específico para etiquetas de inputs */
    .stWidget label p {
        color: #CBD5E1 !important;
    }

    /* Inputs con fondo oscuro pero bordes visibles */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
    }

    /* Tarjetas de Licitación (Glassmorphism ligero) */
    .card { 
        border: 1px solid #334155; 
        padding: 20px; 
        border-radius: 12px; 
        background: #1E293B; 
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    /* Botón Principal Verde para resaltar sobre el azul */
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
    
    /* Badge de Estado */
    .badge {
        background-color: #334155;
        color: #38BDF8;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #38BDF8;
    }

    /* Barra lateral */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. ONBOARDING (PERSONAS NATURALES Y JURÍDICAS) ---
if 'perfil' not in st.session_state:
    st.title("🤝 Bienvenido a Asisteme")
    st.subheader("Configura tu Perfil Estratégico")
    
    with st.form("onboarding_completo"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("1. Razón Social o Nombre Completo")
            g = st.text_input("2. Giro o Rubro (¿Qué vendes?)")
            p = st.selectbox("3. Tipo de Personería", ["Persona Natural", "Persona Jurídica"])
            t = st.selectbox("4. Tamaño / Segmento", ["Micro/Pyme", "Mediana", "Grande", "Independiente"])
            exp = st.slider("5. Años de experiencia", 0, 40, 1)
        
        with c2:
            reg = st.selectbox("6. Región principal", ["Metropolitana", "Valparaíso", "Biobío", "Otras"])
            cap = st.selectbox("7. Capacidad de Monto", ["Hasta 10M", "10M - 50M", "50M - 200M", "Sin límite"])
            certs = st.multiselect("8. Atributos especiales", ["Sello Mujer", "Cooperativa", "Proveedor Local", "Certificación ISO"])
            dolor = st.text_area("9. Mayor dificultad al postular")
            interes = st.text_input("10. Palabras clave (ej: Aseo, Consultoría)")

        if st.form_submit_button("Guardar y Comenzar Análisis"):
            if n and g:
                st.session_state.perfil = {
                    "nom": n, "giro": g, "tipo": p, "tam": t, 
                    "exp": exp, "reg": reg, "cap": cap, "certs": certs, 
                    "dolor": dolor, "keywords": interes
                }
                st.rerun()
            else:
                st.error("Nombre y Giro son obligatorios.")
    st.stop()

# --- 5. LÓGICA DE API ---
def call_api(path, params):
    url = f"https://api.mercadopublico.cl/servicios/v1/Publico/{path}"
    params["ticket"] = MP_TICKET
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
        
        with st.spinner("Conectando con Mercado Público..."):
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
                    <h4 style="margin:10px 0; color:#F8FAFC !important;">{lic['Nombre']}</h4>
                    <p style="font-size:13px; color:#94A3B8 !important;">ID: {lic['CodigoExterno']}<br><b>{lic['NombreOrganismo']}</b></p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Analizar Viabilidad", key=lic['CodigoExterno']):
                    st.session_state.focus = lic

with c_analisis:
    if 'focus' in st.session_state:
        item = st.session_state.focus
        st.subheader("Asisteme")
        
        with st.status("Analizando perfil y normativa...", expanded=True):
            # Instrucción personalizada para Persona Natural vs Jurídica
            doc_extra = "Documentos de identidad y carpeta tributaria de persona natural" if st.session_state.perfil['tipo'] == "Persona Natural" else "Escrituras y poderes legales de la sociedad"
            
            prompt = f"""
            Actúa como consultor experto en licitaciones Mercado Público Chile.
            PERFIL: {st.session_state.perfil}
            LICITACIÓN: {item}
            
            Analiza con tono humano y directo:
            1. **Factibilidad:** Siendo {st.session_state.perfil['tipo']}, ¿es recomendable este negocio?
            2. **Documentación Crítica:** Recordando que es {st.session_state.perfil['tipo']}, indica que {doc_extra} debe preparar.
            3. **Puntos de Dolor:** Sugerencia para superar su dificultad: '{st.session_state.perfil['dolor']}'.
            4. **Probabilidad de éxito:** Del 1 al 100 basado en su experiencia de {st.session_state.perfil['exp']} años.
            """
            st.markdown(model.generate_content(prompt).text)
            
        if st.button("Cerrar Análisis"):
            del st.session_state.focus
            st.rerun()
