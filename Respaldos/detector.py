import tkinter as tk
from PIL import Image, ImageTk
from automata.fa.nfa import NFA

# ---------------------------------------------------------
# 1. ALFABETOS Y AFND
# ---------------------------------------------------------
LETRAS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITOS = set("0123456789")
ALFANUMERICO = LETRAS | DIGITOS
SIMBOLOS = {':', '/', '.', '?', '=', '-', '&'}

nfa_url = NFA(
    states={
        'q0', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q21', 'q7',
        'subdominio', 'subdominio_guion', 'dominio_guion', '1caracter_dominio', 'dominio',  # <- Estado agregado
        'extension', '1letra', '2letra', '3letra',
        'PAIS', '1LETRA', '2LETRA', 'tld_largo',
        'puerto', '1num', '2num', '3num', '4num', '5num',
        'ruta', 'consulta_inicio', 'consulta_clave', 'consulta_valor_inicio', 'consulta_valor', 'q20'
    },
    input_symbols=ALFANUMERICO | SIMBOLOS,
    transitions={
        'q0': {
            'h': {'q1', 'subdominio', 'dominio'},
            **{c: {'subdominio', 'dominio'} for c in ALFANUMERICO if c != 'h'}
        },
        'q1': {'t': {'q2'}},
        'q2': {'t': {'q3'}},
        'q3': {'p': {'q4'}},
        'q4': {'s': {'q5'}, ':': {'q6'}},
        'q5': {':': {'q6'}},
        'q6': {'/': {'q21'}},
        'q21': {'/': {'q7'}},
        'q7': {c: {'subdominio', 'dominio'} for c in ALFANUMERICO},

        # --- VALIDACIÓN SUBDOMINIO Y DOMINIO ---
        'subdominio': {
            '.': {'1caracter_dominio'},
            '-': {'subdominio_guion'},
            **{c: {'subdominio'} for c in ALFANUMERICO}
            },
            
        'subdominio_guion': {
            '-': {'subdominio_guion'},
            **{c: {'subdominio'} for c in ALFANUMERICO}
            },

        '1caracter_dominio': {
            # Consume 1 carácter alfanumérico obligatorio para entrar a 'dominio'
            c: {'dominio'} for c in ALFANUMERICO
        },
        'dominio': {
            '.': {'extension', '1caracter_dominio', 'PAIS'},
            '-': {'dominio_guion'},
            **{c: {'dominio'} for c in ALFANUMERICO}
            },
            
        'dominio_guion': {
            '-': {'dominio_guion'},
            **{c: {'dominio'} for c in ALFANUMERICO}
            },
        # ----------------------------------------

        'extension': {c: {'1letra'} for c in LETRAS},
        '1letra': {c: {'2letra'} for c in LETRAS},
        '2letra': {c: {'3letra'} for c in LETRAS},

        '3letra': {
            ':': {'puerto'},
            '/': {'ruta'},
            '.': {'PAIS'},
            '?': {'consulta_inicio'},
            **{c: {'tld_largo'} for c in LETRAS}
            },

        'tld_largo': {
            ':': {'puerto'},
            '/': {'ruta'},
            '.': {'PAIS'},
            '?': {'consulta_inicio'},
            **{c: {'tld_largo'} for c in LETRAS}
            },

        'PAIS': {c: {'1LETRA'} for c in LETRAS},
        '1LETRA': {c: {'2LETRA'} for c in LETRAS},

        '2LETRA': {
            ':': {'puerto'},
            '?': {'consulta_inicio'},
            '/': {'ruta'}
        },

        'puerto': {c: {'1num'} for c in DIGITOS},
        '1num': {'/': {'ruta'}, '?': {'consulta_inicio'}, **{c: {'2num'} for c in DIGITOS}},
        '2num': {'/': {'ruta'}, '?': {'consulta_inicio'}, **{c: {'3num'} for c in DIGITOS}},
        '3num': {'/': {'ruta'}, '?': {'consulta_inicio'}, **{c: {'4num'} for c in DIGITOS}},
        '4num': {'/': {'ruta'}, '?': {'consulta_inicio'}, **{c: {'5num'} for c in DIGITOS}},
        '5num': {'/': {'ruta'}, '?': {'consulta_inicio'}, **{c: {'5num'} for c in DIGITOS}},

        'ruta': {
            '?': {'consulta_inicio'},
            **{c: {'q20'} for c in ALFANUMERICO}
            },
            
        'q20': {
            '/': {'ruta'},
            '?': {'consulta_inicio'},
            **{c: {'q20'} for c in ALFANUMERICO}
            },

        'consulta_inicio': {
            c: {'consulta_clave'} for c in ALFANUMERICO
            },
            
        'consulta_clave': {
            '=': {'consulta_valor_inicio'},
            **{c: {'consulta_clave'} for c in ALFANUMERICO}
            },
            
        'consulta_valor_inicio': {
            c: {'consulta_valor'} for c in ALFANUMERICO
            },
            
        'consulta_valor': {
            '&': {'consulta_inicio'},
            **{c: {'consulta_valor'} for c in ALFANUMERICO}
            }
    },
    initial_state='q0',
    final_states={'3letra', '2LETRA', 'tld_largo', '1num', '2num', '3num', '4num', '5num', 'ruta', 'consulta_valor', 'q20'}
)

# ---------------------------------------------------------
# 2. IDENTIFICACIÓN DE ESTRUCTURA POR TRAZA
# ---------------------------------------------------------
def obtener_camino_exitoso(nfa, cadena):
    def dfs(estado_actual, idx, camino):
        if idx == len(cadena):
            if estado_actual in nfa.final_states:
                return camino
            return None

        simbolo = cadena[idx]
        transiciones = nfa.transitions.get(estado_actual, {})
        if simbolo in transiciones:
            for siguiente in transiciones[simbolo]:
                res = dfs(siguiente, idx + 1, camino + [siguiente])
                if res:
                    return res
        return None

    return dfs(nfa.initial_state, 0, [nfa.initial_state])


def analizar_estructura_por_estados(nfa, cadena):
    camino = obtener_camino_exitoso(nfa, cadena)
    if not camino:
        return None

    componentes = []
    if 'q1' in camino or 'q7' in camino:
        componentes.append("protocolo (HTTPS)" if 'q5' in camino else "protocolo (HTTP)")
    if 'subdominio' in camino:
        componentes.append("subdominio")
    if 'dominio' in camino or '1caracter_dominio' in camino:
        componentes.append("dominio")
    if '3letra' in camino:
        componentes.append("extensión TLD")
    if '2LETRA' in camino:
        componentes.append("extensión territorial (ccTLD)")
    if 'puerto' in camino or '1num' in camino:
        componentes.append("puerto TCP")
    if 'ruta' in camino or 'q20' in camino:
        componentes.append("ruta/path")
    if 'consulta_inicio' in camino:
        componentes.append("parámetros de consulta")

    return " con ".join(componentes)

# ---------------------------------------------------------
# 3. INTERFAZ GRÁFICA CON PANEL CON SCROLL PARA LA IMAGEN
# ---------------------------------------------------------

def evaluar_url():
    cadena = entrada_url.get().strip().lower()

    if not cadena:
        lbl_resultado.config(
            text="Por favor, ingrese una URL",
            fg="orange"
        )
        lbl_estructura.config(text="")
        return

    try:
        es_valida = nfa_url.accepts_input(cadena)

        if es_valida:
            camino = obtener_camino_exitoso(nfa_url, cadena)

            # Comprobar el rango del puerto
            if camino and 'puerto' in camino:
                posicion = camino.index('puerto')
                digitos_puerto = ""

                while posicion < len(cadena) and cadena[posicion] in DIGITOS:
                    digitos_puerto += cadena[posicion]
                    posicion += 1

                numero_puerto = int(digitos_puerto)

                if numero_puerto > 65535:
                    lbl_resultado.config(
                        text="✗ PUERTO FUERA DE RANGO",
                        fg="#c62828"
                    )
                    lbl_estructura.config(
                        text="El puerto debe estar entre 0 y 65535.",
                        fg="#555555"
                    )
                    return

            # URL aceptada
            estructura = analizar_estructura_por_estados(nfa_url, cadena)

            lbl_resultado.config(
                text="✓ URL CON ESTRUCTURA VÁLIDA",
                fg="#2e7d32"
            )
            lbl_estructura.config(
                text=f"Estructura detectada: {estructura}",
                fg="#1565c0"
            )

        else:
            # URL rechazada por el AFND
            lbl_resultado.config(
                text="✗ URL CON ESTRUCTURA INVÁLIDA",
                fg="#c62828"
            )
            lbl_estructura.config(
                text="La cadena no cumple con las reglas del autómata.",
                fg="#555555"
            )

    except Exception as e:
        print(f"Error durante la validación: {e}")

        lbl_resultado.config(
            text="✗ ERROR AL VALIDAR LA URL",
            fg="#c62828"
        )
        lbl_estructura.config(text="")


ventana = tk.Tk()
ventana.title("Validador de URLs - AFND")
ventana.geometry("950x700")
ventana.config(bg="#f5f5f5")

lbl_titulo = tk.Label(ventana, text="Detector de URLs por Autómata Finito", font=("Helvetica", 14, "bold"), bg="#f5f5f5")
lbl_titulo.pack(pady=10)

frame_entrada = tk.Frame(ventana, bg="#f5f5f5")
frame_entrada.pack(pady=5)

entrada_url = tk.Entry(frame_entrada, width=45, font=("Consolas", 11))
entrada_url.pack(side=tk.LEFT, padx=5)
entrada_url.focus()

btn_validar = tk.Button(frame_entrada, text="Evaluar con AFND", font=("Helvetica", 10, "bold"), bg="#1976d2", fg="white", padx=10, pady=4, command=evaluar_url)
btn_validar.pack(side=tk.LEFT, padx=5)

lbl_resultado = tk.Label(ventana, text="", font=("Helvetica", 12, "bold"), bg="#f5f5f5")
lbl_resultado.pack(pady=5)

lbl_estructura = tk.Label(ventana, text="", font=("Helvetica", 10, "italic"), bg="#f5f5f5", wraplength=850)
lbl_estructura.pack(pady=5)

lbl_img_titulo = tk.Label(ventana, text="Diagrama de Estados (desplázate para navegar):", font=("Helvetica", 10, "bold"), bg="#f5f5f5")
lbl_img_titulo.pack(pady=(10, 2))

# ---------------------------------------------------------
# CONTENEDOR DE IMAGEN CON SCROLLBARS (Navegación fluida)
# ---------------------------------------------------------
RUTA_IMAGEN_PNG = "automata_graphviz.png"

try:
    # 1. Cargar y escalar la imagen
    img_orig = Image.open(RUTA_IMAGEN_PNG)
    
    factor_escala = 0.6  # Ajusta entre 0.5 y 1.0 según la pantalla
    ancho_nuevo = int(img_orig.width * factor_escala)
    alto_nuevo = int(img_orig.height * factor_escala)
    
    img_resiz = img_orig.resize((ancho_nuevo, alto_nuevo), Image.Resampling.LANCZOS)
    img_tk = ImageTk.PhotoImage(img_resiz)

    # 2. Crear el contenedor con Scrollbars (solo si la imagen abrió con éxito)
    frame_canvas = tk.Frame(ventana, bg="#cccccc")
    frame_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 20))

    canvas = tk.Canvas(frame_canvas, bg="#ffffff")
    scroll_x = tk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL, command=canvas.xview)
    scroll_y = tk.Scrollbar(frame_canvas, orient=tk.VERTICAL, command=canvas.yview)

    canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 3. Insertar la imagen en el Canvas
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
    canvas.config(scrollregion=(0, 0, ancho_nuevo, alto_nuevo))
    canvas.image = img_tk

except FileNotFoundError:
    # Mensaje de error si la imagen no se encuentra en el directorio
    lbl_imagen = tk.Label(
        ventana, 
        text="No se encontró 'automata_graphviz.png'. Ejecute el generador de gráfico primero.", 
        font=("Helvetica", 9), fg="red", bg="#ffebee", padx=10, pady=10
    )
    lbl_imagen.pack(pady=5)

ventana.mainloop()