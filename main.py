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
    /* Degradat de blau fosc a un blau més viu */
    background: linear-gradient(90deg, #2c3e50 0%, #4ca1af 100%);
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.2); /* Una ombra més marcada perquè ressalti */
}
.header-container h1 {
    text-align: center;
    color: white !important; 
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3); /* Ombra al text per a millor lectura */
}
.bk-btn {
    font-size: 16px !important;
    font-weight: bold !important;
}
"""

pn.extension(raw_css=[estils_css], sizing_mode="stretch_width")

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
    '<div class="header-container"><h1>🐟 Classificador de Peixos</h1></div>',
    sizing_mode="stretch_width",
)

btn_buscar_origen = pn.widgets.Button(
    name="📁 Cercar", width=120, height=45, button_type="primary", align="end"
)
input_dir_widget = pn.widgets.TextInput(
    name="1. Carpeta d'Origen", value=str(Path.cwd()), width=500
)
btn_buscar_origen.on_click(lambda e: abrir_selector_carpeta(e, input_dir_widget))
row_origen = pn.Row(btn_buscar_origen, input_dir_widget)

btn_buscar_destino = pn.widgets.Button(
    name="📁 Cercar", width=120, height=45, button_type="primary", align="end"
)
output_dir_widget = pn.widgets.TextInput(
    name="2. Carpeta de Destinació",
    value=str(Path.cwd() / "peixos_classificats"),
    width=500,
)
btn_buscar_destino.on_click(lambda e: abrir_selector_carpeta(e, output_dir_widget))
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
imagen_visor = pn.pane.JPG(sizing_mode="scale_both", max_height=600, align="center")
mensaje = pn.pane.Alert(
    "Configura les carpetes per començar.",
    alert_type="secondary",
    width=800,
    align="center",
)

btn_like = pn.widgets.Button(
    name="👍 M'AGRADA (Classificar)", button_type="success", height=60, width=380
)
btn_dislike = pn.widgets.Button(
    name="👎 PASSAR (Següent Imatge)", button_type="danger", height=60, width=380
)
row_like_dislike = pn.Row(
    btn_like, btn_dislike, visible=False, width=800, align="center"
)

btn_limpiar_descartes = pn.widgets.Button(
    name="♻️ Restaurar Descartades",
    button_type="danger",
    button_style="outline",
    height=40,
    width=800,
    align="center",
)

# 1a Columna (Imatge i controls principals)
col_imatge_esquerra = pn.Column(
    imagen_visor, row_like_dislike, mensaje, btn_limpiar_descartes, width=850
)

# 2a i 3a Columna: Famílies i Espècies
btn_volver = pn.widgets.Button(name="🔙 Tornar", button_type="light", height=40)
contenedor_familias = pn.Column(
    "## 1. Família", btn_volver, pn.layout.Divider(), visible=False
)
contenedor_especies = pn.Column("## 2. Espècie", visible=False)

seccion_otro = pn.widgets.TextInput(name="Manual:", placeholder="Nom científic...")
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
    ind_pendents,
    ind_classificats,
    ind_descartades,
    align="center",
)


# --- SUPER CONTENIDOR PRINCIPAL RESPONSIVE ---

# 1a Columna: La imagen (Mantenemos un ancho mínimo grande)
col_imatge_esquerra = pn.Column(
    imagen_visor,
    row_like_dislike,
    mensaje,
    btn_limpiar_descartes,
    sizing_mode="stretch_width",
    min_width=700,  # Esto asegura que la imagen siempre tenga un espacio protagonista
    margin=(0, 10),
)

# 2a, 3a y 4a Columna: Se adaptarán proporcionalmente
app_container = pn.Row(
    col_imatge_esquerra,
    pn.Column(contenedor_familias, sizing_mode="stretch_width", min_width=200),
    pn.Column(
        contenedor_especies,
        contenedor_manual,
        sizing_mode="stretch_width",
        min_width=200,
    ),
    pn.Column(
        pn.layout.VSpacer(),
        grup_comptadors_vertical,
        sizing_mode="stretch_width",
        min_width=150,
        align="center",
    ),
    visible=False,
    sizing_mode="stretch_width",  # Hace que la fila ocupe todo el ancho de la pantalla
)


# --- LÒGICA ---


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
    if not state.imagenes_pendientes:
        state.current_image = None
        imagen_visor.object = None
        row_like_dislike.visible = False
        actualizar_indicadores()
        mensaje.object = "🎉 Has acabat!"
        mensaje.alert_type = "success"
        return
    state.current_image = random.choice(state.imagenes_pendientes)
    state.imagenes_pendientes.remove(state.current_image)
    imagen_visor.object = state.current_image
    mensaje.object = f"Mostrant: **{os.path.basename(state.current_image)}**"
    actualizar_indicadores()


def seleccionar_familia(event):
    familia = event.obj.name
    if familia == "Altre (Manual)":
        contenedor_especies.visible = False
        contenedor_manual.visible = True
        return
    contenedor_manual.visible = False
    contenedor_especies.visible = True
    state.familia_seleccionada = familia
    contenedor_especies.clear()
    contenedor_especies.append(f"### Espècies de {familia}")

    especies = list(PECES_DB[familia].keys()) + ["Altre"]
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
        cargar_nueva_imagen()
    except Exception as e:
        mensaje.object = f"Error: {e}"


def seleccionar_especie(event):
    if event.obj.name == "Altre":
        contenedor_especies.visible = False
        contenedor_manual.visible = True
    else:
        ejecutar_duplicado_y_renombrado(
            PECES_DB[state.familia_seleccionada][event.obj.name]
        )


def accion_limpiar_descartes(event):
    if os.path.exists(ARCHIVO_DESCARTES):
        os.remove(ARCHIVO_DESCARTES)
        mensaje.object = "♻️ Imatges restaurades. Re-escanejant la carpeta..."
        mensaje.alert_type = "success"
        iniciar_app(None)
    else:
        mensaje.object = "ℹ️ No hi ha imatges descartades per restaurar."
        mensaje.alert_type = "info"


# --- CONNECCIONS DE BOTONS ---
btn_empezar.on_click(iniciar_app)
btn_like.on_click(lambda e: accion_like(e))
btn_dislike.on_click(accion_dislike)
btn_volver.on_click(lambda e: accion_volver(e))
btn_limpiar_descartes.on_click(accion_limpiar_descartes)
boton_confirmar_otro.on_click(
    lambda e: ejecutar_duplicado_y_renombrado(seccion_otro.value)
)


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


# --- GENERAR BOTONS DE FAMÍLIES ---
for fam in PECES_DB.keys():
    btn_fam = pn.widgets.Button(name=fam, button_type="primary", height=50)
    btn_fam.on_click(seleccionar_familia)
    contenedor_familias.append(btn_fam)

btn_fam_otro = pn.widgets.Button(
    name="Altre (Manual)", button_type="warning", height=50
)
btn_fam_otro.on_click(seleccionar_familia)
contenedor_familias.append(pn.layout.Divider())
contenedor_familias.append(btn_fam_otro)

# --- RENDERITZAT FINAL ---
layout = pn.Column(
    titulo, setup_container, app_container, align="center", sizing_mode="stretch_width"
)
layout.servable()
