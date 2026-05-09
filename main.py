import panel as pn
import json
import random
import os
import shutil
import re
from pathlib import Path

# --- ESTILS CSS ACTUALITZATS ---
estils_css = """
body {
    background-color: #c6d6d5; 
}
.header-container {
    background: linear-gradient(90deg, #2c3e50 0%, #4ca1af 100%);
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.2); 
}
.header-container h1 {
    text-align: center;
    color: white !important; 
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3); 
}
.bk-btn {
    font-size: 16px !important;
    font-weight: bold !important;
}

/* -- ESTILS PER FER EL POP-UP GEGANT I SÒLID -- */
.notyf__toast, .bk-toast {
    max-width: 600px !important;
    padding: 30px 50px !important;
    border-radius: 20px !important;
    background-image: none !important; 
    opacity: 1 !important;             
    box-shadow: 0px 5px 15px rgba(0,0,0,0.3) !important;
}
.notyf__message, .bk-toast-message {
    font-size: 28px !important;
    font-weight: bold !important;
    text-align: center !important;
}

.notyf__toast--success, .bk-toast-success {
    background-color: #27ae60 !important; 
}
.notyf__toast--error, .bk-toast-error {
    background-color: #e74c3c !important; 
}

/* -- LIGHTBOX NATIVO (MODE GEGANT) -- */

/* 1. El contenedor por defecto está escondido */
.contenedor-lightbox {
    display: none !important; 
}

/* 2. Solo cuando añadimos la clase '.actiu' se despliega y oscurece todo */
.contenedor-lightbox.actiu {
    display: flex !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    background-color: rgba(0, 0, 0, 0.98) !important;
    z-index: 999999 !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 10px !important;
    margin: 0 !important;
}

/* 3. La imagen dentro del lightbox activo (AQUÍ ES DONDE SE HACE ENORME) */
.contenedor-lightbox.actiu img {
    max-height: 92vh !important; /* Casi toda la altura de la pantalla */
    max-width: 95vw !important;  /* Casi todo el ancho */
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
    border: 2px solid #333;
    box-shadow: 0px 0px 60px rgba(0,0,0,1);
}

.btn-cerrar-lightbox {
    margin-top: 15px !important;
}
"""

pn.extension(raw_css=[estils_css], sizing_mode="stretch_width", notifications=True)
pn.state.notifications.position = "center-right"

# --- CÀRREGA DE DADES I CONFIGURACIÓ ---
ARCHIVO_DATOS = "peixos.json"
ARCHIVO_DESCARTES = "descartats.txt"
EXTENSIONES_VALIDAS = (".jpg", ".jpeg", ".png", ".webp")


def cargar_datos_peces():
    datos_por_defecto = {"Serranidae (Meros)": {"Mero gegant": "Epinephelus itajara"}}
    if not os.path.exists(ARCHIVO_DATOS) or os.path.getsize(ARCHIVO_DATOS) == 0:
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
            json.dump(datos_por_defecto, f, indent=4, ensure_ascii=False)
        return datos_por_defecto
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return datos_por_defecto


PECES_DB = cargar_datos_peces()


# --- ESTAT DE L'APP ---
class EstadoApp:
    def __init__(self):
        self.input_folder = ""
        self.output_folder = ""
        self.current_image = None
        self.familia_seleccionada = None
        self.imagenes_pendientes = []
        self.n_classificats = 0
        self.n_descartats = 0


state = EstadoApp()


# --- FUNCIONS AUXILIARS ---
def limpiar_nombre_carpeta(nombre):
    return re.sub(r'[<>:"/\\|?*]', "", nombre).strip()


def abrir_selector_carpeta(event, text_widget):
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    carpeta = filedialog.askdirectory(title="Selecciona una carpeta")
    root.destroy()
    if carpeta:
        text_widget.value = carpeta


# --- COMPONENTS UI: CONFIGURACIÓ INICIAL ---
titulo = pn.pane.HTML(
    '<div class="header-container"><h1>🐟 Classificador de Peixos de Torredembarra</h1></div>',
    sizing_mode="stretch_width",
)

btn_buscar_origen = pn.widgets.Button(
    name="📁 Cercar", width=120, height=45, button_type="primary", align="end"
)
input_dir_widget = pn.widgets.TextInput(
    name="1. Carpeta d'Origen", value=str(Path.cwd()), width=500
)
row_origen = pn.Row(btn_buscar_origen, input_dir_widget)

btn_buscar_destino = pn.widgets.Button(
    name="📁 Cercar", width=120, height=45, button_type="primary", align="end"
)
output_dir_widget = pn.widgets.TextInput(
    name="2. Carpeta de Destinació",
    value=str(Path.cwd() / "peixos_classificats"),
    width=500,
)
row_destino = pn.Row(btn_buscar_destino, output_dir_widget)

btn_empezar = pn.widgets.Button(
    name="🚀 Començar a Classificar",
    button_type="success",
    height=50,
    width=680,
    align="center",
)

setup_container = pn.Column(
    "## Configuració de Carpetes",
    row_origen,
    row_destino,
    pn.layout.Divider(),
    btn_empezar,
    width=700,
    align="center",
)

# --- COMPONENTS UI: CLASSIFICACIÓ ---
imagen_visor = pn.pane.Image(
    sizing_mode="scale_both",
    max_height=600,
    align="center",
    css_classes=["visor-imatge"],
)
mensaje = pn.pane.Alert(
    "Configura les carpetes per començar.",
    alert_type="secondary",
    sizing_mode="stretch_width",  # <-- CAMBIADO
    align="center",
    styles={
        "font-size": "14px",
        "padding": "2px 20px",
        "text-align": "center",
    },
)

btn_like = pn.widgets.Button(
    name="👍 M'AGRADA (Classificar)",
    button_type="success",
    height=60,
    sizing_mode="stretch_width",
)
btn_dislike = pn.widgets.Button(
    name="👎 PASSAR (Següent Imatge)",
    button_type="danger",
    height=60,
    sizing_mode="stretch_width",
)
row_like_dislike = pn.Row(
    btn_like, btn_dislike, visible=False, sizing_mode="stretch_width", align="center"
)

# --- BOTÓN PARA ABRIR LIGHTBOX ---
btn_fullscreen = pn.widgets.Button(
    name="🔍 VEURE EN GRAN",
    button_type="primary",
    button_style="outline",
    height=45,
    sizing_mode="stretch_width",  # <-- CAMBIADO
    align="center",
)

btn_limpiar_descartes = pn.widgets.Button(
    name="♻️ Restaurar Descartades",
    button_type="danger",
    button_style="outline",
    height=40,
    sizing_mode="stretch_width",  # <-- CAMBIADO
    align="center",
)

btn_confirmar_si = pn.widgets.Button(
    name="✅ Sí, restaurar",
    button_type="danger",
    height=40,
    sizing_mode="stretch_width",
)
btn_confirmar_no = pn.widgets.Button(
    name="❌ Cancel·lar", button_type="success", height=40, sizing_mode="stretch_width"
)
row_confirmacion_descartes = pn.Row(
    btn_confirmar_si,
    btn_confirmar_no,
    visible=False,
    sizing_mode="stretch_width",
    align="center",
)

# --- COMPONENTS LIGHTBOX ---
imagen_lightbox = pn.pane.Image(sizing_mode="scale_both", align="center")
btn_cerrar_lightbox = pn.widgets.Button(
    name="❌ TANCAR (Tornar a la classificació)",
    button_type="danger",
    height=50,
    width=400,
    align="center",
    css_classes=["btn-cerrar-lightbox"],
)

# El panel empieza con la clase base (que tiene display: none)
lightbox_panel = pn.Column(
    imagen_lightbox,
    btn_cerrar_lightbox,
    css_classes=["contenedor-lightbox"],
    sizing_mode="stretch_both",
)

btn_volver = pn.widgets.Button(name="🔙 Tornar", button_type="danger", height=40)
contenedor_familias = pn.Column(
    "## 1. Família", btn_volver, pn.layout.Divider(), visible=False
)
contenedor_especies = pn.Column("## 2. Espècie", visible=False)

seccion_otro = pn.widgets.TextInput(
    name="ESCIURE AQUÍ A SOTA EL NOM DE L'ESPÈCIE:", placeholder="Nom científic..."
)
boton_confirmar_otro = pn.widgets.Button(
    name="Desar Nom", button_type="warning", height=50
)
contenedor_manual = pn.Column(seccion_otro, boton_confirmar_otro, visible=False)

# --- 4a COLUMNA: INDICADORS VISUALS ---
ind_pendents = pn.indicators.Number(
    name="Pendents",
    value=0,
    format="{value}",
    font_size="22pt",
    title_size="13pt",
    colors=[(100, "#2980b9")],
    align="center",
)
ind_classificats = pn.indicators.Number(
    name="Classificades",
    value=0,
    format="{value}",
    font_size="22pt",
    title_size="13pt",
    colors=[(100, "#27ae60")],
    align="center",
)
ind_descartades = pn.indicators.Number(
    name="Descartades",
    value=0,
    format="{value}",
    font_size="22pt",
    title_size="13pt",
    colors=[(100, "#e74c3c")],
    align="center",
)

grup_comptadors_vertical = pn.Column(
    ind_pendents, ind_classificats, ind_descartades, align="center"
)

# --- SUPER CONTENIDOR PRINCIPAL RESPONSIVE ---
col_imatge_esquerra = pn.Column(
    imagen_visor,
    btn_fullscreen,
    row_like_dislike,
    mensaje,
    btn_limpiar_descartes,
    row_confirmacion_descartes,
    sizing_mode="stretch_width",
    min_width=350,  # <-- Reducido para que quepa en pantallas pequeñas
    margin=(0, 15),
)

app_container = pn.Row(
    col_imatge_esquerra,
    # Fijamos el ancho de las columnas de menús para proteger los botones
    pn.Column(contenedor_familias, width=260),
    pn.Column(
        contenedor_especies,
        contenedor_manual,
        width=260,
    ),
    pn.Column(
        pn.layout.VSpacer(),
        grup_comptadors_vertical,
        width=150,
        align="center",
    ),
    visible=False,
    sizing_mode="stretch_width",
)


# --- LÒGICA (FUNCIONES) ---
def actualizar_indicadores():
    ind_pendents.value = len(state.imagenes_pendientes) + (
        1 if state.current_image else 0
    )
    ind_classificats.value = state.n_classificats
    ind_descartades.value = state.n_descartats


def cargar_nueva_imagen():
    row_like_dislike.visible = True
    contenedor_familias.visible = False
    contenedor_especies.visible = False
    contenedor_manual.visible = False

    while state.imagenes_pendientes:
        state.current_image = random.choice(state.imagenes_pendientes)
        state.imagenes_pendientes.remove(state.current_image)
        try:
            imagen_visor.object = state.current_image
            mensaje.object = f"Mostrant: **{os.path.basename(state.current_image)}**"
            actualizar_indicadores()
            return
        except Exception as e:
            print(
                f"⚠️ Saltant imatge il·legible: {os.path.basename(state.current_image)} - Error: {e}"
            )

    state.current_image = None
    imagen_visor.object = None
    row_like_dislike.visible = False
    actualizar_indicadores()
    mensaje.object = "🎉 Has acabat!"
    mensaje.alert_type = "success"


def seleccionar_familia(event):
    familia = event.obj.name

    if familia == "✏️ ALTRE (ESCRIURE) ✏️":
        contenedor_especies.visible = False
        contenedor_manual.visible = True
        return

    contenedor_manual.visible = False
    contenedor_especies.visible = True
    state.familia_seleccionada = familia
    contenedor_especies.clear()

    # --- NUEVA LÓGICA: Categoría de especies de la carpeta ---
    if familia == "📂 Altres (Ja creades) 📂":
        contenedor_especies.append(f"### {familia}")

        # 1. Recopilar todos los nombres que ya están en el JSON para ignorarlos
        nombres_db = set(
            limpiar_nombre_carpeta(nom)
            for fam in PECES_DB.values()
            for nom in fam.values()
        )

        # 2. Leer las carpetas del directorio destino
        especies_extra = []
        if os.path.exists(state.output_folder):
            for item in os.listdir(state.output_folder):
                ruta_item = os.path.join(state.output_folder, item)
                # Si es una carpeta y no está en el JSON, la añadimos a la lista
                if os.path.isdir(ruta_item) and item not in nombres_db:
                    especies_extra.append(item)

        # 3. Generar los botones o mostrar mensaje si está vacío
        if not especies_extra:
            contenedor_especies.append("*(No s'han trobat carpetes noves)*")
        else:
            for especie in sorted(especies_extra):
                btn = pn.widgets.Button(name=especie, button_type="light", height=45)
                btn.on_click(seleccionar_especie)
                contenedor_especies.append(btn)

        # Añadimos también el botón manual por si acaso
        btn_manual = pn.widgets.Button(
            name="✏️ ALTRE (ESCRIURE) ✏️", button_type="light", height=45
        )
        btn_manual.on_click(seleccionar_especie)
        contenedor_especies.append(pn.layout.Divider())
        contenedor_especies.append(btn_manual)
        return

    # --- LÓGICA ORIGINAL PARA FAMILIAS NORMALES ---
    contenedor_especies.append(f"### Espècies de {familia}")
    especies = list(PECES_DB[familia].keys()) + ["✏️ ALTRE (ESCRIURE) ✏️"]
    for especie in especies:
        btn = pn.widgets.Button(name=especie, button_type="light", height=45)
        btn.on_click(seleccionar_especie)
        contenedor_especies.append(btn)


def iniciar_app(event):
    state.input_folder = input_dir_widget.value
    state.output_folder = output_dir_widget.value
    os.makedirs(state.output_folder, exist_ok=True)

    n_class_reals = 0
    nombres_procesados = set()
    for p in Path(state.output_folder).rglob("*"):
        if p.is_file() and "_[" in p.name:
            n_class_reals += 1
            nombres_procesados.add(f"{p.name.split('_[')[0]}{p.suffix}")

    state.n_classificats = n_class_reals

    n_desc_reals = 0
    nombres_descartados = set()
    if os.path.exists(ARCHIVO_DESCARTES):
        with open(ARCHIVO_DESCARTES, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    n_desc_reals += 1
                    nombres_descartados.add(line.strip())

    state.n_descartats = n_desc_reals

    state.imagenes_pendientes = [
        str(p)
        for p in Path(state.input_folder).rglob("*")
        if p.suffix.lower() in EXTENSIONES_VALIDAS
        and p.name not in nombres_procesados
        and p.name not in nombres_descartados
    ]

    setup_container.visible = False
    app_container.visible = True
    cargar_nueva_imagen()


def accion_dislike(event):
    with open(ARCHIVO_DESCARTES, "a", encoding="utf-8") as f:
        f.write(f"{Path(state.current_image).name}\n")
    state.n_descartats += 1
    cargar_nueva_imagen()


def ejecutar_duplicado_y_renombrado(nombre_cientifico):
    if not nombre_cientifico.strip():
        return
    try:
        path_orig = Path(state.current_image)
        folder = Path(state.output_folder) / limpiar_nombre_carpeta(nombre_cientifico)
        os.makedirs(folder, exist_ok=True)
        shutil.copy2(
            path_orig,
            folder / f"{path_orig.stem}_[{nombre_cientifico}]{path_orig.suffix}",
        )
        state.n_classificats += 1
        pn.state.notifications.success(
            f"✅ Classificat: {nombre_cientifico}", duration=3000
        )
        cargar_nueva_imagen()
    except Exception as e:
        mensaje.object = f"Error: {e}"
        pn.state.notifications.error(f"Error al desar: {e}", duration=5000)


def seleccionar_especie(event):
    if event.obj.name == "✏️ ALTRE (ESCRIURE) ✏️":
        contenedor_especies.visible = False
        contenedor_manual.visible = True
    elif state.familia_seleccionada == "📂 Altres (Ja creades) 📂":
        # --- NUEVO: Si viene de la carpeta extra, el nombre del botón ya es el nombre científico ---
        ejecutar_duplicado_y_renombrado(event.obj.name)
    else:
        # Original: Busca en el JSON
        ejecutar_duplicado_y_renombrado(
            PECES_DB[state.familia_seleccionada][event.obj.name]
        )


# --- NUEVAS FUNCIONES DE CONFIRMACIÓN ---
def pedir_confirmacion_descartes(event):
    btn_limpiar_descartes.visible = False
    row_confirmacion_descartes.visible = True
    mensaje.object = (
        "⚠️ **Estàs segur que vols restaurar totes les imatges descartades?**"
    )
    mensaje.alert_type = "warning"


def cancelar_restauracion(event):
    row_confirmacion_descartes.visible = False
    btn_limpiar_descartes.visible = True
    # Volvemos a mostrar el nombre de la imagen actual
    if state.current_image:
        mensaje.object = f"Mostrant: **{os.path.basename(state.current_image)}**"
    else:
        mensaje.object = "🎉 Has acabat!"
    mensaje.alert_type = "secondary"


def accion_limpiar_descartes(event):
    # Restauramos la visibilidad de los botones
    row_confirmacion_descartes.visible = False
    btn_limpiar_descartes.visible = True

    if os.path.exists(ARCHIVO_DESCARTES):
        os.remove(ARCHIVO_DESCARTES)
        mensaje.object = "♻️ Imatges restaurades. Re-escanejant la carpeta..."
        mensaje.alert_type = "success"
        iniciar_app(None)
    else:
        mensaje.object = "ℹ️ No hi ha imatges descartades per restaurar."
        mensaje.alert_type = "info"
        if state.current_image:
            mensaje.object = f"ℹ️ No hi ha descartades. Mostrant: **{os.path.basename(state.current_image)}**"


def accion_like(e):
    row_like_dislike.visible = False
    contenedor_familias.visible = True


def accion_volver(e):
    contenedor_familias.visible = False
    contenedor_especies.visible = False
    contenedor_manual.visible = False
    row_like_dislike.visible = True
    mensaje.object = "🔙 Tornant a avaluar la imatge..."
    mensaje.alert_type = "secondary"


def abrir_lightbox(e):
    imagen_lightbox.object = state.current_image
    # Añadimos la clase 'actiu' para que el CSS lo muestre
    lightbox_panel.css_classes = ["contenedor-lightbox", "actiu"]


def cerrar_lightbox(e):
    # Quitamos la clase 'actiu' para que el CSS lo vuelva a ocultar
    lightbox_panel.css_classes = ["contenedor-lightbox"]


# Conexiones
btn_fullscreen.on_click(abrir_lightbox)
btn_cerrar_lightbox.on_click(cerrar_lightbox)


# --- GENERAR BOTONS DE FAMÍLIES ---
for fam in PECES_DB.keys():
    btn_fam = pn.widgets.Button(
        name=fam, button_type="primary", height=50, sizing_mode="stretch_width"
    )
    btn_fam.on_click(seleccionar_familia)
    contenedor_familias.append(btn_fam)

btn_fam_carpetas = pn.widgets.Button(
    name="📂 Altres (Ja creades) 📂",
    button_type="primary",
    height=50,
    sizing_mode="stretch_width",
)
btn_fam_carpetas.on_click(seleccionar_familia)
contenedor_familias.append(btn_fam_carpetas)

btn_fam_otro = pn.widgets.Button(
    name="✏️ ALTRE (ESCRIURE) ✏️",
    button_type="warning",
    height=50,
    sizing_mode="stretch_width",
)
btn_fam_otro.on_click(seleccionar_familia)
contenedor_familias.append(pn.layout.Divider())
contenedor_familias.append(btn_fam_otro)

# --- CONNECCIONS DE BOTONS ---
btn_buscar_origen.on_click(lambda e: abrir_selector_carpeta(e, input_dir_widget))
btn_buscar_destino.on_click(lambda e: abrir_selector_carpeta(e, output_dir_widget))
btn_empezar.on_click(iniciar_app)
btn_like.on_click(accion_like)
btn_dislike.on_click(accion_dislike)
btn_volver.on_click(accion_volver)
btn_limpiar_descartes.on_click(pedir_confirmacion_descartes)
btn_confirmar_si.on_click(accion_limpiar_descartes)
btn_confirmar_no.on_click(cancelar_restauracion)
boton_confirmar_otro.on_click(
    lambda e: ejecutar_duplicado_y_renombrado(seccion_otro.value)
)

# --- RENDERITZAT FINAL ---
layout = pn.Column(
    titulo,
    setup_container,
    app_container,
    lightbox_panel,  # Asegúrate de que esto está aquí
    align="center",
    sizing_mode="stretch_width",
)
layout.servable()
