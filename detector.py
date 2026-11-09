from pathlib import Path
from collections import defaultdict
import re
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
            mensaje = f'El puerto {puerto} excede el valor máximo permitido (65535).'
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


