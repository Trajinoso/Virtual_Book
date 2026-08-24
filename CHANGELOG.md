# Changelog

All notable changes to the **Biblioteca Virtual** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-24

### 🚀 Added
- **Reconocimiento Visual con IA (Gemini Vision):** Integración del modelo `gemini-2.5-flash` (`google-genai`) para procesar imágenes de portadas o estanterías con múltiples lomos y extraer la lista de títulos y autores en formato JSON.
- **Enriquecimiento de Datos (Google Books API):** Búsqueda automática de metadatos tras la extracción de IA para obtener la portada oficial, número de páginas, fecha de publicación e ISBN.
- **Base de Datos Persistente (SQLite):** Implementación de almacenamiento local (`biblioteca.db`) para conservar los libros escaneados de forma permanente entre recargas y sesiones.
- **Prevención de Duplicados:** Verificación automática mediante consulta a la base de datos para evitar re-insertar libros existentes por ISBN o título/autor.
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