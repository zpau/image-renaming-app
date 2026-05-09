# Guía de Instalación: Classificador de Peixos (Mac)

Sigue estos pasos en el Mac de tu padre para dejar la aplicación lista:

### 1. Crea el archivo `Inicia_App.command`

Crea un archivo de texto en la misma carpeta donde está `main.py`, ponle el nombre `Inicia_App.command` y pega este contenido:

```bash
#!/bin/bash

# Magic de Mac para situarse en la carpeta del script
cd "$(dirname "$0")"

# --- MEJORA: LIMPIEZA DE PUERTO ---
# Cerramos cualquier sesión anterior que se haya quedado abierta en el puerto 5006
lsof -ti:5006 | xargs kill -9 2>/dev/null

echo "========================================="
echo "   Iniciant el Classificador de Peixos..."
echo "========================================="

# Comprobación del entorno virtual (venv)
if [ ! -d "venv" ]; then
    echo ""
    echo "[!] Es la primera vegada que s'obre l'app."
    echo "[!] Configurant el sistema... Aixo trigara un minutet."
    echo ""
    python3 -m venv venv
    source venv/bin/activate
    pip3 install panel
else
    # Si ya existe, simplemente lo activa
    source venv/bin/activate
fi

echo ""
echo "Obrint l'aplicacio al navegador..."
# Lanzamos la app asegurando el puerto 5006
python3 -m panel serve main.py --show --port 5006
```

> **Nota Importante:** Una vez creado el archivo, abre la Terminal y escribe `chmod +x ` (con un espacio al final), arrastra el archivo `Inicia_App.command` a la ventana y pulsa Enter. Esto le da permiso para ejecutarse.

---

### 2. Configura la App con Automator

Para que tu padre no tenga que ver la terminal, usaremos Automator para crearle un icono de aplicación:

1.  **Abre Automator:** Pulsa `Cmd + Espacio`, escribe "Automator" y ábrelo.
2.  **Nuevo Documento:** Selecciona **"Aplicación"** (Application) y dale a "Seleccionar".
3.  **Añade la acción:** En el buscador de la izquierda escribe **"Ejecutar el script de la shell"** (Run Shell Script) y arrástralo al área de la derecha.
4.  **Configura el script:**
    * En el recuadro que aparece, borra cualquier texto (como `cat`).
    * Escribe la palabra `bash` seguido de un espacio.
    * **Arrastra** tu archivo `Inicia_App.command` dentro del recuadro. Automator escribirá la ruta completa por ti.
    * Debería quedar algo como: `bash /Users/Nombre/Desktop/Peixos/Inicia_App.command`
5.  **Guarda la App:** Ve a **Archivo -> Guardar** (Cmd + S).
    * Nombre: **Clasificador de Peces**.
    * Ubicación: **Escritorio**.

---

### ¿Cómo funciona ahora?

1.  **Doble clic:** Tu padre hace doble clic en el icono del robot (o el que le pongas) en su escritorio.
2.  **Limpieza:** Automator ejecuta el script, que primero "mata" cualquier proceso que estuviera usando el puerto 5006.
3.  **Carga:** Activa el entorno virtual silenciosamente.
4.  **Navegador:** Se abre Safari o Chrome directamente con la aplicación lista para clasificar imágenes.

Con este setup, aunque tu padre cierre mal la aplicación o le dé dos veces al icono, el script siempre limpiará el puerto antes de empezar, evitando cualquier mensaje de error técnico.