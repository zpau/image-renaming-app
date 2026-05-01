import panel as pn
import json
import random
import os
import shutil
import re
from pathlib import Path

pn.extension(sizing_mode="stretch_width")

# --- CARGA DE DATOS Y CONFIGURACIÓN ---
ARCHIVO_DATOS = "peces.json"
ARCHIVO_DESCARTES = "descartados.txt"
EXTENSIONES_VALIDAS = (".jpg", ".jpeg", ".png", ".webp")


def cargar_datos_peces():
    datos_por_defecto = {"Serranidae (Meros)": {"Mero gigante": "Epinephelus itajara"}}
    if not os.path.exists(ARCHIVO_DATOS) or os.path.getsize(ARCHIVO_DATOS) == 0:
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
            json.dump(datos_por_defecto, f, indent=4, ensure_ascii=False)
        return datos_por_defecto
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ ERROR: El archivo {ARCHIVO_DATOS} está mal formateado.")
        return datos_por_defecto


PECES_DB = cargar_datos_peces()


# --- ESTADO DE LA APP ---
class EstadoApp:
    def __init__(self):
        self.input_folder = ""
        self.output_folder = ""
        self.current_image = None
        self.familia_seleccionada = None
        self.imagenes_pendientes = []


state = EstadoApp()


# --- FUNCIONES AUXILIARES ---
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


# --- COMPONENTES UI: CONFIGURACIÓN INICIAL ---
titulo = pn.pane.Markdown("# 🐟 Clasificador de Peces", align="center")

input_dir_widget = pn.widgets.TextInput(
    name="1. Carpeta de Origen", value=str(Path.cwd())
)
btn_buscar_origen = pn.widgets.Button(
    name="📁 Buscar", width=100, align="end", button_type="light"
)
btn_buscar_origen.on_click(lambda e: abrir_selector_carpeta(e, input_dir_widget))
row_origen = pn.Row(input_dir_widget, btn_buscar_origen)

output_dir_widget = pn.widgets.TextInput(
    name="2. Carpeta de Destino", value=str(Path.cwd() / "peces_clasificados")
)
btn_buscar_destino = pn.widgets.Button(
    name="📁 Buscar", width=100, align="end", button_type="light"
)
btn_buscar_destino.on_click(lambda e: abrir_selector_carpeta(e, output_dir_widget))
row_destino = pn.Row(output_dir_widget, btn_buscar_destino)

btn_empezar = pn.widgets.Button(
    name="🚀 Empezar a Clasificar", button_type="primary", height=50
)

setup_container = pn.Column(
    "### Configuración de Carpetas",
    row_origen,
    row_destino,
    btn_empezar,
)

# --- COMPONENTES UI: CLASIFICACIÓN ---
imagen_visor = pn.pane.JPG(width=500, height=400, sizing_mode="scale_both")
mensaje = pn.pane.Alert("Configura las carpetas para empezar.", alert_type="secondary")

# Fase 1: Like / Dislike
btn_like = pn.widgets.Button(
    name="👍 ME GUSTA (Clasificar)", button_type="success", height=70, width=240
)
btn_dislike = pn.widgets.Button(
    name="👎 PASAR (Siguiente)", button_type="danger", height=70, width=240
)
row_like_dislike = pn.Row(btn_like, btn_dislike, visible=False, align="center")

# Botón de descartes movido a la interfaz de clasificación
btn_limpiar_descartes = pn.widgets.Button(
    name="♻️ Restaurar Descartes",
    button_type="danger",
    button_style="outline",
    height=35,
    width=180,
)

# Fase 2: Familias y Especies
btn_volver = pn.widgets.Button(
    name="🔙 Me he equivocado (Volver)",
    button_type="light",
    button_style="solid",
    height=40,
)
contenedor_familias = pn.Column(
    "### 1. Selecciona la Familia", btn_volver, pn.layout.Divider(), visible=False
)
contenedor_especies = pn.Column("### 2. Selecciona la Especie", visible=False)

seccion_otro = pn.widgets.TextInput(
    name="Escribe la especie manualmente:", placeholder="Nombre científico..."
)
boton_confirmar_otro = pn.widgets.Button(
    name="Confirmar y Guardar", button_type="warning"
)
contenedor_manual = pn.Column(seccion_otro, boton_confirmar_otro, visible=False)

app_container = pn.Row(
    pn.Column(
        imagen_visor, row_like_dislike, mensaje, btn_limpiar_descartes, width=550
    ),
    pn.Column(contenedor_familias, width=250),
    pn.Column(contenedor_especies, contenedor_manual, width=250),
    visible=False,
)

# --- LÓGICA CORE ---


def accion_limpiar_descartes(event):
    if os.path.exists(ARCHIVO_DESCARTES):
        os.remove(ARCHIVO_DESCARTES)
        mensaje.object = "♻️ Descartes restaurados. Re-escaneando imágenes..."
        mensaje.alert_type = "success"
        # Forzar un re-escaneo para que las descartadas vuelvan a entrar en la cola ahora mismo
        iniciar_app(None)
    else:
        mensaje.object = "ℹ️ No hay imágenes descartadas para limpiar."
        mensaje.alert_type = "info"


def iniciar_app(event):
    state.input_folder = input_dir_widget.value
    state.output_folder = output_dir_widget.value

    if not os.path.exists(state.input_folder):
        mensaje.object = "❌ La carpeta de origen no existe. Revisa la ruta."
        mensaje.alert_type = "danger"
        return

    os.makedirs(state.output_folder, exist_ok=True)

    nombres_procesados = set()
    for p in Path(state.output_folder).rglob("*"):
        if p.is_file() and "_[" in p.name:
            nombre_base = p.name.split("_[")[0]
            nombre_original_reconstruido = f"{nombre_base}{p.suffix}"
            nombres_procesados.add(nombre_original_reconstruido)

    nombres_descartados = set()
    if os.path.exists(ARCHIVO_DESCARTES):
        with open(ARCHIVO_DESCARTES, "r", encoding="utf-8") as f:
            nombres_descartados = set(line.strip() for line in f if line.strip())

    state.imagenes_pendientes = []
    for p in Path(state.input_folder).rglob("*"):
        if p.suffix.lower() in EXTENSIONES_VALIDAS:
            if p.name not in nombres_procesados and p.name not in nombres_descartados:
                state.imagenes_pendientes.append(str(p))

    setup_container.visible = False
    app_container.visible = True

    # Solo cargamos nueva imagen si es el arranque inicial o si nos habíamos quedado sin fotos
    if event is not None or state.current_image is None:
        cargar_nueva_imagen()


def cargar_nueva_imagen():
    row_like_dislike.visible = True
    contenedor_familias.visible = False
    contenedor_especies.visible = False
    contenedor_manual.visible = False
    seccion_otro.value = ""

    if not state.imagenes_pendientes:
        state.current_image = None
        imagen_visor.object = None
        row_like_dislike.visible = False
        mensaje.object = "🎉 ¡Has terminado! No quedan imágenes nuevas por clasificar."
        mensaje.alert_type = "success"
        return

    state.current_image = random.choice(state.imagenes_pendientes)
    state.imagenes_pendientes.remove(state.current_image)

    imagen_visor.object = state.current_image
    mensaje.object = f"Mostrando: **{os.path.basename(state.current_image)}**"
    mensaje.alert_type = "info"


def accion_dislike(event):
    nombre_archivo = Path(state.current_image).name
    with open(ARCHIVO_DESCARTES, "a", encoding="utf-8") as f:
        f.write(f"{nombre_archivo}\n")
    mensaje.object = f"⏭️ Imagen {nombre_archivo} descartada."
    mensaje.alert_type = "warning"
    cargar_nueva_imagen()


def accion_like(event):
    row_like_dislike.visible = False
    contenedor_familias.visible = True
    contenedor_especies.clear()
    contenedor_especies.append("### 2. Selecciona la Especie")
    contenedor_especies.visible = True


def accion_volver(event):
    contenedor_familias.visible = False
    contenedor_especies.visible = False
    contenedor_manual.visible = False
    row_like_dislike.visible = True
    mensaje.object = "🔙 Volviendo a evaluar..."
    mensaje.alert_type = "secondary"


def seleccionar_familia(event):
    familia = event.obj.name

    if familia == "Otro (Escribir Manual)":
        contenedor_especies.visible = False
        contenedor_manual.visible = True
        return

    contenedor_manual.visible = False
    contenedor_especies.visible = True
    state.familia_seleccionada = familia
    contenedor_especies.clear()
    contenedor_especies.append(f"### Especies de {familia}")

    especies = list(PECES_DB[familia].keys()) + ["Otro"]
    for especie in especies:
        btn = pn.widgets.Button(name=especie, button_type="light", height=45)
        btn.on_click(seleccionar_especie)
        contenedor_especies.append(btn)


def seleccionar_especie(event):
    especie = event.obj.name
    if especie == "Otro":
        contenedor_especies.visible = False
        contenedor_manual.visible = True
    else:
        nombre_cientifico = PECES_DB[state.familia_seleccionada][especie]
        ejecutar_duplicado_y_renombrado(nombre_cientifico)


def ejecutar_duplicado_y_renombrado(nombre_cientifico):
    if not nombre_cientifico.strip():
        mensaje.object = "⚠️ Debes escribir un nombre."
        mensaje.alert_type = "danger"
        return

    try:
        path_original = Path(state.current_image)
        nombre_seguro_carpeta = limpiar_nombre_carpeta(nombre_cientifico)

        carpeta_especie = Path(state.output_folder) / nombre_seguro_carpeta
        os.makedirs(carpeta_especie, exist_ok=True)

        nuevo_nombre = (
            f"{path_original.stem}_[{nombre_cientifico}]{path_original.suffix}"
        )
        nuevo_path = carpeta_especie / nuevo_nombre

        shutil.copy2(path_original, nuevo_path)

        mensaje.object = f"✅ Guardado en: **{nombre_seguro_carpeta} / {nuevo_nombre}**"
        mensaje.alert_type = "success"
        cargar_nueva_imagen()
    except Exception as e:
        mensaje.object = f"❌ Error guardando: {str(e)}"
        mensaje.alert_type = "danger"


# --- CONECTAR EVENTOS E INICIALIZAR FAMILIAS ---
btn_limpiar_descartes.on_click(accion_limpiar_descartes)
btn_empezar.on_click(iniciar_app)
btn_like.on_click(accion_like)
btn_dislike.on_click(accion_dislike)
btn_volver.on_click(accion_volver)
boton_confirmar_otro.on_click(
    lambda e: ejecutar_duplicado_y_renombrado(seccion_otro.value)
)

for fam in PECES_DB.keys():
    btn_fam = pn.widgets.Button(name=fam, button_type="primary", height=50)
    btn_fam.on_click(seleccionar_familia)
    contenedor_familias.append(btn_fam)

btn_fam_otro = pn.widgets.Button(
    name="Otro (Escribir Manual)", button_type="warning", height=50
)
btn_fam_otro.on_click(seleccionar_familia)
contenedor_familias.append(pn.layout.Divider())
contenedor_familias.append(btn_fam_otro)

# --- LAYOUT FINAL ---
layout = pn.Column(titulo, setup_container, app_container)

layout.servable()
