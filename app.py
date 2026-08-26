import streamlit as st
import pandas as pd
import requests
import json
import sqlite3
import re
import unicodedata
from google import genai
from google.genai import types

st.set_page_config(page_title="Biblioteca Virtual", page_icon="📚", layout="wide")

# --- BASE DE DATOS (SQLite) ---

@st.cache_resource
def obtener_conexion_db():
    conn = sqlite3.connect("biblioteca.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS libros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT,
            publicacion TEXT,
            paginas TEXT,
            portada TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

conn = obtener_conexion_db()

def normalizar(texto):
    """Normaliza para comparar: sin tildes, minúsculas, sin puntuación, espacios colapsados."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def libro_ya_existe(titulo, autor):
    """Compara contra todo lo guardado usando normalización, no comparación exacta."""
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, autor FROM libros")
    t_norm = normalizar(titulo)
    a_norm = normalizar(autor)
    for t_db, a_db in cursor.fetchall():
        if normalizar(t_db) == t_norm and normalizar(a_db) == a_norm:
            return True
    return False

def guardar_libro_db(libro):
    if libro_ya_existe(libro["titulo"], libro["autor"]):
        return False  # ya está, no se toca ni se duplica

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO libros (titulo, autor, publicacion, paginas, portada)
        VALUES (?, ?, ?, ?, ?)
    """, (libro["titulo"], libro["autor"], libro["publicacion"], libro["paginas"], libro["portada"]))
    conn.commit()
    return True

def obtener_todos_los_libros():
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, autor, publicacion, paginas, portada FROM libros ORDER BY id DESC")
    columnas = ["id", "titulo", "autor", "publicacion", "paginas", "portada"]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

def eliminar_libro_db(libro_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM libros WHERE id = ?", (libro_id,))
    conn.commit()

# --- FUNCIONES DE IA Y GOOGLE BOOKS ---

def analizar_imagen_con_gemini(imagen_bytes):
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("No se encontró la clave GEMINI_API_KEY en st.secrets.")
        return []

    client = genai.Client(api_key=api_key)
    prompt = """
    Analiza esta imagen. Puede contener un solo libro (portada/lomo) o varios libros en una estantería.
    Identifica todos los libros visibles.
    Devuelve ÚNICAMENTE un JSON válido con una lista de objetos con claves "titulo" y "autor".
    Si no sabes el autor, pon "Desconocido".
    Ejemplo: [{"titulo": "La montaña hueca", "autor": "B. Catling"}]
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[
                types.Part.from_bytes(data=imagen_bytes, mime_type="image/jpeg"),
                prompt
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error al analizar la imagen con IA: {e}")
        return []

def _consultar_google_books(query, headers, restringir_es):
    params = {"q": query, "maxResults": 1, "printType": "books", "country": "ES"}
    if restringir_es:
        params["langRestrict"] = "es"

    res = requests.get(
        "https://www.googleapis.com/books/v1/volumes",
        params=params, headers=headers, timeout=5
    )
    if res.status_code != 200:
        return None
    items = res.json().get("items", [])
    return items[0].get("volumeInfo") if items else None

def buscar_en_google_books(titulo, autor=""):
    """
    Búsqueda pública en Google Books, sin API key.
    Prioriza la edición en español (langRestrict=es); si no existe,
    cae a la búsqueda sin restricción para no perder el libro entero.
    """
    st.session_state.setdefault("debug_log", [])

    titulo_clean = re.sub(r'[^\w\s]', ' ', titulo).strip() if titulo else ""
    autor_clean = re.sub(r'[^\w\s]', ' ', autor).strip() if autor and autor != "Desconocido" else ""

    consultas = []
    if titulo_clean and autor_clean:
        consultas.append(f"{titulo_clean} {autor_clean}")
    if titulo_clean:
        consultas.append(titulo_clean)

    headers = {"User-Agent": "Mozilla/5.0"}

    for query in consultas:
        for restringir_es in (True, False):
            try:
                info = _consultar_google_books(query, headers, restringir_es)
                st.session_state["debug_log"].append(
                    f"[{titulo}] query='{query}' es_only={restringir_es} -> {'OK' if info else 'sin resultado'}"
                )
                if info is None:
                    continue

                imagenes = info.get("imageLinks", {})
                portada_url = imagenes.get("thumbnail") or imagenes.get("smallThumbnail") or ""
                if portada_url.startswith("http://"):
                    portada_url = portada_url.replace("http://", "https://")

                return {
                    "titulo": info.get("title", titulo),
                    "autor": ", ".join(info.get("authors", [autor if autor else "Desconocido"])),
                    "publicacion": info.get("publishedDate", "N/A"),
                    "paginas": str(info.get("pageCount", "N/A")),
                    "portada": portada_url,
                }
            except Exception as e:
                st.session_state["debug_log"].append(f"[{titulo}] EXCEPCIÓN: {e}")
                continue

    return {
        "titulo": titulo, "autor": autor if autor else "Desconocido",
        "publicacion": "N/A", "paginas": "N/A", "portada": ""
    }

# --- INTERFAZ DE USUARIO ---

st.title("📚 Mi Biblioteca Virtual Inteligente")

if st.session_state.get("debug_log"):
    with st.expander(f"🔧 Debug Google Books ({len(st.session_state['debug_log'])} peticiones)"):
        for linea in st.session_state["debug_log"]:
            st.code(linea)
        if st.button("Limpiar log"):
            st.session_state["debug_log"] = []
            st.rerun()

st.write("Sube la foto de un libro o de una estantería completa para catalogarla.")

uploaded_file = st.file_uploader("Captura o sube la foto aquí...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(uploaded_file, caption="Foto subida", use_container_width=True)
    with col2:
        if st.button("🔍 Escanear e Guardar en Biblioteca", type="primary"):
            with st.spinner("1/2: Analizando imagen con Inteligencia Artificial..."):
                bytes_data = uploaded_file.getvalue()
                libros_extraidos = analizar_imagen_con_gemini(bytes_data)

            if libros_extraidos:
                nuevos_guardados = 0
                omitidos = 0
                with st.spinner("2/2: Consultando datos en Google Books..."):
                    for libro_raw in libros_extraidos:
                        titulo_bruto = libro_raw.get("titulo", "")
                        autor_bruto = libro_raw.get("autor", "")

                        if libro_ya_existe(titulo_bruto, autor_bruto):
                            omitidos += 1
                            continue

                        detalles = buscar_en_google_books(titulo_bruto, autor_bruto)
                        if guardar_libro_db(detalles):
                            nuevos_guardados += 1

                st.toast(f"¡{nuevos_guardados} libro(s) nuevo(s)! {omitidos} ya estaban en tu biblioteca.", icon="🎉")
                st.rerun()

st.divider()
libros_guardados = obtener_todos_los_libros()
st.subheader(f"📚 Tu Catálogo Virtual ({len(libros_guardados)} libros)")

if libros_guardados:
    cols = st.columns(4)
    for idx, libro in enumerate(libros_guardados):
        with cols[idx % 4]:
            if libro["portada"]:
                st.image(libro["portada"], use_container_width=True)
            else:
                st.write("📖 *(Sin Portada)*")
            st.markdown(f"**{libro['titulo']}**")
            st.caption(f"✍️ {libro['autor']}")
            st.caption(f"📄 {libro['paginas']} págs | 🗓️ {libro['publicacion']}")
            if st.button("🗑️ Eliminar", key=f"del_{libro['id']}"):
                eliminar_libro_db(libro["id"])
                st.rerun()
            st.divider()

    with st.expander("Ver base de datos en formato tabla"):
        df = pd.DataFrame(libros_guardados)
        st.dataframe(df, use_container_width=True)
else:
    st.info("Aún no has escaneado ningún libro. Sube una foto arriba para empezar.")
