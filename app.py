import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import os
import resend
import json
import pandas as pd
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
        border-radius: 20px; border: none; padding: 10px 15px; transition: transform 0.2s, background-color 0.2s;
    }
    .stButton button:hover { transform: scale(1.03); background-color: #27AE60 !important; }
    
    .login-box {
        background-color: #FFFDE0; padding: 30px; border-radius: 15px; margin-top: 20px;
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
        st.toast("✉️ Notificación enviada al administrador.")
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
# PANEL DE ADMINISTRADOR (SI ES EL USUARIO 'admin')
# ==========================================
if st.session_state.usuario_actual == "admin":
    mostrar_titulo_chemita()
    st.subheader("🛠️ Panel de Administración de Usuarios")
    st.write("Edita la tabla como si fuera Excel. Para agregar un usuario nuevo, escribe en la última fila vacía. Para guardar los cambios, da clic en el botón verde.")

    usuarios_dict = cargar_usuarios()
    # Convertir a formato tabla (DataFrame) para el editor de Excel
    df_usuarios = pd.DataFrame.from_dict(usuarios_dict, orient='index').reset_index()
    df_usuarios.rename(columns={'index': 'Usuario', 'password': 'Contraseña', 'bloqueado_hasta': 'Bloqueado_Hasta', 'ultimo_correo': 'Ultimo_Correo'}, inplace=True)
    
    # Mostrar el editor tipo Excel
    edited_df = st.data_editor(
        df_usuarios,
        num_rows="dynamic", # Permite agregar y borrar filas
        use_container_width=True,
        key="editor_usuarios"
    )

    col_save, col_logout = st.columns(2)
    with col_save:
        if st.button("💾 Guardar Cambios en la Base de Datos", use_container_width=True):
            # Limpiar valores vacíos (NaN) y volver a diccionario
            edited_df = edited_df.where(pd.notnull(edited_df), None)
            edited_df['Contraseña'] = edited_df['Contraseña'].astype(str).replace('None', None)
            nuevo_dict = edited_df.set_index('Usuario').to_dict(orient='index')
            
            # Renombrar de vuelta a las keys originales
            for user, data in nuevo_dict.items():
                data['password'] = data.pop('Contraseña')
                data['bloqueado_hasta'] = data.pop('Bloqueado_Hasta')
                data['ultimo_correo'] = data.pop('Ultimo_Correo')
                
            guardar_usuarios(nuevo_dict)
            st.success("✅ Base de datos actualizada correctamente.")
            
    with col_logout:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario_actual = None
            st.rerun()
    
    st.stop() # Detiene la ejecución aquí para que el admin no vea el chat

# ==========================================
# APP PRINCIPAL (CHAT PARA NIÑOS)
# ==========================================
mostrar_titulo_chemita()

col_cerrar1, col_cerrar2, col_cerrar3 = st.columns([2, 1, 1])
with col_cerrar3:
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.session_state.messages = []
        st.rerun()

# CONEXIÓN CON GROQ
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
1. **Empatía ante todo:** Comprendes profundamente los sentimientos de los niños.
2. **Método Socrático:** ¡Eres un guía, NO un banco de respuestas! NUNCA des respuestas directas a tareas. Haz preguntas paso a paso.
3. **Lenguaje amigable:** Hablas de forma clara y divertida. Usas emojis (🏃‍♂️⚽🎨📺✨😊).
**REGLAS IMPORTANTES:**
- NUNCA desmoralizas a un niño.
- NUNCA des respuestas directas a tareas académicas.
- **REGLA DE LONGITUD ESTRICTA:** NUNCA escribas más de dos párrafos cortos. Ve directo al punto con cariño.
"""

if not st.session_state.messages:
    bienvenida = f"✨ ¡Hola, {st.session_state.usuario_actual}! ¡Soy Chemita! Tu amigo y tutor. ¡Adelante siempre adelante! ¿En qué te ayudo a pensar hoy? 😊⚽🎨"
    st.session_state.messages.append({"role": "assistant", "content": bienvenida})
    st.session_state.last_response = bienvenida

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
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

def procesar_respuesta(user_input):
    estado = revisar_seguridad(user_input)
    if estado == "peligro":
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)
        msg_apoyo = "💧 Entiendo que estás pasando por un momento muy difícil y me duele saber que te sientes así. No estás solo. Por favor, habla ahora mismo con un adulto de confianza o llama a una línea de ayuda como el SAPTEL: 55 5259-8121. ¡Tu vida es muy valiosa, adelante siempre adelante! ❤️"
        with st.chat_message("assistant"):
            st.markdown(msg_apoyo)
        st.session_state.messages.append({"role": "assistant", "content": msg_apoyo})
        st.session_state.last_response = msg_apoyo
        historial = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        enviar_correo(f"🚨 ALERTA GRAVE - Usuario: {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} escribió algo preocupante.\n\nHistorial:\n\n{historial}")
        return

    elif estado == "bloqueo":
        st.session_state.messages.append({"role": "user", "content": user_input})
        usuarios = cargar_usuarios()
        if st.session_state.usuario_actual in usuarios:
            usuarios[st.session_state.usuario_actual]["bloqueado_hasta"] = (datetime.now() + timedelta(hours=24)).isoformat()
            guardar_usuarios(usuarios)
        msg_bloqueo = "🚫 ¡Oops! Usaste palabras inapropiadas. Como buen josefino, debemos ser amables y respetuosos. Has sido suspendido por 24 horas. Usa este tiempo para reflexionar. ¡Hasta pronto!"
        st.session_state.messages.append({"role": "assistant", "content": msg_bloqueo})
        enviar_correo(f"⚠️ Usuario bloqueado: {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} dijo:\n\n{user_input}\n\nY ha sido bloqueado 24h en la base de datos.")
        st.rerun()

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
                verificar_correo_semanal(st.session_state.usuario_actual)
            except Exception as e:
                st.error(f"✨ Ups... Chemita tuvo un problema: {str(e)}")

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
