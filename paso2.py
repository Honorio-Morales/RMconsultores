import pandas as pd
import numpy as np
import os

# Crear carpeta de destino para el Data Warehouse estructurado
os.makedirs('02_Modelo_Dimensional', exist_ok=True)

print("🚀 INICIANDO PIPELINE ETL: DATA-DRIVEN CFO...")

# ==========================================
# EXTRAER (E): Lectura de Fuentes Heterogéneas
# ==========================================
df_fin_raw = pd.read_excel('01_Datos_Crudos/contabilidad_erp.xlsx')
df_nom_raw = pd.read_csv('01_Datos_Crudos/sipe_nominas.csv')
df_trib_raw = pd.read_csv('01_Datos_Crudos/dgi_impuestos.csv')

log_errores = {"Nulos Eliminados": 0, "Fechas Corregidas": 0, "Duplicados Eliminados": 0}

# ==========================================
# TRANSFORMAR (T) - FASE 1: Limpieza de Calidad de Datos
# ==========================================

# --- 1. Corrección de Formatos de Fechas (Estandarización ISO) ---
def limpiar_fecha(df, columna):
    conteo_antes = df[columna].astype(str).str.contains(r'[^0-9-]').sum()
    # Forzar conversión flexible usando pandas.to_datetime (Corregido sin caracteres extraños)
    df[columna] = pd.to_datetime(df[columna], errors='coerce')
    # Convertir al formato estándar YYYY-MM-DD
    df[columna] = pd.to_datetime(df[columna]).dt.strftime('%Y-%m-%d')
    return conteo_antes

log_errores["Fechas Corregidas"] += limpiar_fecha(df_fin_raw, 'Mes_Periodo')
log_errores["Fechas Corregidas"] += limpiar_fecha(df_nom_raw, 'Periodo')
log_errores["Fechas Corregidas"] += limpiar_fecha(df_trib_raw, 'Periodo')

# --- 2. Eliminación de Registros Duplicados Exactos ---
filas_antes_fin = len(df_fin_raw)
df_fin_raw = df_fin_raw.drop_duplicates()
log_errores["Duplicados Eliminados"] += (filas_antes_fin - len(df_fin_raw))

filas_antes_nom = len(df_nom_raw)
df_nom_raw = df_nom_raw.drop_duplicates()
log_errores["Duplicados Eliminados"] += (filas_antes_nom - len(df_nom_raw))

filas_antes_trib = len(df_trib_raw)
df_trib_raw = df_trib_raw.drop_duplicates()
log_errores["Duplicados Eliminados"] += (filas_antes_trib - len(df_trib_raw))

# --- 3. Filtrado e Infección de Valores Nulos en Campos Críticos ---
filas_antes_fin = len(df_fin_raw)
df_fin_raw = df_fin_raw.dropna(subset=['Utilidad_Neta'])
log_errores["Nulos Eliminados"] += (filas_antes_fin - len(df_fin_raw))

filas_antes_nom = len(df_nom_raw)
df_nom_raw = df_nom_raw.dropna(subset=['Salario_Bruto'])
log_errores["Nulos Eliminados"] += (filas_antes_nom - len(df_nom_raw))

filas_antes_trib = len(df_trib_raw)
df_trib_raw = df_trib_raw.dropna(subset=['Monto_Pagado'])
log_errores["Nulos Eliminados"] += (filas_antes_trib - len(df_trib_raw))


# ==========================================
# TRANSFORMAR (T) - FASE 2: Modelado Dimensional (Star Schema)
# ==========================================

# --- DIMENSIÓN 1: DIM_CLIENTE ---
clientes_data = [
    {'cliente_id': '15523-2-65342 DV 45', 'razon_social': 'Inversiones Pacifico S.A.', 'sector': 'Comercio', 'pais': 'Panamá', 'fecha_inicio_servicio': '2024-01-01', 'activo': True},
    {'cliente_id': '8-842-1324 DV 12', 'razon_social': 'TechServ Panama S.A.', 'sector': 'Servicios TI', 'pais': 'Panamá', 'fecha_inicio_servicio': '2024-01-01', 'activo': True},
    {'cliente_id': '4-721-985 DV 88', 'razon_social': 'Agroexport Chiriqui S.A.', 'sector': 'Agroindustrial', 'pais': 'Panamá', 'fecha_inicio_servicio': '2024-01-01', 'activo': True}
]
dim_cliente = pd.DataFrame(clientes_data)
dim_cliente.insert(0, 'cliente_sk', range(1, len(dim_cliente) + 1))

# --- DIMENSIÓN 2: DIM_TIEMPO ---
# Generar una tabla de tiempo robusta desde 2024 a 2025 para Power BI
fechas_rango = pd.date_range(start='2024-01-01', end='2025-12-31', freq='D')
dim_tiempo = pd.DataFrame({'fecha': fechas_rango})
dim_tiempo['tiempo_sk'] = dim_tiempo['fecha'].dt.strftime('%Y%m%d').astype(int)
dim_tiempo['anio'] = dim_tiempo['fecha'].dt.year
dim_tiempo['trimestre'] = dim_tiempo['fecha'].dt.quarter
dim_tiempo['mes'] = dim_tiempo['fecha'].dt.month
dim_tiempo['nombre_mes'] = dim_tiempo['fecha'].dt.strftime('%B')
dim_tiempo['semana_iso'] = dim_tiempo['fecha'].dt.isocalendar().week
dim_tiempo['es_fin_de_mes'] = dim_tiempo['fecha'].dt.is_month_end
dim_tiempo['fecha'] = dim_tiempo['fecha'].dt.strftime('%Y-%m-%d')

# --- DIMENSIÓN 3: DIM_IMPUESTO ---
impuestos_data = [
    {'codigo_impuesto': 'ITBMS', 'nombre_impuesto': 'Impuesto de Transferencia de Bienes Muebles y Servicios', 'periodicidad': 'Mensual', 'tasa_referencia': 0.0700, 'ente_recaudador': 'DGI'},
    {'codigo_impuesto': 'ISR_Juridico', 'nombre_impuesto': 'Impuesto sobre la Renta Jurídica', 'periodicidad': 'Anual', 'tasa_referencia': 0.2500, 'ente_recaudador': 'DGI'},
    {'codigo_impuesto': 'CSS', 'nombre_impuesto': 'Caja de Seguro Social (Cuota Obrero Patronal)', 'periodicidad': 'Mensual', 'tasa_referencia': 0.2200, 'ente_recaudador': 'CSS'}
]
dim_impuesto = pd.DataFrame(impuestos_data)
dim_impuesto.insert(0, 'impuesto_sk', range(1, len(dim_impuesto) + 1))

# --- DIMENSIÓN 4: DIM_EMPLEADO ---
dim_empleado_raw = df_nom_raw[['Cedula_Empleado', 'Nombre_Completo', 'Cargo', 'Departamento', 'Tipo_Contrato', 'Fecha_Ingreso', 'RUC_Patrono']].drop_duplicates(subset=['Cedula_Empleado'])
dim_empleado = dim_empleado_raw.merge(dim_cliente[['cliente_id', 'cliente_sk']], left_on='RUC_Patrono', right_on='cliente_id', how='left')
dim_empleado = dim_empleado.drop(columns=['RUC_Patrono', 'cliente_id'])
dim_empleado.rename(columns={'Cedula_Empleado': 'cedula', 'Nombre_Completo': 'nombre_completo', 'Cargo': 'cargo', 'Departamento': 'departamento', 'Tipo_Contrato': 'tipo_contrato', 'Fecha_Ingreso': 'fecha_ingreso'}, inplace=True)
dim_empleado.insert(0, 'empleado_sk', range(1, len(dim_empleado) + 1))


# ==========================================
# MAPEO Y CREACIÓN DE TABLAS DE HECHOS (FACTS)
# ==========================================

# Mapear SKs a Fact Financiero
# Mapear SKs a Fact Financiero
fact_financiero = df_fin_raw.merge(dim_cliente, left_on='Empresa_RUC', right_on='cliente_id', how='left')
# Solución: Convertir a fecha, rellenar posibles errores con un valor por defecto y luego a entero seguro
fact_financiero['fecha_join'] = pd.to_datetime(fact_financiero['Mes_Periodo'], errors='coerce').dt.strftime('%Y%m%d').fillna(0).astype(int)
fact_financiero = fact_financiero.merge(dim_tiempo, left_on='fecha_join', right_on='tiempo_sk', how='left')

fact_financiero = fact_financiero[['cliente_sk', 'tiempo_sk', 'Activo_Corriente', 'Pasivo_Corriente', 'Inventarios', 'Deuda_Total', 'Patrimonio_Neto', 'Ingresos_Totales', 'Utilidad_Neta', 'Utilidad_Operativa', 'Depreciacion']]
fact_financiero.columns = [col.lower() for col in fact_financiero.columns]
fact_financiero.insert(0, 'financiero_sk', range(1, len(fact_financiero) + 1))

# Mapear SKs a Fact Nómina
# Mapear SKs a Fact Nómina
fact_nomina = df_nom_raw.merge(dim_cliente, left_on='RUC_Patrono', right_on='cliente_id', how='left')
fact_nomina = fact_nomina.merge(dim_empleado, left_on='Cedula_Empleado', right_on='cedula', how='left', suffixes=('', '_dim'))
# Solución: Evitar nulos al convertir a clave de tiempo entera
fact_nomina['fecha_join'] = pd.to_datetime(fact_nomina['Periodo'], errors='coerce').dt.strftime('%Y%m%d').fillna(0).astype(int)
fact_nomina = fact_nomina.merge(dim_tiempo, left_on='fecha_join', right_on='tiempo_sk', how='left')

fact_nomina = fact_nomina[['cliente_sk', 'empleado_sk', 'tiempo_sk', 'Salario_Bruto', 'Deducciones_CSS', 'Patronal_CSS', 'Impuesto_Renta_Retenido', 'Salario_Neto', 'Estado_Empleado']]
fact_nomina.columns = [col.lower() for col in fact_nomina.columns]
fact_nomina.insert(0, 'nomina_sk', range(1, len(fact_nomina) + 1))

# Mapear SKs a Fact Tributario
fact_tributario = df_trib_raw.merge(dim_cliente, left_on='RUC', right_on='cliente_id', how='left')
fact_tributario = fact_tributario.merge(dim_impuesto, left_on='Tipo_Impuesto', right_on='codigo_impuesto', how='left')
# Solución: Evitar nulos al convertir a clave de tiempo entera
fact_tributario['fecha_join'] = pd.to_datetime(fact_tributario['Periodo'], errors='coerce').dt.strftime('%Y%m%d').fillna(0).astype(int)
fact_tributario = fact_tributario.merge(dim_tiempo, left_on='fecha_join', right_on='tiempo_sk', how='left')

fact_tributario = fact_tributario[['cliente_sk', 'impuesto_sk', 'tiempo_sk', 'Monto_Debito', 'Monto_Credito', 'Monto_Pagado', 'Fecha_Vencimiento', 'Fecha_Presentacion', 'Estado_Declaracion']]
fact_tributario.columns = [col.lower() for col in fact_tributario.columns]
fact_tributario.insert(0, 'tributario_sk', range(1, len(fact_tributario) + 1))


# ==========================================
# CARGA (L): Almacenamiento en Data Warehouse Limpio

from sqlalchemy import create_engine

# ==========================================
# CARGA (L): Inyección al Data Warehouse en PostgreSQL
# ==========================================

# 1. Copia de respaldo local en archivos CSV (Opcional, por seguridad)
dim_cliente.to_csv('02_Modelo_Dimensional/dim_cliente.csv', index=False)
dim_tiempo.to_csv('02_Modelo_Dimensional/dim_tiempo.csv', index=False)
dim_empleado.to_csv('02_Modelo_Dimensional/dim_empleado.csv', index=False)
dim_impuesto.to_csv('02_Modelo_Dimensional/dim_impuesto.csv', index=False)
fact_financiero.to_csv('02_Modelo_Dimensional/fact_financiero.csv', index=False)
fact_nomina.to_csv('02_Modelo_Dimensional/fact_nomina.csv', index=False)
fact_tributario.to_csv('02_Modelo_Dimensional/fact_tributario.csv', index=False)


# 2. Conexión física a PostgreSQL
# ⚠️ IMPORTANTE: Reemplaza 'tu_contraseña' por la clave que usas para entrar a pgAdmin
USUARIO = "postgres"
PASSWORD = "Iisaac578" 
SERVIDOR = "localhost"
PUERTO = "5432"
BASE_DATOS = "db_cfo_panama"

try:
    print("\n🗄️ Estableciendo conexión con el servidor PostgreSQL...")
    cadena_conexion = f"postgresql://{USUARIO}:{PASSWORD}@{SERVIDOR}:{PUERTO}/{BASE_DATOS}"
    engine = create_engine(cadena_conexion)
    
    print("🚀 Cargando dimensiones y hechos al Data Warehouse institucional...")
    
    # Inyectar DataFrames directamente a tablas en la Base de Datos
    dim_cliente.to_sql('dim_cliente', engine, if_exists='replace', index=False)
    dim_tiempo.to_sql('dim_tiempo', engine, if_exists='replace', index=False)
    dim_empleado.to_sql('dim_empleado', engine, if_exists='replace', index=False)
    dim_impuesto.to_sql('dim_impuesto', engine, if_exists='replace', index=False)
    
    fact_financiero.to_sql('fact_financiero', engine, if_exists='replace', index=False)
    fact_nomina.to_sql('fact_nomina', engine, if_exists='replace', index=False)
    fact_tributario.to_sql('fact_tributario', engine, if_exists='replace', index=False)
    
    print("💯 ¡Data Warehouse actualizado en PostgreSQL con ÉXITO total!")

except Exception as e:
    print(f"❌ Error al conectar o cargar en la base de datos: {e}")
    print("⚠️ Revisa que PostgreSQL esté corriendo y que tu contraseña sea la correcta.")


# Validación de Cuadro de Control contra Tesis Universitaria (Se mantiene igual)
print("\n=== LOG DE AUDITORÍA Y CALIDAD (ETL) ===")
print(f"✔️ Errores de nulos solucionados de forma segura: {log_errores['Nulos Eliminados']} registros.")
print(f"✔️ Formatos de fecha ambiguos unificados a ISO: {log_errores['Fechas Corregidas']} campos.")
print(f"✔️ Registros duplicados limpiados por completo: {log_errores['Duplicados Eliminados']} filas.")
print(f"💯 Total de errores de calidad resueltos: {sum(log_errores.values())} de 204 esperados.")
print("========================================")