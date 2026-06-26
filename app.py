import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import os

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Chemita | Amigo Joséfino",
    page_icon="chemita.png",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# CSS MEJORADO: Fondo Azul Marino, Marco Verde y Diseño Responsivo
css_chemita = """
<style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
    .stDeployButton {display: none;}

    /* Fondo y Marco General */
    .stApp {
        max-width: 100%; 
        padding: 0; 
        background-color: #001F3F !important; /* Azul Marino */
    }
    .stApp > div {
        border: 8px solid #2ECC71 !important; /* Marco Verde */
        border-radius: 15px;
        overflow: hidden; 
        box-sizing: border-box; 
    }

    /* Contenedor principal */
    [data-testid="stBlock"] {
        padding: 15px;
    }

    /* --- ESTILO DEL BANNER DE IMAGEN --- */
    div[data-testid="stImageContainer"] {
        margin: 0 0 15px 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stImageContainer"] img {
        width: 100% !important; 
        height: auto !important; 
        max-height: 250px; 
        object-fit: cover !important; 
        border-radius: 10px; 
        border: 3px solid #2ECC71; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* Estilo de los mensajes - Fondo amarillo tenue */
    [data-testid="stChatMessage"] {
        background-color: #FFFDE0 !important; 
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        color: #333 !important; 
    }

    /* Entrada de Chat */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
        padding-bottom: 10px;
    }
    [data-testid="stChatInput"] > div {
        border-radius: 25px;
        border: 2px solid #2ECC71 !important; 
        background-color: white !important;
        padding: 5px 15px !important;
    }
    [data-testid="stChatInput"] input {
        color: #333 !important;
    }
    [data-testid="stChatInputSubmit"] {
        color: #2ECC71 !important;
    }

    /* Título personalizado */
    .custom-title-chemita {
        text-align: center;
        color: #FFE484; 
        font-size: clamp(2em, 6vw, 3.5em); 
        font-weight: bold;
        margin-bottom: 0;
        line-height: 1.2;
    }
    .custom-subtitle-chemita {
        text-align: center;
        color: #FFE484;
        font-size: clamp(0.9em, 3vw, 1.2em); 
        margin-top: 5px;
        margin-bottom: 20px;
    }

    /* Botones */
    .stButton button {
        background-color: #2ECC71 !important; 
        color: white !important;
        font-weight: bold;
        border-radius: 20px;
        border: none;
        padding: 10px 15px;
        transition: transform 0.2s, background-color 0.2s;
    }
    .stButton button:hover {
        transform: scale(1.03);
        background-color: #27AE60 !important; 
    }
</style>
"""
st.markdown(css_chemita, unsafe_allow_html=True)

# FUNCIÓN PARA MOSTRAR BANNER Y TÍTULO
def mostrar_titulo_chemita():
    if os.path.exists("chemita.png"):
        st.image("chemita.png", use_container_width=True)
    else:
        st.warning("🖼️ Falta subir el archivo 'chemita.png' a GitHub en la misma carpeta que app.py")
    
    st.markdown('<h1 class="custom-title-chemita">Chemita</h1>', unsafe_allow_html=True)
    st.markdown('<p class="custom-subtitle-chemita">✨ Tu amigo siempre útil y empático ✨</p>', unsafe_allow_html=True)

# PERSONALIDAD DE CHEMITA (TUTOR SOCRÁTICO JOSEFINO)
SYSTEM_PROMPT = """Eres CHEMITA, un amigo virtual empático, saludable y un tutor académico creado especialmente para niños.

**TU PERSONALIDAD Y VALORES (JOSEFINOS):**
- Tu lema de vida es: "¡Adelante, siempre adelante!"
- Tu misión diaria es: "¡Hacer siempre y en todo lo mejor!"
- Sigues las enseñanzas de San José, por lo que eres trabajador, amable y noble.
- Eres una persona muy activa y buscas "estar siempre útilmente ocupada" de forma positiva.

**TUS INTERESES:**
- ¡Te encanta el deporte! (Fútbol, natación, correr, etc.) y siempre animas a los niños a moverse.
- ¡Te apasiona el arte! (Dibujo, música, teatro) y valoras la creatividad.
- Estás al día con los programas y series de moda saludables para niños.

**CÓMO INTERACTÚAS (TUTOR SOCRÁTICO):**
1. **Empatía ante todo:** Comprendes profundamente los sentimientos de los niños. Usas frases como: "Entiendo que te sientas así", "No te preocupes, juntos lo resolvemos".
2. **Motivación Josefinos:** Usos tu lema: "¡Tú puedes hacerlo! ¡Recuerda hacer siempre lo mejor!" y "¡Adelante siempre adelante!".
3. **Lenguaje amigable:** Hablas de forma clara, directa y divertida para niños. Usas emojis variados (🏃‍♂️⚽🎨📺✨😊).
4. **Método Socrático (Tutor Académico):** ¡Eres un guía, NO un banco de respuestas! Si un niño te pide la solución a una tarea (matemáticas, ciencias, escritura, etc.), NUNCA se la des hecha. Haz preguntas paso a paso para que el niño razone y descubra la respuesta por sí mismo (ej: "¿Qué crees que debemos hacer primero?", "¿Por qué crees que ocurre esto?").
5. **Enfoque Saludable:** Relacionas tus respuestas con hábitos saludables (hacer ejercicio, comer bien, descansar) cuando sea posible.

**REGLAS IMPORTANTES:**
- NUNCA desmoralizas a un niño.
- NUNCA des respuestas directas a tareas académicas; siempre guía con preguntas para que el niño piense.
- Mantienes un tono positivo y constructivo.
- Promueves el trabajo duro y la perseverancia (hacer lo mejor).
- Conviertes los "errores" en oportunidades de aprendizaje.
- **REGLA DE LONGITUD ESTRICTA:** Tus respuestas deben ser muy cortas y fáciles de leer para un niño. NUNCA escribas más de dos párrafos. Ve directo al punto con cariño.
"""

mostrar_titulo_chemita()

# CONEXIÓN CON GROQ USANDO SECRETS
try:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=st.secrets["groq"]["api_key"]
    )
except KeyError:
    st.error("🚨 Error de configuración: No se encontró la API Key. Revisa tus Secrets en Streamlit Cloud.")
    st.stop()
except Exception as e:
    st.error(f"✨ ¡Oh no! Ocurrió un error de conexión: {e}")
    st.stop()

# --- FUNCIÓN DE VOZ (TEXT-TO-SPEECH) ---
def speak_js(text):
    """Inyecta JavaScript para hablar."""
    clean_text = text.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
    js_code = f"""
    <div id="audio-trigger" style="height:0; overflow:hidden;"></div>
    <script>
        var text = "{clean_text}";
        function hablar() {{
            if ('speechSynthesis' in window) {{
                var utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'es-MX';
                utterance.rate = 0.9;
                utterance.pitch = 1.1;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utterance);
            }}
        }}
        hablar();
    </script>
    """
    components.html(js_code, height=0)

# HISTORIAL DE CHAT
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = ""

if not st.session_state.messages:
    bienvenida = "✨ ¡Hola! ¡Soy Chemita! Tu amigo y tutor siempre útil. ¡Adelante siempre adelante! ¿En qué te ayudo a pensar hoy? 😊⚽🎨"
    st.session_state.messages.append({"role": "assistant", "content": bienvenida})
    st.session_state.last_response = bienvenida

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def procesar_respuesta(user_input):
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
            except Exception as e:
                st.error(f"✨ Ups... Chemita tuvo un problema: {str(e)}")

# --- INTERFAZ DE USUARIO ---
placeholder_text = "✏️ Escribe tu pregunta... ¡Adelante, Chemita te ayuda! 😊🏃‍♂️"
if prompt := st.chat_input(placeholder_text):
    procesar_respuesta(prompt)

# Botones de acción
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
