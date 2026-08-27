# Changelog

All notable changes to the **Biblioteca Virtual** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-08-27

### 🚀 Added
- **Segunda clave API obligatoria (`GOOGLE_BOOKS_API_KEY`):** la búsqueda en Google Books deja de depender exclusivamente de peticiones anónimas. Se añade soporte para clave propia, con cuota individual, evitando el `429 Quota exceeded` que sufría el modo anónimo al escanear estanterías completas.
- **Preferencia de idioma español:** cada búsqueda intenta primero `langRestrict=es`; si no hay edición en español indexada, cae automáticamente a la búsqueda sin restricción de idioma en lugar de descartar el libro.
- **Reintentos automáticos en Gemini:** ante un `503 UNAVAILABLE` (modelo saturado), la app reintenta hasta 3 veces con espera progresiva (2s/4s/8s) antes de fallar.
- **Panel de depuración persistente:** expander "🔧 Debug Google Books" que registra, por cada consulta, la query enviada, si se restringió a español, el `status` HTTP y el número de resultados. Se guarda en `st.session_state` para sobrevivir a los `st.rerun()`, a diferencia de un `st.warning()` suelto dentro del bucle de escaneo.
- **Normalización en la comparación de duplicados:** la detección de libros ya existentes ahora compara título y autor sin tildes, mayúsculas ni puntuación (`unicodedata` + regex), no solo `LOWER()` exacto.

### 🔧 Fixed
- **`403 Cannot determine user location`:** Google Books bloqueaba las peticiones desde IPs de hosting en la nube (Streamlit Community Cloud) al no poder geolocalizarlas. Resuelto añadiendo `country=ES` a todas las peticiones.
- **`401 API keys are not supported by this API`:** causado por usar una clave de API vinculada a una cuenta de servicio (tipo válido solo para Vertex AI / Gemini). Resuelto documentando y usando una clave "clásica" sin cuenta de servicio, restringida explícitamente a Books API.
- **`404 models/... is not found for generateContent`:** el modelo de Gemini usado no era válido para el método `generateContent` en `v1beta`. Corregido a `gemini-3.5-flash`.
- **Excepciones silenciosas:** el bloque original `except Exception: continue` ocultaba el código de estado real de cualquier fallo de red, impidiendo diagnosticar los errores anteriores. Sustituido por logging explícito del `status_code` y cuerpo de la respuesta.

### ⚠️ Changed
- **Esquema de datos reducido:** por decisión de producto, se eliminan del catálogo los campos `isbn`, `editorial`, `idioma`, `categorias`, `descripcion` y `valoracion` (añadidos y revertidos en la misma sesión). El esquema final conserva únicamente `titulo`, `autor`, `publicacion`, `paginas` y `portada`.
- **Deduplicación:** cuando un libro ya existe, ahora se **ignora por completo** (ni se inserta ni se actualiza), sustituyendo el comportamiento anterior de completar campos vacíos (`N/A`) si aparecían mejores datos en un escaneo posterior.
- **Corrección de registro histórico (1.0.0):** la entrada original de "Prevención de Duplicados" indicaba comparación *"por ISBN o título/autor"*. Eso nunca fue así: el código de la 1.0.0 solo comparaba título/autor con `LOWER()` exacto — no existía lógica de deduplicación por ISBN en ninguna versión. Se corrige aquí para que el historial no arrastre una afirmación que el código nunca cumplió.

---

## [1.0.0] - 2026-08-24

### 🚀 Added
- **Reconocimiento Visual con IA (Gemini Vision):** Integración del modelo `gemini-2.5-flash` (`google-genai`) para procesar imágenes de portadas o estanterías con múltiples lomos y extraer la lista de títulos y autores en formato JSON.
- **Enriquecimiento de Datos (Google Books API):** Búsqueda automática de metadatos tras la extracción de IA para obtener la portada oficial, número de páginas, fecha de publicación e ISBN.
- **Base de Datos Persistente (SQLite):** Implementación de almacenamiento local (`biblioteca.db`) para conservar los libros escaneados de forma permanente entre recargas y sesiones.
- **Prevención de Duplicados:** Verificación automática mediante consulta a la base de datos para evitar re-insertar libros existentes por título/autor. *(Corrección posterior: la referencia original a "ISBN" en este punto era inexacta — ver [1.1.0].)*
- **Interfaz Web Interactiva (`app.py`):**
  - Módulo de carga de imágenes con vista previa.
  - Flujo de trabajo en 2 pasos con notificaciones visuales (`st.spinner`, `st.toast`).
  - Galería responsiva en cuadrícula de 4 columnas para visualizar portadas e información del libro.
  - Opción de borrado individual (`🗑️ Eliminar`) por cada libro.
  - Vista desplegable en formato tabla (`st.dataframe`) para consultar la base de datos completa.
- **Archivos de Configuración del Repositorio:**
  - `requirements.txt`: Especificación de dependencias del proyecto (`streamlit`, `google-genai`, `requests`, `pandas`, `pillow`).
  - `.gitignore`: Reglas para omitir entornos virtuales, cachés de Python, archivos de bases de datos locales (`.db`) y secretos.
  - `README.md`: Guía completa de arquitectura, requisitos y despliegue en Streamlit Community Cloud.

### ⚙️ Seguridad y Rendimiento
- Gestión segura de llaves API mediante Streamlit Secrets (`st.secrets["GEMINI_API_KEY"]`).
- Conexión optimizada a SQLite con caché de recursos de Streamlit (`@st.cache_resource`).