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
    dot.attr(rankdir='LR', size='16,10', dpi='300')
    dot.attr('node', shape='circle', fontname='Helvetica', fontsize='10')
    dot.attr('edge', fontname='Helvetica', fontsize='8')

    # 1. ESTADOS FINALES / DE ACEPTACIÓN (Doble círculo)
    estados_finales = [
        '3letra', '2LETRA', 
        '1num', '2num', '3num', '4num', '5num', 
        'q20'
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

    # Subdominio, Dominio y Validación con '1caracter_dominio'
    dot.edge('q0', 'subdominio', label='[a-zA-Z0-9]')
    dot.edge('q0', 'dominio', label='[a-zA-Z0-9]')
    
    dot.edge('subdominio', 'subdominio', label='[a-zA-Z0-9]')
    
    # --- Transición corregida para evitar puntos dobles (e.g., www..com) ---
    dot.edge('subdominio', '1caracter_dominio', label='.')
    dot.edge('1caracter_dominio', 'dominio', label='[a-zA-Z0-9]')
    # ------------------------------------------------------------------------

    dot.edge('dominio', 'dominio', label='[a-zA-Z0-9]')
    dot.edge('dominio', 'extension', label='.')
    dot.edge('dominio', 'subdominio', label='.')   
    dot.edge('dominio', 'PAIS', label='.')  

    # Extensión TLD (3 letras obligatorias)
    dot.edge('extension', '1letra', label='[a-zA-Z]')
    dot.edge('1letra', '2letra', label='[a-zA-Z]')
    dot.edge('2letra', '3letra', label='[a-zA-Z]')

    # Extensión ccTLD / País (2 letras opcionales)
    dot.edge('3letra', 'PAIS', label='.')
    dot.edge('PAIS', '1LETRA', label='[a-zA-Z]')
    dot.edge('1LETRA', '2LETRA', label='[a-zA-Z]')

    # Puerto TCP (1 a 5 dígitos)
    dot.edge('3letra', 'puerto', label=':')
    dot.edge('2LETRA', 'puerto', label=':')
    dot.edge('puerto', '1num', label='[0-9]')
    dot.edge('1num', '2num', label='[0-9]')
    dot.edge('2num', '3num', label='[0-9]')
    dot.edge('3num', '4num', label='[0-9]')
    dot.edge('4num', '5num', label='[0-9]')

    # Ruta / Path
    dot.edge('3letra', 'ruta', label='/')
    dot.edge('2LETRA', 'ruta', label='/')
    dot.edge('1num', 'ruta', label='/')
    dot.edge('2num', 'ruta', label='/')
    dot.edge('3num', 'ruta', label='/')
    dot.edge('4num', 'ruta', label='/')
    dot.edge('5num', 'ruta', label='/')
    
    dot.edge('ruta', 'q20', label='[a-zA-Z0-9]')
    dot.edge('q20', 'q20', label='[a-zA-Z0-9]')

    # 4. RENDERIZADO DEL ARCHIVO PNG
    try:
        nombre_archivo = dot.render('automata_graphviz', cleanup=True)
        print(f"✓ Imagen generada exitosamente: {nombre_archivo}")
    except Exception as e:
        print(f"✗ Error al generar la imagen con Graphviz: {e}")

if __name__ == '__main__':
    generar_grafico_automata()