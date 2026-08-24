# 📚 Biblioteca Virtual con IA

Aplicación web desarrollada en Streamlit que permite catalogar libros físicos escaneando portadas o estanterías enteras mediante Inteligencia Artificial (Gemini Vision) y enriqueciendo los datos con la API oficial de Google Books.

## 🚀 Características
- Reconocimiento de múltiples lomos/libros en una sola imagen.
- Búsqueda automática de portada oficial, páginas, fecha y código ISBN.
- Almacenamiento persistente en base de datos SQLite.
- Interfaz gráfica en cuadrícula responsiva.

## 🛠️ Configuración en Streamlit Cloud

1. Haz un Fork o suba este repositorio a tu cuenta de GitHub.
2. Inicia sesión en [Streamlit Community Cloud](https://share.streamlit.io/).
3. Crea una nueva App conectando este repositorio y seleccionando `app.py`.
4. En la configuración de la App (`Settings -> Secrets`), añade tu clave de Google Gemini:

```toml
GEMINI_API_KEY = "tu_clave_api_aqui"