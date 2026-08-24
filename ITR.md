```python
itr_content = """# Documento de Requisitos e Historial del Proyecto (ITR)

**Proyecto:** Biblioteca Virtual Inteligente  
**Fecha de Emisión:** 24 de Agosto de 2026  
**Versión:** 1.0.0  
**Estado:** Desplegado en Streamlit Community Cloud & GitHub  

---

## 1. Visión General del Proyecto

La **Biblioteca Virtual Inteligente** es una aplicación web *Low-Code* desarrollada en Python con **Streamlit** que permite a usuarios catalogar su colección de libros físicos a partir de fotografías de portadas individuales o de estanterías completas (múltiples lomos). 

El sistema utiliza modelos de visión por inteligencia artificial (**Google Gemini 2.5 Flash**) para detectar los libros presentes en las imágenes y extrae sus metadatos detallados (portada oficial, número de páginas, año de publicación e ISBN) mediante la **API pública de Google Books**, guardando la información de manera persistente en una base de datos **SQLite**.

---

## 2. Historial de Requisitos Solicitados y Evolución del Proyecto

A lo largo del desarrollo conversacional se plantearon y resolvieron de forma progresiva las siguientes necesidades y requerimientos:

### Fase 1: Concepción de la Idea y Definición de Arquitectura
* **Solicitud del usuario:** Crear una biblioteca virtual a partir de fotos de estanterías/libros sin requerir conocimientos profundos de programación.
* **Propuesta y decisión:** Se evaluaron tres alternativas (No-Code con Make/Glide, Soluciones comerciales y Desarrollo asistido por IA). Se optó por el **Desarrollo Asistido por IA** utilizando Python + Streamlit + Gemini Vision + Google Books API.

### Fase 2: Configuración del Entorno sin Instalación Local
* **Solicitud del usuario:** No realizar instalaciones locales inicialmente, trabajar mediante un repositorio en GitHub y desplegar la app en la nube.
* **Solución técnica:** Uso de **GitHub** como control de versiones y **Streamlit Community Cloud** (`share.streamlit.io`) como servidor de despliegue gratuito con enlace público.

### Fase 3: Integración de Modelos de Visión e Inteligencia Artificial
* **Solicitud del usuario:** Conectar la API de Google Gemini para interpretar imágenes de estanterías (múltiples lomos) o portadas y extraer títulos/autores.
* **Solución técnica:**
  * Uso de la librería `google-genai` con el modelo `gemini-2.5-flash`.
  * Configuración de un *prompt* en formato estructurado JSON (`response_mime_type="application/json"`).
  * Gestión segura de credenciales mediante **Streamlit Secrets** (`st.secrets["GEMINI_API_KEY"]`).

### Fase 4: Enriquecimiento Automático de Datos y Portadas
* **Solicitud del usuario:** Obtener las portadas oficiales de los libros, páginas, año de publicación y código ISBN.
* **Solución técnica:** Consulta automática en segundo plano a la **API pública de Google Books** (`https://www.googleapis.com/books/v1/volumes?q=...`), formateando URLs de portadas a `https` para evitar errores de seguridad.

### Fase 5: Persistencia de Datos y Gestión del Frontend
* **Solicitud del usuario:** Evitar que los libros escaneados se borren al cerrar la aplicación o recargar el navegador.
* **Solución técnica:**
  * Implementación de base de datos **SQLite** (`biblioteca.db`) local.
  * Verificación y prevención de duplicados por combinación de ISBN o Título/Autor.
  * Botón para eliminar registros individuales (`🗑️ Eliminar`).
  * Integración de caché de recursos con `@st.cache_resource` para gestionar las conexiones a la BD.

### Fase 6: Preparación para GitHub, Despliegue y Personalización
* **Solicitud del usuario:** Generar todos los archivos necesarios del repositorio, changelog de la V1 y resolver dudas sobre la personalización visual e integración de las APIs.
* **Entregables creados:**
  1. `app.py`: Código fuente principal.
  2. `requirements.txt`: Lista de dependencias (`streamlit`, `google-genai`, `requests`, `pandas`, `pillow`).
  3. `.gitignore`: Regla para ignorar entornos virtuales, archivos de base de datos y secretos.
  4. `README.md`: Guía de inicio y configuración.
  5. `CHANGELOG.md`: Registro formal de cambios de la v1.0.0.

---

## 3. Arquitectura y Stack Tecnológico


```

[ Captura de Imagen / Foto ]
│
▼
[ Streamlit Web App (app.py) ] ── (Secrets) ──> [ GEMINI_API_KEY ]
│
├─── (1) Envió de Imagen ──> [ Google Gemini 2.5 Flash ]
│                                      │ (Retorna JSON: título, autor)
│                                      ▼
├─── (2) Consulta Búsqueda ──> [ Google Books API ]
│                                      │ (Retorna Portada, ISBN, Págs, Año)
│                                      ▼
├─── (3) Guardado Seguro ───> [ SQLite (biblioteca.db) ]
│
▼
[ Interfaz Grid / Tabla Exportable ]

```

| Componente | Tecnología | Descripción / Propósito |
| :--- | :--- | :--- |
| **Frontend & Servidor** | Streamlit | Marco de trabajo web escrito 100% en Python. |
| **IA & Visión** | Google Gemini 2.5 Flash (`google-genai`) | Reconocimiento de lomos y portadas en imágenes. |
| **Enriquecimiento** | Google Books API | Extracción de metadatos oficiales y portadas HTTP(S). |
| **Base de Datos** | SQLite (`sqlite3`) | Almacenamiento persistente en archivo ejecutable. |
| **Alojamiento / Cloud** | Streamlit Community Cloud | Servidor público conectado al repositorio de GitHub. |
| **Control de Versiones** | GitHub | Repositorio remoto centralizado. |

---

## 4. Estructura Completa del Repositorio (`biblioteca-virtual`)

```text
biblioteca-virtual/
├── .gitignore          # Archivos excluidos del control de versiones (.db, secrets, etc.)
├── CHANGELOG.md        # Registro de cambios formal bajo norma SemVer (v1.0.0)
├── README.md           # Documentación general y guía de instalación/despliegue
├── ITR.md              # Documento de Requisitos e Historial Técnico (Este documento)
├── app.py              # Código fuente principal de la aplicación
└── requirements.txt    # Librerías Python requeridas por el servidor

```

---

## 5. Código Fuente Implementado (`app.py`)

```python
import streamlit as st
import pandas as pd
import requests
import json
import sqlite3
from google import genai
from google.genai import types

# Configuración de la página
st.set_page_config(page_title="Biblioteca Virtual", page_icon="📚", layout="wide")

# --- BASE DE DATOS (SQLite) ---

@st.cache_resource
def obtener_conexion_db():
    conn = sqlite3.connect("biblioteca.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS libros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT,
            publicacion TEXT,
            paginas TEXT,
            portada TEXT,
            isbn TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    conn.commit()
    return conn

conn = obtener_conexion_db()

def guardar_libro_db(libro):
    cursor = conn.cursor()
    if libro["isbn"] != "N/A":
        cursor.execute("SELECT id FROM libros WHERE isbn = ?", (libro["isbn"],))
    else:
        cursor.execute("SELECT id FROM libros WHERE titulo = ? AND autor = ?", (libro["titulo"], libro["autor"]))
        
    if cursor.fetchone() is None:
        cursor.execute(\"\"\"
            INSERT INTO libros (titulo, autor, publicacion, paginas, portada, isbn)
            VALUES (?, ?, ?, ?, ?, ?)
        \"\"\", (libro["titulo"], libro["autor"], libro["publicacion"], libro["paginas"], libro["portada"], libro["isbn"]))
        conn.commit()
        return True
    return False

def obtener_todos_los_libros():
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, autor, publicacion, paginas, portada, isbn FROM libros ORDER BY id DESC")
    columnas = ["id", "titulo", "autor", "publicacion", "paginas", "portada", "isbn"]
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
    prompt = \"\"\"
    Analiza esta imagen. Puede contener un solo libro (portada/lomo) o varios libros en una estantería.
    Identifica todos los libros visibles.
    Devuelve ÚNICAMENTE un JSON válido con una lista de objetos con claves "titulo" y "autor".
    Ejemplo: [{"titulo": "1984", "autor": "George Orwell"}]
    \"\"\"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
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

def buscar_en_google_books(titulo, autor=""):
    query = f"{titulo} {autor}".strip()
    url = f"[https://www.googleapis.com/books/v1/volumes?q=](https://www.googleapis.com/books/v1/volumes?q=){requests.utils.quote(query)}&maxResults=1"
    
    try:
        res = requests.get(url)
        datos = res.json()
        if "items" in datos and len(datos["items"]) > 0:
            info = datos["items"][0]["volumeInfo"]
            imagenes = info.get("imageLinks", {})
            portada_url = imagenes.get("thumbnail") or imagenes.get("smallThumbnail") or ""
            if portada_url.startswith("http://"):
                portada_url = portada_url.replace("http://", "https://")
                
            return {
                "titulo": info.get("title", titulo),
                "autor": ", ".join(info.get("authors", [autor])),
                "publicacion": info.get("publishedDate", "N/A"),
                "paginas": str(info.get("pageCount", "N/A")),
                "portada": portada_url,
                "isbn": info.get("industryIdentifiers", [{}])[0].get("identifier", "N/A")
            }
    except Exception as e:
        st.warning(f"No se pudieron obtener los detalles de '{titulo}': {e}")
        
    return {"titulo": titulo, "autor": autor, "publicacion": "N/A", "paginas": "N/A", "portada": "", "isbn": "N/A"}

# --- INTERFAZ DE USUARIO ---

st.title("📚 Mi Biblioteca Virtual Inteligente")
st.write("Sube la foto de un libro o de una estantería completa para catalogarla.")

uploaded_file = st.file_uploader("Captura o sube la foto aquí...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(uploaded_file, caption="Foto subida", use_container_width=True)
    with col2:
        if st.button("🔍 Escanear e Guardar en Biblioteca", type="primary"):
            with st.spinner("1/2: Analizando imagen con IA..."):
                bytes_data = uploaded_file.getvalue()
                libros_extraidos = analizar_imagen_con_gemini(bytes_data)
                
            if libros_extraidos:
                nuevos_guardados = 0
                with st.spinner("2/2: Obteniendo datos de Google Books..."):
                    for libro_raw in libros_extraidos:
                        detalles = buscar_en_google_books(libro_raw.get("titulo"), libro_raw.get("autor"))
                        if guardar_libro_db(detalles):
                            nuevos_guardados += 1
                            
                st.toast(f"¡{nuevos_guardados} libro(s) añadido(s)!", icon="🎉")
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
        st.dataframe(df[["id", "titulo", "autor", "publicacion", "paginas", "isbn"]], use_container_width=True)

```

---

## 6. Guía de Despliegue y Secretos

1. **Creación del Repositorio:** Subir todos los archivos mencionados a la rama `main` del repositorio de GitHub.
2. **Conexión con Streamlit Cloud:**
* Entrar a [share.streamlit.io](https://share.streamlit.io).


* Crear nueva app seleccionando el repositorio y marcando `app.py` como archivo ejecutable principal.




3. **Configuración de Variables de Entorno (Secrets):**
* Ir a **Settings** $\rightarrow$ **Secrets** en el panel de la app.


* Pegar la clave generada en [Google AI Studio](https://aistudio.google.com/):


```toml
GEMINI_API_KEY = "tu_clave_api_aqui"

```





"""

with open("ITR.md", "w", encoding="utf-8") as f:
f.write(itr_content)

print("ITR.md generado exitosamente.")

```



```python?code_reference&code_event_index=2
itr_content = """# Documento de Requisitos e Historial del Proyecto (ITR)

**Proyecto:** Biblioteca Virtual Inteligente  
**Fecha de Emisión:** 24 de Agosto de 2026  
**Versión:** 1.0.0  
**Estado:** Desplegado en Streamlit Community Cloud & GitHub  

---

## 1. Visión General del Proyecto

La **Biblioteca Virtual Inteligente** es una aplicación web *Low-Code* desarrollada en Python con **Streamlit** que permite a usuarios catalogar su colección de libros físicos a partir de fotografías de portadas individuales o de estanterías completas (múltiples lomos). 

El sistema utiliza modelos de visión por inteligencia artificial (**Google Gemini 2.5 Flash**) para detectar los libros presentes en las imágenes y extrae sus metadatos detallados (portada oficial, número de páginas, año de publicación e ISBN) mediante la **API pública de Google Books**, guardando la información de manera persistente en una base de datos **SQLite**.

---

## 2. Historial de Requisitos Solicitados y Evolución del Proyecto

A lo largo del desarrollo conversacional se plantearon y resolvieron de forma progresiva las siguientes necesidades y requerimientos:

### Fase 1: Concepción de la Idea y Definición de Arquitectura
* **Solicitud del usuario:** Crear una biblioteca virtual a partir de fotos de estanterías/libros sin requerir conocimientos profundos de programación.
* **Propuesta y decisión:** Se evaluaron tres alternativas (No-Code con Make/Glide, Soluciones comerciales y Desarrollo asistido por IA). Se optó por el **Desarrollo Asistido por IA** utilizando Python + Streamlit + Gemini Vision + Google Books API.

### Fase 2: Configuración del Entorno sin Instalación Local
* **Solicitud del usuario:** No realizar instalaciones locales inicialmente, trabajar mediante un repositorio en GitHub y desplegar la app en la nube.
* **Solución técnica:** Uso de **GitHub** como control de versiones y **Streamlit Community Cloud** (`share.streamlit.io`) como servidor de despliegue gratuito con enlace público.

### Fase 3: Integración de Modelos de Visión e Inteligencia Artificial
* **Solicitud del usuario:** Conectar la API de Google Gemini para interpretar imágenes de estanterías (múltiples lomos) o portadas y extraer títulos/autores.
* **Solución técnica:**
  * Uso de la librería `google-genai` con el modelo `gemini-2.5-flash`.
  * Configuración de un *prompt* en formato estructurado JSON (`response_mime_type="application/json"`).
  * Gestión segura de credenciales mediante **Streamlit Secrets** (`st.secrets["GEMINI_API_KEY"]`).

### Fase 4: Enriquecimiento Automático de Datos y Portadas
* **Solicitud del usuario:** Obtener las portadas oficiales de los libros, páginas, año de publicación y código ISBN.
* **Solución técnica:** Consulta automática en segundo plano a la **API pública de Google Books** (`https://www.googleapis.com/books/v1/volumes?q=...`), formateando URLs de portadas a `https` para evitar errores de seguridad.

### Fase 5: Persistencia de Datos y Gestión del Frontend
* **Solicitud del usuario:** Evitar que los libros escaneados se borren al cerrar la aplicación o recargar el navegador.
* **Solución técnica:**
  * Implementación de base de datos **SQLite** (`biblioteca.db`) local.
  * Verificación y prevención de duplicados por combinación de ISBN o Título/Autor.
  * Botón para eliminar registros individuales (`🗑️ Eliminar`).
  * Integración de caché de recursos con `@st.cache_resource` para gestionar las conexiones a la BD.

### Fase 6: Preparación para GitHub, Despliegue y Personalización
* **Solicitud del usuario:** Generar todos los archivos necesarios del repositorio, changelog de la V1 y resolver dudas sobre la personalización visual e integración de las APIs.
* **Entregables creados:**
  1. `app.py`: Código fuente principal.
  2. `requirements.txt`: Lista de dependencias (`streamlit`, `google-genai`, `requests`, `pandas`, `pillow`).
  3. `.gitignore`: Regla para ignorar entornos virtuales, archivos de base de datos y secretos.
  4. `README.md`: Guía de inicio y configuración.
  5. `CHANGELOG.md`: Registro formal de cambios de la v1.0.0.

---

## 3. Arquitectura y Stack Tecnológico


```

[ Captura de Imagen / Foto ]
│
▼
[ Streamlit Web App (app.py) ] ── (Secrets) ──> [ GEMINI_API_KEY ]
│
├─── (1) Envío de Imagen ──> [ Google Gemini 2.5 Flash ]
│                                      │ (Retorna JSON: título, autor)
│                                      ▼
├─── (2) Consulta Búsqueda ──> [ Google Books API ]
│                                      │ (Retorna Portada, ISBN, Págs, Año)
│                                      ▼
├─── (3) Guardado Seguro ───> [ SQLite (biblioteca.db) ]
│
▼
[ Interfaz Grid / Tabla Exportable ]

```

| Componente | Tecnología | Descripción / Propósito |
| :--- | :--- | :--- |
| **Frontend & Servidor** | Streamlit | Marco de trabajo web escrito 100% en Python. |
| **IA & Visión** | Google Gemini 2.5 Flash (`google-genai`) | Reconocimiento de lomos y portadas en imágenes. |
| **Enriquecimiento** | Google Books API | Extracción de metadatos oficiales y portadas HTTP(S). |
| **Base de Datos** | SQLite (`sqlite3`) | Almacenamiento persistente en archivo ejecutable. |
| **Alojamiento / Cloud** | Streamlit Community Cloud | Servidor público conectado al repositorio de GitHub. |
| **Control de Versiones** | GitHub | Repositorio remoto centralizado. |

---

## 4. Estructura Completa del Repositorio (`biblioteca-virtual`)

```text
biblioteca-virtual/
├── .gitignore          # Archivos excluidos del control de versiones (.db, secrets, etc.)
├── CHANGELOG.md        # Registro de cambios formal bajo norma SemVer (v1.0.0)
├── README.md           # Documentación general y guía de instalación/despliegue
├── ITR.md              # Documento de Requisitos e Historial Técnico (Este documento)
├── app.py              # Código fuente principal de la aplicación
└── requirements.txt    # Librerías Python requeridas por el servidor

```

---

## 5. Código Fuente Implementado (`app.py`)

```python
import streamlit as st
import pandas as pd
import requests
import json
import sqlite3
from google import genai
from google.genai import types

# Configuración de la página
st.set_page_config(page_title="Biblioteca Virtual", page_icon="📚", layout="wide")

# --- BASE DE DATOS (SQLite) ---

@st.cache_resource
def obtener_conexion_db():
    conn = sqlite3.connect("biblioteca.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS libros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT,
            publicacion TEXT,
            paginas TEXT,
            portada TEXT,
            isbn TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

conn = obtener_conexion_db()

def guardar_libro_db(libro):
    cursor = conn.cursor()
    if libro["isbn"] != "N/A":
        cursor.execute("SELECT id FROM libros WHERE isbn = ?", (libro["isbn"],))
    else:
        cursor.execute("SELECT id FROM libros WHERE titulo = ? AND autor = ?", (libro["titulo"], libro["autor"]))
        
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO libros (titulo, autor, publicacion, paginas, portada, isbn)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (libro["titulo"], libro["autor"], libro["publicacion"], libro["paginas"], libro["portada"], libro["isbn"]))
        conn.commit()
        return True
    return False

def obtener_todos_los_libros():
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, autor, publicacion, paginas, portada, isbn FROM libros ORDER BY id DESC")
    columnas = ["id", "titulo", "autor", "publicacion", "paginas", "portada", "isbn"]
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
    prompt = '''
    Analiza esta imagen. Puede contener un solo libro (portada/lomo) o varios libros en una estantería.
    Identifica todos los libros visibles.
    Devuelve ÚNICAMENTE un JSON válido con una lista de objetos con claves "titulo" y "autor".
    Ejemplo: [{"titulo": "1984", "autor": "George Orwell"}]
    '''

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
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

def buscar_en_google_books(titulo, autor=""):
    query = f"{titulo} {autor}".strip()
    url = f"[https://www.googleapis.com/books/v1/volumes?q=](https://www.googleapis.com/books/v1/volumes?q=){requests.utils.quote(query)}&maxResults=1"
    
    try:
        res = requests.get(url)
        datos = res.json()
        if "items" in datos and len(datos["items"]) > 0:
            info = datos["items"][0]["volumeInfo"]
            imagenes = info.get("imageLinks", {})
            portada_url = imagenes.get("thumbnail") or imagenes.get("smallThumbnail") or ""
            if portada_url.startswith("http://"):
                portada_url = portada_url.replace("http://", "https://")
                
            return {
                "titulo": info.get("title", titulo),
                "autor": ", ".join(info.get("authors", [autor])),
                "publicacion": info.get("publishedDate", "N/A"),
                "paginas": str(info.get("pageCount", "N/A")),
                "portada": portada_url,
                "isbn": info.get("industryIdentifiers", [{}])[0].get("identifier", "N/A")
            }
    except Exception as e:
        st.warning(f"No se pudieron obtener los detalles de '{titulo}': {e}")
        
    return {"titulo": titulo, "autor": autor, "publicacion": "N/A", "paginas": "N/A", "portada": "", "isbn": "N/A"}

# --- INTERFAZ DE USUARIO ---

st.title("📚 Mi Biblioteca Virtual Inteligente")
st.write("Sube la foto de un libro o de una estantería completa para catalogarla.")

uploaded_file = st.file_uploader("Captura o sube la foto aquí...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(uploaded_file, caption="Foto subida", use_container_width=True)
    with col2:
        if st.button("🔍 Escanear e Guardar en Biblioteca", type="primary"):
            with st.spinner("1/2: Analizando imagen con IA..."):
                bytes_data = uploaded_file.getvalue()
                libros_extraidos = analizar_imagen_con_gemini(bytes_data)
                
            if libros_extraidos:
                nuevos_guardados = 0
                with st.spinner("2/2: Obteniendo datos de Google Books..."):
                    for libro_raw in libros_extraidos:
                        detalles = buscar_en_google_books(libro_raw.get("titulo"), libro_raw.get("autor"))
                        if guardar_libro_db(detalles):
                            nuevos_guardados += 1
                            
                st.toast(f"¡{nuevos_guardados} libro(s) añadido(s)!", icon="🎉")
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
        st.dataframe(df[["id", "titulo", "autor", "publicacion", "paginas", "isbn"]], use_container_width=True)

```

---

## 6. Guía de Despliegue y Secretos

1. **Creación del Repositorio:** Subir todos los archivos mencionados a la rama `main` del repositorio de GitHub.
2. **Conexión con Streamlit Cloud:**
* Entrar a [share.streamlit.io](https://share.streamlit.io).
* Crear nueva app seleccionando el repositorio y marcando `app.py` como archivo ejecutable principal.


3. **Configuración de Variables de Entorno (Secrets):**
* Ir a **Settings** $\rightarrow$ **Secrets** en el panel de la app.
* Pegar la clave generada en [Google AI Studio](https://aistudio.google.com/):
```toml
GEMINI_API_KEY = "tu_clave_api_aqui"

```





"""

with open("ITR.md", "w", encoding="utf-8") as f:
f.write(itr_content)

print("ITR.md generado exitosamente.")

```



```python?code_reference&code_event_index=3
itr_content = """# Documento de Requisitos e Historial del Proyecto (ITR)

**Proyecto:** Biblioteca Virtual Inteligente  
**Fecha de Emisión:** 24 de Agosto de 2026  
**Versión:** 1.0.0  
**Estado:** Desplegado en Streamlit Community Cloud & GitHub  

---

## 1. Visión General del Proyecto

La **Biblioteca Virtual Inteligente** es una aplicación web *Low-Code* desarrollada en Python con **Streamlit** que permite a usuarios catalogar su colección de libros físicos a partir de fotografías de portadas individuales o de estanterías completas (múltiples lomos). 

El sistema utiliza modelos de visión por inteligencia artificial (**Google Gemini 2.5 Flash**) para detectar los libros presentes en las imágenes y extrae sus metadatos detallados (portada oficial, número de páginas, año de publicación e ISBN) mediante la **API pública de Google Books**, guardando la información de manera persistente en una base de datos **SQLite**.

---

## 2. Historial de Requisitos Solicitados y Evolución del Proyecto

A lo largo del desarrollo conversacional se plantearon y resolvieron de forma progresiva las siguientes necesidades y requerimientos:

### Fase 1: Concepción de la Idea y Definición de Arquitectura
* **Solicitud del usuario:** Crear una biblioteca virtual a partir de fotos de estanterías/libros sin requerir conocimientos profundos de programación.
* **Propuesta y decisión:** Se evaluaron tres alternativas (No-Code con Make/Glide, Soluciones comerciales y Desarrollo asistido por IA). Se optó por el **Desarrollo Asistido por IA** utilizando Python + Streamlit + Gemini Vision + Google Books API.

### Fase 2: Configuración del Entorno sin Instalación Local
* **Solicitud del usuario:** No realizar instalaciones locales inicialmente, trabajar mediante un repositorio en GitHub y desplegar la app en la nube.
* **Solución técnica:** Uso de **GitHub** como control de versiones y **Streamlit Community Cloud** (`share.streamlit.io`) como servidor de despliegue gratuito con enlace público.

### Fase 3: Integración de Modelos de Visión e Inteligencia Artificial
* **Solicitud del usuario:** Conectar la API de Google Gemini para interpretar imágenes de estanterías (múltiples lomos) o portadas y extraer títulos/autores.
* **Solución técnica:**
  * Uso de la librería `google-genai` con el modelo `gemini-2.5-flash`.
  * Configuración de un *prompt* en formato estructurado JSON (`response_mime_type="application/json"`).
  * Gestión segura de credenciales mediante **Streamlit Secrets** (`st.secrets["GEMINI_API_KEY"]`).

### Fase 4: Enriquecimiento Automático de Datos y Portadas
* **Solicitud del usuario:** Obtener las portadas oficiales de los libros, páginas, año de publicación y código ISBN.
* **Solución técnica:** Consulta automática en segundo plano a la **API pública de Google Books** (`https://www.googleapis.com/books/v1/volumes?q=...`), formateando URLs de portadas a `https` para evitar errores de seguridad.

### Fase 5: Persistencia de Datos y Gestión del Frontend
* **Solicitud del usuario:** Evitar que los libros escaneados se borren al cerrar la aplicación o recargar el navegador.
* **Solución técnica:**
  * Implementación de base de datos **SQLite** (`biblioteca.db`) local.
  * Verificación y prevención de duplicados por combinación de ISBN o Título/Autor.
  * Botón para eliminar registros individuales (`🗑️ Eliminar`).
  * Integración de caché de recursos con `@st.cache_resource` para gestionar las conexiones a la BD.

### Fase 6: Preparación para GitHub, Despliegue y Personalización
* **Solicitud del usuario:** Generar todos los archivos necesarios del repositorio, changelog de la V1 y resolver dudas sobre la personalización visual e integración de las APIs.
* **Entregables creados:**
  1. `app.py`: Código fuente principal.
  2. `requirements.txt`: Lista de dependencias (`streamlit`, `google-genai`, `requests`, `pandas`, `pillow`).
  3. `.gitignore`: Regla para ignorar entornos virtuales, archivos de base de datos y secretos.
  4. `README.md`: Guía de inicio y configuración.
  5. `CHANGELOG.md`: Registro formal de cambios de la v1.0.0.

---

## 3. Arquitectura y Stack Tecnológico


```

[ Captura de Imagen / Foto ]
│
▼
[ Streamlit Web App (app.py) ] ── (Secrets) ──> [ GEMINI_API_KEY ]
│
├─── (1) Envío de Imagen ──> [ Google Gemini 2.5 Flash ]
│                                      │ (Retorna JSON: título, autor)
│                                      ▼
├─── (2) Consulta Búsqueda ──> [ Google Books API ]
│                                      │ (Retorna Portada, ISBN, Págs, Año)
│                                      ▼
├─── (3) Guardado Seguro ───> [ SQLite (biblioteca.db) ]
│
▼
[ Interfaz Grid / Tabla Exportable ]

```

| Componente | Tecnología | Descripción / Propósito |
| :--- | :--- | :--- |
| **Frontend & Servidor** | Streamlit | Marco de trabajo web escrito 100% en Python. |
| **IA & Visión** | Google Gemini 2.5 Flash (`google-genai`) | Reconocimiento de lomos y portadas en imágenes. |
| **Enriquecimiento** | Google Books API | Extracción de metadatos oficiales y portadas HTTP(S). |
| **Base de Datos** | SQLite (`sqlite3`) | Almacenamiento persistente en archivo ejecutable. |
| **Alojamiento / Cloud** | Streamlit Community Cloud | Servidor público conectado al repositorio de GitHub. |
| **Control de Versiones** | GitHub | Repositorio remoto centralizado. |

---

## 4. Estructura Completa del Repositorio (`biblioteca-virtual`)

```text
biblioteca-virtual/
├── .gitignore          # Archivos excluidos del control de versiones (.db, secrets, etc.)
├── CHANGELOG.md        # Registro de cambios formal bajo norma SemVer (v1.0.0)
├── README.md           # Documentación general y guía de instalación/despliegue
├── ITR.md              # Documento de Requisitos e Historial Técnico (Este documento)
├── app.py              # Código fuente principal de la aplicación
└── requirements.txt    # Librerías Python requeridas por el servidor

```

---

## 5. Guía de Despliegue y Secretos

1. **Creación del Repositorio:** Subir todos los archivos mencionados a la rama `main` del repositorio de GitHub.
2. **Conexión con Streamlit Cloud:**
* Entrar a [share.streamlit.io](https://share.streamlit.io).
* Crear nueva app seleccionando el repositorio y marcando `app.py` como archivo ejecutable principal.


3. **Configuración de Variables de Entorno (Secrets):**
* Ir a **Settings** $\rightarrow$ **Secrets** en el panel de la app.
* Pegar la clave generada en [Google AI Studio](https://aistudio.google.com/):
```toml
GEMINI_API_KEY = "tu_clave_api_aqui"

```





"""

with open("ITR.md", "w", encoding="utf-8") as f:
f.write(itr_content)

print("ITR.md generado exitosamente.")

```



```python?code_reference&code_event_index=4
with open("ITR.md", "w", encoding="utf-8") as f:
    f.write("""# Documento de Requisitos e Historial del Proyecto (ITR)

**Proyecto:** Biblioteca Virtual Inteligente  
**Fecha de Emisión:** 24 de Agosto de 2026  
**Versión:** 1.0.0  
**Estado:** Desplegado en Streamlit Community Cloud & GitHub  

---

## 1. Visión General del Proyecto

La **Biblioteca Virtual Inteligente** es una aplicación web *Low-Code* desarrollada en Python con **Streamlit** que permite a usuarios catalogar su colección de libros físicos a partir de fotografías de portadas individuales o de estanterías completas (múltiples lomos). 

El sistema utiliza modelos de visión por inteligencia artificial (**Google Gemini 2.5 Flash**) para detectar los libros presentes en las imágenes y extrae sus metadatos detallados (portada oficial, número de páginas, año de publicación e ISBN) mediante la **API pública de Google Books**, guardando la información de manera persistente en una base de datos **SQLite**.

---

## 2. Historial de Requisitos Solicitados y Evolución del Proyecto

A lo largo del desarrollo conversacional se plantearon y resolvieron de forma progresiva las siguientes necesidades y requerimientos:

### Fase 1: Concepción de la Idea y Definición de Arquitectura
* **Solicitud del usuario:** Crear una biblioteca virtual a partir de fotos de estanterías/libros sin requerir conocimientos profundos de programación.
* **Propuesta y decisión:** Se evaluaron tres alternativas (No-Code con Make/Glide, Soluciones comerciales y Desarrollo asistido por IA). Se optó por el **Desarrollo Asistido por IA** utilizando Python + Streamlit + Gemini Vision + Google Books API.

### Fase 2: Configuración del Entorno sin Instalación Local
* **Solicitud del usuario:** No realizar instalaciones locales inicialmente, trabajar mediante un repositorio en GitHub y desplegar la app en la nube.
* **Solución técnica:** Uso de **GitHub** como control de versiones y **Streamlit Community Cloud** (`share.streamlit.io`) como servidor de despliegue gratuito con enlace público.

### Fase 3: Integración de Modelos de Visión e Inteligencia Artificial
* **Solicitud del usuario:** Conectar la API de Google Gemini para interpretar imágenes de estanterías (múltiples lomos) o portadas y extraer títulos/autores.
* **Solución técnica:**
  * Uso de la librería `google-genai` con el modelo `gemini-2.5-flash`.
  * Configuración de un *prompt* en formato estructurado JSON (`response_mime_type="application/json"`).
  * Gestión segura de credenciales mediante **Streamlit Secrets** (`st.secrets["GEMINI_API_KEY"]`).

### Fase 4: Enriquecimiento Automático de Datos y Portadas
* **Solicitud del usuario:** Obtener las portadas oficiales de los libros, páginas, año de publicación y código ISBN.
* **Solución técnica:** Consulta automática en segundo plano a la **API pública de Google Books** (`https://www.googleapis.com/books/v1/volumes?q=...`), formateando URLs de portadas a `https` para evitar errores de seguridad.

### Fase 5: Persistencia de Datos y Gestión del Frontend
* **Solicitud del usuario:** Evitar que los libros escaneados se borren al cerrar la aplicación o recargar el navegador.
* **Solución técnica:**
  * Implementación de base de datos **SQLite** (`biblioteca.db`) local.
  * Verificación y prevención de duplicados por combinación de ISBN o Título/Autor.
  * Botón para eliminar registros individuales (`🗑️ Eliminar`).
  * Integración de caché de recursos con `@st.cache_resource` para gestionar las conexiones a la BD.

### Fase 6: Preparación para GitHub, Despliegue y Personalización
* **Solicitud del usuario:** Generar todos los archivos necesarios del repositorio, changelog de la V1 y resolver dudas sobre la personalización visual e integración de las APIs.
* **Entregables creados:**
  1. `app.py`: Código fuente principal.
  2. `requirements.txt`: Lista de dependencias (`streamlit`, `google-genai`, `requests`, `pandas`, `pillow`).
  3. `.gitignore`: Regla para ignorar entornos virtuales, archivos de base de datos y secretos.
  4. `README.md`: Guía de inicio y configuración.
  5. `CHANGELOG.md`: Registro formal de cambios de la v1.0.0.

---

## 3. Arquitectura y Stack Tecnológico


```

[ Captura de Imagen / Foto ]
│
▼
[ Streamlit Web App (app.py) ] ── (Secrets) ──> [ GEMINI_API_KEY ]
│
├─── (1) Envío de Imagen ──> [ Google Gemini 2.5 Flash ]
│                                      │ (Retorna JSON: título, autor)
│                                      ▼
├─── (2) Consulta Búsqueda ──> [ Google Books API ]
│                                      │ (Retorna Portada, ISBN, Págs, Año)
│                                      ▼
├─── (3) Guardado Seguro ───> [ SQLite (biblioteca.db) ]
│
▼
[ Interfaz Grid / Tabla Exportable ]

```

| Componente | Tecnología | Descripción / Propósito |
| :--- | :--- | :--- |
| **Frontend & Servidor** | Streamlit | Marco de trabajo web escrito 100% en Python. |
| **IA & Visión** | Google Gemini 2.5 Flash (`google-genai`) | Reconocimiento de lomos y portadas en imágenes. |
| **Enriquecimiento** | Google Books API | Extracción de metadatos oficiales y portadas HTTP(S). |
| **Base de Datos** | SQLite (`sqlite3`) | Almacenamiento persistente en archivo ejecutable. |
| **Alojamiento / Cloud** | Streamlit Community Cloud | Servidor público conectado al repositorio de GitHub. |
| **Control de Versiones** | GitHub | Repositorio remoto centralizado. |

---

## 4. Estructura Completa del Repositorio (`biblioteca-virtual`)

```text
biblioteca-virtual/
├── .gitignore          # Archivos excluidos del control de versiones (.db, secrets, etc.)
├── CHANGELOG.md        # Registro de cambios formal bajo norma SemVer (v1.0.0)
├── README.md           # Documentación general y guía de instalación/despliegue
├── ITR.md              # Documento de Requisitos e Historial Técnico (Este documento)
├── app.py              # Código fuente principal de la aplicación
└── requirements.txt    # Librerías Python requeridas por el servidor

```

---

## 5. Guía de Despliegue y Secretos

1. **Creación del Repositorio:** Subir todos los archivos mencionados a la rama `main` del repositorio de GitHub.
2. **Conexión con Streamlit Cloud:**
* Entrar a [share.streamlit.io](https://share.streamlit.io).
* Crear nueva app seleccionando el repositorio y marcando `app.py` como archivo ejecutable principal.


3. **Configuración de Variables de Entorno (Secrets):**
* Ir a **Settings** $\rightarrow$ **Secrets** en el panel de la app.
* Pegar la clave generada en [Google AI Studio](https://aistudio.google.com/):
```toml
GEMINI_API_KEY = "tu_clave_api_aqui"

```





""")

```

Se ha generado el documento **`ITR.md`** (*Individual Technical Requirement / Informe Técnico de Requisitos*) recabando todo el historial de la conversación, solicitudes, decisiones técnicas y el código final implementado.

### Contenido del archivo `ITR.md`:

```markdown
# Documento de Requisitos e Historial del Proyecto (ITR)

**Proyecto:** Biblioteca Virtual Inteligente  
**Fecha de Emisión:** 24 de Agosto de 2026  
**Versión:** 1.0.0  
**Estado:** Desplegado en Streamlit Community Cloud & GitHub  

---

## 1. Visión General del Proyecto

La **Biblioteca Virtual Inteligente** es una aplicación web *Low-Code* desarrollada en Python con **Streamlit** que permite a usuarios catalogar su colección de libros físicos a partir de fotografías de portadas individuales o de estanterías completas (múltiples lomos)[cite: 1]. 

El sistema utiliza modelos de visión por inteligencia artificial (**Google Gemini 2.5 Flash**) para detectar los libros presentes en las imágenes y extrae sus metadatos detallados (portada oficial, número de páginas, año de publicación e ISBN) mediante la **API pública de Google Books**, guardando la información de manera persistente en una base de datos **SQLite**[cite: 1].

---

## 2. Historial de Requisitos Solicitados y Evolución del Proyecto

A lo largo del desarrollo conversacional se plantearon y resolvieron de forma progresiva las siguientes necesidades y requerimientos:

### Fase 1: Concepción de la Idea y Definición de Arquitectura
* **Solicitud del usuario:** Crear una biblioteca virtual a partir de fotos de estanterías/libros sin requerir conocimientos profundos de programación[cite: 1].
* **Propuesta y decisión:** Se evaluaron tres alternativas (No-Code con Make/Glide, Soluciones comerciales y Desarrollo asistido por IA)[cite: 1]. Se optó por el **Desarrollo Asistido por IA** utilizando Python + Streamlit + Gemini Vision + Google Books API[cite: 1].

### Fase 2: Configuración del Entorno sin Instalación Local
* **Solicitud del usuario:** No realizar instalaciones locales inicialmente, trabajar mediante un repositorio en GitHub y desplegar la app en la nube[cite: 1].
* **Solución técnica:** Uso de **GitHub** como control de versiones y **Streamlit Community Cloud** (`share.streamlit.io`) como servidor de despliegue gratuito con enlace público[cite: 1].

### Fase 3: Integración de Modelos de Visión e Inteligencia Artificial
* **Solicitud del usuario:** Conectar la API de Google Gemini para interpretar imágenes de estanterías (múltiples lomos) o portadas y extraer títulos/autores[cite: 1].
* **Solución técnica:**
  * Uso de la librería `google-genai` con el modelo `gemini-2.5-flash`[cite: 1].
  * Configuración de un *prompt* en formato estructurado JSON (`response_mime_type="application/json"`)[cite: 1].
  * Gestión segura de credenciales mediante **Streamlit Secrets** (`st.secrets["GEMINI_API_KEY"]`)[cite: 1].

### Fase 4: Enriquecimiento Automático de Datos y Portadas
* **Solicitud del usuario:** Obtener las portadas oficiales de los libros, páginas, año de publicación y código ISBN[cite: 1].
* **Solución técnica:** Consulta automática en segundo plano a la **API pública de Google Books** (`https://www.googleapis.com/books/v1/volumes?q=...`), formateando URLs de portadas a `https` para evitar errores de seguridad[cite: 1].

### Fase 5: Persistencia de Datos y Gestión del Frontend
* **Solicitud del usuario:** Evitar que los libros escaneados se borren al cerrar la aplicación o recargar el navegador[cite: 1].
* **Solución técnica:**
  * Implementación de base de datos **SQLite** (`biblioteca.db`) local[cite: 1].
  * Verificación y prevención de duplicados por combinación de ISBN o Título/Autor[cite: 1].
  * Botón para eliminar registros individuales (`🗑️ Eliminar`)[cite: 1].
  * Integración de caché de recursos con `@st.cache_resource` para gestionar las conexiones a la BD[cite: 1].

### Fase 6: Preparación para GitHub, Despliegue y Personalización
* **Solicitud del usuario:** Generar todos los archivos necesarios del repositorio, changelog de la V1 y resolver dudas sobre la personalización visual e integración de las APIs[cite: 1, 2].
* **Entregables creados:**
  1. `app.py`: Código fuente principal[cite: 1].
  2. `requirements.txt`: Lista de dependencias (`streamlit`, `google-genai`, `requests`, `pandas`, `pillow`)[cite: 1].
  3. `.gitignore`: Regla para ignorar entornos virtuales, archivos de base de datos y secretos[cite: 1].
  4. `README.md`: Guía de inicio y configuración[cite: 1].
  5. `CHANGELOG.md`: Registro formal de cambios de la v1.0.0[cite: 1].

---

## 3. Arquitectura y Stack Tecnológico

```text
[ Captura de Imagen / Foto ]
           │
           ▼
[ Streamlit Web App (app.py) ] ── (Secrets) ──> [ GEMINI_API_KEY ]
           │
           ├─── (1) Envío de Imagen ──> [ Google Gemini 2.5 Flash ]
           │                                      │ (Retorna JSON: título, autor)
           │                                      ▼
           ├─── (2) Consulta Búsqueda ──> [ Google Books API ]
           │                                      │ (Retorna Portada, ISBN, Págs, Año)
           │                                      ▼
           ├─── (3) Guardado Seguro ───> [ SQLite (biblioteca.db) ]
           │
           ▼
[ Interfaz Grid / Tabla Exportable ]

```

| Componente | Tecnología | Descripción / Propósito |
| --- | --- | --- |
| **Frontend & Servidor** | Streamlit | Marco de trabajo web escrito 100% en Python.

 |
| **IA & Visión** | Google Gemini 2.5 Flash (`google-genai`) | Reconocimiento de lomos y portadas en imágenes.

 |
| **Enriquecimiento** | Google Books API | Extracción de metadatos oficiales y portadas HTTP(S).

 |
| **Base de Datos** | SQLite (`sqlite3`) | Almacenamiento persistente en archivo ejecutable.

 |
| **Alojamiento / Cloud** | Streamlit Community Cloud | Servidor público conectado al repositorio de GitHub.

 |
| **Control de Versiones** | GitHub | Repositorio remoto centralizado.

 |

---

## 4. Estructura Completa del Repositorio (`biblioteca-virtual`)

```text
biblioteca-virtual/
├── .gitignore          # Archivos excluidos del control de versiones (.db, secrets, etc.)
├── CHANGELOG.md        # Registro de cambios formal bajo norma SemVer (v1.0.0)
├── README.md           # Documentación general y guía de instalación/despliegue
├── ITR.md              # Documento de Requisitos e Historial Técnico (Este documento)
├── app.py              # Código fuente principal de la aplicación
└── requirements.txt    # Librerías Python requeridas por el servidor

```

---

## 5. Guía de Despliegue y Secretos

1. **Creación del Repositorio:** Subir todos los archivos mencionados a la rama `main` del repositorio de GitHub.


2. **Conexión con Streamlit Cloud:**
* Entrar a [share.streamlit.io](https://share.streamlit.io).


* Crear nueva app seleccionando el repositorio y marcando `app.py` como archivo ejecutable principal.




3. **Configuración de Variables de Entorno (Secrets):**
* Ir a **Settings** $\rightarrow$ **Secrets** en el panel de la app.


* Pegar la clave generada en [Google AI Studio](https://aistudio.google.com/):


```toml
GEMINI_API_KEY = "tu_clave_api_aqui"

```





```

Puedes guardar directamente el bloque anterior creando un archivo llamado **`ITR.md`** en la raíz de tu repositorio de GitHub para tener documentado todo el historial y especificaciones del proyecto.

```
