# Data-Driven CFO: RM Consultores (Panamá)

Este proyecto implementa una arquitectura completa de Business Intelligence de extremo a extremo para el monitoreo financiero, laboral y tributario de clientes corporativos en Panamá.

Arquitectura del Proyecto

1. **Extracción y Limpieza (ETL):** Script en `Python` para corregir la calidad de datos crudos.
2. **Data Warehouse:** Almacenamiento relacional estructurado en un modelo en estrella dentro de `PostgreSQL`.
3. **Visualización:** Dashboard ejecutivo interactivo desarrollado en `Power BI`.

## Cómo Replicar el Proyecto

1. Clona este repositorio.
2. Crea una base de datos en PostgreSQL llamada `db\_cfo\_panama`.
3. Abre pgAdmin, usa la herramienta *Query Tool* en tu nueva base de datos, copia el contenido de `/03\_Database/backup\_db\_cfo.sql` y ejecútalo para restaurar todas las tablas con datos reales.
4. Abre el archivo de Power BI en `/04\_Dashboard/` y actualiza las credenciales de tu base de datos local para interactuar con los visuales en vivo.

