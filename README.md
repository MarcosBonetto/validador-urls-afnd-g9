# Validador Sintáctico de URLs mediante AFND

Proyecto desarrollado para la materia **Fundamentos Teóricos de Informática** de la Universidad Nacional de la Patagonia San Juan Bosco.
Integrantes:
Grupo 9
- Marcos Gonzalez Bonetto
- Mateo Cárcamo
- Gonzalo Gomes dos Ramos

## Descripción

El proyecto consiste en un validador sintáctico de URLs implementado mediante un **Autómata Finito No Determinista (AFND)**.

El sistema analiza una cadena ingresada y determina si cumple con la estructura definida para el lenguaje de URLs considerado en el proyecto.

Además, incluye una interfaz gráfica desarrollada en Python y una representación visual del autómata.

## Funcionalidades

El validador reconoce actualmente:

- Protocolo opcional `http://`
- Protocolo opcional `https://`
- Dominio principal
- Subdominios
- TLD de 3 letras
- Código de país opcional de 2 letras
- Puerto opcional de 1 a 5 dígitos
- Ruta opcional

Actualmente quedan fuera del alcance:

- Parámetros de consulta o query strings
- Direcciones IPv4
- Direcciones IPv6

## Tecnologías utilizadas

- Python
- automata-lib
- Tkinter
- Pillow
- Graphviz
- JFLAP

## Requisitos

Para ejecutar el proyecto es necesario tener instalado:

- Python 3
- Graphviz
- Las siguientes librerías de Python:
  - automata-lib
  - Pillow
  - graphviz

Las librerías pueden instalarse desde una terminal con:

```bash
python -m pip install automata-lib Pillow graphviz
