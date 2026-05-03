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
    background-color: #c6d6d5; /* <-- AFEGEIX AIXÒ PER CANVIAR EL COLOR DE FONS DE L'APP */
}
.header-container {
    background-color: #2c3e50; /* Color del fons del Header */
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.header-container h1 {
    text-align: center;
    color: white !important; /* Color del text del Header */
    margin: 0;
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
# Header amb background color definit al CSS
titulo = pn.pane.HTML(
    '<div class="header-container"><h1>🐟 Classificador de Peixos</h1></div>',
    sizing_mode="stretch_width",
)

btn_buscar_origen = pn.widgets.Button(
    name="📁 Cercar", width=120, height=45, button_type="primary", align="end"
)
input_dir_widget = pn.widgets.TextInput(
    name="1. Carpeta d'Origen", value=str(Path.cwd()), width=450
)
btn_buscar_origen.on_click(lambda e: abrir_selector_carpeta(e, input_dir_widget))
row_origen = pn.Row(btn_buscar_origen, input_dir_widget)

btn_buscar_destino = pn.widgets.Button(
    name="📁 Cercar", width=120, height=45, button_type="primary", align="end"
)
output_dir_widget = pn.widgets.TextInput(
    name="2. Carpeta de Destinació",
    value=str(Path.cwd() / "peixos_classificats"),
    width=450,
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
    "### Configuració de Carpetes",
    row_origen,
    row_destino,
    pn.layout.Divider(),
    btn_empezar,
    width=700,
    align="center",
)

# --- COMPONENTS UI: CLASSIFICACIÓ ---
imagen_visor = pn.pane.JPG(width=800, height=600, sizing_mode="fixed", align="center")
mensaje = pn.pane.Alert(
    "Configura les carpetes per començar.",
    alert_type="secondary",
    width=800,
    align="center",
)

btn_like = pn.widgets.Button(
    name="👍 M'AGRADA (Classificar)", button_type="success", height=80, width=380
)
btn_dislike = pn.widgets.Button(
    name="👎 PASSAR (Següent Imatge)", button_type="danger", height=80, width=380
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

col_imatge_esquerra = pn.Column(
    imagen_visor, row_like_dislike, mensaje, btn_limpiar_descartes, width=850
)

# Fase 2: Famílies i Espècies
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

app_container = pn.Row(
    col_imatge_esquerra,
    pn.Column(contenedor_familias, width=250),
    pn.Column(contenedor_especies, contenedor_manual, width=250),
    visible=False,
)

# --- LÒGICA ---


def cargar_nueva_imagen():
    row_like_dislike.visible = True
    contenedor_familias.visible = False
    contenedor_especies.visible = False
    contenedor_manual.visible = False
    if not state.imagenes_pendientes:
        state.current_image = None
        imagen_visor.object = None
        row_like_dislike.visible = False
        mensaje.object = "🎉 Has acabat!"
        mensaje.alert_type = "success"
        return
    state.current_image = random.choice(state.imagenes_pendientes)
    state.imagenes_pendientes.remove(state.current_image)
    imagen_visor.object = state.current_image
    mensaje.object = f"Mostrant: **{os.path.basename(state.current_image)}**"


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
        # AQUÍ MODIFIQUES EL COLOR DE LES ESPÈCIES
        # Pots usar button_type o styles={'background': '#XXXXXX'}
        btn = pn.widgets.Button(name=especie, button_type="light", height=45)
        btn.on_click(seleccionar_especie)
        contenedor_especies.append(btn)


# (Rest de funcions igual que abans...)
def iniciar_app(event):
    state.input_folder = input_dir_widget.value
    state.output_folder = output_dir_widget.value
    os.makedirs(state.output_folder, exist_ok=True)
    nombres_procesados = set()
    for p in Path(state.output_folder).rglob("*"):
        if p.is_file() and "_[" in p.name:
            nombres_procesados.add(f"{p.name.split('_[')[0]}{p.suffix}")
    nombres_descartados = set()
    if os.path.exists(ARCHIVO_DESCARTES):
        with open(ARCHIVO_DESCARTES, "r", encoding="utf-8") as f:
            nombres_descartados = set(line.strip() for line in f if line.strip())
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
    cargar_nueva_imagen()


def ejecutar_duplicado_y_renombrado(nombre_cientifico):
    try:
        path_orig = Path(state.current_image)
        folder = Path(state.output_folder) / limpiar_nombre_carpeta(nombre_cientifico)
        os.makedirs(folder, exist_ok=True)
        shutil.copy2(
            path_orig,
            folder / f"{path_orig.stem}_[{nombre_cientifico}]{path_orig.suffix}",
        )
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


btn_empezar.on_click(iniciar_app)
btn_like.on_click(lambda e: accion_like(e))
btn_dislike.on_click(accion_dislike)
btn_volver.on_click(lambda e: accion_volver(e))
boton_confirmar_otro.on_click(
    lambda e: ejecutar_duplicado_y_renombrado(seccion_otro.value)
)


def accion_like(e):
    row_like_dislike.visible = False
    contenedor_familias.visible = True


def accion_volver(e):
    # Ocultem absolutament tots els panells de classificació
    contenedor_familias.visible = False
    contenedor_especies.visible = False
    contenedor_manual.visible = False

    # Tornem a mostrar els botons de Like / Dislike
    row_like_dislike.visible = True

    # Actualitzem el missatge
    mensaje.object = "🔙 Tornant a avaluar la imatge..."
    mensaje.alert_type = "secondary"


# GENERAR BOTONS DE FAMÍLIES
for fam in PECES_DB.keys():
    # AQUÍ MODIFIQUES EL COLOR DE LES FAMÍLIES
    btn_fam = pn.widgets.Button(name=fam, button_type="primary", height=50)
    btn_fam.on_click(seleccionar_familia)
    contenedor_familias.append(btn_fam)

btn_fam_otro = pn.widgets.Button(
    name="Altre (Manual)", button_type="warning", height=50
)
btn_fam_otro.on_click(seleccionar_familia)
contenedor_familias.append(pn.layout.Divider())
contenedor_familias.append(btn_fam_otro)

layout = pn.Column(titulo, setup_container, app_container, align="center")
layout.servable()
