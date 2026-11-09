from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

NOMBRE_PREDETERMINADO = "automata_afnd_actualizado.png"


class VisorGrafo:
    """Ventana Tkinter con zoom, desplazamiento, ajuste y actualización."""

    def __init__(self, padre, imagen, regenerar=None):
        from PIL import Image, ImageTk

        self.Image = Image
        self.ImageTk = ImageTk
        self.regenerar = regenerar
        self.ruta_imagen = Path(imagen)
        self._cargar_original(self.ruta_imagen)
        self.escala = 1.0
        self.imagen_tk = None
        self.identificador = None
        self.ventana = tk.Toplevel(padre)
        self.ventana.title("URLCHECK · Grafo del AFND")
        self.ventana.geometry("1150x720")
        self.ventana.minsize(680, 440)
        self.ventana.configure(bg="#F5F7FB")

        barra = tk.Frame(self.ventana, bg="white", padx=15, pady=12)
        barra.pack(fill="x")
        tk.Label(
            barra, text="Grafo del autómata (34 estados)", bg="white",
            fg="#182335", font=("Segoe UI", 12, "bold")
        ).pack(side="left")
        botones = tk.Frame(barra, bg="white")
        botones.pack(side="right")
        for texto, accion in [
            ("−", lambda: self.cambiar_zoom(1 / 1.25)),
            ("+", lambda: self.cambiar_zoom(1.25)),
            ("100 %", lambda: self.zoom(1)),
            ("Ajustar", self.ajustar),
            ("Abrir PNG", self.abrir_otra_imagen),
        ]:
            self._boton(botones, texto, accion)
        if regenerar is not None:
            self._boton(botones, "Actualizar desde AFND", self.actualizar_desde_afnd)

        contenedor = tk.Frame(self.ventana, bg="#DFE6EF")
        contenedor.pack(fill="both", expand=True, padx=14, pady=(12, 0))
        self.canvas = tk.Canvas(contenedor, bg="white", cursor="fleur",
                                highlightthickness=0)
        scroll_x = tk.Scrollbar(contenedor, orient="horizontal", command=self.canvas.xview)
        scroll_y = tk.Scrollbar(contenedor, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        pie = tk.Frame(self.ventana, bg="#F5F7FB", padx=17, pady=9)
        pie.pack(fill="x")
        self.info = tk.Label(pie, bg="#F5F7FB", fg="#182335", font=("Segoe UI", 9))
        self.info.pack(side="left")
        tk.Label(
            pie, bg="#F5F7FB", fg="#5E6C81",
            text="Arrastrá para moverte · Rueda para desplazarte · Ctrl + rueda para zoom",
            font=("Segoe UI", 9)
        ).pack(side="right")

        self.canvas.bind("<ButtonPress-1>", self._marcar)
        self.canvas.bind("<B1-Motion>", self._arrastrar)
        self.canvas.bind("<MouseWheel>", self._rueda)
        self.canvas.bind("<Control-MouseWheel>", self._rueda_zoom)
        self.canvas.bind("<Button-4>", lambda _e: self._scroll_linux(-3))
        self.canvas.bind("<Button-5>", lambda _e: self._scroll_linux(3))
        self.ventana.after(100, self.ajustar)
        self.ventana.lift()

    def _boton(self, parent, texto, accion):
        tk.Button(
            parent, text=texto, command=accion, bg="#EAF0FF", fg="#1E4AC2",
            activebackground="#D9E5FF", activeforeground="#1E4AC2",
            relief="flat", cursor="hand2", font=("Segoe UI", 9),
            padx=11, pady=6
        ).pack(side="left", padx=(5, 0))

    def _cargar_original(self, ruta):
        with self.Image.open(ruta) as archivo:
            self.original = archivo.convert("RGB")
        self.ruta_imagen = Path(ruta)

    def _marcar(self, evento):
        self.canvas.scan_mark(evento.x, evento.y)
        return "break"

    def _arrastrar(self, evento):
        self.canvas.scan_dragto(evento.x, evento.y, gain=1)
        return "break"

    def _rueda(self, evento):
        paso = -3 if evento.delta > 0 else 3
        self.canvas.yview_scroll(paso, "units")
        return "break"

    def _rueda_zoom(self, evento):
        self.cambiar_zoom(1.25 if evento.delta > 0 else 1 / 1.25)
        return "break"

    def _scroll_linux(self, paso):
        self.canvas.yview_scroll(paso, "units")
        return "break"

    def ajustar(self):
        ancho = max(1, self.canvas.winfo_width() - 12)
        alto = max(1, self.canvas.winfo_height() - 12)
        self.zoom(min(ancho / self.original.width, alto / self.original.height, 1))

    def cambiar_zoom(self, factor):
        self.zoom(self.escala * factor)

    def zoom(self, factor):
        factor = max(0.04, min(1.5, factor))
        anterior_ancho = self.original.width * self.escala
        anterior_alto = self.original.height * self.escala
        centro_x = self.canvas.canvasx(self.canvas.winfo_width() / 2) / max(anterior_ancho, 1)
        centro_y = self.canvas.canvasy(self.canvas.winfo_height() / 2) / max(anterior_alto, 1)
        self.escala = factor
        ancho = max(1, round(self.original.width * factor))
        alto = max(1, round(self.original.height * factor))
        reducida = self.original.resize((ancho, alto), self.Image.Resampling.LANCZOS)
        self.imagen_tk = self.ImageTk.PhotoImage(reducida, master=self.ventana)
        if self.identificador is None:
            self.identificador = self.canvas.create_image(0, 0, anchor="nw", image=self.imagen_tk)
        else:
            self.canvas.itemconfigure(self.identificador, image=self.imagen_tk)
        self.canvas.configure(scrollregion=(0, 0, ancho, alto))
        self.info.configure(text=f"Zoom: {factor * 100:.0f} %  ·  {self.original.width} × {self.original.height} px")
        if ancho > self.canvas.winfo_width():
            x = (centro_x * ancho - self.canvas.winfo_width() / 2) / ancho
            self.canvas.xview_moveto(max(0, min(x, 1)))
        else:
            self.canvas.xview_moveto(0)
        if alto > self.canvas.winfo_height():
            y = (centro_y * alto - self.canvas.winfo_height() / 2) / alto
            self.canvas.yview_moveto(max(0, min(y, 1)))
        else:
            self.canvas.yview_moveto(0)

    def abrir_otra_imagen(self):
        ruta = filedialog.askopenfilename(
            parent=self.ventana, title="Seleccionar imagen del autómata",
            initialdir=str(self.ruta_imagen.parent),
            filetypes=[("Imagen PNG", "*.png"), ("Imágenes", "*.png *.jpg *.jpeg")]
        )
        if ruta:
            try:
                self._cargar_original(ruta)
                self.ajustar()
            except (OSError, ValueError) as exc:
                messagebox.showerror("Imagen inválida", str(exc), parent=self.ventana)

    def actualizar_desde_afnd(self):
        if self.regenerar is None:
            return
        destino = Path(__file__).resolve().parent / NOMBRE_PREDETERMINADO
        try:
            self.ventana.configure(cursor="watch")
            self.ventana.update_idletasks()
            nuevo = self.regenerar(destino)
            self._cargar_original(nuevo)
            self.ajustar()
        except Exception as exc:
            messagebox.showerror(
                "No se pudo actualizar el grafo",
                "No fue posible generar la imagen. Comprobá que Graphviz esté instalado "
                "y disponible en el PATH.\n\n" + str(exc),
                parent=self.ventana,
            )
        finally:
            self.ventana.configure(cursor="")


def abrir_visor_grafo(padre, regenerar=None):
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        messagebox.showerror("Falta Pillow", "Instalá Pillow: py -m pip install Pillow", parent=padre)
        return None

    carpeta = Path(__file__).resolve().parent
    imagen = carpeta / NOMBRE_PREDETERMINADO
    if not imagen.is_file():
        if regenerar is not None:
            try:
                imagen = Path(regenerar(imagen))
            except Exception as exc:
                messagebox.showerror("Sin diagrama", "Falta la imagen del AFND y no se pudo "
                    "generar desde el motor.\n\n" + str(exc), parent=padre)
                return None
        else:
            ruta = filedialog.askopenfilename(parent=padre, title="Seleccionar diagrama",
                filetypes=[("Imágenes PNG", "*.png")])
            if not ruta: return None
            imagen = Path(ruta)
    try:
        return VisorGrafo(padre, imagen, regenerar=regenerar)
    except (OSError, ValueError) as exc:
        messagebox.showerror("No se pudo abrir el diagrama", str(exc), parent=padre)
        return None
