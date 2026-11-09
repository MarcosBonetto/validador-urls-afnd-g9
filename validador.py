"""Interfaz de escritorio para la validación sintáctica de direcciones web.

Ejecutar: py validador_urls.py
El reconocimiento lo realiza motor_validacion.py.
"""
from datetime import datetime
from urllib.parse import urlsplit
import tkinter as tk

from motor_validacion import evaluar_cadena, nfa_url


class Paleta:
    FONDO = '#F5F7FB'
    BLANCO = '#FFFFFF'
    BORDE = '#DFE6EF'
    TEXTO = '#182335'
    SECUNDARIO = '#5E6C81'
    SUAVE = '#8593A6'
    AZUL = '#285DE5'
    AZUL_HOVER = '#1748C7'
    AZUL_CLARO = '#EAF0FF'
    AZUL_TEXTO = '#1E4AC2'
    VERDE = '#178453'
    VERDE_CLARO = '#EAF8F0'
    ROJO = '#C34146'
    ROJO_CLARO = '#FFF1F1'
    AMARILLO = '#A56F16'
    AMARILLO_CLARO = '#FFF8E8'
    SUAVE_BG = '#F8FAFC'
    TIPOGRAFIA = 'Segoe UI'
    MONO = 'Consolas'


class ValidadorURLs:
    def __init__(self, root):
        self.root = root
        self.root.title('Verificador de URLs')
        self.root.geometry('1130x820')
        self.root.minsize(970, 720)
        self.root.configure(bg=Paleta.FONDO)
        self.valor = tk.StringVar()
        self.historial = []
        self.estado_actual = None
        self._construir()
        self.valor.trace_add('write', self._marcar_pendiente)
        self.entrada.focus_set()
        self.root.bind('<Control-Return>', lambda _e: self.validar())

    def _texto(self, parent, texto, tam=10, color=None, negrita=False, **kwargs):
        return tk.Label(
            parent, text=texto, bg=kwargs.pop('bg', parent.cget('bg')),
            fg=color or Paleta.TEXTO,
            font=(Paleta.TIPOGRAFIA, tam, 'bold' if negrita else 'normal'),
            anchor=kwargs.pop('anchor', 'w'), **kwargs
        )

    def _boton(self, parent, texto, accion, principal=False, compacto=False):
        fondo = Paleta.AZUL if principal else Paleta.BLANCO
        delante = Paleta.BLANCO if principal else Paleta.TEXTO
        hover = Paleta.AZUL_HOVER if principal else Paleta.AZUL_CLARO
        boton = tk.Button(
            parent, text=texto, command=accion, bg=fondo, fg=delante,
            activebackground=hover, activeforeground=delante,
            cursor='hand2', relief='flat', bd=0, highlightthickness=0,
            padx=16 if compacto else 24, pady=7 if compacto else 13,
            font=(Paleta.TIPOGRAFIA, 10, 'bold')
        )
        boton.bind('<Enter>', lambda _e: boton.configure(bg=hover))
        boton.bind('<Leave>', lambda _e: boton.configure(bg=fondo))
        return boton

    def _tarjeta(self, parent, margen=22):
        exterior = tk.Frame(parent, bg=Paleta.BORDE)
        interior = tk.Frame(exterior, bg=Paleta.BLANCO)
        interior.pack(fill='both', expand=True, padx=1, pady=1)
        cuerpo = tk.Frame(interior, bg=Paleta.BLANCO)
        cuerpo.pack(fill='both', expand=True, padx=margen, pady=margen)
        return exterior, cuerpo

    def _etiqueta_dato(self, padre, titulo, default='—'):
        grupo = tk.Frame(padre, bg=Paleta.BLANCO)
        self._texto(grupo, titulo.upper(), 9, Paleta.SUAVE, negrita=True).pack(anchor='w')
        etiqueta = self._texto(grupo, default, 11, Paleta.TEXTO, wraplength=330,
                               justify='left')
        etiqueta.pack(anchor='w', pady=(5, 0))
        return grupo, etiqueta

    def _construir(self):
        cabecera = tk.Frame(self.root, bg=Paleta.BLANCO)
        cabecera.pack(fill='x')
        cabecera_interior = tk.Frame(cabecera, bg=Paleta.BLANCO)
        cabecera_interior.pack(fill='x', padx=48, pady=19)
        marca = tk.Frame(cabecera_interior, bg=Paleta.BLANCO)
        marca.pack(side='left')
        logotipo = tk.Frame(marca, bg=Paleta.AZUL, width=35, height=35)
        logotipo.pack(side='left')
        logotipo.pack_propagate(False)
        self._texto(logotipo, '↗', 19, Paleta.BLANCO, negrita=True,
                    bg=Paleta.AZUL, anchor='center').pack(fill='both', expand=True)
        self._texto(marca, 'URLCHECK', 15, Paleta.TEXTO, negrita=True).pack(
            side='left', padx=(12, 0))
        self._texto(cabecera_interior, 'Herramienta de validación de direcciones web',
                    9, Paleta.SECUNDARIO).pack(side='right')
        tk.Frame(self.root, bg=Paleta.BORDE, height=1).pack(fill='x')

        # Contenido desplazable: evita paneles cortados en pantallas de menor altura.
        visor = tk.Frame(self.root, bg=Paleta.FONDO)
        visor.pack(fill='both', expand=True)
        self.canvas_pagina = tk.Canvas(visor, bg=Paleta.FONDO, bd=0,
                                       highlightthickness=0)
        desplazamiento = tk.Scrollbar(visor, orient='vertical',
                                      command=self.canvas_pagina.yview,
                                      relief='flat', bd=0)
        self.canvas_pagina.configure(yscrollcommand=desplazamiento.set)
        desplazamiento.pack(side='right', fill='y')
        self.canvas_pagina.pack(side='left', fill='both', expand=True)
        contenedor = tk.Frame(self.canvas_pagina, bg=Paleta.FONDO)
        item = self.canvas_pagina.create_window((0, 0), window=contenedor, anchor='nw')
        contenedor.configure(padx=48, pady=27)
        contenedor.bind('<Configure>', lambda _e: self.canvas_pagina.configure(
            scrollregion=self.canvas_pagina.bbox('all')))
        self.canvas_pagina.bind('<Configure>', lambda e: self.canvas_pagina.itemconfigure(
            item, width=e.width))
        self.root.bind_all('<MouseWheel>', self._rueda)
        self.root.bind_all('<Button-4>', lambda _e: self.canvas_pagina.yview_scroll(-3, 'units'))
        self.root.bind_all('<Button-5>', lambda _e: self.canvas_pagina.yview_scroll(3, 'units'))

        encabezado = tk.Frame(contenedor, bg=Paleta.FONDO)
        encabezado.pack(fill='x', pady=(0, 20))
        self._texto(encabezado, 'Verificá una dirección web', 24,
                    Paleta.TEXTO, negrita=True).pack(anchor='w')
        self._texto(encabezado,
                    'Comprobá el formato de una URL y revisá sus componentes en segundos.',
                    11, Paleta.SECUNDARIO).pack(anchor='w', pady=(7, 0))

        entrada_card, formulario = self._tarjeta(contenedor, 21)
        entrada_card.pack(fill='x', pady=(0, 19))
        self._texto(formulario, 'DIRECCIÓN URL', 9, Paleta.SECUNDARIO,
                    negrita=True).pack(anchor='w')
        fila = tk.Frame(formulario, bg=Paleta.BLANCO)
        fila.pack(fill='x', pady=(10, 0))
        contorno_campo = tk.Frame(fila, bg=Paleta.BORDE)
        contorno_campo.pack(side='left', fill='x', expand=True, padx=(0, 11))
        self.entrada = tk.Entry(
            contorno_campo, textvariable=self.valor,
            font=(Paleta.MONO, 12), bg=Paleta.SUAVE_BG,
            fg=Paleta.TEXTO, insertbackground=Paleta.AZUL,
            relief='flat', bd=0, highlightthickness=0
        )
        self.entrada.pack(fill='x', padx=1, pady=1, ipady=14, ipadx=13)
        self.entrada.bind('<Return>', lambda _e: self.validar())
        self._boton(fila, 'Validar URL', self.validar, principal=True).pack(side='left')

        ejemplos = tk.Frame(formulario, bg=Paleta.BLANCO)
        ejemplos.pack(fill='x', pady=(15, 0))
        self._texto(ejemplos, 'Ejemplos:', 9, Paleta.SUAVE).pack(side='left', padx=(0, 7))
        for rotulo, url in (
            ('.ar', 'https://ejemplo.ar'),
            ('Con ruta', 'https://tienda-online.com/productos/123'),
            ('Con parámetros', 'https://ejemplo.com?categoria=ropa&pagina=2'),
            ('Con puerto', 'https://ejemplo.com:8080'),
        ):
            b = self._boton(ejemplos, rotulo, lambda u=url: self._usar_ejemplo(u), compacto=True)
            b.configure(font=(Paleta.TIPOGRAFIA, 9), pady=5,
                        fg=Paleta.AZUL_TEXTO, activeforeground=Paleta.AZUL_TEXTO)
            b.pack(side='left', padx=(0, 5))

        columnas = tk.Frame(contenedor, bg=Paleta.FONDO)
        columnas.pack(fill='both', expand=True)
        izquierda = tk.Frame(columnas, bg=Paleta.FONDO)
        izquierda.pack(side='left', fill='both', expand=True, padx=(0, 15))
        derecha = tk.Frame(columnas, bg=Paleta.FONDO, width=284)
        derecha.pack(side='right', fill='y')

        resultado_card, caja_resultado = self._tarjeta(izquierda, 23)
        resultado_card.pack(fill='x', pady=(0, 14))
        self.estado = tk.Frame(caja_resultado, bg=Paleta.AMARILLO_CLARO)
        self.estado.pack(fill='x')
        mensaje = tk.Frame(self.estado, bg=Paleta.AMARILLO_CLARO)
        mensaje.pack(fill='x', padx=17, pady=15)
        self.icono_estado = self._texto(mensaje, '○', 21, Paleta.AMARILLO,
                                        negrita=True, bg=Paleta.AMARILLO_CLARO)
        self.icono_estado.pack(side='left', padx=(0, 13))
        estado_texto = tk.Frame(mensaje, bg=Paleta.AMARILLO_CLARO)
        estado_texto.pack(side='left', fill='x', expand=True)
        self.titulo_estado = self._texto(estado_texto, 'Sin verificar', 15,
                                        Paleta.TEXTO, negrita=True,
                                        bg=Paleta.AMARILLO_CLARO)
        self.titulo_estado.pack(anchor='w')
        self.detalle_estado = self._texto(estado_texto, 'Ingresá una URL para analizar su formato.',
                                         9, Paleta.SECUNDARIO, bg=Paleta.AMARILLO_CLARO,
                                         wraplength=455, justify='left')
        self.detalle_estado.pack(anchor='w', pady=(5, 0))
        fecha = tk.Frame(caja_resultado, bg=Paleta.BLANCO)
        fecha.pack(fill='x', pady=(16, 0))
        self._texto(fecha, 'ESTADO DE LA VERIFICACIÓN', 9, Paleta.SUAVE,
                    negrita=True).pack(side='left')
        self.fecha_estado = self._texto(fecha, 'Sin actividad', 9, Paleta.SUAVE)
        self.fecha_estado.pack(side='right')

        detalles_card, caja_detalles = self._tarjeta(izquierda, 22)
        detalles_card.pack(fill='both', expand=True)
        self._texto(caja_detalles, 'Detalles de la dirección', 12, negrita=True).pack(anchor='w')
        self._texto(caja_detalles, 'Componentes identificados en la URL.', 9,
                    Paleta.SECUNDARIO).pack(anchor='w', pady=(4, 16))
        matriz = tk.Frame(caja_detalles, bg=Paleta.BLANCO)
        matriz.pack(fill='x')
        self.campos = {}
        datos = [('Protocolo', 'protocolo'), ('Dominio', 'dominio'),
                 ('Puerto', 'puerto'), ('Ruta', 'ruta'),
                 ('Parámetros', 'consulta')]
        for i, (titulo, clave) in enumerate(datos):
            grupo, etiqueta = self._etiqueta_dato(matriz, titulo)
            grupo.grid(row=i // 2, column=i % 2, sticky='new', padx=(0, 15), pady=(0, 15))
            self.campos[clave] = etiqueta
        matriz.grid_columnconfigure(0, weight=1)
        matriz.grid_columnconfigure(1, weight=1)

        info_card, caja_info = self._tarjeta(derecha, 21)
        info_card.pack(fill='x', pady=(0, 14))
        self._texto(caja_info, 'Qué se verifica', 12, negrita=True).pack(anchor='w')
        for detalle in (
            'Estructura del dominio',
            'Protocolo HTTP o HTTPS',
            'Rutas y sus segmentos',
            'Parámetros de consulta',
            'Puerto entre 0 y 65535',
        ):
            renglon = tk.Frame(caja_info, bg=Paleta.BLANCO)
            renglon.pack(fill='x', pady=(14, 0))
            self._texto(renglon, '✓', 11, Paleta.VERDE,
                        negrita=True).pack(side='left', padx=(0, 9))
            self._texto(renglon, detalle, 9, Paleta.TEXTO,
                        wraplength=185).pack(side='left')

        alcance_card, caja_alcance = self._tarjeta(derecha, 21)
        alcance_card.pack(fill='x', pady=(0, 14))
        self._texto(caja_alcance, 'Importante', 12, negrita=True).pack(anchor='w')
        self._texto(caja_alcance,
                    'La verificación es sintáctica: no consulta sitios web, '
                    'no comprueba que el dominio exista ni determina si es seguro.',
                    9, Paleta.SECUNDARIO, wraplength=230,
                    justify='left').pack(anchor='w', pady=(10, 0))
        self._texto(caja_alcance,
                    'Se admite un subconjunto de formatos de URL. Algunas direcciones '
                    'válidas en la web pueden quedar fuera de ese alcance.',
                    9, Paleta.SECUNDARIO, wraplength=230,
                    justify='left').pack(anchor='w', pady=(10, 0))

        rec_card, caja_rec = self._tarjeta(derecha, 19)
        rec_card.pack(fill='both', expand=True)
        self._texto(caja_rec, 'Verificaciones recientes', 12,
                    negrita=True).pack(anchor='w')
        self._texto(caja_rec, 'Solo durante esta sesión', 9,
                    Paleta.SUAVE).pack(anchor='w', pady=(3, 10))
        self.lista_recientes = tk.Frame(caja_rec, bg=Paleta.BLANCO)
        self.lista_recientes.pack(fill='x')
        self._refrescar_historial()

        pie = tk.Frame(contenedor, bg=Paleta.FONDO)
        pie.pack(fill='x', pady=(19, 1))
        self._texto(pie, 'Validación local de formato · Sin solicitudes de red',
                    9, Paleta.SUAVE).pack(side='left')
        self._texto(pie, 'Enter para validar', 9, Paleta.SUAVE).pack(side='right')

    def _rueda(self, evento):
        self.canvas_pagina.yview_scroll(int(-evento.delta / 120), 'units')

    def _cambiar_estado(self, nombre, detalle, clase, fecha):
        colores = {
            'ok': (Paleta.VERDE_CLARO, Paleta.VERDE, '✓'),
            'error': (Paleta.ROJO_CLARO, Paleta.ROJO, '×'),
            'pendiente': (Paleta.AMARILLO_CLARO, Paleta.AMARILLO, '○'),
        }
        fondo, tinta, simbolo = colores[clase]
        self.estado.configure(bg=fondo)
        interior = self.icono_estado.master
        interior.configure(bg=fondo)
        self.titulo_estado.master.configure(bg=fondo)
        self.icono_estado.configure(text=simbolo, fg=tinta, bg=fondo)
        self.titulo_estado.configure(text=nombre, bg=fondo)
        self.detalle_estado.configure(text=detalle, bg=fondo)
        self.fecha_estado.configure(text=fecha)

    def _marcar_pendiente(self, *_args):
        if self.estado_actual is not None:
            self.estado_actual = None
            self._cambiar_estado('Sin verificar',
                                 'La dirección cambió. Volvé a validarla para actualizar el resultado.',
                                 'pendiente', 'Pendiente')
            for widget in self.campos.values():
                widget.configure(text='—')

    def _usar_ejemplo(self, url):
        self.valor.set(url)
        self.validar()

    def validar(self):
        texto = self.valor.get().strip()
        resultado = evaluar_cadena(nfa_url, texto)
        self.estado_actual = resultado
        hora = datetime.now().strftime('%H:%M')

        if not texto:
            self._cambiar_estado('Ingresá una URL',
                                 'Escribí una dirección web para comenzar.',
                                 'pendiente', hora)
            for widget in self.campos.values():
                widget.configure(text='—')
            return

        if resultado['aceptada']:
            self._cambiar_estado('Formato válido',
                                 'La dirección cumple con el formato admitido.',
                                 'ok', hora)
            partes = self._descomponer(resultado['cadena'])
            for clave, widget in self.campos.items():
                widget.configure(text=partes[clave])
        else:
            if 'puerto' in resultado['mensaje'].lower() and '65535' in resultado['mensaje']:
                explicacion = 'El número de puerto debe estar entre 0 y 65535.'
            elif 'posición' in resultado['mensaje']:
                explicacion = resultado['mensaje'].replace('Sin transiciones posibles en ',
                                                             'Revisá el formato cerca de ')
            else:
                explicacion = ('La dirección no coincide con el formato admitido. '
                               'Revisá el dominio y los separadores.')
            self._cambiar_estado('Formato no válido', explicacion, 'error', hora)
            for widget in self.campos.values():
                widget.configure(text='—')

        self.historial.insert(0, (texto, resultado['aceptada']))
        self.historial = self.historial[:4]
        self._refrescar_historial()

    def _descomponer(self, cadena):
        # urlsplit interpreta la parte inicial sin esquema como ruta si falta '//'.
        # Agregamos '//' solo para extraer componentes, nunca para validar.
        tiene_esquema = '://' in cadena
        parsed = urlsplit(cadena if tiene_esquema else '//' + cadena)
        host = parsed.hostname or '—'
        puerto = None
        if parsed.netloc and ':' in parsed.netloc:
            puerto = parsed.netloc.rsplit(':', 1)[-1]
        return {
            'protocolo': parsed.scheme.upper() if tiene_esquema else 'No especificado',
            'dominio': host,
            'puerto': puerto or 'No indicado',
            'ruta': parsed.path or 'Sin ruta',
            'consulta': parsed.query or 'Sin parámetros',
        }

    def _refrescar_historial(self):
        for hijo in self.lista_recientes.winfo_children():
            hijo.destroy()
        if not self.historial:
            self._texto(self.lista_recientes, 'Todavía no hay comprobaciones.',
                        9, Paleta.SUAVE, wraplength=225).pack(anchor='w', pady=(5, 0))
            return
        for i, (url, valido) in enumerate(self.historial):
            fila = tk.Frame(self.lista_recientes, bg=Paleta.BLANCO)
            fila.pack(fill='x', pady=(3, 2))
            color = Paleta.VERDE if valido else Paleta.ROJO
            self._texto(fila, '●', 9, color).pack(side='left', padx=(0, 7))
            abreviado = url if len(url) < 29 else url[:26] + '…'
            texto = self._texto(fila, abreviado, 9, Paleta.TEXTO)
            texto.pack(side='left')
            # Clic sobre el registro: recupera esa URL para volver a verificarla.
            for widget in (fila, texto):
                widget.bind('<Button-1>', lambda _e, valor=url: self._usar_ejemplo(valor))
                widget.configure(cursor='hand2')


if __name__ == '__main__':
    ventana = tk.Tk()
    ValidadorURLs(ventana)
    ventana.mainloop()
