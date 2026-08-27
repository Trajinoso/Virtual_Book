# 📚 Biblioteca Virtual con IA

Aplicación web desarrollada en Streamlit que permite catalogar libros físicos escaneando portadas o estanterías enteras mediante Inteligencia Artificial (Gemini Vision) y enriqueciendo los datos con la API pública de Google Books.

## 🚀 Características

- Reconocimiento de múltiples lomos/libros en una sola imagen mediante Gemini Vision.
- Búsqueda automática de portada, páginas y fecha de publicación en Google Books.
- Preferencia por la edición en español cuando existe (`langRestrict=es`), con fallback automático a cualquier idioma si no hay edición española indexada.
- Reintentos automáticos con espera progresiva si Gemini responde con error 503 (modelo saturado).
- Detección de libros duplicados por título y autor normalizados (sin tildes, mayúsculas ni puntuación) antes de guardar o de gastar una consulta a Google Books.
- Almacenamiento persistente en base de datos SQLite local (`biblioteca.db`).
- Panel de depuración desplegable con el resultado (`status`, número de resultados) de cada consulta a Google Books, persistente entre recargas de la app.
- Interfaz gráfica en cuadrícula responsiva.

## 🔑 Claves necesarias (dos, no una)

Esta app necesita **dos** claves distintas en `st.secrets`. Usar solo la de Gemini es insuficiente y provoca fallos silenciosos o errores 401/429 en la parte de Google Books.

```toml
GEMINI_API_KEY = "tu_clave_de_gemini_aqui"
GOOGLE_BOOKS_API_KEY = "tu_clave_de_google_books_aqui"
```

### GEMINI_API_KEY
Clave estándar de [Google AI Studio](https://aistudio.google.com/) para el modelo `gemini-3.5-flash`. Sin `fields`/restricciones especiales.

### GOOGLE_BOOKS_API_KEY
**Debe ser una clave "clásica", no vinculada a una cuenta de servicio.** En Google Cloud Console, al crear credenciales nuevas, si la clave aparece vinculada automáticamente a una cuenta de servicio (`...iam.gserviceaccount.com`), esa clave **solo sirve para Vertex AI y Gemini** y devolverá un error `401 - API keys are not supported by this API` al llamar a Books API. Necesitas el flujo de creación de API key "de toda la vida", y después restringirla explícitamente a **"Books API"** en la sección de restricciones de API de esa clave.

Pasos para verificar que la clave es del tipo correcto:
1. Google Cloud Console → APIs & Services → Credentials.
2. La clave para Books **no** debe mostrar una "Cuenta vinculada" de tipo `...gserviceaccount.com` en su pantalla de edición.
3. En "Restricciones de API" de esa clave, "Books API" debe aparecer seleccionable y marcada.
4. En APIs & Services → Library, "Books API" debe figurar como **habilitada** para el proyecto.

Sin clave (`GOOGLE_BOOKS_API_KEY` vacía o ausente), la app sigue funcionando en modo anónimo, pero con cuota diaria muy limitada — suficiente para pruebas puntuales, insuficiente para escanear una estantería completa sin toparse con `429 Quota exceeded`.

## 🛠️ Configuración en Streamlit Cloud

1. Haz un Fork o sube este repositorio a tu cuenta de GitHub.
2. Inicia sesión en [Streamlit Community Cloud](https://share.streamlit.io/).
3. Crea una nueva App conectando este repositorio y seleccionando `app.py`.
4. En la configuración de la App (`Settings → Secrets`), añade **ambas** claves como se indica arriba.

## 🐞 Panel de depuración

La app incluye un expander "🔧 Debug Google Books" que muestra, por cada libro escaneado, la query enviada, si se restringió a español, el `status` HTTP devuelto y cuántos resultados (`items`) se encontraron. Es la primera fuente a mirar si un libro concreto no trae portada, páginas o fecha:

- `status=200` con `items=0` → Google Books no tiene coincidencia para ese título/autor; no es un fallo de la app, es un límite de cobertura de la API (habitual en ediciones raras o autopublicadas).
- `status=429` → cuota agotada (diaria si ocurre en bloque desde el principio, por minuto si ocurre tras escanear muchos libros seguidos).
- `status=401/403` → problema de configuración de la clave (ver sección de claves arriba).
- Ausencia total de línea para un libro → el fallo ocurrió en la fase de Gemini, no en Google Books; revisa si Gemini transcribió bien el título de ese lomo en la imagen original.

## ⚠️ Limitaciones conocidas

- La deduplicación compara título y autor normalizados; **no** deduplica por ISBN. Si Gemini transcribe el mismo libro con títulos ligeramente distintos en dos escaneos distintos (por ejemplo, errores de OCR en un lomo poco legible), puede guardarse dos veces.
- El país usado en las consultas a Google Books está fijado a `country=ES`. Es necesario porque, sin él, Google devuelve `403 Cannot determine user location` desde IPs de hosting en la nube (Streamlit Cloud incluido). Si despliegas esta app para usuarios de otras regiones, este valor fijo dejaría de ser correcto para ellos.
- Si Gemini devuelve `503 UNAVAILABLE` (modelo saturado) más de 3 veces seguidas para la misma imagen, el escaneo de esa foto falla del todo; es un límite de infraestructura de Google, no de la app, y no tiene solución de código más allá de reintentar más tarde.
