import pandas as pd
import numpy as np
import os
import random

# Crear carpeta de datos crudos
os.makedirs('01_Datos_Crudos', exist_ok=True)

# Configuración base de la simulación (24 meses: 2024-01 a 2025-12)
periodos = pd.date_range(start='2024-01-01', end='2025-12-01', freq='MS')
clientes = [
    {'ruc': '15523-2-65342 DV 45', 'nombre': 'Inversiones Pacifico S.A.', 'empleados': 14},
    {'ruc': '8-842-1324 DV 12', 'nombre': 'TechServ Panama S.A.', 'empleados': 16},
    {'ruc': '4-721-985 DV 88', 'nombre': 'Agroexport Chiriqui S.A.', 'empleados': 30}
]

# Listas para almacenar los registros crudos
lista_financiero = []
lista_nomina = []
lista_tributario = []

# Empleados fijos asignados (60 empleados en total para cumplir la escala del proyecto)
empleados_pool = []
cargo_opciones = ['Analista', 'Gerente', 'Supervisor', 'Operario', 'Coordinador']
depto_opciones = ['Finanzas', 'Operaciones', 'Tecnologia', 'Ventas', 'Logistica']
contrato_opciones = ['Indefinido', 'Temporal', 'Por Obra']

for c in clientes:
    for i in range(c['empleados']):
        empleados_pool.append({
            'RUC_Patrono': c['ruc'],
            'Cedula_Empleado': f"PE-{random.randint(10,99)}-{random.randint(100,999)}",
            'Nombre_Completo': f"Empleado_{c['nombre'][:3]}_{i+1}",
            'Cargo': random.choice(cargo_opciones),
            'Departamento': random.choice(depto_opciones),
            'Tipo_Contrato': random.choice(contrato_opciones),
            'Fecha_Ingreso': '2023-05-15'
        })

# ==========================================
# GENERACIÓN DE DATOS TEMPORALES (24 MESES)
# ==========================================
for idx_mes, mes in enumerate(periodos):
    mes_str = mes.strftime('%Y-%m-%d')
    trimestre = (mes.month - 1) // 3 + 1
    
    for c in clientes:
        # --- 1. Reglas de Negocio para FACT_FINANCIERO ---
        base_ingresos = 300000 if c['nombre'].startswith('Inversiones') else (200000 if c['nombre'].startswith('TechServ') else 350000)
        
        # Aplicar comportamientos del negocio descritos en la tesis
        if c['nombre'].startswith('Inversiones'):
            # Tendencia positiva sostenida
            ingresos = base_ingresos + (idx_mes * 5000) + random.randint(-10000, 10000)
            utilidad_neta = ingresos * random.uniform(0.08, 0.12)
            activo_corr = 120000 + (idx_mes * 4000)
            pasivo_corr = 80000 + (idx_mes * 1500)
        
        elif c['nombre'].startswith('TechServ'):
            # Pérdida operativa severa en Q3 2024 (Meses index 6, 7, 8)
            if mes.year == 2024 and trimestre == 3:
                ingresos = base_ingresos * 0.55  # Cae 45%
                utilidad_neta = -random.randint(5000, 15000) # Pérdida
            else:
                ingresos = base_ingresos + random.randint(-15000, 15000)
                utilidad_neta = ingresos * random.uniform(0.05, 0.09)
            activo_corr = 95000 + random.randint(-5000, 5000)
            pasivo_corr = 65000 + random.randint(-3000, 3000)
            
        elif c['nombre'].startswith('Agroexport'):
            # Estacionalidad fuerte en Q4 (Oct, Nov, Dic)
            if trimestre == 4:
                ingresos = base_ingresos * 1.5 + random.randint(10000, 30000)
            else:
                ingresos = base_ingresos * 0.85 + random.randint(-10000, 10000)
            
            utilidad_neta = ingresos * random.uniform(0.06, 0.10)
            # Liquidez inicial < 1.0 en los primeros 6 meses de 2024, luego se recupera
            if mes.year == 2024 and mes.month <= 6:
                activo_corr = 70000 + (idx_mes * 1000)
                pasivo_corr = activo_corr * 1.15  # Pasivo mayor que Activo (Liquidez < 1)
            else:
                activo_corr = 130000 + (idx_mes * 2000)
                pasivo_corr = 100000 + (idx_mes * 500)

        utilidad_op = utilidad_neta * 1.3
        depreciacion = ingresos * 0.02
        inventarios = activo_corr * 0.25
        deuda_total = pasivo_corr * 1.4
        patrimonio = (activo_corr * 2) - deuda_total
        
        lista_financiero.append({
            'Empresa_RUC': c['ruc'], 'Mes_Periodo': mes_str, 'Activo_Corriente': round(activo_corr, 2),
            'Pasivo_Corriente': round(pasivo_corr, 2), 'Inventarios': round(inventarios, 2),
            'Deuda_Total': round(deuda_total, 2), 'Patrimonio_Neto': round(patrimonio, 2),
            'Ingresos_Totales': round(ingresos, 2), 'Utilidad_Neta': round(utilidad_neta, 2),
            'Utilidad_Operativa': round(utilidad_op, 2), 'Depreciacion': round(depreciacion, 2)
        })
        
        # --- 2. Reglas de Negocio para FACT_NOMINA ---
        emp_del_cliente = [e for e in empleados_pool if e['RUC_Patrono'] == c['ruc']]
        for emp in emp_del_cliente:
            sal_bruto = random.uniform(800, 3500)
            ded_css = sal_bruto * 0.0975  # Seguro Social Empleado Panamá
            pat_css = sal_bruto * 0.1225  # Seguro Social Patrono
            isr_ret = sal_bruto * 0.05 if sal_bruto > 1100 else 0
            sal_neto = sal_bruto - ded_css - isr_ret
            
            lista_nomina.append({
                'RUC_Patrono': c['ruc'], 'Periodo': mes_str, 'Cedula_Empleado': emp['Cedula_Empleado'],
                'Nombre_Completo': emp['Nombre_Completo'], 'Cargo': emp['Cargo'],
                'Departamento': emp['Departamento'], 'Tipo_Contrato': emp['Tipo_Contrato'],
                'Fecha_Ingreso': emp['Fecha_Ingreso'], 'Salario_Bruto': round(sal_bruto, 2),
                'Deducciones_CSS': round(ded_css, 2), 'Patronal_CSS': round(pat_css, 2),
                'Impuesto_Renta_Retenido': round(isr_ret, 2), 'Salario_Neto': round(sal_neto, 2),
                'Estado_Empleado': 'Activo'
            })
            
        # --- 3. Reglas de Negocio para FACT_TRIBUTARIO ---
        for impuesto, tasa in [('ITBMS', 0.07), ('ISR_Juridico', 0.25), ('CSS', 0.22)]:
            debito = ingresos * tasa if impuesto != 'CSS' else (len(emp_del_cliente) * 1500 * tasa)
            credito = debito * random.uniform(0.3, 0.6) if impuesto == 'ITBMS' else 0
            pagado = debito - credito
            estado = 'PAGADO' if random.random() > 0.1 else 'VENCIDO'
            
            lista_tributario.append({
                'RUC': c['ruc'], 'Periodo': mes_str, 'Tipo_Impuesto': impuesto,
                'Monto_Debito': round(debito, 2), 'Monto_Credito': round(credito, 2),
                'Monto_Pagado': round(pagado, 2), 'Fecha_Vencimiento': (mes + pd.Timedelta(days=15)).strftime('%Y-%m-%d'),
                'Fecha_Presentacion': mes_str if estado == 'PAGADO' else None, 'Estado_Declaracion': estado
            })

# Convertir a DataFrames para manipulación e inyección de errores estructurales
df_fin = pd.DataFrame(lista_financiero)
df_nom = pd.DataFrame(lista_nomina)
df_trib = pd.DataFrame(lista_tributario)

# ==========================================
# INYECCIÓN DE ERRORES SINTÉTICOS (SECCIÓN 1.6.1)
# ==========================================
np.random.seed(42)

# 1. Valores Nulos (138 nulos en campos clave)
for _ in range(50):
    df_fin.loc[df_fin.sample(1).index, 'Utilidad_Neta'] = np.nan
for _ in range(50):
    df_nom.loc[df_nom.sample(1).index, 'Salario_Bruto'] = np.nan
for _ in range(38):
    df_trib.loc[df_trib.sample(1).index, 'Monto_Pagado'] = np.nan

# 2. Formato de fechas alterados (42 errores de formato)
formatos_raros = ['%m/%Y', '%m-%Y', '%Y/%m']
for _ in range(14):
    idx = df_fin.sample(1).index
    df_fin.loc[idx, 'Mes_Periodo'] = pd.to_datetime(df_fin.loc[idx, 'Mes_Periodo']).dt.strftime(random.choice(formatos_raros))
for _ in range(14):
    idx = df_nom.sample(1).index
    df_nom.loc[idx, 'Periodo'] = pd.to_datetime(df_nom.loc[idx, 'Periodo']).dt.strftime(random.choice(formatos_raros))
for _ in range(14):
    idx = df_trib.sample(1).index
    df_trib.loc[idx, 'Periodo'] = pd.to_datetime(df_trib.loc[idx, 'Periodo']).dt.strftime(random.choice(formatos_raros))

# 3. Registros Duplicados (24 duplicados exactos)
df_fin = pd.concat([df_fin, df_fin.sample(4)], ignore_index=True)
df_nom = pd.concat([df_nom, df_nom.sample(15)], ignore_index=True)
df_trib = pd.concat([df_trib, df_trib.sample(5)], ignore_index=True)

# Guardar los archivos de datos crudos institucionales
df_fin.to_excel('01_Datos_Crudos/contabilidad_erp.xlsx', index=False)
df_nom.to_csv('01_Datos_Crudos/sipe_nominas.csv', index=False)
df_trib.to_csv('01_Datos_Crudos/dgi_impuestos.csv', index=False)

# Validación de escala final
total_filas = len(df_fin) + len(df_nom) + len(df_trib)
print(f"--- PASO 1 COMPLETADO CON ÉXITO ---")
print(f"Archivos guardados en la carpeta '01_Datos_Crudos'.")
print(f"Total de registros generados en la simulación: {total_filas} filas.")