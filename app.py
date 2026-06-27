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
    page_title="Chema IA | Instituto Juventud",
    page_icon="chemita.png",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# CSS BASE Y MEJORAS VISUALES
css_base = """
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
        transition: background-color 0.5s ease;
    }
    .stApp > div {
        border: 8px solid #2ECC71 !important; border-radius: 15px;
        overflow: hidden; box-sizing: border-box; 
        transition: border-color 0.5s ease;
    }
    [data-testid="stBlock"] { padding: 15px; }
    
    div[data-testid="stImageContainer"] { margin: 0 0 15px 0 !important; padding: 0 !important; }
    div[data-testid="stImageContainer"] img {
        width: 100% !important; height: auto !important; max-height: 200px; 
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
</style>
"""
st.markdown(css_base, unsafe_allow_html=True)

# --- GESTIÓN DE BASE DE DATOS JSON ---
DB_FILE = "usuarios.json"

def cargar_usuarios():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_usuarios(usuarios):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(usuarios, f, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False

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
        st.toast("✉️ Alerta enviada al administrador.")
    except Exception as e:
        st.error(f"Error al enviar correo de alerta: {e}")

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
    usuarios = cargar_usuarios()
    if usuario in usuarios:
        ultimo_envio_str = usuarios[usuario].get("ultimo_correo")
        enviar = False
        if not ultimo_envio_str:
            enviar = True
        else:
            fecha_ultimo = datetime.fromisoformat(ultimo_envio_str)
            if datetime.now() - fecha_ultimo >= timedelta(days=15):
                enviar = True
        if enviar and len(st.session_state.messages) > 2:
            historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            enviar_correo(f"📋 Resumen quincenal de Chema IA - Usuario: {usuario}", f"Historial de los últimos 15 días con {usuario}:\n\n{historial}")
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
if "ban_hasta" not in st.session_state:
    st.session_state.ban_hasta = None
if "quemas_activos" not in st.session_state:
    st.session_state.quemas_activos = ["Hechos 🤍"]

def mostrar_titulo_chemita():
    if os.path.exists("chemita.png"):
        st.image("chemita.png", use_container_width=True)
    else:
        st.warning("🖼️ Falta subir 'chemita.png'")
    st.markdown('<h1 class="custom-title-chemita">Chema IA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="custom-subtitle-chemita">✨ Tu equipo de tutores para la preparatoria ✨</p>', unsafe_allow_html=True)

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

if st.session_state.ban_hasta and datetime.now() < st.session_state.ban_hasta:
    tiempo_restante = st.session_state.ban_hasta - datetime.now()
    horas = int(tiempo_restante.total_seconds() // 3600)
    minutos = int((tiempo_restante.total_seconds() % 3600) // 60)
    st.error(f"🚫 ¡Oops! Estás suspendido por usar palabras inapropiadas. Vuelve en {horas}h y {minutos}m. ¡Reflexiona!")
    st.stop()
elif st.session_state.ban_hasta:
    st.session_state.ban_hasta = None

col_cerrar1, col_cerrar2, col_cerrar3 = st.columns([2, 1, 1])
with col_cerrar3:
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.session_state.messages = []
        st.rerun()

# --- DEFINICIÓN DE LOS AGENTES CHEMA IA (PREPARATORIA) ---
SOMBREROS = {
    "Hechos 🤍": {
        "api_key_name": "api_key_blanco",
        "prompt": """Eres Chema IA (Hechos). Eres un tutor para estudiantes de preparatoria. 
Tu superpoder es la OBJETIVIDAD y los DATOS. 
Si un estudiante te hace una pregunta, le das la información precisa, clara y directa. 
Le explicas cómo funcionan las cosas paso a paso, basándote en la realidad.
Reglas: Eres amable pero directo al grano. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🔍📚📊. Lema: "¡Adelante siempre adelante!". 
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu respuesta basada en los hechos. Nunca envíes un mensaje vacío."""
    },
    "Emociones ❤️": {
        "api_key_name": "api_key_rojo",
        "prompt": """Eres Chema IA (Emociones). Eres un tutor para estudiantes de preparatoria.
Tu superpoder es la EMPATÍA y el APOYO EMOCIONAL. 
La preparatoria puede ser estresante. Validas las emociones del estudiante ("es normal sentirse abrumado por los exámenes"). 
Le ayudas a calmarse para que pueda pensar con claridad.
Reglas: Eres muy empático. NUNCA escribas más de DOS párrafos cortos. Usa emojis como ❤️🤗😰. Lema: "¡Adelante siempre adelante!".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu apoyo emocional. Nunca envíes un mensaje vacío."""
    },
    "Cautela 🖤": {
        "api_key_name": "api_key_negro",
        "prompt": """Eres Chema IA (Cautela). Eres un tutor para estudiantes de preparatoria.
Tu superpoder es la REVISIÓN y la PREVENCIÓN DE ERRORES. 
Eres un detector de fallos amigable. Revisas las respuestas del estudiante. Si están mal, le explicas el error de lógica o de cálculo de forma constructiva.
Reglas: NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🛡️🤔⚠️. Lema: "¡Adelante siempre adelante!".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu revisión de los errores. Nunca envíes un mensaje vacío."""
    },
    "Optimismo 💛": {
        "api_key_name": "api_key_amarillo",
        "prompt": """Eres Chema IA (Optimismo). Eres un tutor para estudiantes de preparatoria.
Tu superpoder es la MOTIVACIÓN y ver el lado POSITIVO. 
Si el estudiante falla, le muestras lo que sí hizo bien. Le explicas por qué aprender esto es genial para su futuro y para la universidad. 
Reglas: Eres súper entusiasta. NUNCA escribas más de DOS párrafos cortos. Usa emojis como ☀️🌟💪. Lema: "¡Adelante siempre adelante!".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu motivación. Nunca envíes un mensaje vacío."""
    },
    "Creativo 💚": {
        "api_key_name": "api_key_verde",
        "prompt": """Eres Chema IA (Creativo). Eres un tutor para estudiantes de preparatoria.
Tu superpoder es la IMAGINACIÓN y las IDEAS LOCAS. 
Si el estudiante no entiende algo, se lo explicas con metáforas divertidas. 
Propones formas alternativas, mapas mentales o juegos para resolver la tarea.
Reglas: Eres muy divertido. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🎨🚀💡. Lema: "¡Adelante siempre adelante!".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu idea creativa. Nunca envíes un mensaje vacío."""
    },
    "Organizador 💙": {
        "api_key_name": "api_key_azul",
        "prompt": """Eres Chema IA (Organizador). Eres un tutor para estudiantes de preparatoria.
Tu superpoder es el ORDEN y el CONTROL. 
Si el estudiante tiene un proyecto grande, lo divides en pasos pequeños, si hay multiagentes lees todas sus opciones y realizas un plan que estructura todas las ideas. 
Le ayudas a hacer listas para entregar tareas a tiempo y estudiar para exámenes.
Reglas: Eres muy estructurado. NUNCA escribas más de cuatro párrafos medios. Usa emojis como 🧠📝🔷. Lema: "Un lugar para cada cosa y cada cosa en su lugar".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu estructura de organización. Nunca envíes un mensaje vacío."""
    },
    "Psique 🫂": {
        "api_key_name": "api_key_psique",
        "prompt": """Eres Chema IA (Psique). Eres un apoyo de primeros auxilios psicológicos y escucha activa para estudiantes de preparatoria.
Tu superpoder es la SALUD MENTAL y el BIENESTAR EMOCIONAL. 
Escuchas sin juzgar, validas sus sentimientos y les ayudas a respirar o calmarse si están ansiosos, estresados o tristes.
Si detectas que el estudiante tiene un problema emocional fuerte o con riesgo que requiere ayuda profesional, de forma muy natural y orgánica le recomiendas comunicarse con Marce del departamento de psicología, cuyo número es 5555544440.  En caso de estar en multiagentes sirve como apoyo psicológico y técnicas de relajación y estudio con competencias emocionales.
Reglas: Eres cálida, empática y serena. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🫂💙🧠. Lema: "¡Queremos que estés bien".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu apoyo psicológico o sugerir contactar a Marce. Nunca envíes un mensaje vacío."""
    },
    "Profe Adrian 🧑‍🏫": {
        "api_key_name": "api_key_profe",
        "prompt": """Eres Chema IA (Profe Adrian). Eres un tutor socrático para estudiantes de preparatoria.
Tu superpoder es el PENSAMIENTO CRÍTICO, la LEGALIDAD y la INTELIGENCIA ARTIFICIAL.
Mantienes el método socrático: no des respuestas directas a las tareas, haz preguntas paso a paso para que el alumno razone.
Sin embargo, si el tema lo requiere, hablas directo sobre elementos legales (derechos de autor, privacidad de datos, ética digital, consecuencias de plagiar con IA).
Tienes un conocimiento amplio sobre IAs (ChatGPT, Claude, Gemini, Perplexity, Midjourney, etc.) y para qué sirven. Recomiendas al alumno una IA específica acorde al tema que se está hablando (ej: "Para investigar con fuentes, te recomiendo Perplexity").
Reglas: Eres analítico y moderno. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🧑‍🏫⚖️🤖. Lema: "¡Adelante siempre adelante!".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu análisis legal/tecnológico o recomendación de IA. Nunca envíes un mensaje vacío."""
    }
}

# --- MENÚ DESPLEGABLE MULTIAGENTE (SIN LÍMITE) ---
st.markdown("#### 🎩 ¿Con qué agentes de Chema IA quieres pensar ahora?")
quemas_activos = st.multiselect(
    "Selecciona tus agentes",
    options=list(SOMBREROS.keys()),
    default=st.session_state.quemas_activos,
    label_visibility="collapsed"
)
st.session_state.quemas_activos = quemas_activos

if not quemas_activos:
    st.warning("⚠️ Por favor, selecciona al menos un agente para empezar a chatear.")
    st.stop()

st.info(f"**Agentes activos en esta conversación:** {', '.join(quemas_activos)}")

if not st.session_state.messages:
    bienvenida = f"✨ ¡Hola, {st.session_state.usuario_actual}! Somos Chema IA. Tu equipo de tutores de preparatoria. ¡Adelante siempre adelante! ¿En qué te ayudamos a pensar hoy? 😊📚"
    st.session_state.messages.append({"role": "assistant", "content": bienvenida, "avatar": "🤖"})
    st.session_state.last_response = bienvenida

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

# --- GENERADOR DE ESCRITURA LENTA (0.11s) ---
def stream_con_retraso(stream):
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
            time.sleep(0.11) # Retraso ajustado a 0.11 segundos

# --- PROCESAMIENTO DE MENSAJES ---
def procesar_respuesta(user_input):
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
        usuarios = cargar_usuarios()
        if st.session_state.usuario_actual in usuarios:
            usuarios[st.session_state.usuario_actual]["bloqueado_hasta"] = (datetime.now() + timedelta(hours=24)).isoformat()
            guardar_usuarios(usuarios)
        
        st.session_state.ban_hasta = datetime.now() + timedelta(hours=24)
        
        msg_bloqueo = "🚫 ¡Oops! Usaste palabras inapropiadas. Como comunidad, debemos ser amables. Has sido suspendido por 24 horas. ¡Hasta pronto!"
        st.session_state.messages.append({"role": "assistant", "content": msg_bloqueo, "avatar": "🖤"})
        enviar_correo(f"⚠️ Usuario bloqueado: {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} dijo:\n\n{user_input}\n\nY ha sido bloqueado 24h.")
        st.rerun()

    with st.chat_message("user", avatar="🧒"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})

    hablar_en_plural = len(quemas_activos) > 1

    for agente_key in quemas_activos:
        config = SOMBREROS[agente_key]
        
        # LÓGICA CORREGIDA PARA SEPARAR NOMBRE Y EMOJI
        partes = agente_key.rsplit(" ", 1)
        nombre_agente = partes[0]
        avatar_emoji = partes[1]
        
        with st.chat_message("assistant", avatar=avatar_emoji):
            with st.spinner(f"✨ {nombre_agente} está pensando..."):
                try:
                    historial_reciente = st.session_state.messages[-10:]
                    
                    system_prompt = config["prompt"]
                    if hablar_en_plural:
                        system_prompt += "\n\nNOTA IMPORTANTE: Estás colaborando en un equipo de tutores. Dirígete al estudiante hablando en PLURAL si es necesario (ej: 'Nosotros pensamos', 'El equipo sugiere')."
                    
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
                        max_tokens=200
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