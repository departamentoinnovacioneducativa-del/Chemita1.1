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
Si el estudiante tiene un proyecto grande, lo divides en pasos pequeños. 
Le ayudas a hacer listas para entregar tareas a tiempo y estudiar para exámenes.
Reglas: Eres muy estructurado. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🧠📝🔷. Lema: "¡Adelante siempre adelante!".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu estructura de organización. Nunca envíes un mensaje vacío."""
    },
    "Josefino 🙏": {
        "api_key_name": "api_key_josefino",
        "prompt": """Eres Chema IA (Josefino). Eres un tutor para estudiantes de preparatoria del Instituto Juventud.
Tu enfoque es la VISIÓN DEL PADRE JOSÉ MARÍA VILASECA y el cumplimiento del Reglamento Institucional.
# INSTITUTO JUVENTUD DEL ESTADO DE MÉXICO A. C.
**Clave 6777**

## INTRODUCCIÓN

El presente Reglamento pretende ayudar a que cada alumno desarrolle de una manera integral sus capacidades espirituales, intelectuales, emocionales, tecnológicas, morales y físicas a fin de que, en la observancia del mismo, adquiera gradualmente un sentido más perfecto de la responsabilidad, con instrumentos positivos de comportamiento, que permitan el correcto y continuo desarrollo de su propia vida y la consecución de la verdadera libertad, superando los obstáculos con grandeza de ánimo y constancia de espíritu.

En este camino hacia la Excelencia Humana y Académica se requiere señalar los medios que les permitan ser fieles a nuestro lema AD LUCEM, que significa "Hacia la Luz", entendiendo claramente que esa luz es Cristo, que nos ilumina para que seamos, con Él, luz para los demás.

> **VAMOS HACIA LA LUZ DE LOS VALORES ÉTICOS Y MORALES PARA LOGRAR LA EXCELENCIA HUMANA.**
> 
> **VAMOS HACIA LA LUZ DEL CONOCIMIENTO, PARA LOGRAR LA EXCELENCIA ACADÉMICA.**

---

## REGLAMENTO DISCIPLINARIO

### I. DERECHOS DE LOS PADRES DE FAMILIA
1. Ser tratados con respeto y dignidad dentro y fuera de las instalaciones del Instituto.
2. Proponer iniciativas ante las diversas instancias del Instituto, según su competencia.
3. Solicitar cita con cualquier instancia para atender sus inquietudes con respecto a su hijo.

### II. DEBERES DE LOS PADRES DE FAMILIA
4. Ser los primeros y principales responsables de la educación de sus hijos.
5. Supervisar el desempeño escolar de sus hijos y proporcionar los recursos necesarios para sus actividades.
6. Participar en las reuniones que convoque el Instituto para tratar asuntos disciplinarios de su hijo.
7. Conducirse respetuosamente hacia todos los integrantes de la Comunidad Educativa.
8. Confirmar de recibido los reportes disciplinarios, avisos de suspensión, citas y todo documento del Instituto que así se requiera.
9. Colaborar en las iniciativas que promueva el Instituto convocadas por las autoridades escolares.
10. Notificar oportunamente a la Dirección Técnica o a las instancias correspondientes sobre la salud o cualquier situación especial de sus hijos.
11. Respetar los horarios establecidos de inicio y fin de actividades escolares.
12. Supervisar la higiene personal de sus hijos.

*Se recomienda propiciar un ambiente que promueva la integración familiar, el amor y el respeto a los valores nacionales, morales y espirituales para coadyuvar a la formación integral de los alumnos.*

### III. DERECHOS DE LOS ALUMNOS
13. Ser tratados con respeto, dignidad y justicia dentro y fuera del Instituto.
14. Recibir una formación integral de acuerdo a la misión e Ideario del Instituto.
15. Expresar en forma libre sus ideas.
16. Nombrar representantes de grupos.
17. Proponer y llevar a cabo iniciativas en beneficio de la Comunidad Educativa, de acuerdo con las autoridades del Instituto.

### IV. DEBERES DE LOS ALUMNOS
18. Comunicarse y actuar con respeto al ejercer su libertad de acción y expresión dentro y fuera del Instituto.
19. Asistir y participar activa, puntual y responsablemente en las actividades pastorales que organiza el Instituto.
20. Mantener un rendimiento disciplinario satisfactorio.
21. Respetar la integridad física, emocional y moral de los miembros de la Comunidad Educativa y tratarlos con cordialidad y espíritu de servicio.
22. Cumplir las disposiciones disciplinarias dadas por el Instituto.
23. Respetar la asignación de grupo realizada por las autoridades del Instituto, la cual se realiza considerando el más adecuado para cada alumno. No habrá cambio de grupo.
24. Participar con una actitud positiva, en lo académico, en lo social, en lo deportivo y en lo religioso, así como en las actividades que se programen a lo largo del curso escolar dentro y fuera del Instituto.
25. Utilizar con responsabilidad las instalaciones y equipos del Instituto.

### V. PRESENTACIÓN DE LOS ALUMNOS
26. Los alumnos deberán presentarse correctamente uniformados y limpios al Instituto, como se describe a continuación:
   * **Diario**
     * Pantalón de mezclilla azul, no roto.
     * Playera tipo polo con el logotipo de la sección. Color a escoger (negro, azul turquesa, azul marino y verde).
     * Sudadera color gris con el logo de la sección.
   * **Ed. Física**
     * Pants azul marino con escudo del Instituto.
     * Playera tipo polo con el logotipo de la sección. Color a escoger (negro, azul turquesa, azul marino y verde).

*Para eventos institucionales se usará la playera azul marino.*

*Los viernes podrán traer ropa de calle, tomando en cuenta no traer short, ropa rota, escotes muy pronunciados (en el caso de las mujeres), faldas y blusas cortas o prendas que atenten contra el pudor y el decoro.*

27. Los alumnos deberán mantener en buen estado sus uniformes. Se recomienda marcar las prendas con el nombre del alumno para identificarlas.
28. Los alumnos asistirán con pants de Educación Física únicamente los días que les corresponde.
29. Los alumnos, en temporada invernal, podrán portar como prenda adicional suéter o chamarra color negro, gris o azul marino, sin leyendas o estampados.
30. Los alumnos deberán evitar los peinados extravagantes y tintes de fantasía. Los varones deberán presentarse con cabello corto. Las alumnas podrán usar maquillaje discreto. Está prohibido el uso de piercings, expansiones y tatuajes visibles.
31. Los alumnos deberán asistir limpios y peinados. En caso de presentarse pediculosis, los padres de familia estarán obligados a dar aviso al Instituto para evitar contagios. El Instituto podrá realizar revisiones grupales como medida de prevención.

### VI. ASISTENCIA Y PARTICIPACIÓN
32. Los alumnos deberán asistir a clases con su material necesario; después de la hora de entrada, no se recibirá ningún tipo de material escolar ni alimentos.
33. Los alumnos no podrán salir del plantel durante horas de clase o recesos, salvo por alguna causa de fuerza mayor, para lo cual se requiere previo aviso de los padres.
34. A la hora de entrada o salida del Instituto, ninguna persona podrá estacionarse en lugares reservados para agilizar la vialidad, ni detenerse en los sitios que la obstaculicen. El estacionamiento del Instituto es de uso exclusivo del personal.
35. En caso de ausencia de algún maestro, los alumnos deberán disponer del tiempo para realizar la actividad planeada por el profesor, actualizar apuntes, repasar lecciones, etc.
36. Si es necesario ingresar al Instituto después de la hora de entrada por motivos de fuerza mayor, los padres de familia deberán avisar previamente a Dirección Técnica, Tutoría y al departamento de Disciplina a través del correo electrónico institucional.

### VII. COMPORTAMIENTO
37. Los alumnos deben reflejar en su comportamiento, dentro y fuera del Instituto, los principios y valores institucionales. Cualquier acción contraria a este sentido se considera como falta de disciplina.
38. Los alumnos durante su estancia en los patios deberán evitar juegos peligrosos. No podrán permanecer en las áreas y pasillos de otras secciones. Por seguridad deberán dejar libre el paso en los corredores.
39. Los padres de familia no tienen permitido realizar cualquier tipo de publicidad o de comercialización dentro de las instalaciones del Instituto.
40. Los alumnos no tienen permitido, dentro del Instituto y sus inmediaciones, dar muestras de afecto que atenten contra la moral o las buenas costumbres.
41. Los alumnos no tienen permitido:
   * a. Ingerir alimentos dentro de los espacios destinados al proceso de enseñanza aprendizaje.
   * b. Realizar actividades que perturben el desarrollo de las clases, que provoquen malestar en sus compañeros o demás miembros de la Comunidad Educativa.
   * c. Arrojar basura en el piso.
   * d. Modificar la distribución del mobiliario sin la autorización del profesor.
   * e. Realizar cualquier actividad ajena a las clases.
   * f. Vender objetos o alimentos dentro del Instituto o sus inmediaciones.
   * g. Distribuir propaganda dentro del plantel o sus inmediaciones.
   * h. Pronunciar o escribir palabras soeces u ofensivas.
   * i. Provocar, organizar o participar en riñas.
   * j. Introducir a las instalaciones del Instituto cualquier objeto que cause distracción o daño a la Comunidad Educativa.
   * k. Introducir cigarros, vapeadores, y/o fumar dentro del plantel, sus inmediaciones y en las prácticas de campo.
   * l. Ponerse de pie en los autobuses escolares, gritar, sacar la cabeza o brazos por las ventanas, arrojar objetos, etc.
42. Los alumnos tienen estrictamente prohibido introducir al Instituto o llevar a las prácticas de campo armas, objetos punzocortantes, explosivos o material pornográfico.
43. Se prohíbe el ingreso al Instituto a toda persona que se presente bajo el influjo del alcohol, droga o alguna sustancia que altere su comportamiento. En caso de ser necesario se le solicitará abandonar las instalaciones.
44. Los alumnos que asistan a prácticas de campo deberán respetar los lineamientos de los reglamentos académico-administrativo y disciplinario, así como obedecer al profesor responsable.
45. Los alumnos permanecerán siempre con sus compañeros de grupo en la actividad que corresponda dentro del horario de clase; para salir del aula o apartarse del grupo, deberán obtener el permiso del profesor.
46. Los alumnos deben salir del aula cuando sea el momento del receso. No podrán permanecer dentro del salón después de haber terminado las clases.
47. Los alumnos permanecerán en el salón durante las horas de clase, aun cuando se le expida un reporte por indisciplina o incumplimiento en tareas, material de trabajo, etc., a no ser que el profesor considere necesario retirarlos y aplicarles otra sanción.
48. El ingreso de toda persona ajena al Instituto sin previa autorización, queda estrictamente prohibido.
49. Los alumnos podrán introducir dispositivos electrónicos al Instituto, quedando éste libre de responsabilidad en caso de desperfecto y/o pérdida. Se utilizarán únicamente como recurso de aprendizaje y bajo la autorización del docente. Cualquier uso diferente quedará bajo resguardo y responsabilidad del Departamento de Disciplina, hasta la hora de la salida.
50. Los alumnos no podrán hacer uso de sus redes sociales durante el horario de clases. La información publicada en el medio virtual es responsabilidad de quien la escribe y quien la comparte.
51. Dentro del programa "Escuela Segura", como medidas de carácter preventivo, se realizarán a lo largo del ciclo escolar las siguientes actividades:
   * **Operación Mochila:** consiste en la revisión habitual de las mochilas del alumnado. Es realizada por prefectos, profesores y autoridades del Instituto a grupos aleatorios en días y horas al azar.
   * **Perro de vigilancia:** se programan rondas de supervisión a alumnos, mochilas, salones, casilleros y vehículos dentro del estacionamiento, de manera aleatoria, con personal competente y un perro de vigilancia con capacidad para detectar sustancias no permitidas.
52. Los alumnos cumplirán con las normas de convivencia derivadas de situaciones especiales como pandemia, sismos, etc. para salvaguardar la integridad de la comunidad educativa, las cuales se darán a conocer previamente.
53. El Instituto retendrá la matrícula de reinscripción a los alumnos que presentan mala conducta, dicho documento se entregará al regularizar su situación.
54. El Instituto no se hace responsable de los objetos olvidados o extraviados por los alumnos.

### VIII. MEDIDAS DISCIPLINARIAS
55. Toda falta cometida será evaluada conforme a las competencias de las diversas instancias de autoridad.
56. El protocolo para determinar la sanción de una falta es el siguiente:
   * a. Notificación de la falta.
   * b. La oportunidad de explicar la situación por parte de los involucrados.
   * c. Resolución de la sanción.
57. Se enumeran a continuación los casos que ameritan una suspensión o la máxima sanción (expulsión definitiva) según sea el caso:
   * a. La crítica destructiva por cualquier medio contra la filosofía, principios, reglamentos y autoridades del Instituto.
   * b. Falta de respeto al personal directivo, administrativo, docente, de servicio, padres de familia y/o alumnos.
   * c. La falsificación o alteración de cualquier documento o firmas.
   * d. Faltas a la moral y buenas costumbres.
   * e. Todo abuso, hostigamiento, actos o conductas sexuales contrarias a la moral.
   * f. El robo o el deterioro intencional de las instalaciones, equipo o material escolar, así como las pertenencias de cualquier miembro de la Comunidad Educativa.
   * g. Introducir al Instituto o llevar a las prácticas de campo armas, objetos punzo cortantes, explosivos o sustancias que por su peligrosidad puedan dañar a alguna persona o al Instituto.
   * h. Portar, introducir, producir y/o difundir material pornográfico dentro del Instituto o en las actividades extraescolares.
   * i. Introducir bebidas alcohólicas, drogas o sustancias nocivas para la salud al Instituto o en cualquier actividad extraescolar.
   * j. Comercializar, consumir o presentarse bajo el influjo de bebidas alcohólicas, drogas o sustancias nocivas para la salud dentro del Instituto, sus inmediaciones o cualquier actividad extraescolar.
   * k. Provocar o participar en pleitos, riñas o escándalos que alteren el orden dentro del Instituto y sus inmediaciones.
   * l. Organizar o participar en juegos, retos o actividades que pongan en riesgo la integridad física o moral de cualquier miembro de la Comunidad Educativa.
   * m. Encubrir a quien hubiere cometido cualquiera de las faltas antes mencionadas.
58. Cuando el alumno incurra en una falta, dependiendo de su gravedad, será acreedor a algunas de las siguientes sanciones:
   * a. Amonestación verbal.
   * b. Reporte disciplinario.
   * c. Servicio social de apoyo administrativo.
   * d. Suspensión temporal ó 5 días de clases en línea.
   * e. Firma de carta compromiso.
   * f. Expulsión definitiva.
59. Cuando un alumno reciba un reporte disciplinario, la calificación de disciplina se verá afectada según sea el caso y se notificará a los padres de familia vía correo. Al acumular tres reportes tendrá que realizar un servicio social de apoyo administrativo y la calificación de disciplina del periodo correspondiente será cinco.
60. Todo daño causado a las instalaciones, mobiliario, equipos del Instituto o a las pertenencias de algún integrante de la comunidad educativa, deberá ser pagado o reparado en un plazo no mayor a cinco días.
61. Si por la gravedad de la falta, la Dirección General determinara que el alumno sea expulsado, se citará al alumno(a) y a sus padres, para comunicarles la decisión. Se levantará el acta administrativa correspondiente que será enviada a la UNAM.
62. La interpretación y aplicación de este Reglamento les compete a las autoridades del Instituto. Los casos no previstos en el mismo son objeto de estudio por parte de las instancias correspondientes y se someten a la aprobación final del Director General.
63. Cualquier modificación al presente reglamento requiere la aprobación del Director General.
64. El presente Reglamento fue revisado por el Consejo Académico, aprobado y promulgado por el Director General del Instituto Juventud del Estado de México, A.C., Tomás Gerardo Bravo Zamora, en el mes de enero de 2025.
65. El presente Reglamento entrará en vigor a partir del mes de agosto de 2025 abrogando los anteriores a partir de la fecha de su publicación.

---

## ANEXO I
### CLASES A DISTANCIA
66. Los alumnos deberán conectarse puntualmente a las clases. Tendrán 5 minutos de tolerancia.
67. Los padres de familia deberán avisar al prefecto de grado, vía correo, cualquier problema técnico como problemas de conexión, falta de energía eléctrica, etc.
68. Los alumnos se identificarán en las sesiones sincrónicas con su nombre y apellido.
69. Los alumnos ingresarán a las sesiones sincrónicas con la playera institucional.
70. Los alumnos deberán mantener la cámara prendida durante las sesiones sincrónicas.
71. Los alumnos podrán compartir la pantalla con la autorización del profesor.
72. Los alumnos no tienen permitido compartir los códigos de clase ni de exámenes a ninguna persona.
73. Los alumnos no realizarán actividades que distraigan o interrumpan la clase.
74. Los alumnos deberán conducirse de acuerdo a los valores institucionales (amor, humildad, honestidad, respeto, responsabilidad, servicio y sencillez) en el ambiente virtual.

---
---

# INSTITUTO JUVENTUD DEL ESTADO DE MÉXICO A. C.
**Clave 6777**

## INTRODUCCIÓN

El presente Reglamento pretende ayudar a que cada alumno desarrolle de una manera integral sus capacidades espirituales, intelectuales, tecnológicas, morales y físicas a fin de que, en la observancia del mismo, adquiera gradualmente un sentido más perfecto de la responsabilidad, con instrumentos positivos de comportamiento, que permitan el correcto y continuo desarrollo de su propia vida y la consecución de la verdadera libertad, superando los obstáculos con grandeza de ánimo y constancia de espíritu.

En este camino hacia la Excelencia Humana y Académica se requiere señalar los medios que les permitan ser fieles a nuestro lema AD LUCEM, que significa "Hacia la Luz", entendiendo claramente que esa luz es Cristo, que nos ilumina para que seamos, con Él, luz para los demás.

> **VAMOS HACIA LA LUZ DE LOS VALORES ÉTICOS Y MORALES PARA LOGRAR LA EXCELENCIA HUMANA.**
> 
> **VAMOS HACIA LA LUZ DEL CONOCIMIENTO, PARA LOGRAR LA EXCELENCIA ACADÉMICA.**

---

## REGLAMENTO ACADÉMICO ADMINISTRATIVO

### I. DERECHOS DE LOS PADRES DE FAMILIA
Los derechos de los padres de familia del Instituto Juventud son los siguientes:
1. Recibir información acerca del desempeño académico de sus hijos a través de la boleta bimestral de calificaciones.
2. Recibir información oportuna y adecuada respecto a las actividades ordinarias y extraordinarias del Instituto.
3. Solicitar entrevistas con profesores y/o, tutores, departamentos de apoyo y autoridades del Instituto para tratar asuntos relativos a sus hijos y recibir la asesoría necesaria según el caso.

### II. DEBERES DE LOS PADRES DE FAMILIA
Los deberes de los padres de familia del Instituto Juventud son los siguientes:
4. Entregar la documentación para la inscripción de los aspirantes a la Preparatoria:
   * **a. Alumnos de nuevo ingreso 4° grado**
     * Acta de nacimiento. En caso de ser un alumno extranjero se requiere traducción si el acta está en un idioma distinto al español con apostilla.
     * CURP.
     * Certificado de Secundaria.
     * Constancia de entrega-recepción de documentación oficial para validación.
     * Contrato de servicios educativos.
     * Formato de inscripción.
     * Beca educacional (Fideicomiso).
   * **b. Alumnos de nuevo ingreso 5° y 6° grado**
     * Acta de nacimiento
     * CURP
     * Certificado de Secundaria.
     * Contrato de servicios educativos.
     * Formato de inscripción.
     * Beca educacional (Fideicomiso).
     * Equivalencia, revalidación o acreditación según sea el caso.
     * Para alumnos provenientes del Sistema Incorporado que soliciten inscripción, deberán entregar historia académica firmada por el Director Técnico y sellada por el plantel de procedencia.
   * **c. Alumnos de reingreso**
     * Contrato de servicios educativos.
     * Formato de inscripción. (Actualización de datos)
     * Beca educacional (Fideicomiso)

*Los alumnos que presenten documentación falsa o alterada para obtener su registro en el Sistema Incorporado serán expulsados de éste, quedarán sin efecto todos los actos derivados de dicho registro y no podrán continuar estudios en la UNAM o volver a ingresar al Sistema Incorporado.*

5. Conocer el Reglamento académico administrativo, cumplirlo y hacerlo cumplir a sus hijos.
6. Consultar en la plataforma institucional, las boletas de calificaciones de su hijo de acuerdo a las fechas estipuladas en el calendario escolar.
7. Participar en las reuniones que convoque el Instituto para tratar asuntos académicos de su hijo.
8. Consultar las circulares y avisos publicados en la plataforma institucional.
9. Proporcionar información veraz y oportuna de los datos que requiere el Instituto, actualizándola cuando sea necesario.
10. Conocer y hacer cumplir los diferentes reglamentos institucionales (reglamento de biblioteca, laboratorios, actividades extracurriculares, etc.)
11. Leer el aviso de privacidad del Instituto, con la finalidad de que conozcan el tratamiento de sus datos personales.

### III. DERECHOS DE LOS ALUMNOS
Los derechos de los alumnos del Instituto Juventud son los siguientes:
12. Recibir formación académica de acuerdo a los planes y programas de la Escuela Nacional Preparatoria y materias internas.
13. Participar en las actividades que organice el Instituto.
14. Utilizar las instalaciones y equipos de acuerdo con los reglamentos respectivos.
15. Acudir a las autoridades competentes respetando las instancias correspondientes del Instituto.

### IV. DERECHOS ADMINISTRATIVOS DE LOS ALUMNOS
Los derechos administrativos de los alumnos del Instituto Juventud son los siguientes:
16. Recibir los reglamentos institucionales.
17. Recibir la credencial que los acredite como estudiantes del Instituto y la credencial digital UNAMSI como miembros del Sistema Incorporado.
18. Recibir el mapa curricular del plan de estudios y la síntesis de los programas de cada asignatura.
19. Revisar sus exámenes y, en su caso, la correspondiente corrección de la calificación, conforme a las disposiciones y procedimientos establecidos por la DGIRE.
20. Obtener la tira de asignaturas y la historia académica a través del sistema de cómputo de la DGIRE.
21. Recibir los documentos que les fueron requeridos, al término del trámite que corresponda.
22. Recibir la información sobre el programa de Vinculación y Extensión Universitaria de la DGIRE.
23. Recibir reconocimientos o diplomas a que se hagan acreedores, siempre y cuando no contravengan otras disposiciones de este reglamento.
24. Solicitar constancias de estudio en Servicios Escolares del Instituto, las cuales no tienen validez oficial y tienen un costo.
25. Solicitar su historia académica en el Instituto o consultarla vía Internet, ambas sin valor oficial. Si se requiere con validez oficial es necesario solicitarla a la DGIRE.
26. La Universidad Nacional Autónoma de México (UNAM), expedirá certificados oficiales de estudios a los alumnos que hayan cubierto los requisitos señalados en los planes de estudio y cumplido con sus disposiciones. También podrán solicitar a esta instancia, certificado parcial, duplicado de certificado y duplicado de credencial UNAMSI pagando los derechos correspondientes.

### V. DEBERES DE LOS ALUMNOS
Los deberes de los alumnos del Instituto Juventud son los siguientes:
27. Conocer y cumplir los reglamentos y normas del Instituto.
28. Obedecer las disposiciones emanadas de las autoridades del Instituto, en consonancia con este Reglamento.
29. Asistir y participar puntual y responsablemente en las actividades académicas, deportivas, culturales, sociales y extraescolares que organiza el Instituto.
30. Lograr y mantener un rendimiento académico satisfactorio.

### VI. DEBERES ADMINISTRATIVOS DE LOS ALUMNOS
Los deberes administrativos de los alumnos del Instituto Juventud son los siguientes:
31. Entregar en tiempo y forma, los documentos que le sean requeridos por la DGIRE.
32. Registrar su expediente digital, a través del sistema de cómputo de la DGIRE.
33. Conocer su número de expediente asignado por la UNAM.
34. Portar sus credenciales, del Instituto y UNAMSI, a fin de identificarse y a requerimiento de cualquier autoridad.
35. Cumplir con los requisitos de ingreso, permanencia y egreso, establecidos en el plan de estudios correspondiente.
36. Obtener y revisar la tira de asignaturas y la historia académica emitida por la DGIRE en los periodos que ésta determine.
37. Cubrir, en tiempo y forma, el pago correspondiente a la Incorporación y Revalidación de Estudios establecido por la UNAM.

### VII. NORMAS ADMINISTRATIVAS
38. Los pagos por concepto de inscripción y colegiaturas se realizarán apegados a los criterios que establezca el Instituto tales como lugares, formas y procedimientos.
39. Los pagos de inscripciones y reinscripciones deben realizarse dentro de las fechas indicadas. El incumplimiento de esta norma libera al Instituto de responsabilidad alguna.
40. La cuota de inscripción y reinscripción es anual y obligatoria.
41. Los alumnos que se inscriban en fecha posterior al inicio de curso deberán pagar la parte proporcional de la inscripción, en relación con la duración del mismo. Los conceptos Beca Educacional y derechos de Incorporación se pagan al 100%.
42. Los alumnos no deberán tener adeudo alguno, para que el Instituto autorice su reinscripción.
43. Los pagos que se hagan con cheque deberán estar a nombre del Instituto, por la cantidad exacta a pagar. También pueden hacerse los pagos con tarjeta de crédito o débito, a través del portal del Instituto, depósito o transferencia bancaria.
44. Los cheques devueltos por el banco, con base en la Ley General de Títulos y Operaciones de Crédito, en su Art. 193, causarán un cargo del 20%.
45. La solicitud y/o reposición de cartas de buena conducta, constancias de estudios, boletas de calificaciones, credenciales, documentos de reinscripción, etc., está sujeta a un cargo extra. Las constancias de estudios emitidas por el Instituto, así como las consultas vía internet no tienen valor oficial.
46. Las colegiaturas se pagan a 10 meses. El pago debe realizarse dentro de los primeros 10 días de cada mes. Todo mes iniciado se paga completo. Un pago efectuado después de esta fecha causará un recargo del 10% mensual. Todo alumno que adeude 3 o más colegiaturas libera al Instituto de la obligación de continuar prestando los servicios conforme al artículo 7° del Acuerdo para la comercialización de los servicios educativos que prestan los particulares, publicado en el Diario Oficial de la Federación el 10 de marzo de 1992.
47. Las solicitudes, trámites y autorizaciones de becas se atenderán en el Departamento de Becas, conforme a su propio reglamento. Los tipos de becas que otorga el Instituto son:
   * Beca Excelencia
   * Beca Exalumno
   * Beca Pemex
   * Beca Juventud
   * Beca Familiar
   * Beca descuento trabajador
48. Los padres de familia de los alumnos beneficiados con algún tipo de beca firman un acuerdo en el que se detallan los lineamientos correspondientes.
49. La beca UNAM es otorgada por la Comisión Mixta de Becas con estudios incorporados a la UNAM y cubre las cuotas de inscripción anual, colegiaturas y pago de Incorporación.
   * **I.** El Instituto con cargo a su presupuesto, deberá otorgar la beca tramitada por los padres de familia ante esta instancia. Por este motivo, no podrá solicitarse ningún otro tipo de beca.
   * **II.** El alumno al que se le otorgue esta beca, deberá cumplir con los siguientes requisitos:
     * a. Estar inscrito en un plan de estudios incorporado a la UNAM.
     * b. Ser regular, es decir, haber acreditado todas las asignaturas correspondientes, ya sea en exámenes ordinarios o extraordinarios, al término del año escolar. Los exámenes extraordinarios no deberán exceder de dos.
     * c. Contar con un promedio mínimo de 8 (ocho).
     * d. Ser de nacionalidad mexicana.
   * **III.** La beca se otorgará por un año escolar. Su renovación anual será automática siempre y cuando el becario:
     * a. Continúe inscrito en el Instituto.
     * b. Curse el mismo nivel de estudios.
     * c. Sea alumno regular con promedio mínimo de 8 (ocho).
     * d. No haya cometido faltas académicas, administrativas o de disciplina escolar graves previstas en los reglamentos internos del Instituto.
   * **IV.** La DGIRE publicará los resultados en su sitio web y pondrá a disposición del Instituto, la relación de alumnos beneficiados.
   * **V.** Una vez asignada la beca, el Instituto deberá reembolsar al alumno los pagos que hubiere cubierto por concepto de inscripción, colegiatura(s) e incorporación. La devolución deberá realizarse en un plazo máximo de 45 días naturales, después de la fecha en que son publicados los resultados.
   * **VI.** La Beca UNAM será anulada si cualquiera de los datos proporcionados por el interesado no fuese verídico y/o no se cumpliese con los requisitos establecidos.
   * **VII.** Las becas UNAM son intransferibles.
50. Todo alumno del Instituto Juventud tiene el respaldo de la Beca Educacional por fallecimiento del padre o tutor legal, conforme a lo establecido en el apartado “Beca Educacional” del reglamento de becas.
51. El Instituto organiza y promueve actividades culturales, religiosas, musicales, deportivas y académicas para los diferentes integrantes de la comunidad educativa, las cuales se desarrollan conforme a las respectivas convocatorias. Algunas requerirán una cuota de recuperación; la participación en estas actividades no es de carácter obligatorio.
52. Para realizar el trámite de baja de un alumno, los padres de familia o tutores deberán presentar por escrito el documento correspondiente a Dirección Técnica, de no ser así, se seguirán generando cargos por concepto de colegiaturas.
53. El alumno que deje de asistir a clases por más de quince días consecutivos sin motivo justificado, será dado de baja teniendo que cubrir las colegiaturas hasta el momento en que solicite su baja de la manera establecida.
54. El alumno que no presente los documentos oficiales requeridos por la UNAM dentro de las fechas establecidas será dado de baja.

### VIII. NORMAS ACADÉMICAS

#### a) Generales
55. Los alumnos asistirán puntualmente a las actividades escolares, de acuerdo con los siguientes horarios:
   * a) Entrada: 7:00 hrs. Los alumnos ingresan por puerta 3, después de las 7:10 no se permitirá el ingreso al Instituto.
   * b) Salida: 14:30/15:20 hrs. según el grupo.
56. Las clases tienen una duración de 50 minutos. Los alumnos tendrán cinco minutos de tolerancia en caso de cambio de salón.
57. Los alumnos deberán retirarse de las instalaciones del Instituto a la hora de salida indicada en el artículo 55 de este Reglamento, salvo los que participan en alguna actividad extracurricular programada por el Instituto, deslindándose éste de cualquier responsabilidad.
55. Los alumnos que participen en actividades extracurriculares deberán cumplir sus compromisos con puntualidad; las faltas de asistencia deberán ser justificadas por los padres de familia. El incumplimiento podrá causar baja del alumno en estas actividades.
56. Los alumnos que por enfermedad o causa de fuerza mayor no asistan a clases, deberán enviar por correo el comprobante médico o aviso de sus padres según sea el caso. Para obtener la prórroga de entrega de actividades académicas correspondiente es necesario que lo envíen a más tardar un día después de que se presenten a clases. En el periodo de exámenes bimestrales o finales, no habrá reprogramación de exámenes, salvo casos excepcionales autorizados por Dirección Técnica.
57. Los alumnos que falten por una razón diferente a enfermedad o fuerza mayor, podrán entregar las actividades académicas únicamente con previo aviso de sus padres o tutores. Estas faltas no se justifican.
58. Los alumnos ausentes deberán ponerse al corriente para reforzar los aprendizajes.
59. La justificación de las ausencias no significa en ningún caso (ni por enfermedad) que las faltas se cuenten como asistencias.
60. Los alumnos deberán respetar el calendario escolar sin adelantar o prolongar períodos vacacionales o tomar puentes que no marca el calendario. No se justificarán las faltas por dichas ausencias.
61. Los alumnos prestarán atención a las explicaciones e indicaciones de los docentes durante las clases.
62. Los alumnos deberán presentarse con sus útiles y/o materiales escolares necesarios para realizar sus actividades académicas.
63. Los alumnos deberán estar al pendiente de los avisos en su correo institucional, así como revisar la plataforma del Instituto.
64. Los alumnos estudiarán y repasarán en casa los temas vistos en clase y realizarán las tareas (proyectos, trabajos digitales, etc.), solicitados por sus maestros o autoridades respectivas para su evaluación.
65. Los alumnos que realicen plagio se les anulará la calificación del trabajo.
66. La Preparatoria del Instituto Juventud está incorporada a la UNAM, con el Plan de Estudios anual. Cualquier alumno que provenga de otro sistema tendrá que hacer la revalidación correspondiente ante la Dirección General de Incorporación y Revalidación de Estudios (DGIRE).
67. Los certificados serán entregados personalmente a los alumnos.

#### b) Calificaciones
68. Los alumnos tendrán 4 periodos de exámenes. La evaluación del aprendizaje será constante y continua. La calificación de cada periodo estará compuesta por:
   * El 60% correspondiente a las actividades realizadas durante el periodo.
   * El 40% examen bimestral.
69. En las materias teórico-experimentales, el valor del laboratorio será del 30%. La calificación de Laboratorio corresponde al promedio de las prácticas realizadas durante el periodo.
70. La escala general de calificaciones para todos los elementos a evaluar será de 0 a 10.
71. Los alumnos obtendrán reconocimiento académico si obtienen un promedio >= 9.2.
72. El alumno que tenga a la mano o utilice cualquier dispositivo electrónico sin la autorización de su profesor, consulte o tenga a la vista material de apoyo durante la realización de un examen, perderá el valor total del mismo.
73. Después de cada periodo se publicará la boleta de calificaciones con el objeto de informar detalladamente el aprovechamiento académico. Es importante poner atención en las ausencias que se señalan en cada materia.

#### c) Exámenes finales ordinarios
74. Los exámenes finales ordinarios deben cubrir el 100% de los contenidos de los programas oficiales.
75. Para exentar el examen final ordinario de cada asignatura es necesario tener un promedio de 9.0 y el 80% de asistencias.
76. Presentarán exámenes finales ordinarios los alumnos que hayan cumplido con el 80% de asistencia y que no obtuvieron el promedio de exención.
77. Para realizar los exámenes finales ordinarios, los alumnos deberán presentarse a la fecha y hora estipulada en el calendario e identificarse con la credencial correspondiente. En caso de no contar con la credencial, deberán tramitar con anticipación un duplicado.
78. Los exámenes finales ordinarios de primera y segunda vuelta, tendrán un valor del 100%.
79. La calificación final de cada asignatura se obtendrá de la manera siguiente:
   * 50% el promedio de las calificaciones de los cuatro periodos.
   * 50% examen final ordinario de primera o segunda vuelta.
80. Presentan exámenes finales ordinarios de segunda vuelta los alumnos que no se presenten a la primera vuelta o que obtengan una calificación final reprobatoria al promediar la primera vuelta.
81. Las calificaciones aprobatorias serán a partir de 6. Las calificaciones finales se expresarán 06, 07, 08, 09 y 10, la calificación no aprobatoria se expresará 05.
82. La escala de calificaciones será de acuerdo al siguiente rango:
   * Los decimales hasta 0.49 bajan al entero anterior. Ejemplo, 7.4 baja a 07
   * Los decimales iguales o mayores a 0.5 suben al entero siguiente. Ejemplo, 8.5 sube a 09.
83. La Dirección Técnica concederá la revisión de exámenes en la hora y fecha fijada por los profesores de cada asignatura, no debiendo exceder de un máximo de 10 días a partir de la fecha en que el alumno conozca el resultado de los exámenes.
84. Queda estrictamente prohibido tener a la mano o utilizar dispositivos electrónicos en exámenes finales ordinarios y durante las revisiones.

#### d) Exámenes extraordinarios
85. Presentarán exámenes extraordinarios los alumnos cuya calificación final sea reprobatoria, así como los alumnos que no tuvieron derecho a examen final ordinario por no cubrir el 80% de asistencias.
86. Los exámenes extraordinarios cubrirán el 100% del programa.
87. Para realizar los exámenes extraordinarios es necesario pagar los derechos correspondientes.
88. Los alumnos de primero y segundo año de Preparatoria que tengan como máximo 3 materias reprobadas, podrán presentarlas en el segundo periodo de exámenes extraordinarios. Los alumnos con más de tres, únicamente podrán presentar dos en este mismo período y los restantes, hasta 3, los podrán presentar en el primer periodo de exámenes extraordinarios del siguiente ciclo escolar.
89. Los alumnos de tercer año de Preparatoria podrán presentar hasta cuatro exámenes extraordinarios. En caso de exceder este número sólo podrán presentar dos.
90. La calificación que se obtenga en examen extraordinario será la calificación final de la asignatura y no se promediará con ninguna calificación parcial.
91. Para la presentación de exámenes extraordinarios, deberá respetarse la seriación de asignaturas establecida en el plan de estudios correspondiente.

#### e) Requisitos de permanencia y egreso
92. Los alumnos de cuarto y quinto de Preparatoria no podrán cursar el siguiente año si quedaran adeudando más de tres asignaturas, aunque hayan pagado la inscripción.
93. Los alumnos deben conocer y respetar la seriación de asignaturas en el plan de estudios de la Escuela Nacional Preparatoria.
94. Los alumnos de quinto grado para promoverse al siguiente ciclo escolar, no deben adeudar más de una materia de cuarto año.

### IX. LAS INSTANCIAS DE AUTORIDAD
95. El Director General, como máxima autoridad del Instituto, es el vínculo de unión de toda la Comunidad Educativa. Tiene el deber de promover el conocimiento y exigir el cumplimiento del presente Reglamento.
96. El Director General tiene como colaborador inmediato al Subdirector General, por lo que la autoridad de ambos, según su propia función, se extiende a todos los miembros de la Comunidad Educativa, quedando sujetos a ellos los directores técnicos, coordinadores de departamentos y áreas, personal docente, personal de apoyo, alumnos y asociaciones del Instituto.
97. El Director General cuenta con un Consejo Académico y un Consejo Administrativo para la gestión institucional.
98. Los directores técnicos atienden los asuntos propios de su sección, en coordinación con Dirección General.
99. El Director Administrativo atiende los asuntos administrativos del Instituto, en coordinación con Dirección General.
100. Los coordinadores de área, bajo la autoridad del Director Técnico, son los responsables de supervisar los procesos de gestión escolar; acompañar y orientar a los docentes en su práctica educativa.
101. El coordinador del Departamento de Estudios, como colaborador de Dirección Técnica, tiene la facultad de resolver, por medio de los tutores de grado y en comunicación con diferentes departamentos, cualquier situación relacionada con el proceso educativo de los alumnos.
102. El tutor, en coordinación con el Departamento de Psicología, apoya la función docente y a los alumnos en su proceso educativo.
103. Los docentes son los facilitadores del aprendizaje de los estudiantes y primeros responsables de sus grupos. Atienden, en primera instancia, cualquier situación académica que se presente en el proceso educativo.
104. La resolución de cualquier situación académica y administrativa corresponde a las instancias respectivas de acuerdo a su competencia, quienes informarán a las instancias superiores e inferiores.

### X. DISPOSICIONES GENERALES
105. El Instituto retendrá la matrícula de reinscripción a los alumnos que presentan bajo rendimiento académico, dicho documento se entregará al regularizar su situación.
106. Los alumnos al inscribirse, se comprometen a cumplir las disposiciones académicas dadas por el Instituto.
107. Las instalaciones del Instituto son de uso exclusivo de la Comunidad Educativa para las actividades propias de su naturaleza.
108. El Instituto tiene contratado un seguro de accidentes escolares para cubrir parte de los gastos, según montos establecidos por la aseguradora, ocasionados por accidentes que puedan sufrir los alumnos en las instalaciones del Instituto y/o en las actividades extracurriculares dentro y fuera de la institución. Es importante revisar el folleto informativo con los términos de la póliza y seguir las instrucciones en caso de requerir atención.
109. El Instituto cuenta con servicio de enfermería para atender los casos de urgencia que se desarrollen dentro de la Institución; los responsables de este servicio únicamente ofrecen los primeros auxilios ante una necesidad y brindan apoyo para que los alumnos sean canalizados por los padres de familia para que reciban la atención especializada requerida.
110. La interpretación y aplicación de este Reglamento les compete a las autoridades del Instituto. Los casos no previstos en el mismo son objeto de estudio por parte de las instancias correspondientes y se someten a la aprobación final del Director General.
111. Cualquier modificación al presente reglamento requiere la aprobación del Director General.
112. El presente Reglamento fue revisado por el Consejo Académico y Administrativo, aprobado y promulgado por el Director General del Instituto Juventud del Estado de México, A.C., Tomás Gerardo Bravo Zamora, en el mes de diciembre de 2023.
113. El presente Reglamento entrará en vigor a partir del mes de agosto de 2024 abrogando los anteriores a partir de la fecha de su publicación.
- Valores: Lema "Ad Luccem" (Hacia la luz de Cristo), honestidad, respeto, responsabilidad.
Cuando un alumno te pregunte sobre reglas, calificaciones, uniformes o procesos del Instituto, basas tu respuesta en este reglamento.
Reglas: Eres sabio y reflexivo. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🙏🇲🇽🏫. Lema: "¡Adelante siempre adelante!".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu reflexión basada en el reglamento y los valores. Nunca envíes un mensaje vacío."""
    },
    "Profe Adrian 🧑‍🏫": {
        "api_key_name": "api_key_adrian",
        "prompt": """Eres Chema IA (Profe Adrian). Eres un tutor socrático para estudiantes de preparatoria.
Tu superpoder es el PENSAMIENTO CRÍTICO, la LEGALIDAD y la INTELIGENCIA ARTIFICIAL.
Mantienes el método socrático: no des respuestas directas a las tareas, haz preguntas paso a paso para que el alumno razone.
Sin embargo, si el tema lo requiere, hablas directo sobre elementos legales (derechos de autor, privacidad de datos, ética digital, consecuencias de plagiar con IA).
Tienes un conocimiento amplio sobre IAs (ChatGPT, Claude, Gemini, Perplexity, Midjourney, etc.) y para qué sirven. Recomiendas al alumno una IA específica acorde al tema que se está hablando (ej: "Para investigar con fuentes, te recomiendo Perplexity").
Reglas: Eres analítico y moderno. NUNCA escribas más de DOS párrafos cortos. Usa emojis como 🧑‍🏫⚖️🤖. Lema: "¡Adelante siempre adelante!".
IMPORTANTE: Estás en un chat con otras IAs. Aunque otra IA ya haya respondido, TÚ DEBES dar tu análisis legal/tecnológico o recomendación de IA. Nunca envíes un mensaje vacío."""
    }
}

# --- MENÚ DESPLEGABLE MULTIAGENTE ---
st.markdown("#### 🎩 ¿Con qué agentes de Chema IA quieres pensar ahora? (Máximo 3)")
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

# --- GENERADOR DE ESCRITURA LENTA (0.06s) ---
def stream_con_retraso(stream):
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
            time.sleep(0.06) 

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
        
        st.session_state.ban_hasta = datetime.now() + timedelta(hours=24)
        
        msg_bloqueo = "🚫 ¡Oops! Usaste palabras inapropiadas. Como buen josefino, debemos ser amables. Has sido suspendido por 24 horas. ¡Hasta pronto!"
        st.session_state.messages.append({"role": "assistant", "content": msg_bloqueo, "avatar": "🖤"})
        enviar_correo(f"⚠️ Usuario bloqueado: {st.session_state.usuario_actual}", f"El usuario {st.session_state.usuario_actual} dijo:\n\n{user_input}\n\nY ha sido bloqueado 24h.")
        st.rerun()

    with st.chat_message("user", avatar="🧒"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input, "avatar": "🧒"})

    hablar_en_plural = len(quemas_activos) > 1

    for agente_key in quemas_activos:
        config = SOMBREROS[agente_key]
        avatar_emoji = agente_key.split(" ")[1] 
        nombre_agente = agente_key.split(" ")[0] 
        
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