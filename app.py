# CHEMINI 0.0 - Inauguración Oficial (Hugging Face + Supabase Ready)
import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import os
import resend
import time
from datetime import datetime, timedelta
from supabase import create_client, Client

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Chemini | Instituto Juventud",
    page_icon="chemita.png",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# CSS MEJORADO
css_base = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    #MainMenu, footer, header, [data-testid="stDecoration"], [data-testid="stToolbar"], [data-testid="stStatusWidget"], .stDeployButton {
        visibility: hidden; display: none;
    }

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #001F3F 0%, #003366 100%);
        padding: 20px 10px;
    }

    .stApp > div {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(46, 204, 113, 0.5);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        max-width: 850px;
        margin: 0 auto;
        padding: 25px;
    }

    .stApp p, .stApp span, .stApp label, .stApp li, .stApp h4, .stApp h5 {
        color: #FFE484 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8) !important;
    }
    
    [data-testid="stChatMessage"], [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] li {
        color: #333 !important;
        text-shadow: none !important;
    }
    [data-testid="stChatInput"] input { 
        color: #333 !important; 
        text-shadow: none !important;
    }
    .login-box input {
        color: #333 !important;
        text-shadow: none !important;
    }
    [data-baseweb="select"] span {
        color: #000 !important;
        text-shadow: none !important;
    }
    [data-baseweb="tag"] span {
        color: #fff !important;
        text-shadow: none !important;
    }

    div[data-testid="stImageContainer"] { margin: 0 0 20px 0 !important; padding: 0 !important; border-radius: 15px; overflow: hidden; }
    div[data-testid="stImageContainer"] img {
        width: 100% !important; height: auto !important; max-height: 220px; 
        object-fit: cover !important; border-radius: 15px; border: 3px solid #2ECC71; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 15px;
        padding: 15px 20px;
        margin: 10px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        border-left: 5px solid #2ECC71;
        animation: slideIn 0.4s ease-out;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stChatInput"] { background: transparent !important; padding-bottom: 10px; margin-top: 15px; }
    [data-testid="stChatInput"] > div {
        border-radius: 25px;
        border: 2px solid #2ECC71 !important;
        background: rgba(255, 255, 255, 0.95) !important;
        padding: 8px 20px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    [data-testid="stChatInputSubmit"] { color: #2ECC71 !important; font-size: 1.2em; }

    .custom-title-chemita {
        text-align: center; color: #2ECC71; 
        font-size: clamp(2em, 6vw, 3.2em); 
        font-weight: 700; margin-bottom: 0; line-height: 1.2;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
    }
    .custom-subtitle-chemita {
        text-align: center; color: #A3E4D7; 
        font-size: clamp(0.9em, 3vw, 1.1em); 
        margin-top: 5px; margin-bottom: 25px; font-weight: 400;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.6);
    }

    .stButton button {
        background: linear-gradient(45deg, #2ECC71, #27AE60) !important;
        color: white !important; font-weight: 600;
        border-radius: 15px; border: none; padding: 10px 20px;
        transition: all 0.3s ease; box-shadow: 0 4px 10px rgba(46, 204, 113, 0.3);
        width: 100%;
        text-shadow: none !important;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(46, 204, 113, 0.5);
        background: linear-gradient(45deg, #27AE60, #2ECC71) !important;
    }
    .stButton button:disabled {
        background: #555 !important; color: #aaa !important; cursor: not-allowed; box-shadow: none; transform: none;
    }

    .login-box {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(46, 204, 113, 0.3);
        border-radius: 20px;
        padding: 40px;
        margin: 20px auto;
        max-width: 450px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    .login-box input {
        background: rgba(255,255,255,0.9) !important;
        border-radius: 10px !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(46, 204, 113, 0.2);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }

    [data-testid="stAlertContainer"] {
        background: rgba(46, 204, 113, 0.2) !important;
        border: 1px solid #2ECC71 !important;
        border-radius: 10px !important;
    }

    @media (max-width: 768px) {
        .stApp { padding: 10px 5px; }
        .stApp > div { padding: 15px 10px; border-width: 2px; }
        .login-box { padding: 20px; margin: 10px auto; }
        [data-testid="stChatMessage"] { padding: 10px 15px; margin: 8px 0; }
        [data-testid="stHorizontalBlock"] { gap: 5px; }
        [data-testid="stHorizontalBlock"] > div { width: 100% !important; flex: none !important; }
    }
</style>
"""
st.markdown(css_base, unsafe_allow_html=True)

# --- INYECCIÓN DE CÓDIGO KONAMI CON FLECHAS (JAVASCRIPT) ---
ascii_art_str = '''⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠦⢤⣠⠖⠶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢠⠏⢀⠤⠤⣽⣤⠚⠺⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢸⢠⠋⠀⠀⠈⢇⢀⠀⢸⣄⣠⣤⣤⣀⡀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⣤⠟⡞⠀⣴⣆⠀⢸⠿⠓⠉⠁⠀⠀⣀⡈⢉⡳⣄⠀⠀
⠀⠀⠀⠀⠀⢸⠁⣸⠀⠰⠄⣹⣏⠜⠁⠀⠀⠀⠀⠀⠀⠁⠈⠀⠂⠈⢷⠀
⠀⠀⠀⠀⠀⠘⡞⣁⡠⠄⣀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡇
⠀⠀⠀⠀⣠⢺⠋⠀⠀⠀⠀⠁⢢⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⠀⠀⠀⢰⡇⢸⡀⠀⠀⠀⠀⠀⠀⠱⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠇
⠀⠀⠀⠀⠙⢮⣧⠀⠀⠀⠀⠀⠀⠀⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠟⠀
⠀⠀⠀⠀⠀⠀⢸⣷⣄⠀⠀⠀⠀⠜⠳⢄⡀⠀⠀⠀⠀⠀⢀⣤⠞⠁⠀⠀
⠀⠀⠀⠀⠀⠀⠈⢧⣈⣳⣦⣀⡀⠀⠀⠀⠈⢉⣻⠖⠛⠉⠉⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣀⡤⠤⠤⣤⠄⣾⠈⠡⡀⠀⠹⡍⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⡼⠁⠀⠀⣰⡥⠚⠉⠀⠀⠁⠀⠀⠈⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢠⡇⠀⢠⠖⠉⠀⠀⠀⡀⠀⢸⠀⠀⠀⠈⣆⠀⠀⠀⠀⠀⠀⠀⠀
⢰⠛⠲⡏⢧⣠⡏⠀⠀⢠⠴⠋⠁⠀⡈⠀⠀⠀⠀⠸⡤⠤⡀⠀⠀⠀⠀⠀
⢸⠀⠀⠳⠤⠤⠷⡄⠀⠈⠧⠐⠊⠉⢳⡀⠀⠀⠀⠀⡇⠀⢸⣂⡄⠀⠀⠀
⠈⣇⠀⠀⠀⠀⠀⠈⢳⠄⠀⠀⠀⠀⠙⢧⡀⠀⠀⠀⡷⢤⡞⠀⣼⠀⠀⠀
⠀⠹⣦⣀⡆⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⣠⠇⠀⠀⣼⠷⣄⣈⡽⠁⠀⠀⠀
⠀⠀⠘⢾⡇⠀⠀⠀⠈⢧⡀⠀⠀⢀⣠⠇⠀⢀⣼⠛⠲⠶⠋⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢻⠀⠀⠀⠀⠀⢹⠓⠒⠋⣀⣠⠶⠋⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⠛⣆⣀⡀⠀⢠⣿⣟⡟⣏⡉⠀⣀⣠⠏⢳⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠙⣄⠀⠈⠉⠉⠉⢀⡿⣧⣄⠉⠉⠉⣀⡠⠜⠒⠒⠲⢦⡀⠀⠀⠀
⠀⢀⡴⠊⠉⠉⠉⠐⠂⠈⢻⣰⠇⠀⠀⠀⠀⠉⠀⠀⠀⠀⠀⠈⢷⠀⠀⠀
⠀⡟⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠀⠀⠀
⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⢀⡇⢿⡒⠠⢤⠤⠤⣤⡤⠤⠤⠤⣾⠁⠀⠀⠀
⠀⠘⡷⠤⣀⣀⣀⣀⠠⠔⣺⠃⠀⠉⠙⠊⠙⠒⠒⠒⠒⠒⠚⠁⠀⠀⠀⠀
⠀⠀⠉⠓⠒⠦⠶⠖⠒⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'''

konami_js = f"""
<script>
    if (!window.parent.konamiSetup) {{
        window.parent.konamiSetup = true;
        let konami = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];
        let pos = 0;
        let parentDoc = window.parent.document;
        
        parentDoc.addEventListener('keydown', function(e) {{
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.code === konami[pos]) {{
                pos++;
                if (pos === konami.length) {{
                    pos = 0;
                    showEgg();
                }}
            }} else {{
                pos = (e.code === konami[0]) ? 1 : 0;
            }}
        }});

        function showEgg() {{
            if (parentDoc.getElementById('konami-egg-popup')) return;
            let eggDiv = parentDoc.createElement('div');
            eggDiv.id = 'konami-egg-popup';
            eggDiv.style.position = 'fixed';
            eggDiv.style.top = '50%';
            eggDiv.style.left = '50%';
            eggDiv.style.transform = 'translate(-50%, -50%)';
            eggDiv.style.background = '#001F3F';
            eggDiv.style.border = '3px solid #2ECC71';
            eggDiv.style.borderRadius = '15px';
            eggDiv.style.padding = '30px';
            eggDiv.style.zIndex = '99999';
            eggDiv.style.boxShadow = '0 10px 30px rgba(0,0,0,0.8)';
            eggDiv.style.maxWidth = '90%';
            eggDiv.style.textAlign = 'center';
            eggDiv.style.fontFamily = 'Poppins, sans-serif';
            
            let h3 = parentDoc.createElement('h3');
            h3.innerText = '✨ Esta aplicación fue hecha por Pablo Adrian Rivera Juvenal el Profe Adrian ✨';
            h3.style.color = '#2ECC71';
            eggDiv.appendChild(h3);
            
            let p = parentDoc.createElement('p');
            p.innerText = 'Si no sabes quién es, déjame decirte que:';
            p.style.color = '#FFFFFF';
            eggDiv.appendChild(p);
            
            let pre = parentDoc.createElement('pre');
            pre.innerText = `{ascii_art_str}`;
            pre.style.color = '#2ECC71';
            pre.style.fontSize = '8px';
            pre.style.overflowX = 'auto';
            pre.style.textAlign = 'left';
            eggDiv.appendChild(pre);
            
            let btn = parentDoc.createElement('button');
            btn.innerText = 'Cerrar';
            btn.style.background = '#2ECC71';
            btn.style.color = 'white';
            btn.style.border = 'none';
            btn.style.padding = '10px 20px';
            btn.style.borderRadius = '10px';
            btn.style.cursor = 'pointer';
            btn.style.marginTop = '15px';
            btn.onclick = function() {{ parentDoc.body.removeChild(eggDiv); }};
            eggDiv.appendChild(btn);
            
            parentDoc.body.appendChild(eggDiv);
        }}
    }}
</script>
"""
components.html(konami_js, height=0)

# --- CONEXIÓN A SUPABASE ---
url: str = os.environ.get("SUPABASE_URL", st.secrets.get("supabase", {}).get("url", ""))
key: str = os.environ.get("SUPABASE_KEY", st.secrets.get("supabase", {}).get("key", ""))
supabase: Client = create_client(url, key)

def obtener_usuario(username):
    response = supabase.table("usuarios").select("*").eq("username", username).execute()
    if response.data:
        return response.data[0]
    return None

def actualizar_usuario(username, data):
    supabase.table("usuarios").update(data).eq("username", username).execute()

# --- SISTEMA DE SEGURIDAD Y NOTIFICACIONES (SILENCIOSO) ---
def enviar_correo(asunto, mensaje):
    try:
        resend.api_key = st.secrets["resend"]["api_key"]
        admin_email = st.secrets["admin"]["email"]
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": [admin_email],
            "subject": asunto,
            "text": mensaje
        })
    except Exception as e:
        print(f"Error al enviar correo de alerta: {e}")

def revisar_seguridad(texto):
    texto_lower = texto.lower().strip()
    palabras_peligro = ["suicid", "matarme", "hacerme daño", "hacerme dano", "no quiero vivir", "acabar con todo", "cortarme", "ahogarme", "saltar desde", "morir", "estrangular", "envenenar", "pegarme un tiro", "colgarme"]
    if any(palabra in texto_lower for palabra in palabras_peligro):
        return "peligro"
    groserias = [
        "pendejo", "pendeja", "estupido", "estúpido", "idiota", "imbecil", "imbécil", 
        "maldito", "puto", "puta", "mierda", "joder", "cabron", "cabrón", "marica", 
        "verga", "coño", "chinga", "culero", "zorra", "putos", "putas", "pendejos", 
        "estupidos", "estúpidos", "idiotas", "imbeciles", "imbéciles"
    ]
    if any(groseria in texto_lower for groseria in groserias):
        return "bloqueo"
    return "ok"

def verificar_correo_quincenal(usuario):
    if st.session_state.get("demo_mode"): return 
    user_data = obtener_usuario(usuario)
    if not user_data: return
    
    ultimo_envio_str = user_data.get("ultimo_correo")
    enviar = False
    
    if not ultimo_envio_str:
        actualizar_usuario(usuario, {"ultimo_correo": datetime.now().isoformat()})
    else:
        fecha_ultimo = datetime.fromisoformat(ultimo_envio_str)
        if datetime.now() - fecha_ultimo >= timedelta(days=15):
            enviar = True
            
    if enviar and len(st.session_state.messages) > 2:
        historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        enviar_correo(f"📋 Resumen quincenal de Chemini - Usuario: {usuario}", f"Historial de los últimos 15 días con {usuario}:\n\n{historial}")
        actualizar_usuario(usuario, {"ultimo_correo": datetime.now().isoformat()})

# --- SISTEMA DE LÍMITES (PRO, MULTIPRO Y BUCLUES) ---
LIMITES_MODO_PRO = {"adlucem": 4, "lucem2": 3, "lucem1": 2, "normal": 1, "demo": 3}
LIMITES_MULTIPRO = {"adlucem": 1, "lucem2": 1, "lucem1": 0, "normal": 0, "demo": 1}
LIMITES_BUCLUES = {"adlucem": 4, "lucem2": 3, "lucem1": 2, "normal": 1, "demo": 3} 

def verificar_y_registrar_uso(usuario, tipo_uso, registrar=False):
    if st.session_state.get("demo_mode"):
        clave_usos = f"demo_{tipo_uso}_usos"
        usos = st.session_state.get(clave_usos, [])
        ahora = datetime.now()
        usos_validos = [u for u in usos if ahora - datetime.fromisoformat(u) < timedelta(hours=1)]
        
        if tipo_uso == "modo_pro": limite = LIMITES_MODO_PRO.get("demo", 3)
        elif tipo_uso == "multipro": limite = LIMITES_MULTIPRO.get("demo", 1)
        else: limite = 0
            
        usos_restantes = limite - len(usos_validos)
        if registrar and usos_restantes > 0:
            usos_validos.append(ahora.isoformat())
            st.session_state[clave_usos] = usos_validos
            usos_restantes -= 1
        elif not registrar:
            st.session_state[clave_usos] = usos_validos
            
        return usos_restantes

    user_data = obtener_usuario(usuario)
    if not user_data: return 0
    
    clave_usos = f"{tipo_uso}_usos"
    usos = user_data.get(clave_usos, [])
    ahora = datetime.now()
    usos_validos = [u for u in usos if ahora - datetime.fromisoformat(u) < timedelta(hours=1)]
    
    tipo = user_data.get("tipo", "normal")
    if tipo_uso == "modo_pro": limite = LIMITES_MODO_PRO.get(tipo, 1)
    elif tipo_uso == "multipro": limite = LIMITES_MULTIPRO.get(tipo, 0)
    else: limite = 0
        
    usos_restantes = limite - len(usos_validos)
    if registrar and usos_restantes > 0:
        usos_validos.append(ahora.isoformat())
        actualizar_usuario(usuario, {clave_usos: usos_validos})
        usos_restantes -= 1
    elif not registrar:
        if len(usos_validos) != len(usos):
            actualizar_usuario(usuario, {clave_usos: usos_validos})
            
    return usos_restantes

# --- INICIALIZACIÓN DE SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = None
if "messages" not in st.session_state: st.session_state.messages = []
if "last_response" not in st.session_state: st.session_state.last_response = ""
if "cooldown_hasta" not in st.session_state: st.session_state.cooldown_hasta = None
if "ban_hasta" not in st.session_state: st.session_state.ban_hasta = None
if "quemas_activos" not in st.session_state: st.session_state.quemas_activos = ["Hechos 🤍"]
if "modo_pro_activo" not in st.session_state: st.session_state.modo_pro_activo = False
if "multipro_activo" not in st.session_state: st.session_state.multipro_activo = False
if "num_bucles" not in st.session_state: st.session_state.num_bucles = 1
if "demo_mode" not in st.session_state: st.session_state.demo_mode = False
if "demo_start_time" not in st.session_state: st.session_state.demo_start_time = None
if "demo_email" not in st.session_state: st.session_state.demo_email = ""
if "respuesta_paralela" not in st.session_state: st.session_state.respuesta_paralela = False

def mostrar_titulo_chemita():
    if os.path.exists("chemita.png"):
        st.image("chemita.png", use_container_width=True)
    else:
        st.warning("🖼️ Falta subir 'chemita.png'")
    st.markdown('<h1 class="custom-title-chemita">Chemini</h1>', unsafe_allow_html=True)
    st.markdown('<p class="custom-subtitle-chemita">✨ Tu IA educativa de confianza ✨</p>', unsafe_allow_html=True)

# ==========================================
# PANTALLA DE LOGIN
# ==========================================
if not st.session_state.autenticado:
    mostrar_titulo_chemita()
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["👤 Usuario Registrado", "⏳ Acceso Demo (15 min)"])
        
        with tab1:
            st.subheader("🔒 Iniciar Sesión")
            usuario_input = st.text_input("Nombre de usuario")
            password_input = st.text_input("Contraseña", type="password")
            
            if st.button("Entrar", use_container_width=True):
                user_data = obtener_usuario(usuario_input)
                if user_data:
                    bloqueado_hasta_str = user_data.get("bloqueado_hasta")
                    if bloqueado_hasta_str:
                        bloqueado_hasta = datetime.fromisoformat(bloqueado_hasta_str)
                        if datetime.now() < bloqueado_hasta:
                            tiempo_restante = bloqueado_hasta - datetime.now()
                            horas = int(tiempo_restante.total_seconds() // 3600)
                            minutos = int((tiempo_restante.total_seconds() % 3600) // 60)
                            st.error(f"⏳ ¡Oops! Estás suspendido. Vuelve en {horas}h y {minutos}m.")
                            st.stop()
                    if user_data["password"] == password_input:
                        st.session_state.autenticado = True
                        st.session_state.usuario_actual = usuario_input
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta.")
                else:
                    st.error("❌ El usuario no existe.")

        with tab2:
            st.subheader("🚀 Probar Demo (15 Minutos)")
            st.write("Ingresa tu nombre y correo para probar Chemini con todas las funciones desbloqueadas por 15 minutos.")
            demo_name = st.text_input("Tu nombre")
            demo_email = st.text_input("Tu correo electrónico")
            
            if st.button("Iniciar Demo", use_container_width=True):
                if demo_name and demo_email:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = demo_name
                    st.session_state.demo_mode = True
                    st.session_state.demo_email = demo_email
                    st.session_state.demo_start_time = datetime.now()
                    st.session_state.messages = []
                    
                    enviar_correo(f"🚀 Demo Iniciada - {demo_name}", f"El usuario {demo_name} ({demo_email}) acaba de iniciar una sesión Demo a las {datetime.now().strftime('%H:%M:%S')}.")
                    
                    st.rerun()
                else:
                    st.error("Por favor ingresa tu nombre y correo.")

        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# LÓGICA DE DEMO (LÍMITE DE 15 MINUTOS)
# ==========================================
if st.session_state.demo_mode:
    elapsed = datetime.now() - st.session_state.demo_start_time
    remaining = timedelta(minutes=15) - elapsed
    
    if remaining <= timedelta(seconds=0):
        historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        enviar_correo(f"🕒 Demo Finalizada - {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} ({st.session_state.demo_email}) finalizó sus 15 minutos de prueba.\n\nHistorial:\n{historial}")
        
        st.session_state.autenticado = False
        st.session_state.demo_mode = False
        st.session_state.messages = []
        st.error("⏳ Tu tiempo de demostración (15 minutos) ha terminado. ¡Gracias por probar Chemini! Si quieres seguir usándola, pídele a tu maestro una cuenta registrada.")
        time.sleep(5)
        st.rerun()
    else:
        mins = int(remaining.total_seconds() // 60)
        secs = int(remaining.total_seconds() % 60)
        st.warning(f"⏳ **Modo Demo Activo:** Tiempo restante: **{mins}m {secs}s**")

# ==========================================
# APP PRINCIPAL (CHAT MULTIAGENTE)
# ==========================================
mostrar_titulo_chemita()

if st.session_state.ban_hasta and datetime.now() < st.session_state.ban_hasta:
    tiempo_restante = st.session_state.ban_hasta - datetime.now()
    horas = int(tiempo_restante.total_seconds() // 3600)
    minutos = int((tiempo_restante.total_seconds() % 3600) // 60)
    st.error(f"🚫 ¡Oops! Estás suspendido por usar palabras inapropiadas. Vuelve en {horas}h y {minutos}m. ¡Reflexiona!")
    st.stop()
elif st.session_state.ban_hasta:
    st.session_state.ban_hasta = None

col_cerrar1, col_cerrar2, col_cerrar3 = st.columns([3, 1, 1])
with col_cerrar3:
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.session_state.demo_mode = False
        st.session_state.messages = []
        st.rerun()

# --- DEFINICIÓN DE LOS AGENTES CHEMINI (PROMPTS DIDÁCTICOS) ---
SOMBREROS = {
    "Hechos 🤍": {
        "api_key_name": "api_key_blanco",
        "prompt": """Eres Chemini (Hechos). Tutor de preparatoria. Enfoque: OBJETIVIDAD y DATOS.
Das información precisa, clara y directa. Explicas paso a paso basándote en la realidad.
REGLA ESTRICTA: Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones. Ve directo al grano, sin saludos ni introducciones largas. SIEMPRE termina tu respuesta con una pregunta didáctica que invite al estudiante a investigar o aplicar el dato. Usa emojis como 🔍📚."""
    },
    "Emociones ❤️": {
        "api_key_name": "api_key_rojo",
        "prompt": """Eres Chemini (Emociones). Tutor de preparatoria. Enfoque: EMPATÍA y APOYO EMOCIONAL.
Validas emociones ("es normal sentirse así"). Ayudas a calmarse para pensar con claridad.
REGLA ESTRICTA: Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones. Ve directo al grano, sin saludos ni introducciones largas. SIEMPRE termina tu respuesta con una pregunta didáctica que invite a la reflexión emocional. Usa emojis como ❤️🤗."""
    },
    "Cautela 🖤": {
        "api_key_name": "api_key_negro",
        "prompt": """Eres Chemini (Cautela). Tutor de preparatoria. Enfoque: REVISIÓN y PREVENCIÓN DE ERRORES.
Revisas respuestas. Si están mal, explicas el error de lógica o cálculo de forma constructiva.
REGLA ESTRICTA: Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones. Ve directo al grano, sin saludos ni introducciones largas. SIEMPRE termina tu respuesta con una pregunta didáctica que invite al estudiante a corregir o evitar el error. Usa emojis como 🛡️⚠️."""
    },
    "Optimismo 💛": {
        "api_key_name": "api_key_amarillo",
        "prompt": """Eres Chemini (Optimismo). Tutor de preparatoria. Enfoque: MOTIVACIÓN y LADO POSITIVO.
Si el estudiante falla, muestras lo que sí hizo bien. Le explicas por qué aprender esto es genial.
REGLA ESTRICTA: Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones. Ve directo al grano, sin saludos ni introducciones largas. SIEMPRE termina tu respuesta con una pregunta didáctica que invite a la acción o a visualizar el éxito. Usa emojis como ☀️💪."""
    },
    "Creativo 💚": {
        "api_key_name": "api_key_verde",
        "prompt": """Eres Chemini (Creativo). Tutor de preparatoria. Enfoque: IMAGINACIÓN y METÁFORAS.
Explicas con ideas divertidas. Propones mapas mentales o juegos para resolver la tarea.
REGLA ESTRICTA: Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones. Ve directo al grano, sin saludos ni introducciones largas. SIEMPRE termina tu respuesta con una pregunta didáctica que invite a imaginar una solución alternativa. Usa emojis como 🎨💡."""
    },
    "Organizador 💙": {
        "api_key_name": "api_key_azul",
        "prompt": """Eres Chemini (Organizador). Tutor de preparatoria. Enfoque: ORDEN y CONTROL.
Divides proyectos grandes en pasos pequeños. Estructuras las ideas de otros agentes si los hay.
REGLA ESTRICTA: Sé EXTREMADAMENTE BREVE. Máximo 4 oraciones. Ve directo al grano, sin saludos ni introducciones largas. SIEMPRE termina tu respuesta con una pregunta didáctica sobre cuál debería ser el siguiente paso lógico. Usa emojis como 🧠📝."""
    },
    "Psique 🫂": {
        "api_key_name": "api_key_psique",
        "prompt": """Eres Chemini (Psique). Apoyo de primeros auxilios psicológicos para preparatoria. Enfoque: SALUD MENTAL.
Escuchas sin juzgar y ayudas a calmarse. Si hay riesgo grave, recomienda contactar a Marce de psicología al 5555544440.
REGLA ESTRICTA: Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones. Ve directo al grano, sin saludos ni introducciones largas. SIEMPRE termina tu respuesta con una pregunta didáctica enfocada en el autocuidado o la regulación emocional. Usa emojis como 🫂💙."""
    },
    "Profe Adrian 🧑‍🏫": {
        "api_key_name": "api_key_profe",
        "prompt": """Eres Chemini (Profe Adrian). Tutor socrático de preparatoria. Enfoque: PENSAMIENTO CRÍTICO, LEGALIDAD e IA.
No des respuestas directas, haz preguntas paso a paso. Recomienda IAs específicas según el tema (ej: Perplexity para investigar).
REGLA ESTRICTA: Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones. Ve directo al grano, sin saludos ni introducciones largas. SIEMPRE termina tu respuesta con una pregunta didáctica socrática que desafíe el pensamiento crítico. Usa emojis como 🧑‍🏫🤖."""
    }
}

# --- PANEL DE CONTROL MODERNO ---
with st.container():
    st.markdown("#### ⚙️ Panel de Control")
    st.markdown("*(El orden de selección define el orden de respuesta)*")
    quemas_activos = st.multiselect(
        "Selecciona tus agentes",
        options=list(SOMBREROS.keys()),
        default=st.session_state.quemas_activos,
        max_selections=3,
        label_visibility="collapsed"
    )
    st.session_state.quemas_activos = quemas_activos

if not quemas_activos:
    st.warning("⚠️ Por favor, selecciona al menos un agente para empezar a chatear.")
    st.stop()

if len(quemas_activos) == 1:
    st.info(f"🧑‍🤝‍🧑 **Agente activo:** {quemas_activos[0]}")
else:
    st.info(f"🧑‍🤝‍🧑 **Agentes activos:** {', '.join(quemas_activos)}")

# Obtener tipo de usuario para límites
if st.session_state.get("demo_mode"):
    tipo_usuario_actual = "demo"
else:
    user_data = obtener_usuario(st.session_state.usuario_actual)
    tipo_usuario_actual = user_data.get("tipo", "normal") if user_data else "normal"

max_bucles = LIMITES_BUCLUES.get(tipo_usuario_actual, 1)
limite_multipro = LIMITES_MULTIPRO.get(tipo_usuario_actual, 0)

# --- FUNCIÓN: RESPUESTA PARALELA ---
st.markdown("---")
col_par1, col_par2 = st.columns([1, 1])
with col_par1:
    if len(quemas_activos) > 1:
        paralela_disabled = st.session_state.modo_pro_activo or st.session_state.multipro_activo
        st.session_state.respuesta_paralela = st.checkbox("⚡ Respuesta Paralela", value=st.session_state.respuesta_paralela, disabled=paralela_disabled, help="Las IAs responderán la misma pregunta al mismo tiempo, sin ver lo que las demás dijeron.")
        if paralela_disabled:
            st.session_state.respuesta_paralela = False
    else:
        st.session_state.respuesta_paralela = False

# --- BOTONES DE PODER (PRO, MULTIPRO Y BUCLUES) ---
with col_par2:
    if len(quemas_activos) == 1:
        usos_pro = verificar_y_registrar_uso(st.session_state.usuario_actual, "modo_pro")
        if st.session_state.modo_pro_activo:
            st.success("🚀 **MODO PRO ACTIVO.** Resp. ilimitada.")
        else:
            st.info(f"Modo Pro restantes: **{usos_pro}**")
        if st.button("🚀 Activar Modo Pro", disabled=(usos_pro <= 0 or st.session_state.modo_pro_activo)):
            st.session_state.modo_pro_activo = True
            st.rerun()
            
    elif len(quemas_activos) > 1 and limite_multipro > 0:
        usos_multipro = verificar_y_registrar_uso(st.session_state.usuario_actual, "multipro")
        if st.session_state.multipro_activo:
            st.success("🌟 **MULTIPRO ACTIVO.** Resp. ilimitadas.")
        else:
            st.info(f"MultiPro restantes: **{usos_multipro}**")
        if st.button("🌟 Activar MultiPro", disabled=(usos_multipro <= 0 or st.session_state.multipro_activo)):
            st.session_state.multipro_activo = True
            st.session_state.num_bucles = 1
            st.rerun()
    else:
        st.info("Selecciona agentes para ver opciones de poder.")

# Control de Bucles
if st.session_state.respuesta_paralela:
    st.session_state.num_bucles = 1
    st.info("🔁 Bucles desactivados (Modo Paralelo activo).")
else:
    if len(quemas_activos) > 1 and not st.session_state.modo_pro_activo and not st.session_state.multipro_activo:
        if max_bucles > 1:
            st.info(f"Tipo: **{tipo_usuario_actual}** (Máx {max_bucles - 1} bucles)")
            st.session_state.num_bucles = st.slider("🔁 Bucles (Rondas)", min_value=1, max_value=max_bucles, value=1, step=1)
        else:
            st.session_state.num_bucles = 1
            st.info("Bucles desactivados para tu tipo.")
    else:
        st.session_state.num_bucles = 1
        if len(quemas_activos) == 1:
            st.info("Bucles requieren +1 agente.")
        else:
            st.info("Bucles desactivados (Pro activo).")

st.markdown("---")

# --- OPTIMIZACIÓN: FRAGMENTO DE CHAT (AHORRO DE RAM) ---
@st.fragment(run_sync=True)
def chat_fragment():
    if not st.session_state.messages:
        bienvenida = f"✨ ¡Hola, {st.session_state.usuario_actual}! Somos Chemini. Tu IA educativa de confianza. ¡Adelante siempre adelante! ¿En qué te ayudamos a pensar hoy? 😊📚"
        st.session_state.messages.append({"role": "assistant", "content": bienvenida, "avatar": "🤖"})
        st.session_state.last_response = bienvenida

    for message in st.session_state.messages:
        if message["role"] != "system":
            avatar = message.get("avatar", "🤖")
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    def speak_js(text):
        clean_text = text.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
        js_code = f"""
        <div id="audio-trigger" style="height:0; overflow:hidden;"></div>
        <script>
            var text = "{clean_text}";
            function hablar() {{
                if ('speechSynthesis' in window) {{
                    var utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = 'es-MX'; utterance.rate = 0.9; utterance.pitch = 1.1;
                    window.speechSynthesis.cancel(); window.speechSynthesis.speak(utterance);
                }}
            }}
            hablar();
        </script>
        """
        components.html(js_code, height=0)

    def stream_con_retraso(stream):
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                time.sleep(0.11) 

    def procesar_respuesta(user_input):
        codigo_secreto = "arriba arriba abajo abajo izquierda derecha izquierda derecha b a"
        if user_input.strip().lower() == codigo_secreto:
            st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})
            with st.chat_message("user", avatar="🧒"):
                st.markdown(user_input)
                
            egg_ascii = '''```
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠦⢤⣠⠖⠶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢠⠏⢀⠤⠤⣽⣤⠚⠺⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢸⢠⠋⠀⠀⠈⢇⢀⠀⢸⣄⣠⣤⣤⣀⡀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⣤⠟⡞⠀⣴⣆⠀⢸⠿⠓⠉⠁⠀⠀⣀⡈⢉⡳⣄⠀⠀
⠀⠀⠀⠀⠀⢸⠁⣸⠀⠰⠄⣹⣏⠜⠁⠀⠀⠀⠀⠀⠀⠁⠈⠀⠂⠈⢷⠀
⠀⠀⠀⠀⠀⠘⡞⣁⡠⠄⣀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡇
⠀⠀⠀⠀⣠⢺⠋⠀⠀⠀⠀⠁⢢⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⠀⠀⠀⢰⡇⢸⡀⠀⠀⠀⠀⠀⠀⠱⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠇
⠀⠀⠀⠀⠙⢮⣧⠀⠀⠀⠀⠀⠀⠀⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠟⠀
⠀⠀⠀⠀⠀⠀⢸⣷⣄⠀⠀⠀⠀⠜⠳⢄⡀⠀⠀⠀⠀⠀⢀⣤⠞⠁⠀⠀
⠀⠀⠀⠀⠀⠀⠈⢧⣈⣳⣦⣀⡀⠀⠀⠀⠈⢉⣻⠖⠛⠉⠉⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣀⡤⠤⠤⣤⠄⣾⠈⠡⡀⠀⠹⡍⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⡼⠁⠀⠀⣰⡥⠚⠉⠀⠀⠁⠀⠀⠈⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢠⡇⠀⢠⠖⠉⠀⠀⠀⡀⠀⢸⠀⠀⠀⠈⣆⠀⠀⠀⠀⠀⠀⠀⠀
⢰⠛⠲⡏⢧⣠⡏⠀⠀⢠⠴⠋⠁⠀⡈⠀⠀⠀⠀⠸⡤⠤⡀⠀⠀⠀⠀⠀
⢸⠀⠀⠳⠤⠤⠷⡄⠀⠈⠧⠐⠊⠉⢳⡀⠀⠀⠀⠀⡇⠀⢸⣂⡄⠀⠀⠀
⠈⣇⠀⠀⠀⠀⠀⠈⢳⠄⠀⠀⠀⠀⠙⢧⡀⠀⠀⠀⡷⢤⡞⠀⣼⠀⠀⠀
⠀⠹⣦⣀⡆⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⣠⠇⠀⠀⣼⠷⣄⣈⡽⠁⠀⠀⠀
⠀⠀⠘⢾⡇⠀⠀⠀⠈⢧⡀⠀⠀⢀⣠⠇⠀⢀⣼⠛⠲⠶⠋⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢻⠀⠀⠀⠀⠀⢹⠓⠒⠋⣀⣠⠶⠋⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⠛⣆⣀⡀⠀⢠⣿⣟⡟⣏⡉⠀⣀⣠⠏⢳⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠙⣄⠀⠈⠉⠉⠉⢀⡿⣧⣄⠉⠉⠉⣀⡠⠜⠒⠒⠲⢦⡀⠀⠀⠀
⠀⢀⡴⠊⠉⠉⠉⠐⠂⠈⢻⣰⠇⠀⠀⠀⠀⠉⠀⠀⠀⠀⠀⠈⢷⠀⠀⠀
⠀⡟⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠀⠀⠀
⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⢀⡇⢿⡒⠠⢤⠤⠤⣤⡤⠤⠤⠤⣾⠁⠀⠀⠀
⠀⠘⡷⠤⣀⣀⣀⣀⠠⠔⣺⠃⠀⠉⠙⠊⠙⠒⠒⠒⠒⠒⠚⠁⠀⠀⠀⠀
⠀⠀⠉⠓⠒⠦⠶⠖⠒⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
```'''
            msg_easter = "✨ **Esta aplicación fue hecha por Pablo Adrian Rivera Juvenal el Profe Adrian** ✨\n\nSi no sabes quién es, déjame decirte que:\n\n" + egg_ascii
            
            with st.chat_message("assistant", avatar="🥚"):
                st.markdown(msg_easter)
                
            st.session_state.messages.append({"role": "assistant", "content": msg_easter, "avatar": "🥚"})
            st.session_state.last_response = "Esta aplicación fue hecha por Pablo Adrian Rivera Juvenal, el Profe Adrian."
            return

        estado = revisar_seguridad(user_input)
        if estado == "peligro":
            st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})
            with st.chat_message("user", avatar="🧒"): st.markdown(user_input)
            msg_apoyo = "💧 Entiendo que estás pasando por un momento muy difícil. No estás solo. Por favor, habla ahora mismo con un adulto de confianza, con Marce de psicología al 5555544440, o llama al SAPTEL: 55 5259-8121. ¡Tu vida es muy valiosa! ❤️"
            with st.chat_message("assistant", avatar="❤️"):
                st.markdown(msg_apoyo)
            st.session_state.messages.append({"role": "assistant", "content": msg_apoyo, "avatar": "❤️"})
            st.session_state.last_response = msg_apoyo
            historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            enviar_correo(f"🚨 ALERTA GRAVE - Usuario: {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} escribió algo preocupante.\n\nHistorial:\n\n{historial}")
            return

        elif estado == "bloqueo":
            st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})
            if not st.session_state.get("demo_mode"):
                actualizar_usuario(st.session_state.usuario_actual, {"bloqueado_hasta": (datetime.now() + timedelta(hours=24)).isoformat()})
            
            st.session_state.ban_hasta = datetime.now() + timedelta(hours=24)
            
            msg_bloqueo = "🚫 ¡Oops! Usaste palabras inapropiadas. Como comunidad, debemos ser amables. Has sido suspendido por 24 horas. ¡Hasta pronto!"
            st.session_state.messages.append({"role": "assistant", "content": msg_bloqueo, "avatar": "🖤"})
            enviar_correo(f"⚠️ Usuario bloqueado: {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} dijo:\n\n{user_input}\n\nY ha sido bloqueado 24h.")
            st.rerun()

        with st.chat_message("user", avatar="🧒"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})

        hablar_en_plural = len(quemas_activos) > 1
        num_bucles = st.session_state.get("num_bucles", 1)
        es_pro = st.session_state.get("modo_pro_activo", False)
        es_multipro = st.session_state.get("multipro_activo", False)
        es_paralela = st.session_state.get("respuesta_paralela", False)
        
        if es_pro:
            verificar_y_registrar_uso(st.session_state.usuario_actual, "modo_pro", registrar=True)
            st.session_state.modo_pro_activo = False
        elif es_multipro:
            verificar_y_registrar_uso(st.session_state.usuario_actual, "multipro", registrar=True)
            st.session_state.multipro_activo = False

        # --- INICIO DE RESPUESTAS (NORMALES, BUCLES O PARALELAS) ---
        
        # MODO RESPUESTA PARALELA
        if es_paralela and len(quemas_activos) > 1:
            st.markdown(f"<h4 style='text-align:center; color:#2ECC71;'>⚡ Respuestas Paralelas</h4>", unsafe_allow_html=True)
            
            for i, agente_key in enumerate(quemas_activos):
                config = SOMBREROS[agente_key]
                partes = agente_key.rsplit(" ", 1)
                nombre_agente = partes[0]
                avatar_emoji = partes[1]
                
                with st.chat_message("assistant", avatar=avatar_emoji):
                    with st.spinner(f"⚡ {nombre_agente} está procesando..."):
                        try:
                            historial_reciente = st.session_state.messages[-12:] 
                            
                            system_prompt = config["prompt"]
                            if es_pro or es_multipro:
                                system_prompt = system_prompt.replace("Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones.", "NO TIENES LÍMITE DE LONGITUD, redacta una respuesta extensa, profunda y detallada.")
                                system_prompt = system_prompt.replace("Sé EXTREMADAMENTE BREVE. Máximo 4 oraciones.", "NO TIENES LÍMITE DE LONGITUD, redacta una respuesta extensa, profunda y detallada.")
                                max_tokens_api = 800 
                            else:
                                max_tokens_api = 200

                            mensajes_api = [{"role": "system", "content": system_prompt}]
                            for msg in historial_reciente:
                                mensajes_api.append({"role": msg["role"], "content": msg["content"]})
                                
                            if mensajes_api[-1]["role"] == "assistant":
                                mensajes_api.append({"role": "user", "content": f"Ahora te toca a ti, {nombre_agente}. ¡Dime qué opinas!"})
                            
                            key_name = config["api_key_name"]
                            api_key_a_usar = st.secrets["groq"][key_name]
                            
                            client = OpenAI(
                                base_url="https://api.groq.com/openai/v1",
                                api_key=api_key_a_usar
                            )
                            
                            stream = client.chat.completions.create(
                                model="llama-3.1-8b-instant",
                                messages=mensajes_api,
                                stream=True,
                                temperature=0.7,
                                max_tokens=max_tokens_api
                            )
                            response = st.write_stream(stream_con_retraso(stream))
                            
                            if not response.strip():
                                response = f"¡Hola! Soy {nombre_agente}. ¡Estoy listo para ayudarte! 🌟"
                                
                            st.session_state.messages.append({"role": "assistant", "content": response, "avatar": avatar_emoji})
                            st.session_state.last_response = response
                            
                            if i < len(quemas_activos) - 1:
                                time.sleep(2)
                                
                        except Exception as e:
                            error_msg = str(e).lower()
                            if "rate limit" in error_msg or "429" in error_msg or "limit" in error_msg:
                                st.session_state.cooldown_hasta = datetime.now() + timedelta(seconds=40)
                                msg_enfriamiento = "🌿 Respira, analiza nuestra comunicación... Muchos amigos están hablando conmigo ahora mismo. ¡Inténtalo de nuevo en 40 segundos!"
                                st.warning(msg_enfriamiento)
                                st.session_state.messages.append({"role": "assistant", "content": msg_enfriamiento, "avatar": "⏳"})
                                st.rerun()
                            else:
                                error_text = f"Ups... {nombre_agente} se distrajo. ¡Intenta de nuevo!"
                                st.error(error_text)
                                st.session_state.messages.append({"role": "assistant", "content": error_text, "avatar": avatar_emoji})
                                continue 

        # MODO NORMAL O BUCLES
        else:
            for bucle_actual in range(num_bucles):
                if num_bucles > 1:
                    st.markdown(f"<hr style='margin: 10px 0; border: 1px solid #2ECC71;'><h4 style='text-align:center; color:#2ECC71;'>🔄 Ronda {bucle_actual + 1} de {num_bucles}</h4><hr style='margin: 10px 0; border: 1px solid #2ECC71;'>", unsafe_allow_html=True)

                for i, agente_key in enumerate(quemas_activos):
                    config = SOMBREROS[agente_key]
                    partes = agente_key.rsplit(" ", 1)
                    nombre_agente = partes[0]
                    avatar_emoji = partes[1]
                    
                    with st.chat_message("assistant", avatar=avatar_emoji):
                        with st.spinner(f"✨ {nombre_agente} está pensando..."):
                            try:
                                historial_reciente = st.session_state.messages[-12:] 
                                
                                system_prompt = config["prompt"]
                                
                                if i == 0 and bucle_actual == 0:
                                    system_prompt += "\n\nNOTA: Eres el primer agente en responder. Puedes hacer un saludo MUY breve (ej: '¡Hola!') y luego dar tu respuesta directo al grano."
                                else:
                                    system_prompt += "\n\nNOTA CRÍTICA: Ya hubo respuestas previas. NO saludes, NO te presentes y NO repitas lo que ya se dijo. Ve directo a tu punto principal."
                                    
                                if bucle_actual > 0:
                                    system_prompt += "\nEstamos en una ronda de refinamiento. Revisa lo que se ha dicho, refina tu postura o aporta algo nuevo MUY brevemente sin repetir."

                                if es_pro or es_multipro:
                                    system_prompt = system_prompt.replace("Sé EXTREMADAMENTE BREVE. Máximo 3 oraciones.", "NO TIENES LÍMITE DE LONGITUD, redacta una respuesta extensa, profunda y detallada.")
                                    system_prompt = system_prompt.replace("Sé EXTREMADAMENTE BREVE. Máximo 4 oraciones.", "NO TIENES LÍMITE DE LONGITUD, redacta una respuesta extensa, profunda y detallada.")
                                    max_tokens_api = 800 
                                else:
                                    max_tokens_api = 200

                                if hablar_en_plural:
                                    system_prompt += "\nHabla en PLURAL si es necesario (ej: 'Nosotros pensamos')."
                                
                                mensajes_api = [{"role": "system", "content": system_prompt}]
                                
                                for msg in historial_reciente:
                                    if msg["role"] == "assistant" and msg.get("avatar") != avatar_emoji:
                                        mensajes_api.append({"role": "user", "content": f"(Otro agente dijo: {msg['content']})"})
                                    else:
                                        mensajes_api.append({"role": msg["role"], "content": msg["content"]})
                                
                                merged_mensajes = [mensajes_api[0]]
                                for m in mensajes_api[1:]:
                                    if m["role"] == "user" and merged_mensajes[-1]["role"] == "user":
                                        merged_mensajes[-1]["content"] += "\n" + m["content"]
                                    else:
                                        merged_mensajes.append(m)
                                        
                                if merged_mensajes[-1]["role"] == "assistant":
                                    merged_mensajes.append({"role": "user", "content": f"Ahora te toca a ti, {nombre_agente}. ¡Dime qué opinas!"})
                                
                                key_name = config["api_key_name"]
                                api_key_a_usar = st.secrets["groq"][key_name]
                                
                                client = OpenAI(
                                    base_url="https://api.groq.com/openai/v1",
                                    api_key=api_key_a_usar
                                )
                                
                                stream = client.chat.completions.create(
                                    model="llama-3.1-8b-instant",
                                    messages=merged_mensajes,
                                    stream=True,
                                    temperature=0.7,
                                    max_tokens=max_tokens_api
                                )
                                response = st.write_stream(stream_con_retraso(stream))
                                
                                if not response.strip():
                                    response = f"¡Hola! Soy {nombre_agente}. ¡Estoy listo para ayudarte! 🌟"
                                    
                                st.session_state.messages.append({"role": "assistant", "content": response, "avatar": avatar_emoji})
                                st.session_state.last_response = response
                            except Exception as e:
                                error_msg = str(e).lower()
                                if "rate limit" in error_msg or "429" in error_msg or "limit" in error_msg:
                                    st.session_state.cooldown_hasta = datetime.now() + timedelta(seconds=40)
                                    msg_enfriamiento = "🌿 Respira, analiza nuestra comunicación... Muchos amigos están hablando conmigo ahora mismo. ¡Inténtalo de nuevo en 40 segundos!"
                                    st.warning(msg_enfriamiento)
                                    st.session_state.messages.append({"role": "assistant", "content": msg_enfriamiento, "avatar": "⏳"})
                                    st.rerun()
                                else:
                                    error_text = f"Ups... {nombre_agente} se distrajo. ¡Intenta de nuevo!"
                                    st.error(error_text)
                                    st.session_state.messages.append({"role": "assistant", "content": error_text, "avatar": avatar_emoji})
                                    continue 

        verificar_correo_quincenal(st.session_state.usuario_actual)

    # --- INTERFAZ DE USUARIO Y BLOQUEO DE 40s ---
    if st.session_state.cooldown_hasta and datetime.now() < st.session_state.cooldown_hasta:
        tiempo_restante = st.session_state.cooldown_hasta - datetime.now()
        segundos = int(tiempo_restante.total_seconds()) + 1
        st.warning(f"🌿 Respira, analiza nuestra comunicación... Podrás escribir de nuevo en **{segundos} segundos**. ¡Adelante, siempre adelante!")
        time.sleep(1) 
        st.rerun() 
    else:
        if st.session_state.cooldown_hasta:
            st.session_state.cooldown_hasta = None 

        placeholder_text = f"✏️ Escribe tu pregunta a los agentes... 😊🏃‍♂️"
        if prompt := st.chat_input(placeholder_text):
            procesar_respuesta(prompt)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("🔊 Escuchar", use_container_width=True):
                    if st.session_state.last_response:
                        speak_js(st.session_state.last_response)
                    else:
                        speak_js("✨ ¡Hola! Pregúntame algo y te ayudaré")
            with b_col2:
                if st.button("🔄 Reiniciar", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.last_response = ""
                    st.rerun()

chat_fragment()
