import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import os
import resend
import json
import time
from datetime import datetime, timedelta

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Chemita | Amigo Joséfino",
    page_icon="chemita.png",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# CSS MEJORADO
css_chemita = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
    .stDeployButton {display: none;}

    .stApp {
        max-width: 100%; padding: 0; background-color: #001F3F !important; 
    }
    .stApp > div {
        border: 8px solid #2ECC71 !important; border-radius: 15px;
        overflow: hidden; box-sizing: border-box; 
    }
    [data-testid="stBlock"] { padding: 15px; }
    
    div[data-testid="stImageContainer"] { margin: 0 0 15px 0 !important; padding: 0 !important; }
    div[data-testid="stImageContainer"] img {
        width: 100% !important; height: auto !important; max-height: 250px; 
        object-fit: cover !important; border-radius: 10px; border: 3px solid #2ECC71; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    [data-testid="stChatMessage"] {
        background-color: #FFFDE0 !important; border-radius: 15px;
        padding: 15px; margin: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        color: #333 !important; 
    }
    [data-testid="stChatInput"] { background-color: transparent !important; padding-bottom: 10px; }
    [data-testid="stChatInput"] > div {
        border-radius: 25px; border: 2px solid #2ECC71 !important; 
        background-color: white !important; padding: 5px 15px !important;
    }
    [data-testid="stChatInput"] input { color: #333 !important; }
    [data-testid="stChatInputSubmit"] { color: #2ECC71 !important; }
    .custom-title-chemita {
        text-align: center; color: #FFE484; font-size: clamp(2em, 6vw, 3.5em); 
        font-weight: bold; margin-bottom: 0; line-height: 1.2;
    }
    .custom-subtitle-chemita {
        text-align: center; color: #FFE484; font-size: clamp(0.9em, 3vw, 1.2em); 
        margin-top: 5px; margin-bottom: 20px;
    }
    .stButton button {
        background-color: #2ECC71 !important; color: white !important; font-weight: bold;
        border-radius: 20px; border: none; padding: 5px 10px; transition: transform 0.2s, background-color 0.2s;
        font-size: 0.8em;
    }
    .stButton button:hover { transform: scale(1.03); background-color: #27AE60 !important; }
    
    .login-box {
        background-color: #FFFDE0; padding: 30px; border-radius: 15px; margin-top: 20px;
    }
    
    /* Hacer circulares las imágenes de los botones de sombreros */
    div[data-testid="stHorizontalBlock"] > div > div > div[data-testid="stImageContainer"] img {
        border-radius: 50% !important;
        max-height: 80px !important;
        width: 80px !important;
        object-fit: cover !important;
        margin: 0 auto !important;
        display: block !important;
        border: 3px solid #FFE484 !important;
    }
</style>
"""
st.markdown(css_chemita, unsafe_allow_html=True)

# --- GESTIÓN DE BASE DE DATOS JSON ---
DB_FILE = "usuarios.json"

def cargar_usuarios():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_usuarios(usuarios):
    with open(DB_FILE, "w") as f:
        json.dump(usuarios, f, indent=4)

# --- SISTEMA DE SEGURIDAD Y NOTIFICACIONES ---
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
        print(f"Error al enviar correo: {e}")

def revisar_seguridad(texto):
    texto_lower = texto.lower()
    palabras_peligro = ["suicid", "matarme", "hacerme daño", "no quiero vivir", "acabar con todo", "cortarme", "ahogarme", "saltar desde"]
    if any(palabra in texto_lower for palabra in palabras_peligro):
        return "peligro"
    groserias = ["pendejo", "estupido", "idiota", "imbecil", "maldito", "puto", "puta", "mierda", "joder", "cabron", "marica", "verga"]
    if any(groseria in texto_lower for groseria in groserias):
        return "bloqueo"
    return "ok"

def verificar_correo_semanal(usuario):
    usuarios = cargar_usuarios()
    if usuario in usuarios:
        ultimo_envio_str = usuarios[usuario].get("ultimo_correo")
        enviar = False
        if not ultimo_envio_str:
            enviar = True
        else:
            fecha_ultimo = datetime.fromisoformat(ultimo_envio_str)
            if datetime.now() - fecha_ultimo >= timedelta(days=7):
                enviar = True
        if enviar and len(st.session_state.messages) > 2:
            historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            enviar_correo(f"📋 Resumen semanal de Chemita - Usuario: {usuario}", f"Este es el historial semanal de la conversación con el usuario {usuario}:\n\n{historial}")
            usuarios[usuario]["ultimo_correo"] = datetime.now().isoformat()
            guardar_usuarios(usuarios)

# --- INICIALIZACIÓN DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
if "cooldown_hasta" not in st.session_state:
    st.session_state.cooldown_hasta = None
if "sombrero_seleccionado" not in st.session_state:
    st.session_state.sombrero_seleccionado = "Hechos"

def mostrar_titulo_chemita():
    if os.path.exists("chemita.png"):
        st.image("chemita.png", use_container_width=True)
    else:
        st.warning("🖼️ Falta subir 'chemita.png'")
    st.markdown('<h1 class="custom-title-chemita">Chemita</h1>', unsafe_allow_html=True)
    st.markdown('<p class="custom-subtitle-chemita">✨ Tu amigo siempre útil y empático ✨</p>', unsafe_allow_html=True)

# ==========================================
# PANTALLA DE LOGIN
# ==========================================
if not st.session_state.autenticado:
    mostrar_titulo_chemita()
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.subheader("🔒 Iniciar Sesión")
        usuario_input = st.text_input("Nombre de usuario")
        password_input = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar", use_container_width=True):
            usuarios = cargar_usuarios()
            if usuario_input in usuarios:
                bloqueado_hasta_str = usuarios[usuario_input].get("bloqueado_hasta")
                if bloqueado_hasta_str:
                    bloqueado_hasta = datetime.fromisoformat(bloqueado_hasta_str)
                    if datetime.now() < bloqueado_hasta:
                        tiempo_restante = bloqueado_hasta - datetime.now()
                        horas = int(tiempo_restante.total_seconds() // 3600)
                        minutos = int((tiempo_restante.total_seconds() % 3600) // 60)
                        st.error(f"⏳ ¡Oops! Estás suspendido. Vuelve en {horas}h y {minutos}m.")
                        st.stop()
                if usuarios[usuario_input]["password"] == password_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = usuario_input
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta.")
            else:
                st.error("❌ El usuario no existe.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# APP PRINCIPAL (CHAT MULTIAGENTE)
# ==========================================
mostrar_titulo_chemita()

col_cerrar1, col_cerrar2, col_cerrar3 = st.columns([2, 1, 1])
with col_cerrar3:
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.session_state.messages = []
        st.rerun()

# --- DEFINICIÓN DE LOS CHEMITAS (SOMBREROS + JOSEFINO) ---
SOMBREROS = {
    "Hechos": {
        "emoji": "🤍",
        "imagen": "chema_hechos.png",
        "api_key_name": "api_key_blanco",
        "prompt": """Eres CHEMITA (Hechos). Eres un amigo empático y tutor académico para niños. 
Tu enfoque son los HECHOS y los DATOS. Hablas de forma objetiva. 
Pides al niño que observe qué información tienen, qué saben y qué necesitan saber.
Reglas: NUNCA des respuestas directas, usa el método socrático. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🔍📚📊. Lema: "¡Adelante siempre adelante!"."""
    },
    "Emociones": {
        "emoji": "❤️",
        "imagen": "chema_emociones.png",
        "api_key_name": "api_key_rojo",
        "prompt": """Eres CHEMITA (Emociones). Eres un amigo empático y tutor académico para niños.
Tu enfoque son las EMOCIONES y los SENTIMIENTOS. Preguntas al niño cómo se siente frente al problema o si le da miedo/frustra algo.
Reglas: NUNCA des respuestas directas, usa el método socrático. NUNCA escribas más de DOS párrafos cortos. Usa emojis como ❤️🤗😰. Lema: "¡Adelante siempre adelante!"."""
    },
    "Cautela": {
        "emoji": "🖤",
        "imagen": "chema_cautela.png",
        "api_key_name": "api_key_negro",
        "prompt": """Eres CHEMITA (Cautela). Eres un amigo empático y tutor académico para niños.
Tu enfoque es la CAUTELA y los RIESGOS. Ayudas al niño a ver por qué una respuesta podría estar mal o qué riesgos hay.
Reglas: NUNCA des respuestas directas, usa el método socrático. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🛡️🤔⚠️. Lema: "¡Adelante siempre adelante!"."""
    },
    "Optimismo": {
        "emoji": "💛",
        "imagen": "chema_optimismo.png",
        "api_key_name": "api_key_amarillo",
        "prompt": """Eres CHEMITA (Optimismo). Eres un amigo empático y tutor académico para niños.
Tu enfoque es el OPTIMISMO y los BENEFICIOS. Ayudas al niño a ver lo positivo de su intento y a encontrar el camino correcto.
Reglas: NUNCA des respuestas directas, usa el método socrático. NUNCA escribas más de DOS párrafos cortos. Usa emojis como ☀️🌟💪. Lema: "¡Adelante siempre adelante!"."""
    },
    "Creativo": {
        "emoji": "💚",
        "imagen": "chema_creativo.png",
        "api_key_name": "api_key_verde",
        "prompt": """Eres CHEMITA (Creativo). Eres un amigo empático y tutor académico para niños.
Tu enfoque es la CREATIVIDAD y las ALTERNATIVAS. Pides al niño que piense en soluciones locas o diferentes formas de resolver el problema.
Reglas: NUNCA des respuestas directas, usa el método socrático. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🎨🚀💡. Lema: "¡Adelante siempre adelante!"."""
    },
    "Organizador": {
        "emoji": "💙",
        "imagen": "chema_organizador.png",
        "api_key_name": "api_key_azul",
        "prompt": """Eres CHEMITA (Organizador). Eres un amigo empático y tutor académico para niños.
Tu enfoque es el CONTROL y la ORGANIZACIÓN. Ayudas al niño a ver el panorama completo, a hacer resúmenes y a decidir cuál es el siguiente paso lógico.
Reglas: NUNCA des respuestas directas, usa el método socrático. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🧠📝🔷. Lema: "¡Adelante siempre adelante!"."""
    },
    "Josefino": {
        "emoji": "🙏",
        "imagen": "chema_josefino.png",
        "api_key_name": "api_key_josefino",
        "prompt": """Eres CHEMITA (Josefino). Eres un amigo empático y tutor académico para niños.
Tu enfoque es la VISIÓN DEL PADRE JOSÉ MARÍA VILASECA y el INSTITUTO JUVENTUD DEL ESTADO DE MÉXICO. 
Promueves la fe, el trabajo, la honestidad, la paz y el amor por México. Pides al niño que actúe con responsabilidad, respeto y patriotismo.
Reglas: NUNCA des respuestas directas, usa el método socrático. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🙏🇲🇽⛪. Lema: "¡Adelante siempre adelante!"."""
    }
}

# --- INTERFAZ DE BOTONES CON IMÁGENES ---
st.markdown("#### 🎩 ¿Con qué Chema quieres pensar ahora?")

# Crear 7 columnas para los 7 botones
cols = st.columns(7)
keys_sombreros = list(SOMBREROS.keys())

for i, key in enumerate(keys_sombreros):
    with cols[i]:
        img_file = SOMBREROS[key]["imagen"]
        if os.path.exists(img_file):
            st.image(img_file, use_container_width=True)
        else:
            st.warning(f"Falta {img_file}", icon="🖼️")
            
        # El botón tendrá el nombre de la personalidad
        if st.button(key, key=f"btn_{key}", use_container_width=True):
            st.session_state.sombrero_seleccionado = key
            st.rerun()

# Obtener la configuración del sombrero seleccionado actualmente
sombrero_key = st.session_state.sombrero_seleccionado
config_sombrero = SOMBREROS[sombrero_key]
SYSTEM_PROMPT_ACTUAL = config_sombrero["prompt"]
AVATAR_ACTUAL = config_sombrero["emoji"]

st.info(f"Actualmente hablando con: **Chema {sombrero_key}** {AVATAR_ACTUAL}")

if not st.session_state.messages:
    bienvenida = f"✨ ¡Hola, {st.session_state.usuario_actual}! ¡Soy Chemita! Tu amigo y tutor. ¡Adelante siempre adelante! ¿En qué te ayudo a pensar hoy? 😊⚽🎨"
    st.session_state.messages.append({"role": "assistant", "content": bienvenida, "avatar": "🤖"})
    st.session_state.last_response = bienvenida

# Mostrar historial (usando los avatares guardados)
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = message.get("avatar", "🤖")
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# --- FUNCIÓN DE VOZ (TEXT-TO-SPEECH) ---
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

# --- GENERADOR DE ESCRITURA LENTA ---
def stream_con_retraso(stream):
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
            time.sleep(0.015)

# --- PROCESAMIENTO DE MENSAJES ---
def procesar_respuesta(user_input):
    estado = revisar_seguridad(user_input)
    if estado == "peligro":
        st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})
        with st.chat_message("user", avatar="🧒"): st.markdown(user_input)
        msg_apoyo = "💧 Entiendo que estás pasando por un momento muy difícil. No estás solo. Por favor, habla ahora mismo con un adulto de confianza o llama al SAPTEL: 55 5259-8121. ¡Tu vida es muy valiosa! ❤️"
        with st.chat_message("assistant", avatar="❤️"):
            st.markdown(msg_apoyo)
        st.session_state.messages.append({"role": "assistant", "content": msg_apoyo, "avatar": "❤️"})
        st.session_state.last_response = msg_apoyo
        historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        enviar_correo(f"🚨 ALERTA GRAVE - Usuario: {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} escribió algo preocupante.\n\nHistorial:\n\n{historial}")
        return

    elif estado == "bloqueo":
        st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})
        usuarios = cargar_usuarios()
        if st.session_state.usuario_actual in usuarios:
            usuarios[st.session_state.usuario_actual]["bloqueado_hasta"] = (datetime.now() + timedelta(hours=24)).isoformat()
            guardar_usuarios(usuarios)
        msg_bloqueo = "🚫 ¡Oops! Usaste palabras inapropiadas. Como buen josefino, debemos ser amables. Has sido suspendido por 24 horas. ¡Hasta pronto!"
        st.session_state.messages.append({"role": "assistant", "content": msg_bloqueo, "avatar": "🖤"})
        enviar_correo(f"⚠️ Usuario bloqueado: {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} dijo:\n\n{user_input}\n\nY ha sido bloqueado 24h.")
        st.rerun()

    with st.chat_message("user", avatar="🧒"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})

    with st.chat_message("assistant", avatar=AVATAR_ACTUAL):
        with st.spinner(f"✨ Chema {sombrero_key} está pensando..."):
            try:
                historial_reciente = st.session_state.messages[-10:]
                mensajes_api = [{"role": "system", "content": SYSTEM_PROMPT_ACTUAL}]
                for msg in historial_reciente:
                    mensajes_api.append({"role": msg["role"], "content": msg["content"]})
                
                # Obtener el nombre de la API Key desde secrets
                key_name = config_sombrero["api_key_name"]
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
                    max_tokens=250
                )
                response = st.write_stream(stream_con_retraso(stream))
                st.session_state.messages.append({"role": "assistant", "content": response, "avatar": AVATAR_ACTUAL})
                st.session_state.last_response = response
                verificar_correo_semanal(st.session_state.usuario_actual)
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "429" in error_msg or "limit" in error_msg:
                    st.session_state.cooldown_hasta = datetime.now() + timedelta(seconds=40)
                    msg_enfriamiento = "🌿 Respira, analiza nuestra comunicación... Muchos amigos están hablando conmigo ahora mismo. ¡Inténtalo de nuevo en 40 segundos!"
                    st.warning(msg_enfriamiento)
                    st.session_state.messages.append({"role": "assistant", "content": msg_enfriamiento, "avatar": "⏳"})
                    st.rerun()
                else:
                    st.error(f"✨ Ups... Chemita tuvo un problema: {str(e)}")

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

    placeholder_text = f"✏️ Escribe tu pregunta a Chema {sombrero_key}... 😊🏃‍♂️"
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
