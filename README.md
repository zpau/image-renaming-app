# Resumen del Proyecto: Clasificador de Imágenes Interactivo (Peces)

Esta aplicación web está diseñada para facilitar la clasificación y organización de grandes colecciones de imágenes (específicamente peces) de manera intuitiva, optimizada para usuarios que prefieren interfaces táctiles o de botones grandes (accesibilidad para personas mayores).

## 1. Propósito y Concepto
El objetivo principal es permitir que el usuario visualice fotos de una carpeta de origen de forma aleatoria y las clasifique utilizando nombres científicos predefinidos. En lugar de renombrar el archivo original, la app genera una copia organizada en una estructura de carpetas lógica.

## 2. Flujo de Trabajo (UX)
1.  **Configuración Inicial:** El usuario selecciona mediante un explorador de archivos nativo la carpeta de origen (donde están las fotos) y la de destino.
2.  **Fase de Filtrado (Tinder-style):**
    * Se muestra una imagen aleatoria.
    * **Botón Dislike (Pasar):** La imagen se descarta. Su nombre se guarda en `descartados.txt` para que no vuelva a aparecer nunca. No se borra el archivo original.
    * **Botón Like (Clasificar):** Se abre el panel de categorías.
3.  **Fase de Clasificación:**
    * **Familias:** El usuario elige la familia del pez mediante botones grandes.
    * **Especies:** Al elegir familia, aparecen los botones de especies asociadas.
    * **Opción "Otro":** Disponible tanto en familias como en especies para introducir nombres manualmente mediante teclado.
4.  **Procesamiento:** Una vez seleccionada la especie, la app realiza la acción de guardado y pasa automáticamente a la siguiente imagen.

## 3. Lógica de Archivos y Seguridad
* **No Destructivo:** La aplicación nunca modifica ni borra los archivos originales en la carpeta de origen.
* **Duplicado y Renombrado:** La imagen se copia a la carpeta de destino. El nuevo nombre sigue el patrón: `nombre_original_[Nombre Científico].ext`.
* **Organización Automática:** Dentro de la carpeta de destino, la app crea subcarpetas automáticamente con el nombre de la especie/familia clasificada, moviendo la imagen dentro.
* **Sistema Anti-Repetición:** Al iniciar, la app escanea:
    1.  La carpeta de destino (para no repetir lo ya clasificado).
    2.  El archivo `descartados.txt` (para no mostrar lo que el usuario decidió saltar).

## 4. Detalles Técnicos
* **Lenguaje:** Python.
* **Framework de UI:** `Panel` (basado en `Bokeh`).
* **Librerías de Apoyo:**
    * `shutil`: Para la copia segura de archivos.
    * `tkinter`: Para invocar el selector de carpetas nativo del sistema operativo.
    * `pathlib`: Para la gestión de rutas y escaneo recursivo de subcarpetas.
    * `json`: Para gestionar la base de datos de especies.
* **Almacenamiento de Datos:**
    * `peces.json`: Diccionario jerárquico que mapea `Familia -> Nombre Común -> Nombre Científico`.
    * `descartados.txt`: Lista plana de nombres de archivos a ignorar.

## 5. Estructura del archivo de datos (peces.json)
```json
{
  "Nombre de Familia": {
    "Nombre Común 1": "Nombre Científico 1",
    "Nombre Común 2": "Nombre Científico 2"
  }
}
```

## 6. Requisitos de Ejecución

Instalación de panel, pillow y bokeh.

Ejecución vía terminal: ` panel serve nombre_archivo.py --show --dev `