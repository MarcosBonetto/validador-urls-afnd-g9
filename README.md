Proyecto del **Grupo 9** de la asignatura **Fundamentos Teóricos de Informática**, Universidad Nacional de la Patagonia San Juan Bosco (UNPSJB).

Es una aplicación de escritorio desarrollada en **Python y Tkinter** que analiza la estructura de una URL mediante un **Autómata Finito No Determinista (AFND) de 34 estados**. Informa si la cadena pertenece al lenguaje definido, descompone las URLs aceptadas en sus componentes y permite visualizar el grafo del autómata.

> **Alcance:** es un validador *sintáctico*. No comprueba si la dirección existe, si el servidor responde ni si el sitio web es seguro.

## Requisitos e instalación

- Python 3, con **Tkinter** disponible.
- Dependencias de `requirements.txt`: `automata-lib`, `Pillow` y `graphviz` (paquete de Python).
- **Graphviz (aplicación de escritorio)** solo es necesario para **regenerar** la imagen del AFND. Para visualizar el PNG incluido no hace falta instalar el ejecutable `dot`.

Abrí una terminal en la carpeta raíz del proyecto e instalá las dependencias:

**Windows (PowerShell):**

```powershell
py -m pip install -r requirements.txt
py validador.py
```

**Linux / macOS** (según la instalación de Python y Tkinter):

```bash
python3 -m pip install -r requirements.txt
python3 validador.py
```

Para comprobar la instalación del programa Graphviz, ejecutá `dot -V`. Si el comando no se reconoce, instalá Graphviz desde <https://graphviz.org/download/> y agregá su carpeta `bin` al `PATH`. El paquete `graphviz` de Python **no incluye** el ejecutable `dot`.

## Funcionalidades

El lenguaje implementado admite:

- Protocolos opcionales `http://` y `https://` (se normalizan las mayúsculas/minúsculas del protocolo antes de evaluar).
- Dominios y subdominios alfanuméricos, con guiones internos y varios niveles; `www` no es obligatorio.
- Extensiones de **dos letras** (`.ar`, `.io`), de **tres o más** (`.com`, `.technology`) y compuestas (`.com.ar`).
- Puertos opcionales de **uno a cinco dígitos**. El AFND verifica la estructura; el código complementario comprueba el rango numérico **0–65535**.
- Rutas con múltiples segmentos alfanuméricos y barra final opcional.
- Consultas con pares `clave=valor`, por ejemplo `?id=10&pagina=2`.

La interfaz ofrece el resultado de aceptación o rechazo, los componentes identificados y un historial de **hasta cuatro verificaciones** durante la sesión.

### Ejemplos para probar

| URL | Resultado esperado |
|---|---|
| `https://www.mi-pagina.com.ar:8080/productos/123?id=10&orden=2` | Aceptada |
| `https://google.technology/usuarios/perfil/` | Aceptada |
| `http://servidor.io:65535?activo=1` | Aceptada |
| `https://pagina-.com/productos` | Rechazada (guion final) |
| `https://google.com:65536` | Rechazada (puerto fuera de rango) |
| `https://google.com/productos//123` | Rechazada (segmento vacío) |

### Limitaciones

Reconoce el **subconjunto de URLs definido para este proyecto**, no todas las variantes previstas por los estándares de Internet. No admite, entre otras, direcciones IPv4/IPv6 como host, fragmentos `#`, codificación porcentual (`%20`) ni caracteres especiales arbitrarios dentro de rutas o parámetros. Tampoco consulta DNS ni realiza conexiones HTTP.

## Visualización del AFND

1. Ejecutá `validador.py`.
2. Presioná **Ver grafo AFND** para abrir `automata_afnd_actualizado.png` en una ventana independiente.
3. Utilizá **+**, **−**, **100 %**, **Ajustar** y las barras de desplazamiento para explorar el diagrama.
4. La opción **Actualizar desde AFND** regenera el PNG directamente a partir de las transiciones de `detector.py`; requiere el programa Graphviz instalado y disponible en `PATH`.
5. Para inspeccionar o simular el autómata en JFLAP, abrí `AFND_actualizado.jff`.

El archivo JFLAP actualizado corresponde a los **34 estados**, **11 estados de aceptación** y las transiciones definidas en el motor. **No uses como modelo de entrega** `detectorUrls-AFND-hechoParaProbar.jff`, que corresponde a una versión anterior.

## Estructura del proyecto

| Archivo o carpeta | Descripción |
|---|---|
| `detector.py` | Definición del AFND, simulación, evaluación de cadenas y generación del grafo. |
| `validador.py` | Interfaz gráfica y presentación de resultados. |
| `visor_grafo.py` | Ventana de visualización, zoom, desplazamiento y actualización del grafo. |
| `AFND_actualizado.jff` | Autómata actualizado en formato JFLAP. |
| `automata_afnd_actualizado.png` | Diagrama vigente usado por el visor. |
| `requirements.txt` | Dependencias de Python. |
| `Respaldos/` | Archivos históricos de desarrollo; no son necesarios para ejecutar la aplicación. |

Si todavía aparecen `automata_graphviz.png` o `detectorUrls-AFND-hechoParaProbar.jff` en el repositorio, **son archivos de versiones anteriores** y no deben confundirse con el diagrama y el JFLAP actualizados. El generador manual `Respaldos/generadorImagen.py` tampoco es la fuente vigente del grafo: el visor puede generarlo desde `detector.py`.

El **informe técnico en PDF** se entrega junto con el proyecto e incluye el modelo formal, la gramática regular, la EBNF y los casos de prueba.

## Integrantes — Grupo 9

- Gonzalez Bonetto Marcos
- Cárcamo Mateo
- Gomes dos Ramos Gonzalo
