# Documento de Requisitos e Historial del Proyecto (ITR)

**Proyecto:** Biblioteca Virtual Inteligente
**Fecha de Emisión original:** 24 de agosto de 2026
**Última actualización:** 27 de agosto de 2026
**Versión:** 1.1.0
**Estado:** Desplegado en Streamlit Community Cloud & GitHub

---

## 1. Visión General del Proyecto

La **Biblioteca Virtual Inteligente** es una aplicación web desarrollada en Python con **Streamlit** que permite catalogar una colección de libros físicos a partir de fotografías de portadas individuales o de estanterías completas (múltiples lomos).

El sistema utiliza un modelo de visión por inteligencia artificial (**Google Gemini, actualmente `gemini-3.5-flash`**) para detectar los libros presentes en las imágenes, y extrae portada, número de páginas y año de publicación mediante la **API pública de Google Books**, priorizando la edición en español cuando existe. La información se guarda de forma persistente en una base de datos **SQLite**.

---

## 2. Historial de Requisitos y Evolución del Proyecto

### Fase 1: Concepción de la Idea y Definición de Arquitectura
- **Solicitud:** Crear una biblioteca virtual a partir de fotos de estanterías/libros sin requerir conocimientos profundos de programación.
- **Decisión:** Desarrollo asistido por IA con Python + Streamlit + Gemini Vision + Google Books API.

### Fase 2: Configuración del Entorno sin Instalación Local
- **Solicitud:** Trabajar mediante repositorio en GitHub y desplegar en la nube sin instalación local.
- **Solución:** GitHub como control de versiones, Streamlit Community Cloud como servidor de despliegue.

### Fase 3: Integración de Gemini Vision
- **Solicitud:** Interpretar imágenes de estanterías o portadas y extraer títulos/autores.
- **Solución:** Librería `google-genai`, prompt en JSON estructurado (`response_mime_type="application/json"`), credenciales vía `st.secrets["GEMINI_API_KEY"]`.

### Fase 4: Enriquecimiento de Datos con Google Books
- **Solicitud:** Obtener portada oficial, páginas, fecha de publicación e ISBN.
- **Solución inicial:** Consulta a `https://www.googleapis.com/books/v1/volumes` sin clave, formateando URLs de portada a `https`.
- **Problema descubierto:** peticiones anónimas desde Streamlit Cloud devolvían `403 Cannot determine user location for geographically restricted operation` — Google no puede geolocalizar IPs de hosting en la nube.
- **Fix:** añadir `country=ES` a todas las peticiones.

### Fase 5: Persistencia de Datos
- **Solicitud:** Evitar que los libros escaneados se pierdan al recargar o cerrar la app.
- **Solución:** SQLite (`biblioteca.db`), `@st.cache_resource` para la conexión, botón de borrado individual.
- **Corrección de registro:** la deduplicación **nunca** se hizo por ISBN, solo por `titulo`/`autor` con `LOWER()` exacto. Una versión previa de este documento afirmaba lo contrario; queda corregido aquí.

### Fase 6: Ampliación y luego reducción de campos
- **Solicitud:** Capturar todos los datos posibles de Google Books sin autenticación (editorial, idioma, categorías, descripción, valoración).
- **Cambio posterior:** se revirtió — solo se conservan `titulo`, `autor`, `publicacion`, `paginas` y `portada`. Se eliminó `isbn` del esquema final.

### Fase 7: Prioridad de idioma español
- **Solicitud:** Que los datos se traigan en español cuando sea posible.
- **Solución:** primer intento con `langRestrict=es`; si no hay edición en español indexada, fallback automático a búsqueda sin restricción de idioma (evita perder libros sin edición española, como series autopublicadas en inglés).

### Fase 8: Depuración de fallos intermitentes en Google Books
Cadena real de incidencias, cada una con causa y fix distintos — documentada porque explica decisiones de arquitectura que no son obvias leyendo solo el código final:

| Síntoma | Causa raíz | Fix aplicado |
|---|---|---|
| `except Exception: continue` ocultaba todos los errores | Manejo de errores demasiado agresivo | Logging explícito de `status_code` y cuerpo de respuesta en `st.session_state["debug_log"]`, persistente entre reruns |
| `404 models/gemini-3.x-flash is not found for generateContent` | Nombre de modelo inválido para ese método de la API | Fijado a `gemini-3.5-flash`, confirmado en la referencia oficial de `generateContent` |
| `429 Quota exceeded... Queries per day` | Peticiones anónimas a Books API (sin `key`) agotaban la cuota pública diaria, agravado por hacer hasta 4 llamadas por libro (2 queries × español/no-español) | Clave propia (`GOOGLE_BOOKS_API_KEY`) con cuota individual |
| `401 API keys are not supported by this API. Expected OAuth2 access token` | La clave creada estaba vinculada a una cuenta de servicio (`...iam.gserviceaccount.com`), tipo válido solo para Vertex AI / Gemini, no para Books API | Clave "clásica" nueva, sin cuenta de servicio, restringida explícitamente a **Books API** en Cloud Console |
| `503 UNAVAILABLE` en Gemini (modelo saturado) | Sobrecarga temporal de infraestructura de Google, no relacionado con configuración propia | Reintentos automáticos con espera progresiva (2s/4s/8s), hasta 3 intentos |

### Fase 9: Documentación del repositorio
- **Solicitud:** Generar y mantener actualizados `README.md`, `CHANGELOG.md` y este `ITR.md` conforme evoluciona el código, incluyendo el requisito, antes no documentado, de una segunda API key.

---

## 3. Arquitectura y Stack Tecnológico

```text
[ Captura de Imagen / Foto ]
           │
           ▼
[ Streamlit Web App (app.py) ] ── (Secrets) ──> [ GEMINI_API_KEY ]
           │                  └── (Secrets) ──> [ GOOGLE_BOOKS_API_KEY ]
           │
           ├─── (1) Envío de Imagen ──> [ Gemini 3.5 Flash ] (con reintento si 503)
           │                                      │ (Retorna JSON: título, autor)
           │                                      ▼
           ├─── (2) ¿Ya existe? (comparación normalizada) ──> si existe, se omite
           │                                      │
           ├─── (3) Consulta Google Books (country=ES, langRestrict=es → fallback) ──> [ Google Books API ]
           │                                      │ (Retorna Portada, Páginas, Año)
           │                                      ▼
           ├─── (4) Guardado ───> [ SQLite (biblioteca.db) ]
           │
           ▼
[ Interfaz Grid / Tabla + Panel de Debug ]
```

| Componente | Tecnología | Descripción / Propósito |
| --- | --- | --- |
| **Frontend & Servidor** | Streamlit | Framework web en Python |
| **IA & Visión** | Gemini 3.5 Flash (`google-genai`) | Reconocimiento de lomos y portadas |
| **Enriquecimiento** | Google Books API (con clave propia, `country=ES`) | Portada, páginas, año de publicación |
| **Base de Datos** | SQLite (`sqlite3`) | Almacenamiento persistente |
| **Alojamiento / Cloud** | Streamlit Community Cloud | Servidor público conectado a GitHub |
| **Control de Versiones** | GitHub | Repositorio remoto |

---

## 4. Estructura del Repositorio

```text
biblioteca-virtual/
├── .gitignore
├── CHANGELOG.md
├── README.md
├── ITR.md
├── app.py
└── requirements.txt
```

---

## 5. Código Fuente Implementado (`app.py`) — estado actual

```python
import streamlit as st
import pandas as pd
import requests
import json
import sqlite3
import re
import time
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
        return False

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

def analizar_imagen_con_gemini(imagen_bytes, intentos=3):
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

    for intento in range(1, intentos + 1):
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
            es_temporal = "UNAVAILABLE" in str(e) or "503" in str(e) or "high demand" in str(e).lower()
            if es_temporal and intento < intentos:
                espera = 2 ** intento
                st.warning(f"Modelo saturado, reintentando en {espera}s... (intento {intento}/{intentos})")
                time.sleep(espera)
                continue
            st.error(f"Error al analizar la imagen con IA: {e}")
            return []

def _consultar_google_books(query, headers, restringir_es):
    api_key = st.secrets.get("GOOGLE_BOOKS_API_KEY")

    params = {"q": query, "maxResults": 1, "printType": "books", "country": "ES"}
    if restringir_es:
        params["langRestrict"] = "es"
    if api_key:
        params["key"] = api_key

    res = requests.get(
        "https://www.googleapis.com/books/v1/volumes",
        params=params, headers=headers, timeout=5
    )
    items = res.json().get("items", []) if res.status_code == 200 else []
    return res.status_code, res.text, items

def buscar_en_google_books(titulo, autor=""):
    """
    Búsqueda en Google Books con clave propia. country=ES evita el bloqueo
    de geolocalización en hosting cloud. Prioriza español, cae a cualquier
    idioma si no hay edición española indexada.
    """
    st.session_state.setdefault("debug_log", [])

    titulo_clean = re.sub(r'[^\w\s]', ' ', titulo).strip() if titulo else ""
    autor_clean = re.sub(r'[^\w\s]', ' ', autor).strip() if autor and autor != "Desconocido" else ""

    consultas = []
    if titulo_clean and autor_clean:
        consultas.append(f"{titulo_clean} {autor_clean}")
    elif titulo_clean:
        consultas.append(titulo_clean)

    headers = {"User-Agent": "Mozilla/5.0"}

    for query in consultas:
        for restringir_es in (True, False):
            try:
                status, texto, items = _consultar_google_books(query, headers, restringir_es)
                st.session_state["debug_log"].append(
                    f"[{titulo}] query='{query}' es_only={restringir_es} status={status} "
                    f"items={len(items)} | {texto[:150] if status != 200 else ''}"
                )

                if not items:
                    continue

                info = items[0].get("volumeInfo", {})
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
```

---

## 6. Guía de Despliegue y Secretos

1. **Repositorio:** subir todos los archivos a la rama `main` de GitHub.
2. **Streamlit Cloud:** [share.streamlit.io](https://share.streamlit.io) → nueva app → seleccionar repositorio → `app.py` como archivo principal.
3. **Secrets** (`Settings → Secrets`) — **dos claves obligatorias**, no una:

```toml
GEMINI_API_KEY = "tu_clave_de_gemini_aqui"
GOOGLE_BOOKS_API_KEY = "tu_clave_de_google_books_aqui"
```

`GOOGLE_BOOKS_API_KEY` debe ser una clave "clásica" (no vinculada a cuenta de servicio) restringida a **Books API** en Google Cloud Console. Ver `README.md` para el detalle completo de este requisito y de los errores que provoca configurarla mal.

---

## 7. Limitaciones Conocidas

- Deduplicación por título/autor normalizado, no por ISBN — la app ya no guarda ISBN en el esquema actual.
- `country=ES` fijo en las peticiones a Google Books; incorrecto si se despliega para usuarios de otras regiones.
- Sin `GOOGLE_BOOKS_API_KEY`, la app funciona en modo anónimo con cuota diaria muy limitada, insuficiente para escanear estanterías grandes.
- Un `503` sostenido de Gemini (no puntual) agota los 3 reintentos y falla igualmente; no hay solución de código para una caída real de infraestructura de Google.
