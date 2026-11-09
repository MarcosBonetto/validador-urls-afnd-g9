from pathlib import Path
from collections import defaultdict
import re
import tkinter as tk
from tkinter import ttk

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
        '5num': {'/': {'ruta'}, '?': {'consulta_inicio'}},  # Máximo 5 dígitos

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
# 2. RECONOCIMIENTO Y SIMULACIÓN (SIN TRANSICIONES LAMBDA)
# ---------------------------------------------------------


def normalizar_protocolo(cadena):
    """El esquema HTTP(S) no distingue mayúsculas; la ruta sí puede hacerlo."""
    return re.sub(r"^https?://", lambda m: m.group(0).lower(), cadena, flags=re.IGNORECASE)


def simular_afnd(nfa, cadena):
    """Después de cada símbolo devuelve TODOS los estados activos del AFND."""
    estados_actuales = {nfa.initial_state}
    pasos = [{
        "indice": 0, "simbolo": None, "estados": estados_actuales.copy(),
        "transiciones": []
    }]

    for indice, simbolo in enumerate(cadena, start=1):
        estados_siguientes = set()
        transiciones_utilizadas = []
        for estado in sorted(estados_actuales):
            destinos = nfa.transitions.get(estado, {}).get(simbolo, set())
            for destino in sorted(destinos):
                estados_siguientes.add(destino)
                transiciones_utilizadas.append((estado, simbolo, destino))

        pasos.append({
            "indice": indice,
            "simbolo": simbolo,
            "estados": estados_siguientes.copy(),
            "transiciones": transiciones_utilizadas,
        })
        estados_actuales = estados_siguientes
    return pasos


def obtener_camino_exitoso(nfa, cadena):
    """Reconstruye una rama aceptada sin recursión y sin elegir estados al azar."""
    padres = [{nfa.initial_state: None}]
    for simbolo in cadena:
        nuevos = {}
        for estado in sorted(padres[-1]):
            for destino in sorted(nfa.transitions.get(estado, {}).get(simbolo, set())):
                nuevos.setdefault(destino, estado)
        padres.append(nuevos)
        if not nuevos:
            return None

    finales = sorted(set(padres[-1]) & set(nfa.final_states))
    if not finales:
        return None

    estado = finales[0]
    camino = [estado]
    for indice in range(len(cadena), 0, -1):
        estado = padres[indice][estado]
        camino.append(estado)
    return list(reversed(camino))


def analizar_estructura_por_estados(nfa, cadena):
    camino = obtener_camino_exitoso(nfa, cadena)
    if not camino:
        return "No se encontró una rama aceptada"

    componentes = []
    if 'q1' in camino or 'q7' in camino:
        componentes.append('HTTPS' if 'q5' in camino else 'HTTP')
    if 'subdominio' in camino:
        componentes.append('subdominio')
    if 'dominio' in camino or '1caracter_dominio' in camino:
        componentes.append('dominio')
    if '3letra' in camino or 'tld_largo' in camino:
        componentes.append('TLD')
    if '2LETRA' in camino:
        componentes.append('sufijo de dos letras')
    if 'puerto' in camino:
        componentes.append('puerto')
    if 'ruta' in camino or 'q20' in camino:
        componentes.append('ruta')
    if 'consulta_inicio' in camino:
        componentes.append('consulta')
    return ' · '.join(componentes) or 'URL'


def extraer_puerto(cadena):
    """Extrae el puerto del componente autoridad; NO decide si la URL es válida."""
    resto = cadena.split('://', 1)[-1] if '://' in cadena else cadena
    autoridad = re.split(r'[/?]', resto, maxsplit=1)[0]
    coincidencia = re.search(r':(\d+)$', autoridad)
    if coincidencia:
        return int(coincidencia.group(1))
    return None


def evaluar_cadena(nfa, texto):
    cadena = normalizar_protocolo(texto.strip())
    pasos = simular_afnd(nfa, cadena)
    estados_finales = pasos[-1]['estados'] & set(nfa.final_states)
    aceptada_afnd = bool(estados_finales)

    if not cadena:
        mensaje = 'Ingresá una URL para validar.'
        aceptada = False
    elif not aceptada_afnd:
        primer_bloqueo = next((p for p in pasos[1:] if not p['estados']), None)
        if primer_bloqueo is not None:
            pos = primer_bloqueo['indice']
            caracter = repr(primer_bloqueo['simbolo'])
            mensaje = f'Sin transiciones posibles en la posición {pos}, al leer {caracter}.'
        else:
            mensaje = 'Se consumió toda la cadena, pero ningún estado activo es final.'
        aceptada = False
    else:
        puerto = extraer_puerto(cadena)
        if puerto is not None and not 0 <= puerto <= 65535:
            mensaje = f'El AFND acepta la estructura, pero el puerto {puerto} excede 65535.'
            aceptada = False
        else:
            mensaje = 'La cadena pertenece al lenguaje reconocido por el validador.'
            aceptada = True

    return {
        'cadena': cadena,
        'pasos': pasos,
        'aceptada_afnd': aceptada_afnd,
        'aceptada': aceptada,
        'mensaje': mensaje,
        'estados_finales': estados_finales,
        'estructura': analizar_estructura_por_estados(nfa, cadena) if aceptada_afnd else None,
    }


# ---------------------------------------------------------
# 3. GRÁFICO GENERADO A PARTIR DEL MISMO AFND
# ---------------------------------------------------------

def abreviar_simbolos(simbolos):
    restantes = set(simbolos)
    partes = []
    for letras, etiqueta in (
        (set('abcdefghijklmnopqrstuvwxyz'), 'a-z'),
        (set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'A-Z'),
        (DIGITOS, '0-9'),
    ):
        if letras <= restantes:
            partes.append(etiqueta)
            restantes.difference_update(letras)
    partes.extend(sorted(restantes))
    return ', '.join(partes)


def generar_grafo(nfa, destino):
    """Evita duplicar a mano las transiciones en generadorImagen.py."""
    from graphviz import Digraph
    grafo = Digraph('AFND_URL', format='png')
    grafo.attr(rankdir='LR', dpi='115', nodesep='0.35', ranksep='0.5')
    grafo.attr('node', fontname='Arial', fontsize='10')
    grafo.attr('edge', fontname='Arial', fontsize='9')
    grafo.node('_inicio_', shape='point')
    grafo.edge('_inicio_', nfa.initial_state)

    for estado in sorted(nfa.states):
        final = estado in nfa.final_states
        grafo.node(estado, shape='doublecircle' if final else 'circle')

    agrupadas = defaultdict(set)
    for origen, por_simbolo in nfa.transitions.items():
        for simbolo, destinos in por_simbolo.items():
            for destino_estado in destinos:
                agrupadas[(origen, destino_estado)].add(simbolo)
    for (origen, destino_estado), simbolos in sorted(agrupadas.items()):
        grafo.edge(origen, destino_estado, label=abreviar_simbolos(simbolos))

    destino = Path(destino)
    resultado = grafo.render(filename=destino.stem, directory=str(destino.parent), cleanup=True)
    return Path(resultado)


# ---------------------------------------------------------
# 4. INTERFAZ MODERNA
# ---------------------------------------------------------

class Tema:
    FONDO = '#0A1221'
    LATERAL = '#0E192C'
    TARJETA = '#142239'
    TARJETA_ALT = '#1B2C47'
    CAMPO = '#0F1B2E'
    BORDE = '#2A3B55'
    TEXTO = '#EDF4FF'
    SECUNDARIO = '#9BABCA'
    APAGADO = '#7186A6'
    ACENTO = '#6E9EFF'
    ACENTO_HOVER = '#4B83EE'
    VERDE = '#59D6A5'
    ROJO = '#FF788C'
    AMARILLO = '#F4C76B'
    FUENTE = 'Segoe UI'
    MONO = 'Consolas'


class AppModerna:
    """Interfaz visual; conserva el AFND y su lógica en un módulo independiente."""

    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title('URL / LAB  |  Validador AFND · Grupo 9')
        self.ventana.geometry('1200x780')
        self.ventana.minsize(950, 650)
        self.ventana.configure(bg=Tema.FONDO)
        self.resultado = None
        self.posicion = 0
        self.pagina_actual = None
        self._img = None
        self._grafo = None
        self.zoom = .65
        self._grafo_iniciado = False
        self._fila_seleccionando = False
        self.url_var = tk.StringVar()
        self.filtro_var = tk.StringVar()
        self._navegacion = {}
        self._pestanas = {}

        self._configurar_estilos()
        self._construir_estructura()
        self._crear_resultado()
        self._crear_simulador()
        self._crear_transiciones()
        self._crear_grafo()
        self.cambiar_pagina('resultado')
        self.entrada.focus_set()
        self.ventana.bind('<Control-Return>', lambda _: self.validar())

    # ---------- Componentes de diseño ----------

    def _configurar_estilos(self):
        estilo = ttk.Style(self.ventana)
        estilo.theme_use('clam')
        estilo.configure('Dark.Treeview', background=Tema.CAMPO,
                         fieldbackground=Tema.CAMPO, foreground=Tema.TEXTO,
                         borderwidth=0, rowheight=31, font=(Tema.MONO, 10))
        estilo.configure('Dark.Treeview.Heading', background=Tema.TARJETA_ALT,
                         foreground=Tema.SECUNDARIO, relief='flat',
                         borderwidth=0, font=(Tema.FUENTE, 10, 'bold'), padding=(8, 9))
        estilo.map('Dark.Treeview', background=[('selected', '#315184')],
                   foreground=[('selected', Tema.TEXTO)])
        estilo.map('Dark.Treeview.Heading', background=[('active', '#263B58')])
        estilo.configure('Dark.Vertical.TScrollbar', background=Tema.TARJETA_ALT,
                         troughcolor=Tema.CAMPO, arrowcolor=Tema.SECUNDARIO)
        estilo.configure('Dark.Horizontal.TScrollbar', background=Tema.TARJETA_ALT,
                         troughcolor=Tema.CAMPO, arrowcolor=Tema.SECUNDARIO)

    def _texto(self, parent, texto, size=10, color=None, peso='normal', **kwargs):
        return tk.Label(parent, text=texto, bg=kwargs.pop('bg', parent.cget('bg')),
                        fg=color or Tema.TEXTO, font=(Tema.FUENTE, size, peso),
                        anchor=kwargs.pop('anchor', 'w'), **kwargs)

    def _boton(self, parent, texto, callback, primary=False, small=False, **kwargs):
        color = Tema.ACENTO if primary else Tema.TARJETA_ALT
        hover = Tema.ACENTO_HOVER if primary else '#2B4060'
        boton = tk.Button(parent, text=texto, command=callback, bg=color,
                          fg='#071428' if primary else Tema.TEXTO,
                          activebackground=hover, activeforeground=Tema.TEXTO,
                          highlightthickness=0, relief='flat', borderwidth=0,
                          cursor='hand2', padx=12 if small else 19,
                          pady=7 if small else 11,
                          font=(Tema.FUENTE, 9 if small else 10, 'bold'), **kwargs)
        boton.bind('<Enter>', lambda _ev: boton.configure(bg=hover))
        boton.bind('<Leave>', lambda _ev: boton.configure(bg=color))
        return boton

    def _tarjeta(self, parent, padding=17):
        borde = tk.Frame(parent, bg=Tema.BORDE)
        interno = tk.Frame(borde, bg=Tema.TARJETA)
        interno.pack(fill='both', expand=True, padx=1, pady=1)
        contenido = tk.Frame(interno, bg=Tema.TARJETA)
        contenido.pack(fill='both', expand=True, padx=padding, pady=padding)
        return borde, contenido

    def _titulo_pagina(self, padre, titulo, subtitulo):
        self._texto(padre, titulo, 18, peso='bold').pack(anchor='w')
        self._texto(padre, subtitulo, 10, Tema.SECUNDARIO).pack(anchor='w', pady=(3, 15))

    def _chip(self, padre, texto, color=None):
        caja = tk.Frame(padre, bg=Tema.TARJETA_ALT, padx=10, pady=5)
        self._texto(caja, texto, 9, color or Tema.SECUNDARIO,
                    bg=Tema.TARJETA_ALT).pack()
        return caja

    def _construir_estructura(self):
        layout = tk.Frame(self.ventana, bg=Tema.FONDO)
        layout.pack(fill='both', expand=True)
        lateral = tk.Frame(layout, bg=Tema.LATERAL, width=224)
        lateral.pack(side='left', fill='y')
        lateral.pack_propagate(False)
        separador = tk.Frame(layout, bg=Tema.BORDE, width=1)
        separador.pack(side='left', fill='y')

        marca = tk.Frame(lateral, bg=Tema.LATERAL)
        marca.pack(fill='x', padx=22, pady=(30, 31))
        logo = tk.Label(marca, text='λ', font=(Tema.FUENTE, 22, 'bold'),
                        fg=Tema.ACENTO, bg=Tema.TARJETA_ALT, width=2, height=1)
        logo.pack(side='left', padx=(0, 11))
        texto_marca = tk.Frame(marca, bg=Tema.LATERAL)
        texto_marca.pack(side='left')
        self._texto(texto_marca, 'URL / LAB', 15, peso='bold').pack(anchor='w')
        self._texto(texto_marca, 'FUNDAMENTOS', 8, Tema.APAGADO,
                    peso='bold').pack(anchor='w', pady=(2, 0))
        self._texto(lateral, 'ESPACIO DE TRABAJO', 8, Tema.APAGADO,
                    peso='bold').pack(anchor='w', padx=25, pady=(0, 10))

        for clave, icono, etiqueta in (
            ('resultado', '◉', 'Validador'),
            ('simulador', '▷', 'Simulador AFND'),
            ('transiciones', '≡', 'Transiciones'),
            ('grafo', '◇', 'Grafo de estados'),
        ):
            nav = tk.Frame(lateral, bg=Tema.LATERAL)
            nav.pack(fill='x', padx=12, pady=3)
            linea = tk.Frame(nav, bg=Tema.LATERAL, width=3)
            linea.pack(side='left', fill='y')
            boton = tk.Button(nav, text=f' {icono}     {etiqueta}', relief='flat',
                              borderwidth=0, highlightthickness=0, anchor='w',
                              bg=Tema.LATERAL, fg=Tema.SECUNDARIO,
                              activebackground=Tema.TARJETA_ALT,
                              activeforeground=Tema.TEXTO,
                              font=(Tema.FUENTE, 10, 'bold'), padx=12, pady=13,
                              cursor='hand2', command=lambda c=clave: self.cambiar_pagina(c))
            boton.pack(side='left', fill='x', expand=True)
            self._navegacion[clave] = (boton, linea)

        pie = tk.Frame(lateral, bg=Tema.LATERAL)
        pie.pack(side='bottom', fill='x', padx=24, pady=28)
        tk.Frame(pie, bg=Tema.BORDE, height=1).pack(fill='x', pady=(0, 17))
        self._texto(pie, '●  MODELO AFND', 9, Tema.VERDE,
                    peso='bold').pack(anchor='w')
        self._texto(pie, 'Grupo 9  ·  Proyecto final', 9,
                    Tema.SECUNDARIO).pack(anchor='w', pady=(8, 0))
        self._texto(pie, 'Tipo 3 · Lenguaje regular', 9,
                    Tema.APAGADO).pack(anchor='w', pady=(3, 0))

        self.principal = tk.Frame(layout, bg=Tema.FONDO)
        self.principal.pack(side='left', fill='both', expand=True, padx=28, pady=23)
        cabecera = tk.Frame(self.principal, bg=Tema.FONDO)
        cabecera.pack(fill='x')
        titulos = tk.Frame(cabecera, bg=Tema.FONDO)
        titulos.pack(side='left', fill='x', expand=True)
        self._texto(titulos, 'Validador de URLs', 22,
                    peso='bold').pack(anchor='w')
        self._texto(titulos, 'Explorá cómo un autómata reconoce estructuras de URL',
                    10, Tema.SECUNDARIO).pack(anchor='w', pady=(5, 0))
        badge = tk.Frame(cabecera, bg=Tema.TARJETA_ALT, padx=12, pady=9)
        badge.pack(side='right', anchor='n', pady=5)
        self._texto(badge, '●  AFND ACTIVO', 9, Tema.VERDE,
                    peso='bold', bg=Tema.TARJETA_ALT).pack()

        entrada_borde, entrada_cuerpo = self._tarjeta(self.principal, padding=18)
        entrada_borde.pack(fill='x', pady=(22, 17))
        self._texto(entrada_cuerpo, 'CADENA DE ENTRADA', 9,
                    Tema.SECUNDARIO, peso='bold').pack(anchor='w')
        fila = tk.Frame(entrada_cuerpo, bg=Tema.TARJETA)
        fila.pack(fill='x', pady=(10, 0))
        self.entrada = tk.Entry(fila, textvariable=self.url_var, bg=Tema.CAMPO,
                                fg=Tema.TEXTO, insertbackground=Tema.ACENTO,
                                selectbackground='#315184', relief='flat', bd=0,
                                font=(Tema.MONO, 12), highlightthickness=1,
                                highlightbackground=Tema.BORDE,
                                highlightcolor=Tema.ACENTO)
        self.entrada.pack(side='left', fill='x', expand=True, ipady=12, padx=(0, 8))
        self.entrada.bind('<Return>', lambda _e: self.validar())
        self._boton(fila, 'Validar URL', self.validar, primary=True).pack(side='left', padx=(0, 7))
        self._boton(fila, 'Simular', self.iniciar_simulacion).pack(side='left')

        ejemplos = tk.Frame(entrada_cuerpo, bg=Tema.TARJETA)
        ejemplos.pack(fill='x', pady=(13, 0))
        self._texto(ejemplos, 'PROBÁ CON:', 8, Tema.APAGADO,
                    peso='bold').pack(side='left', padx=(0, 8))
        for etiqueta, cadena in (
            ('Dominio .ar', 'https://ejemplo.ar'),
            ('Con ruta', 'https://google.com/productos/123'),
            ('Consulta', 'https://google.com?pagina=2&orden=1'),
            ('Puerto', 'https://google.com:8080'),
        ):
            boton = self._boton(ejemplos, etiqueta,
                                lambda valor=cadena: self.establecer_ejemplo(valor), small=True)
            boton.pack(side='left', padx=(0, 6))

        self.area = tk.Frame(self.principal, bg=Tema.FONDO)
        self.area.pack(fill='both', expand=True)
        for nombre in ('resultado', 'simulador', 'transiciones', 'grafo'):
            self._pestanas[nombre] = tk.Frame(self.area, bg=Tema.FONDO)

        self.estado_pie = self._texto(self.principal,
                    'Verificación sintáctica · No se comprueba si el dominio existe',
                    9, Tema.APAGADO)
        self.estado_pie.pack(side='bottom', anchor='w', pady=(12, 0))

    # ---------- Resultado ----------

    def _crear_resultado(self):
        marco = self._pestanas['resultado']
        self._titulo_pagina(marco, 'Resultado del análisis',
                           'Validación y explicación de la cadena de entrada.')
        columnas = tk.Frame(marco, bg=Tema.FONDO)
        columnas.pack(fill='both', expand=True)
        izquierda = tk.Frame(columnas, bg=Tema.FONDO)
        izquierda.pack(side='left', fill='both', expand=True, padx=(0, 9))
        derecha = tk.Frame(columnas, bg=Tema.FONDO, width=265)
        derecha.pack(side='left', fill='y', padx=(9, 0))
        derecha.pack_propagate(False)

        b1, card = self._tarjeta(izquierda, padding=23)
        b1.pack(fill='both', expand=True)
        self.status_label = self._texto(card, '○  SIN EVALUAR', 10,
                                        Tema.SECUNDARIO, peso='bold')
        self.status_label.pack(anchor='w', pady=(6, 10))
        self.status_grande = self._texto(card, 'Ingresá una URL', 23,
                                         peso='bold', wraplength=450)
        self.status_grande.pack(anchor='w', pady=(0, 12))
        self.status_detalle = self._texto(card, 'Escribí una cadena arriba o elegí uno de los ejemplos.\n'
                                               'El AFND determinará si pertenece al lenguaje.',
                                          11, Tema.SECUNDARIO, wraplength=480,
                                          justify='left')
        self.status_detalle.pack(anchor='w', pady=(0, 15))
        tk.Frame(card, bg=Tema.BORDE, height=1).pack(fill='x', pady=(8, 20))
        self._texto(card, 'ESTRUCTURA RECONOCIDA', 9, Tema.APAGADO,
                    peso='bold').pack(anchor='w')
        self.etiqueta_componentes = self._texto(card, 'Todavía no hay datos.', 11,
                                                 Tema.TEXTO, wraplength=490,
                                                 justify='left')
        self.etiqueta_componentes.pack(anchor='w', pady=(8, 0))

        b2, card2 = self._tarjeta(derecha, padding=19)
        b2.pack(fill='x', pady=(0, 15))
        self._texto(card2, 'RESUMEN DEL ANÁLISIS', 9, Tema.APAGADO,
                    peso='bold').pack(anchor='w', pady=(0, 14))
        self.metricas = {}
        for titulo, clave in [('Longitud de entrada', 'longitud'),
                              ('Estados activos al final', 'activos'),
                              ('Estados finales activos', 'finales')]:
            f = tk.Frame(card2, bg=Tema.TARJETA)
            f.pack(fill='x', pady=7)
            self._texto(f, titulo, 9, Tema.SECUNDARIO).pack(anchor='w')
            metrica = self._texto(f, '—', 17, peso='bold')
            metrica.pack(anchor='w', pady=(2, 0))
            self.metricas[clave] = metrica

        tk.Frame(card, bg=Tema.BORDE, height=1).pack(fill='x', pady=(24, 13))
        self._texto(card, 'ALCANCE DEL VALIDADOR', 9, Tema.APAGADO,
                    peso='bold').pack(anchor='w', pady=(0, 7))
        self._texto(card, 'Reconocimiento sintáctico con AFND, más control numérico del puerto. '
                    'No se comprueba si el dominio existe o está disponible.',
                    9, Tema.SECUNDARIO, justify='left',
                    wraplength=490).pack(anchor='w')

    def _procesar(self):
        self.resultado = evaluar_cadena(nfa_url, self.url_var.get())
        r = self.resultado
        self.metricas['longitud'].configure(text=str(len(r['cadena'])))
        self.metricas['activos'].configure(text=str(len(r['pasos'][-1]['estados'])))
        self.metricas['finales'].configure(text=str(len(r['estados_finales'])))
        self.etiqueta_componentes.configure(text=r['estructura'] or 'Sin rama de aceptación.')
        if not r['cadena']:
            texto = 'Ingresá una URL'
            estado = '○  FALTA UNA CADENA'
            color = Tema.AMARILLO
        elif r['aceptada']:
            texto = 'URL aceptada'
            estado = '●  ESTRUCTURA VÁLIDA'
            color = Tema.VERDE
        else:
            texto = 'URL rechazada'
            estado = '●  ESTRUCTURA INVÁLIDA'
            color = Tema.ROJO
        self.status_grande.configure(text=texto, fg=color)
        self.status_label.configure(text=estado, fg=color)
        self.status_detalle.configure(text=r['mensaje'])
        self.estado_pie.configure(text='Última comprobación: ' + r['mensaje'])
        return r

    def establecer_ejemplo(self, texto):
        self.url_var.set(texto)
        self.validar()

    def validar(self):
        self._procesar()
        self.cambiar_pagina('resultado')

    # ---------- Simulador ----------

    def _crear_simulador(self):
        marco = self._pestanas['simulador']
        self._titulo_pagina(marco, 'Simulador paso a paso',
                           'Observá los conjuntos de estados activos al leer cada símbolo.')
        herramientas = tk.Frame(marco, bg=Tema.FONDO)
        herramientas.pack(fill='x', pady=(0, 12))
        self.boton_retroceder = self._boton(herramientas, '← Anterior', self.anterior, small=True)
        self.boton_retroceder.pack(side='left')
        self.boton_avanzar = self._boton(herramientas, 'Siguiente →', self.siguiente, small=True)
        self.boton_avanzar.pack(side='left', padx=7)
        self.boton_reiniciar = self._boton(herramientas, '↺ Inicio', self.reiniciar_simulacion, small=True)
        self.boton_reiniciar.pack(side='left')
        self.label_paso = self._texto(herramientas, 'PASO 0 / 0', 10,
                                     Tema.ACENTO, peso='bold')
        self.label_paso.pack(side='right', pady=9)

        barra = tk.Frame(marco, bg=Tema.BORDE, height=5)
        barra.pack(fill='x', pady=(0, 13))
        barra.pack_propagate(False)
        self.barra_progreso = tk.Frame(barra, bg=Tema.ACENTO)
        self.barra_progreso.place(x=0, y=0, relheight=1, relwidth=0)

        b, cadena_card = self._tarjeta(marco, padding=11)
        b.pack(fill='x', pady=(0, 13))
        self._texto(cadena_card, 'CADENA EN PROCESAMIENTO', 8,
                    Tema.APAGADO, peso='bold').pack(anchor='w')
        self.texto_cadena = tk.Text(cadena_card, height=2, font=(Tema.MONO, 12),
                                   bg=Tema.TARJETA, fg=Tema.TEXTO,
                                   insertbackground=Tema.ACENTO, wrap='none',
                                   relief='flat', bd=0, pady=6)
        self.texto_cadena.pack(fill='x')
        self.texto_cadena.tag_configure('simbolo_actual', background=Tema.ACENTO,
                                        foreground=Tema.FONDO)
        self.texto_cadena.configure(state='disabled')

        panel = tk.Frame(marco, bg=Tema.FONDO)
        panel.pack(fill='both', expand=True)
        izquierda = tk.Frame(panel, bg=Tema.FONDO)
        izquierda.pack(side='left', fill='both', expand=True, padx=(0, 8))
        derecha = tk.Frame(panel, bg=Tema.FONDO, width=315)
        derecha.pack(side='left', fill='both', padx=(8, 0))
        derecha.pack_propagate(False)

        b1, dentro = self._tarjeta(izquierda, padding=10)
        b1.pack(fill='both', expand=True)
        arbol_wrap = tk.Frame(dentro, bg=Tema.TARJETA)
        arbol_wrap.pack(fill='both', expand=True)
        self.tabla_pasos = ttk.Treeview(arbol_wrap, columns=('leido', 'estados'),
                                        show='headings', style='Dark.Treeview')
        for col, label, width in [('leido', 'Símbolo', 105),
                                   ('estados', 'Conjunto de estados activos', 370)]:
            self.tabla_pasos.heading(col, text=label)
            self.tabla_pasos.column(col, width=width,
                                    stretch=col == 'estados', anchor='w')
        scroll = ttk.Scrollbar(arbol_wrap, orient='vertical', command=self.tabla_pasos.yview,
                               style='Dark.Vertical.TScrollbar')
        self.tabla_pasos.configure(yscrollcommand=scroll.set)
        self.tabla_pasos.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tabla_pasos.bind('<<TreeviewSelect>>', self._seleccionar_paso)

        b2, detalle_card = self._tarjeta(derecha, padding=13)
        b2.pack(fill='both', expand=True)
        self._texto(detalle_card, 'ESTADOS ACTIVOS', 9, Tema.APAGADO,
                    peso='bold').pack(anchor='w')
        self.texto_estados = self._texto(detalle_card, '—', 10,
                                        Tema.ACENTO, peso='bold',
                                        wraplength=265, justify='left')
        self.texto_estados.pack(anchor='w', pady=(8, 12))
        tk.Frame(detalle_card, height=1, bg=Tema.BORDE).pack(fill='x', pady=(0, 10))
        self._texto(detalle_card, 'TRANSICIONES DEL PASO', 9,
                    Tema.APAGADO, peso='bold').pack(anchor='w')
        self.detalle_transiciones = tk.Text(detalle_card, bg=Tema.TARJETA,
                                           fg=Tema.TEXTO, wrap='word',
                                           font=(Tema.MONO, 9), relief='flat',
                                           bd=0, width=27, height=9)
        self.detalle_transiciones.pack(fill='both', expand=True, pady=(8, 8))
        self.detalle_transiciones.configure(state='disabled')
        self.estado_simulacion = self._texto(detalle_card, 'Cargá una URL para iniciar.',
                                             9, Tema.SECUNDARIO, wraplength=265,
                                             justify='left')
        self.estado_simulacion.pack(anchor='w', pady=(4, 0))
        self._estado_botones_simulacion()

    def iniciar_simulacion(self):
        r = self._procesar()
        self.posicion = 0
        self.tabla_pasos.delete(*self.tabla_pasos.get_children())
        for paso in r['pasos']:
            num = paso['indice']
            simbolo = 'INICIO' if paso['simbolo'] is None else repr(paso['simbolo'])
            activos = ', '.join(sorted(paso['estados'])) if paso['estados'] else '∅'
            self.tabla_pasos.insert('', 'end', iid=str(num), values=(simbolo, activos))
        self.cambiar_pagina('simulador')
        self._mostrar_paso()

    def _seleccionar_paso(self, _event):
        if self._fila_seleccionando or self.resultado is None:
            return
        seleccion = self.tabla_pasos.selection()
        if seleccion:
            nuevo_indice = int(seleccion[0])
            if nuevo_indice != self.posicion:
                self.posicion = nuevo_indice
                self._mostrar_paso()

    def _mostrar_paso(self):
        if self.resultado is None:
            return
        paso = self.resultado['pasos'][self.posicion]
        texto = self.resultado['cadena']
        self.label_paso.configure(text=f'PASO {self.posicion} / {len(texto)}')
        self.barra_progreso.place_configure(relwidth=(self.posicion / len(texto) if texto else 0))
        self.texto_cadena.configure(state='normal')
        self.texto_cadena.delete('1.0', 'end')
        self.texto_cadena.insert('1.0', texto)
        if self.posicion > 0:
            self.texto_cadena.tag_add('simbolo_actual', f'1.{self.posicion - 1}', f'1.{self.posicion}')
            self.texto_cadena.see(f'1.{self.posicion - 1}')
        self.texto_cadena.configure(state='disabled')
        estados = ', '.join(sorted(paso['estados'])) if paso['estados'] else '∅ · sin ramas posibles'
        self.texto_estados.configure(text=estados)
        if self.posicion == 0:
            transiciones = 'Estado inicial: ' + nfa_url.initial_state
        elif not paso['transiciones']:
            transiciones = 'No existen transiciones válidas para este símbolo.'
        else:
            transiciones = '\n'.join(f'{a}  --{s}→  {b}' for a, s, b in paso['transiciones'])
        self.detalle_transiciones.configure(state='normal')
        self.detalle_transiciones.delete('1.0', 'end')
        self.detalle_transiciones.insert('1.0', transiciones)
        self.detalle_transiciones.configure(state='disabled')
        ult = self.posicion == len(texto)
        final = bool(paso['estados'] & set(nfa_url.final_states))
        if ult and self.resultado['aceptada']:
            mensaje, color = '● ACEPTADA — se alcanza un estado final.', Tema.VERDE
        elif ult and final:
            mensaje, color = '● AFND acepta, pero la regla del puerto rechaza.', Tema.AMARILLO
        elif ult:
            mensaje, color = '● RECHAZADA — ningún estado final activo.', Tema.ROJO
        elif final:
            mensaje, color = 'Un estado final está activo; aún quedan símbolos.', Tema.ACENTO
        else:
            mensaje, color = 'Procesando la entrada...', Tema.SECUNDARIO
        self.estado_simulacion.configure(text=mensaje, fg=color)
        self._fila_seleccionando = True
        if self.tabla_pasos.selection() != (str(self.posicion),):
            self.tabla_pasos.selection_set(str(self.posicion))
        self.tabla_pasos.see(str(self.posicion))
        self._fila_seleccionando = False
        self._estado_botones_simulacion()

    def _estado_botones_simulacion(self):
        disponible = self.resultado is not None
        self.boton_retroceder.configure(state='normal' if disponible and self.posicion > 0 else 'disabled')
        self.boton_avanzar.configure(state='normal' if disponible and self.posicion < len(self.resultado['cadena']) else 'disabled')
        self.boton_reiniciar.configure(state='normal' if disponible and self.posicion > 0 else 'disabled')

    def anterior(self):
        if self.resultado and self.posicion > 0:
            self.posicion -= 1
            self._mostrar_paso()

    def siguiente(self):
        if self.resultado and self.posicion < len(self.resultado['cadena']):
            self.posicion += 1
            self._mostrar_paso()

    def reiniciar_simulacion(self):
        if self.resultado:
            self.posicion = 0
            self._mostrar_paso()

    # ---------- Tabla de transiciones ----------

    def _crear_transiciones(self):
        marco = self._pestanas['transiciones']
        self._titulo_pagina(marco, 'Tabla de transiciones',
                           'Construida directamente a partir de nfa_url.transitions; sin duplicar reglas.')
        herramientas = tk.Frame(marco, bg=Tema.FONDO)
        herramientas.pack(fill='x', pady=(0, 12))
        self._texto(herramientas, f'{len(nfa_url.states)} estados', 10, Tema.ACENTO,
                    peso='bold').pack(side='left')
        self._texto(herramientas, f'   ·   {len(nfa_url.final_states)} finales',
                    10, Tema.SECUNDARIO).pack(side='left')
        self._texto(herramientas, '   ·   Agrupadas por estado y destino',
                    9, Tema.APAGADO).pack(side='left')

        b, buscar_card = self._tarjeta(marco, padding=10)
        b.pack(fill='x', pady=(0, 12))
        buscar = tk.Frame(buscar_card, bg=Tema.TARJETA)
        buscar.pack(fill='x')
        self._texto(buscar, 'BUSCAR', 9, Tema.SECUNDARIO,
                    peso='bold').pack(side='left', padx=(3, 14))
        self.buscar_entrada = tk.Entry(buscar, textvariable=self.filtro_var,
                                       bg=Tema.CAMPO, fg=Tema.TEXTO,
                                       insertbackground=Tema.ACENTO,
                                       font=(Tema.MONO, 10), relief='flat',
                                       highlightthickness=1,
                                       highlightbackground=Tema.BORDE,
                                       highlightcolor=Tema.ACENTO)
        self.buscar_entrada.pack(side='left', fill='x', expand=True, ipady=8)
        self.filtro_var.trace_add('write', lambda *_args: self._refrescar_transiciones())

        b2, interior = self._tarjeta(marco, padding=9)
        b2.pack(fill='both', expand=True)
        table_wrap = tk.Frame(interior, bg=Tema.TARJETA)
        table_wrap.pack(fill='both', expand=True)
        self.tabla_transiciones = ttk.Treeview(table_wrap,
                    columns=('origen', 'simbolo', 'destino'), show='headings',
                    style='Dark.Treeview')
        for clave, titulo, ancho in (
            ('origen', 'Estado actual', 185),
            ('simbolo', 'Entrada / alfabeto', 250),
            ('destino', 'Estados destino', 240),
        ):
            self.tabla_transiciones.heading(clave, text=titulo)
            self.tabla_transiciones.column(clave, width=ancho,
                                             stretch=True, anchor='w')
        vertical = ttk.Scrollbar(table_wrap, orient='vertical', command=self.tabla_transiciones.yview,
                                  style='Dark.Vertical.TScrollbar')
        self.tabla_transiciones.configure(yscrollcommand=vertical.set)
        self.tabla_transiciones.pack(side='left', fill='both', expand=True)
        vertical.pack(side='right', fill='y')
        self.pie_transiciones = self._texto(marco, '', 9, Tema.SECUNDARIO)
        self.pie_transiciones.pack(anchor='w', pady=(10, 0))

        grupos = defaultdict(set)
        for origen, transiciones in nfa_url.transitions.items():
            for simbolo, destinos in transiciones.items():
                for destino in destinos:
                    grupos[(origen, destino)].add(simbolo)
        self.grupos_transiciones = [
            (origen, abreviar_simbolos(caracteres), destino)
            for (origen, destino), caracteres in sorted(grupos.items())
        ]
        self._refrescar_transiciones()

    def _refrescar_transiciones(self):
        if not hasattr(self, 'tabla_transiciones'):
            return
        consulta = self.filtro_var.get().strip().lower()
        tabla = self.tabla_transiciones
        tabla.delete(*tabla.get_children())
        visibles = 0
        for fila in self.grupos_transiciones:
            if consulta and not any(consulta in campo.lower() for campo in fila):
                continue
            tabla.insert('', 'end', values=fila)
            visibles += 1
        self.pie_transiciones.configure(text=f'{visibles} grupos visibles de '
                                            f'{len(self.grupos_transiciones)}  ·  '
                                            f'Las letras y dígitos se muestran agrupados en rangos.')

    # ---------- Diagrama ----------

    def _crear_grafo(self):
        marco = self._pestanas['grafo']
        self._titulo_pagina(marco, 'Grafo del autómata',
                           'Vista completa generada a partir de las transiciones reales del AFND.')
        controles = tk.Frame(marco, bg=Tema.FONDO)
        controles.pack(fill='x', pady=(0, 12))
        self._boton(controles, '↻ Actualizar', self.generar_diagrama, small=True).pack(side='left')
        self._boton(controles, '−', lambda: self.cambiar_zoom(.8), small=True).pack(side='left', padx=(9, 5))
        self._boton(controles, '+', lambda: self.cambiar_zoom(1.25), small=True).pack(side='left')
        self._boton(controles, 'Ajustar', self.ajustar_zoom, small=True).pack(side='left', padx=(9, 0))
        self.etiqueta_grafo = self._texto(controles, 'Abrí esta sección para visualizar el grafo.',
                                          9, Tema.SECUNDARIO)
        self.etiqueta_grafo.pack(side='left', padx=12)
        b, contenedor = self._tarjeta(marco, padding=4)
        b.pack(fill='both', expand=True)
        self.lienzo = tk.Canvas(contenedor, bg='#EDF2FA', relief='flat',
                                borderwidth=0, highlightthickness=0)
        sx = ttk.Scrollbar(contenedor, orient='horizontal', command=self.lienzo.xview,
                           style='Dark.Horizontal.TScrollbar')
        sy = ttk.Scrollbar(contenedor, orient='vertical', command=self.lienzo.yview,
                           style='Dark.Vertical.TScrollbar')
        self.lienzo.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        sx.pack(side='bottom', fill='x')
        sy.pack(side='right', fill='y')
        self.lienzo.pack(side='left', fill='both', expand=True)
        self.lienzo.bind('<ButtonPress-1>', lambda e: self.lienzo.scan_mark(e.x, e.y))
        self.lienzo.bind('<B1-Motion>', lambda e: self.lienzo.scan_dragto(e.x, e.y, gain=1))

    def generar_diagrama(self):
        destino = Path(__file__).resolve().parent / 'automata_afnd_actualizado.png'
        try:
            self._grafo = generar_grafo(nfa_url, destino)
            self.ajustar_zoom()
            self.etiqueta_grafo.configure(text='Actualizado desde el código  ·  Arrastrá para desplazarte.',
                                          fg=Tema.VERDE)
        except Exception as error:
            if destino.is_file():
                self._grafo = destino
                self.ajustar_zoom()
                self.etiqueta_grafo.configure(text='Usando imagen incluida. Falta dot para regenerarla.',
                                              fg=Tema.AMARILLO)
            else:
                self.etiqueta_grafo.configure(text=f'No disponible: {error}. Revisá «dot -V».',
                                              fg=Tema.ROJO)
                self.lienzo.delete('all')

    def ajustar_zoom(self):
        if not self._grafo:
            return
        self.lienzo.update_idletasks()
        with Image.open(self._grafo) as img:
            ancho = max(1, self.lienzo.winfo_width() - 20)
            alto = max(1, self.lienzo.winfo_height() - 20)
            self.zoom = max(.10, min(1.8, min(ancho / img.width, alto / img.height)))
        self._pintar_grafo()

    def cambiar_zoom(self, factor):
        if not self._grafo:
            return
        self.zoom = max(.10, min(2.2, self.zoom * factor))
        self._pintar_grafo()

    def _pintar_grafo(self):
        if not self._grafo:
            return
        with Image.open(self._grafo) as im:
            ancho = max(1, int(im.width * self.zoom))
            alto = max(1, int(im.height * self.zoom))
            resized = im.resize((ancho, alto), Image.Resampling.LANCZOS)
            self._img = ImageTk.PhotoImage(resized)
        self.lienzo.delete('all')
        self.lienzo.create_image(0, 0, image=self._img, anchor='nw')
        self.lienzo.configure(scrollregion=(0, 0, ancho, alto))
        self.lienzo.xview_moveto(0)
        self.lienzo.yview_moveto(0)

    # ---------- Navegación ----------

    def cambiar_pagina(self, pagina):
        if self.pagina_actual == pagina:
            return
        for panel in self._pestanas.values():
            panel.pack_forget()
        self._pestanas[pagina].pack(fill='both', expand=True)
        self.pagina_actual = pagina
        for clave, (boton, barra) in self._navegacion.items():
            activo = clave == pagina
            boton.configure(bg=Tema.TARJETA_ALT if activo else Tema.LATERAL,
                            fg=Tema.TEXTO if activo else Tema.SECUNDARIO)
            barra.configure(bg=Tema.ACENTO if activo else Tema.LATERAL)
        if pagina == 'grafo' and not self._grafo_iniciado:
            self._grafo_iniciado = True
            self.ventana.after_idle(self.generar_diagrama)


if __name__ == '__main__':
    raiz = tk.Tk()
    AppModerna(raiz)
    raiz.mainloop()
