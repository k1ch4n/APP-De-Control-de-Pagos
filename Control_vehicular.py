# -*- coding: utf-8 -*-
"""
Nombre del archivo: Control_vehicular.py
Autor: Cristian Marko Llallihuaman C.
Fecha de creación: 20 de Diciembre de 2023
Fecha de versión final: 20 de Diciembre de 2024
Descripción: Este script realiza el control de pagos y registro vehicular para una residencial.
Contacto: https://www.linkedin.com/in/xtn/
Derechos de autor © 2024 - https://github.com/k1ch4n - Todos los derechos reservados.
"""

from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import numpy as np
from datetime import datetime
import time
import re 

app = Flask(__name__)

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verificar_placa', methods=['POST'])
def verificar_placa():
    # Obtener la placa del formulario y convertirla a mayúsculas
    placa = request.form['placa'].upper()

    # Validar la placa según el patrón
    if not re.match(r'^[A-Z0-9]{3}-[A-Z0-9]{3}$', placa):
        return render_template('index.html', mensaje='Por favor, ingrese una placa válida.', color='red')


    # Leer los archivos Excel
    base_residentes = pd.read_excel('Base_vehiculos_Residentes.xlsx', sheet_name='Base_2024')
    control_pagos = pd.read_excel('Control_Pagos_2024.xlsx', sheet_name='Base_2024')

    # Convertir la columna 'PLACA' a mayúsculas para la comparación
    base_residentes['PLACA'] = base_residentes['PLACA'].str.upper()

    # Buscar información asociada a la placa en el primer archivo
    info_vehiculo = base_residentes[base_residentes['PLACA'] == placa]

    if not info_vehiculo.empty:
        # Obtener información relevante
        block = int(info_vehiculo['BLOCK'].values[0])
        dpto = int(info_vehiculo['DPTO'].values[0])

        # Manejar la posible ausencia de columnas
        propietario_vehiculo = info_vehiculo['NOMBRE Y APELLIDOS DEL DUEÑO'].values[0] if 'NOMBRE Y APELLIDOS DEL DUEÑO' in info_vehiculo.columns else 'Información no disponible'

        # Buscar observaciones en el segundo archivo
        observaciones = control_pagos.loc[(control_pagos['BLOCK'] == block) & (control_pagos['DPTO'] == dpto), 'OBSERVACIONES'].values

        # Filtrar las observaciones que son NaN
        observaciones = [obs for obs in observaciones if pd.notna(obs)]

        # Obtener el tipo de residente
        tipo_residente = info_vehiculo['PROPIETARIO/INQUILINO'].values[0] if 'PROPIETARIO/INQUILINO' in info_vehiculo.columns and pd.notna(info_vehiculo['PROPIETARIO/INQUILINO'].values[0]) else 'Pendiente de actualizar información'

        # Código común para ambos casos
        propietario_residencia = control_pagos.loc[(control_pagos['BLOCK'] == block) & (control_pagos['DPTO'] == dpto), 'NOMBRES_APELLIDOS_PROPIETARIO'].values[0] if 'NOMBRES_APELLIDOS_PROPIETARIO' in control_pagos.columns else 'Información no disponible'
        cochera_info = get_info_cochera(info_vehiculo)

        if observaciones:
            return render_template('resultado.html', color='red', titulo='Residente con observaciones', observaciones=observaciones, propietario_residencia=propietario_residencia, block=block, dpto=dpto, propietario_vehiculo=propietario_vehiculo, placa=placa, cochera_info=cochera_info, tipo_residente=tipo_residente)
        else:
            return render_template('resultado.html', color='blue', titulo='Residente al día', propietario_residencia=propietario_residencia, block=block, dpto=dpto, propietario_vehiculo=propietario_vehiculo, placa=placa, cochera_info=cochera_info, tipo_residente=tipo_residente)
    else:
        # Placa no encontrada
        return render_template('registrar_ingreso_salida.html', placa=placa )

def get_info_cochera(info_vehiculo):
    cochera_privada = info_vehiculo['COCHERA PRIVADA'].values[0] if 'COCHERA PRIVADA' in info_vehiculo.columns and not pd.isna(info_vehiculo['COCHERA PRIVADA'].values[0]) else None
    sticker = info_vehiculo['STIKER'].values[0] if 'STIKER' in info_vehiculo.columns and not pd.isna(info_vehiculo['STIKER'].values[0]) else None

    if cochera_privada:
        return f'Cochera privada N° {cochera_privada}'
    elif sticker:
        return f'Cochera Pública con sticker N° {sticker}'
    else:
        return 'Información no disponible'

##modificado desde aca:


control_vehiculos_externos = pd.read_excel('Control_vehiculos_Externos.xlsx', sheet_name='Registro_2024')
@app.route('/registrar_ingreso_salida', methods=['GET', 'POST'])

def procesar_ingreso_salida():
    global control_vehiculos_externos  # Declarar la variable como global

    if request.method == 'POST':
        #placa = request.form['placa']
        placa = request.form['placa'].upper()
        tipo = request.form['tipo']

        # Validar que la placa no esté en blanco
        if not placa.strip():
            return render_template('registrar_ingreso_salida.html', mensaje='Por favor, ingrese una placa válida.', color='red')


        if tipo == 'ingreso':
            registrar_ingreso(placa)
            mensaje = f"Ingreso registrado para la placa {placa}."
            time.sleep(0.5)  # Añadir un retraso de 3 segundos
            return render_template('Retonrar_consulta.html', placa=placa, tipo=tipo, mensaje=mensaje)
        elif tipo == 'salida':
            registrar_salida(placa)
            mensaje = f"Salida registrada para la placa {placa}."
            time.sleep(0.5)  # Añadir un retraso de 3 segundos
            return render_template('Retonrar_consulta.html', placa=placa, tipo=tipo, mensaje=mensaje)
        else:
            mensaje = "Acción no válida."

        return {'message': mensaje}

    elif request.method == 'GET':
        placa = request.args.get('placa', '')
        tipo = request.args.get('tipo', '')

        return render_template('registrar_ingreso_salida.html', placa=placa, tipo=tipo)

def registrar_ingreso(placa):
    global control_vehiculos_externos  # Declarar la variable como global

    # Obtener la fecha y hora actual
    fecha_ingreso = datetime.now()

    try:
        # Cargar el DataFrame desde el archivo Excel
        control_vehiculos_externos = pd.read_excel('Control_vehiculos_Externos.xlsx', sheet_name='Registro_2024')
    except FileNotFoundError:
        # Si el archivo no existe, crear un DataFrame vacío
        control_vehiculos_externos = pd.DataFrame(columns=['ITEM', 'PLACA', 'FECHA_INGRESO', 'FECHA_SALIDA'])

    # Buscar si hay una entrada sin salida asociada para la placa
    entrada_sin_salida = control_vehiculos_externos[(control_vehiculos_externos['PLACA'] == placa) & (control_vehiculos_externos['FECHA_SALIDA'].isna())]

    if not entrada_sin_salida.empty:
        # Completar la entrada sin salida con el mensaje adecuado
        control_vehiculos_externos.loc[entrada_sin_salida.index, 'FECHA_SALIDA'] = f'No se registró salida en el ingreso {entrada_sin_salida["ITEM"].values[0]}'
        # Añadir un nuevo registro al DataFrame
        nuevo_registro = pd.DataFrame({
            'ITEM': [len(control_vehiculos_externos) + 1],
            'PLACA': [placa],
            'FECHA_INGRESO': [fecha_ingreso],
            'FECHA_SALIDA': [None]
        })
        control_vehiculos_externos = pd.concat([control_vehiculos_externos, nuevo_registro], ignore_index=True)
    else:
        # Añadir un nuevo registro al DataFrame
        nuevo_registro = pd.DataFrame({
            'ITEM': [len(control_vehiculos_externos) + 1],
            'PLACA': [placa],
            'FECHA_INGRESO': [fecha_ingreso],
            'FECHA_SALIDA': [None]
        })

        control_vehiculos_externos = pd.concat([control_vehiculos_externos, nuevo_registro], ignore_index=True)

    # Guardar el DataFrame actualizado en el archivo Excel
    control_vehiculos_externos.to_excel('Control_vehiculos_Externos.xlsx', sheet_name='Registro_2024', index=False)

def registrar_salida(placa):
    global control_vehiculos_externos  # Declarar la variable como global

    # Obtener la fecha y hora actual
    fecha_salida = datetime.now()

    try:
        # Cargar el DataFrame desde el archivo Excel
        control_vehiculos_externos = pd.read_excel('Control_vehiculos_Externos.xlsx', sheet_name='Registro_2024')
    except FileNotFoundError:
        # Si el archivo no existe, crear un DataFrame vacío
        control_vehiculos_externos = pd.DataFrame(columns=['ITEM', 'PLACA', 'FECHA_INGRESO', 'FECHA_SALIDA'])

    # Buscar el registro correspondiente a la placa
    registros_placa = control_vehiculos_externos[control_vehiculos_externos['PLACA'] == placa]

    if not registros_placa.empty:
        # Verificar si hay salidas no registradas
        salidas_no_registradas = registros_placa[registros_placa['FECHA_SALIDA'].isna()]

        if not salidas_no_registradas.empty:
            # Actualizar la fecha de salida en los registros no registrados
            control_vehiculos_externos.loc[salidas_no_registradas.index, 'FECHA_SALIDA'] = fecha_salida

            # Guardar el DataFrame actualizado en el archivo Excel
            control_vehiculos_externos.to_excel('Control_vehiculos_Externos.xlsx', sheet_name='Registro_2024', index=False)
            
            print(f"Salida registrada para la placa {placa}.")
        else:
            print(f"Todas las salidas para la placa {placa} ya han sido registradas.")
    else:
        # Manejar el caso cuando no se encuentra la placa
        print(f"No se encontró la placa {placa} en el registro de ingreso.")


###
#para mostrar el link y asociarlo a QR:

@app.route('/detalle_placa/<placa>', methods=['GET'])
def detalle_placa(placa):
    
    # Obtener la placa del formulario y convertirla a mayúsculas
    #placa = request.form['placa'].upper()
    placa = placa.upper()
    # Leer los archivos Excel
    base_residentes = pd.read_excel('Base_vehiculos_Residentes.xlsx', sheet_name='Base_2024')
    control_pagos = pd.read_excel('Control_Pagos_2024.xlsx', sheet_name='Base_2024')

    # Convertir la columna 'PLACA' a mayúsculas para la comparación
    base_residentes['PLACA'] = base_residentes['PLACA'].str.upper()

    # Buscar información asociada a la placa en el primer archivo
    info_vehiculo = base_residentes[base_residentes['PLACA'] == placa]

    if not info_vehiculo.empty:
        # Obtener información relevante
        block = int(info_vehiculo['BLOCK'].values[0])
        dpto = int(info_vehiculo['DPTO'].values[0])

        # Manejar la posible ausencia de columnas
        propietario_vehiculo = info_vehiculo['NOMBRE Y APELLIDOS DEL DUEÑO'].values[0] if 'NOMBRE Y APELLIDOS DEL DUEÑO' in info_vehiculo.columns else 'Información no disponible'

        # Buscar observaciones en el segundo archivo
        observaciones = control_pagos.loc[(control_pagos['BLOCK'] == block) & (control_pagos['DPTO'] == dpto), 'OBSERVACIONES'].values

        # Filtrar las observaciones que son NaN
        observaciones = [obs for obs in observaciones if pd.notna(obs)]

        # Obtener el tipo de residente
        tipo_residente = info_vehiculo['PROPIETARIO/INQUILINO'].values[0] if 'PROPIETARIO/INQUILINO' in info_vehiculo.columns and pd.notna(info_vehiculo['PROPIETARIO/INQUILINO'].values[0]) else 'Pendiente de actualizar información'

        # Código común para ambos casos
        propietario_residencia = control_pagos.loc[(control_pagos['BLOCK'] == block) & (control_pagos['DPTO'] == dpto), 'NOMBRES_APELLIDOS_PROPIETARIO'].values[0] if 'NOMBRES_APELLIDOS_PROPIETARIO' in control_pagos.columns else 'Información no disponible'
        cochera_info = get_info_cochera(info_vehiculo)

        if observaciones:
            return render_template('detalle_placa.html', color='red', titulo='Residente con observaciones', observaciones=observaciones, propietario_residencia=propietario_residencia, block=block, dpto=dpto, propietario_vehiculo=propietario_vehiculo, placa=placa, cochera_info=cochera_info, tipo_residente=tipo_residente)
        else:
            return render_template('detalle_placa.html', color='blue', titulo='Residente al día', propietario_residencia=propietario_residencia, block=block, dpto=dpto, propietario_vehiculo=propietario_vehiculo, placa=placa, cochera_info=cochera_info, tipo_residente=tipo_residente)
    else:
        # Placa no encontrada
        return render_template('index.html')

###


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
