
import graphviz

# ---------------------------------------------------------
# SCRIPT INDEPENDIENTE: GENERADOR DE DIAGRAMA GRAPHVIZ
# ---------------------------------------------------------
def generar_grafico_automata():
    dot = graphviz.Digraph(
        'NFA_URL', 
        format='png', 
        comment='Autómata Finito No Determinista para Validación de URLs'
    )
    
    # Atributos generales del grafo
    dot.attr(rankdir='LR', size='18,12', dpi='300')
    dot.attr('node', shape='circle', fontname='Helvetica', fontsize='10')
    dot.attr('edge', fontname='Helvetica', fontsize='8')

    # 1. ESTADOS FINALES / DE ACEPTACIÓN (Doble círculo) - Sincronizados con detector.py
    estados_finales = [
        '3letra', '2LETRA', 'tld_largo',
        '1num', '2num', '3num', '4num', '5num', 
        'ruta', 'consulta_valor', 'q20'
    ]
    for estado in estados_finales:
        dot.node(estado, shape='doublecircle', style='filled', fillcolor='#e8f5e9')

    # 2. ESTADO INICIAL (Con flecha de entrada)
    dot.node('invisible_start', style='invis', width='0', height='0')
    dot.edge('invisible_start', 'q0', label='inicio')

    # 3. TRANSICIONES DEL AFND
    
    # Protocolo (http:// o https://)
    dot.edge('q0', 'q1', label='h')
    dot.edge('q1', 'q2', label='t')
    dot.edge('q2', 'q3', label='t')
    dot.edge('q3', 'q4', label='p')
    dot.edge('q4', 'q5', label='s')
    dot.edge('q4', 'q6', label=':')
    dot.edge('q5', 'q6', label=':')
    dot.edge('q6', 'q21', label='/')
    dot.edge('q21', 'q7', label='/')
    dot.edge('q7', 'subdominio', label='[a-zA-Z0-9]')
    dot.edge('q7', 'dominio', label='[a-zA-Z0-9]')

    # Inicio directo sin protocolo explícito (desde q0)
    dot.edge('q0', 'subdominio', label='[a-zA-Z0-9]')
    dot.edge('q0', 'dominio', label='[a-zA-Z0-9]')
    
    # --- Validación Subdominio y Guiones ---
    dot.edge('subdominio', 'subdominio', label='[a-zA-Z0-9]')
    dot.edge('subdominio', '-', label='-') # Representado visualmente o mediante subdominio_guion
    dot.edge('subdominio', 'subdominio_guion', label='-')
    dot.edge('subdominio_guion', 'subdominio_guion', label='-')
    dot.edge('subdominio_guion', 'subdominio', label='[a-zA-Z0-9]')
    
    dot.edge('subdominio', '1caracter_dominio', label='.')
    dot.edge('1caracter_dominio', 'dominio', label='[a-zA-Z0-9]')

    # --- Validación Dominio y Guiones ---
    dot.edge('dominio', 'dominio', label='[a-zA-Z0-9]')
    dot.edge('dominio', 'dominio_guion', label='-')
    dot.edge('dominio_guion', 'dominio_guion', label='-')
    dot.edge('dominio_guion', 'dominio', label='[a-zA-Z0-9]')

    dot.edge('dominio', 'extension', label='.')
    dot.edge('dominio', '1caracter_dominio', label='.') 
    dot.edge('dominio', 'PAIS', label='.')  

    # Extensión TLD (3 letras y TLDs largos)
    dot.edge('extension', '1letra', label='[a-zA-Z]')
    dot.edge('1letra', '2letra', label='[a-zA-Z]')
    dot.edge('2letra', '3letra', label='[a-zA-Z]')
    
    dot.edge('3letra', 'tld_largo', label='[a-zA-Z]')
    dot.edge('tld_largo', 'tld_largo', label='[a-zA-Z]')

    # Extensión ccTLD / País (2 letras opcionales)
    dot.edge('3letra', 'PAIS', label='.')
    dot.edge('tld_largo', 'PAIS', label='.')
    dot.edge('PAIS', '1LETRA', label='[a-zA-Z]')
    dot.edge('1LETRA', '2LETRA', label='[a-zA-Z]')

    # Puerto TCP (1 a 5 dígitos)
    for est_tld in ['3letra', 'tld_largo', '2LETRA']:
        dot.edge(est_tld, 'puerto', label=':')

    dot.edge('puerto', '1num', label='[0-9]')
    dot.edge('1num', '2num', label='[0-9]')
    dot.edge('2num', '3num', label='[0-9]')
    dot.edge('3num', '4num', label='[0-9]')
    dot.edge('4num', '5num', label='[0-9]')
    dot.edge('5num', '5num', label='[0-9]') # Opcional/Permisivo de longitud en autómata

    # Ruta / Path
    estados_previos_ruta = ['3letra', 'tld_largo', '2LETRA', '1num', '2num', '3num', '4num', '5num']
    for est in estados_previos_ruta:
        dot.edge(est, 'ruta', label='/')
    
    dot.edge('ruta', 'q20', label='[a-zA-Z0-9]')
    dot.edge('q20', 'ruta', label='/')
    dot.edge('q20', 'q20', label='[a-zA-Z0-9]')

    # Parámetros de Consulta (Query Strings: ?clave=valor&clave2=valor2)
    estados_permite_consulta = estados_previos_ruta + ['ruta', 'q20']
    for est in estados_permite_consulta:
        dot.edge(est, 'consulta_inicio', label='?')

    dot.edge('consulta_inicio', 'consulta_clave', label='[a-zA-Z0-9]')
    dot.edge('consulta_clave', 'consulta_clave', label='[a-zA-Z0-9]')
    dot.edge('consulta_clave', 'consulta_valor_inicio', label='=')
    dot.edge('consulta_valor_inicio', 'consulta_valor', label='[a-zA-Z0-9]')
    dot.edge('consulta_valor', 'consulta_valor', label='[a-zA-Z0-9]')
    dot.edge('consulta_valor', 'consulta_inicio', label='&')

    # 4. RENDERIZADO DEL ARCHIVO PNG
    try:
        nombre_archivo = dot.render('automata_graphviz', cleanup=True)
        print(f"✓ Imagen generada exitosamente: {nombre_archivo}")
    except Exception as e:
        print(f"✗ Error al generar la imagen con Graphviz: {e}")

if __name__ == '__main__':
    generar_grafico_automata()