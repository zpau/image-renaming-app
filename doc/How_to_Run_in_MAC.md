Sigue estos pasos en el Mac de tu padre:

### 1. Crea el archivo ´"Inicia_App.command"´

```
#!/bin/bash

# Això és màgia de Mac perquè el script sàpiga automàticament a quina carpeta és
cd "$(dirname "$0")"

echo "========================================="
echo "  Iniciant el Classificador de Peixos..."
echo "========================================="

# Comprova si la carpeta venv NO existeix
if [ ! -d "venv" ]; then
    echo ""
    echo "[!] Es la primera vegada que s'obre l'app."
    echo "[!] Configurant el sistema per al papa... Aixo trigara un minutet."
    echo ""
    python3 -m venv venv
    source venv/bin/activate
    pip3 install panel
else
    # Si ja existeix, simplement l'activa
    source venv/bin/activate
fi

echo ""
echo "Obrint l'aplicacio al navegador..."
panel serve main.py --show
```

### 2. Abre Automator
1. Pulsa la lupa de arriba a la derecha (Spotlight) en el Mac o pulsa `Cmd + Espacio`.
2. Escribe **Automator** y abre la aplicación (tiene el icono de un robot con un tubo).
3. Al abrirse, te preguntará qué tipo de documento quieres crear. Selecciona **Aplicación** (o Application) y dale a "Seleccionar".

### 3. Añade el comando
1. En la parte superior izquierda verás un buscador. Escribe **"Ejecutar script de la shell"** (o Run Shell Script si tiene el Mac en inglés).
2. Haz doble clic en esa opción (o arrástrala al espacio gris grande de la derecha).
3. Verás que aparece un recuadro de texto que por defecto tiene escrita la palabra `cat`. Bórrala.
4. En ese recuadro, tienes que escribir `bash`  (con el espacio) y **pegar la ruta exacta** hacia tu archivo `.command`.
   - Truco para no escribir la ruta a mano: Abre la carpeta donde tienes el archivo `Inicia_App.command`, arrástralo y suéltalo dentro de ese recuadro de texto de Automator. Él solo escribirá la ruta completa.
Al final, en el recuadro debería quedar algo así:
´bash /Users/NombreDeTuPadre/Desktop/AppPeces/Inicia_App.command´

1. Guárdalo como una App
En el menú superior del Mac, haz clic en **Archivo -> Guardar** (o ´Cmd + S´).

Ponle el nombre que quieras, por ejemplo: **Clasificador de Peces**.

Elige guardarlo directamente en el **Escritorio**.

¡Y ya lo tienes! Ahora tu padre tendrá una aplicación real en su escritorio. Cuando haga doble clic, Automator se encargará de abrir la terminal por detrás, ejecutar el Plan B y lanzar el navegador con tu código.