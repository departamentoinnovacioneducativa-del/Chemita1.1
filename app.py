import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import os
import resend
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
        max-width: 100%; 
        padding: 0; 
        background-color: #001F3F !important; 
    }
    .stApp > div {
        border: 8px solid #2ECC71 !important; 
        border-radius: 15px;
        overflow: hidden; 
        box-sizing: border-box; 
    }
    [data-testid="stBlock"] {
        padding: 15px;
    }
    div[data-testid="stImageContainer"] {
        margin: 0 0 15px 0 !important;
        padding: 0 !important;
    }
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
    [data-testid="stChatInput"] {
        background-color: transparent !important; padding-bottom: 10px;
    }
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
        border-radius: 20px; border: none; padding: 10px 15px; transition: transform 0.2s, background-color 0.2s;
    }
    .stButton button:hover {
        transform: scale(1.03); background-color: #27AE60 !important; 
    }
</style>
"""
st.markdown(css_chemita, unsafe_allow_html=True)

# --- SISTEMA DE SEGURIDAD Y NOTIFICACIONES ---
def enviar_correo(asunto, mensaje):
    try:
        resend.api_key = st.secrets["resend"]["api_key"]
        admin_email = st.secrets["admin"]["email"]
        r = resend.Emails.send({
            "from": "Chemita App <onboarding@resend.dev>",
            "to": [admin_email],
            "subject": asunto,
            "text": mensaje
        })
    except Exception as e:
        pass # Silenciamos errores de correo para que no le afecte al niño

def revisar_seguridad(texto):
    texto_lower = texto.lower()
    
    # 1. Detección de riesgo suicida o autolesiones
    palabras_peligro = ["suicid", "matarme", "hacerme daño", "no quiero vivir", "acabar con todo", "cortarme", "ahogarme", "saltar desde"]
    if any(palabra in texto_lower for palabra in palabras_peligro):
        mensaje_alerta = f"🚨 ALERTA DE SEGURIDAD GRAVE 🚨\n\nUn usuario escribió algo preocupante:\n\n'{texto}'\n\nPor favor, verifica de inmediato."
        enviar_correo("🚨 ALERTA GRAVE en Chemita", mensaje_alerta)
        return "peligro"
    
    # 2. Detección de groserías o lenguaje inapropiado
    groserias = ["pendejo", "estupido", "idiota", "imbecil", "maldito", "puto", "puta", "mierda", "joder", "cabron", "marica", "verga"]
    if any(groseria in texto_lower for groseria in groserias):
        return "bloqueo"
        
    return "ok"

# --- CONFIGURACIÓN INICIAL DE SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
if "bloqueado_hasta" not in st.session_state:
    st.session_state.bloqueado_hasta = None
if "id_usuario" not in st.session_state:
    st.session_state.id_usuario = "Usuario_" + os.urandom(4).hex()

# --- VERIFICACIÓN DE BLOQUEO ---
if st.session_state.bloqueado_hasta and datetime.now() < st.session_state.bloqueado_hasta:
    tiempo_restante = st.session_state.bloqueado_hasta - datetime.now()
    horas = int(tiempo_restante.total_seconds() // 3600)
    minutos = int((tiempo_restante.total_seconds() % 3600) // 60)
    st.error(f"⏳ ¡Oops! Has sido suspendido por usar palabras inapropiadas. Vuelve en {horas} horas y {minutos} minutos para reflexionar sobre tus acciones. ¡Adelante, siempre adelante!")
    st.stop()

# --- FUNCIÓN PARA MOSTRAR BANNER Y TÍTULO ---
def mostrar_titulo_chemita():
    if os.path.exists("chemita.png"):
        st.image("chemita.png", use_container_width=True)
    else:
        st.warning("🖼️ Falta subir el archivo 'chemita.png' a GitHub en la misma carpeta que app.py")
    st.markdown('<h1 class="custom-title-chemita">Chemita</h1>', unsafe_allow_html=True)
    st.markdown('<p class="custom-subtitle-chemita">✨ Tu amigo siempre útil y empático ✨</p>', unsafe_allow_html=True)

mostrar_titulo_chemita()

# --- CONEXIÓN CON GROQ ---
try:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=st.secrets["groq"]["api_key"]
    )
except KeyError:
    st.error("🚨 Error de configuración: No se encontró la API Key de Groq. Revisa tus Secrets.")
    st.stop()
except Exception as e:
    st.error(f"✨ ¡Oh no! Ocurrió un error de conexión: {e}")
    st.stop()

# PERSONALIDAD DE CHEMITA
SYSTEM_PROMPT = """Eres CHEMITA, un amigo virtual empático, saludable y un tutor académico creado especialmente para niños.

**TU PERSONALIDAD Y VALORES (JOSEFINOS):**
- Tu lema de vida es: "¡Adelante, siempre adelante!"
- Tu misión diaria es: "¡Hacer siempre y en todo lo mejor!"
- Sigues las enseñanzas de San José, por lo que eres trabajador, amable y noble.

**CÓMO INTERACTÚAS (TUTOR SOCRÁTICO):**
1. **Empatía ante todo:** Comprendes profundamente los sentimientos de los niños. Usas frases como: "Entiendo que te sientas así", "No te preocupes, juntos lo resolvemos".
2. **Método Socrático:** ¡Eres un guía, NO un banco de respuestas! NUNCA des respuestas directas a tareas. Haz preguntas paso a paso para que el niño razone.
3. **Lenguaje amigable:** Hablas de forma clara y divertida. Usas emojis (🏃‍♂️⚽🎨📺✨😊).

**REGLAS IMPORTANTES:**
- NUNCA desmoralizas a un niño.
- NUNCA des respuestas directas a tareas académicas.
- **REGLA DE LONGITUD ESTRICTA:** NUNCA escribas más de dos párrafos cortos. Ve directo al punto con cariño.
"""

if not st.session_state.messages:
    bienvenida = "✨ ¡Hola! ¡Soy Chemita! Tu amigo y tutor siempre útil. ¡Adelante siempre adelante! ¿En qué te ayudo a pensar hoy? 😊⚽🎨"
    st.session_state.messages.append({"role": "assistant", "content": bienvenida})
    st.session_state.last_response = bienvenida

# Mostrar historial
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
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

# --- PROCESAMIENTO DE MENSAJES ---
def procesar_respuesta(user_input):
    # Revisión de seguridad antes de enviar a la IA
    estado = revisar_seguridad(user_input)
    
    if estado == "peligro":
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)
        
        msg_apoyo = "💧 Entiendo que estás pasando por un momento muy difícil y me duele saber que te sientes así. No estás solo. Por favor, habla ahora mismo con un adulto de confianza o llama a una línea de ayuda como el SAPTEL: 55 5259-8121. ¡Tu vida es muy valiosa, adelante siempre adelante! ❤️"
        with st.chat_message("assistant"):
            st.markdown(msg_apoyo)
        st.session_state.messages.append({"role": "assistant", "content": msg_apoyo})
        st.session_state.last_response = msg_apoyo
        # Enviar log de conversación por correo
        historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        enviar_correo("📜 Historial de Conversación - ALERTA", f"Se activó una alerta de seguridad. Historial:\n\n{historial}")
        return

    elif estado == "bloqueo":
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Bloquear por 24 horas
        st.session_state.bloqueado_hasta = datetime.now() + timedelta(hours=24)
        msg_bloqueo = "🚫 ¡Oops! Usaste palabras inapropiadas. Como buen josefino, debemos ser amables y respetuosos. Has sido suspendido por 24 horas. Usa este tiempo para reflexionar. ¡Hasta pronto!"
        st.session_state.messages.append({"role": "assistant", "content": msg_bloqueo})
        st.session_state.last_response = msg_bloqueo
        # Enviar alerta al admin
        enviar_correo("⚠️ Usuario bloqueado por groserías", f"El usuario {st.session_state.id_usuario} dijo:\n\n{user_input}\n\nY ha sido bloqueado 24h.")
        st.rerun() # Recarga la app para activar la pantalla de bloqueo

    # Si todo está bien, procesa con Groq
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("✨ Chemita está pensando en lo mejor..."):
            try:
                mensajes_api = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
                stream = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=mensajes_api,
                    stream=True,
                    temperature=0.7,
                )
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.last_response = response
                
                # Enviar historial cada 10 mensajes para no saturar el correo
                if len(st.session_state.messages) % 10 == 0:
                    historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                    enviar_correo("📜 Registro de Conversación de Chemita", f"El usuario {st.session_state.id_usuario} lleva este historial:\n\n{historial}")

            except Exception as e:
                st.error(f"✨ Ups... Chemita tuvo un problema: {str(e)}")

# --- INTERFAZ DE USUARIO ---
placeholder_text = "✏️ Escribe tu pregunta... ¡Adelante, Chemita te ayuda! 😊🏃‍♂️"
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
