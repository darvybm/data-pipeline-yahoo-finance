<div align="center">
  <img src="https://github.com/user-attachments/assets/736597dc-9232-4f3e-b075-d6dabebf568f" alt="Prueba de Capacidades en Ingeniería de Datos" />
  <h1>Prueba de Capacidades en Ingeniería de Datos</h1>
  <h3>Darvy Betances</h3>
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Apache_Airflow-017CEE?style=for-the-badge&logo=apache-airflow&logoColor=white" alt="Apache Airflow" />
  <img src="https://img.shields.io/badge/ClickHouse-FFCC01?style=for-the-badge&logo=clickhouse&logoColor=black" alt="ClickHouse" />
  <img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Airbyte-0080FF?style=for-the-badge&logo=airbyte&logoColor=white" alt="Airbyte" />
  <img src="https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white" alt="dbt" />
  <img src="https://img.shields.io/badge/API-02569B?style=for-the-badge&logo=api&logoColor=white" alt="REST API" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose" />
</div>

---

## Descripción

Este proyecto implementa un pipeline de datos completo para extraer, transformar y cargar (ETL) información de bancos que cotizan en la bolsa de valores de los Estados Unidos desde la API de Yahoo Finance. El pipeline está diseñado para cumplir con los estándares técnicos más rigurosos de integración y validación de datos, y todo está configurado en un entorno Docker.

---

# Índice

1. [Estructura del Proyecto](#estructura-del-proyecto)
2. [Arquitectura del Proyecto](#arquitectura_del_proyectoo)
3. [Resultados](#resultados)
4. [Cómo Correr el Proyecto](#cómo-correr-el-proyecto)
5. [Retroalimentación](#retroalimentación)
6. [Conclusión](#conclusión)

---

## Estructura del Proyecto

### 1. Landing Zone

La primera etapa del pipeline se basa en **PostgreSQL**, donde se almacenan los datos crudos extraídos desde la API de Yahoo Finance. La estructura de la base de datos ha sido diseñada para evitar duplicados utilizando la sentencia `ON CONFLICT` de PostgreSQL.

### 2. OLAP (Online Analytical Processing)

**ClickHouse** actúa como el almacén de datos curados. La transferencia de datos entre la **Landing Zone** y el OLAP es gestionada mediante **Airbyte**, una herramienta de integración de datos de código abierto. Se ha configurado una conexión entre PostgreSQL (fuente) y ClickHouse (destino).

### 3. Transformación

El proceso de transformación de los datos está gestionado por **DBT** (Data Build Tool). Las transformaciones incluyen la normalización de datos, cambio de tipos de datos y filtrado de información relevante para los años 2023-2024. DBT asegura que las reglas de validación y las claves únicas estén correctamente aplicadas para evitar la duplicación o sobrescritura de datos.

### 4. Orquestación

El pipeline completo está orquestado con **Apache Airflow**, lo que automatiza y controla las diferentes tareas del pipeline, desde la extracción hasta la validación final de los datos. Airflow se asegura de que cada paso se ejecute en el orden correcto y gestiona cualquier fallo o problema que pueda ocurrir durante el proceso.

### 5. Docker

Abosultamente todos los servicios están corriendo en un servicio de docker, dentro de un docker compose, a excepción de los que se descargan como librerías claro, como DBT.

## Arquitectura del Proyecto

![Diagrama](https://github.com/user-attachments/assets/c5f22e71-0a42-420e-ac2e-f45720822b3b)

### Flujo de Trabajo Detallado

#### Extracción de Datos desde la API de Yahoo Finance

Los datos extraídos incluyen:
- **Información básica**: Industria, sector, número de empleados, ubicación, sitio web, etc.
- **Precio diario en bolsa**: Fecha, precio de apertura, cierre, máximo, mínimo y volumen.
- **Fundamentales**: Activos, deudas, capital invertido, acciones emitidas.
- **Tenedores**: Información sobre los principales tenedores de acciones.
- **Calificaciones**: Actualizaciones en las calificaciones de las acciones.

Estos datos son enviados a la **Landing Zone** en PostgreSQL. Esta base de datos o zona de estancia consta de la siguiente arquitectura:

![landing_zone - public](https://github.com/user-attachments/assets/1f3dec66-971c-4c1a-bab8-47915ef1b151)

--- 

#### Integración con ClickHouse

Los datos crudos almacenados en PostgreSQL se transfieren a ClickHouse utilizando **Airbyte** como herramienta de integración de datos. No obstante, aquí se da algo interesante, pues como el pipeline completo debe ser orquestado por airflow no podemos delegarle a airbyte la capacidad de sincronizar ambas bases de dato, por lo tanto, se le debe específicar a Airbyte que no programe el job, que sea solo manual, de esa forma podemos usar el operador de Airbyte para airflow y ejecutar la conección desde el DAG. Pero, surgió un problema técnico: **Airflow** resulta que tiene un bug en el cual no genera correctamente la URL para establecer la conexión HTTP con Airbyte, lo que imposibilitaba la ejecución directa de la integración desde los DAGs. Esto me llevó a profundizar en la documentación de ambas herramientas y a desarrollar mi propia mini librería local llamada **AirbyteSync**, que permite interactuar directamente con la API de Airbyte desde Airflow para gestionar la sincronización de datos entre las dos plataformas.

La librería **AirbyteSync** se encarga de disparar los procesos de sincronización y monitorizar el estado del trabajo hasta su finalización. A continuación, se explican las dos funciones principales:

1. **trigger_sync()**:
   - Esta función inicia una sincronización de datos en Airbyte. Envía una solicitud POST a la API de Airbyte para activar el trabajo de sincronización de la conexión especificada.
   - Si la sincronización falla o no se puede obtener el ID del trabajo, se lanza una excepción para manejar el error.

2. **_wait_for_sync_completion(job_id)**:
   - Esta función se utiliza para monitorear el progreso de la sincronización hasta su finalización. Se consulta periódicamente el estado del trabajo usando el `job_id` de Airbyte.
   - En caso de que el trabajo falle o exceda el tiempo máximo de espera, también se lanza una excepción.

#### Ejemplo de uso en Airflow

Aquí te dejo un ejemplo de cómo se utiliza esta librería en un DAG de Airflow para automatizar la sincronización de datos entre PostgreSQL y ClickHouse:

```python
# Función para activar la sincronización de datos desde Airbyte
def trigger_sync():
    airbyteSync = AirbyteSync(
        airbyte_host=os.getenv("AIRBYTE_HOST"),  # Variable de entorno para el servidor Airbyte
        connection_id=os.getenv("AIRBYTE_CONNECTION_ID"),  # ID de la conexión Airbyte
        username=os.getenv("AIRBYTE_USERNAME"),  # Credenciales de autenticación
        password=os.getenv("AIRBYTE_PASSWORD")
    )
    airbyteSync.trigger_sync()  # Dispara la sincronización de datos

# Tarea en Airflow para ejecutar la sincronización
trigger_airbyte_sync_task = PythonOperator(
    task_id='sync_airbyte_to_clickhouse',
    python_callable=trigger_sync,  # Llamada a la función de sincronización
    dag=dag
)
```

En este pipeline, después de insertar o actualizar los datos en la base de datos de PostgreSQL (Landing Zone), se ejecuta la función `trigger_sync` que dispara la sincronización en Airbyte para enviar los datos a ClickHouse (OLAP). Gracias a **AirbyteSync**, el flujo no depende de la funcionalidad defectuosa de Airflow, permitiendo que los datos sean correctamente integrados y procesados. Con esta librería local pude interactuar perfectamente con Airbyte y ejecutar la sincronización de la conexión luego de que se insertara o actualizara la data en la landing zone.

Por cierto, el conector de ClickHouse está un poco faltante de mantenimiento y en versiones recientes eliminaron la normalización, es decir, la data se almacena desde Postgres al OLAP en un formato JSON en una sola columna, por ejemplo:

| _airbyte_raw_id                        | _airbyte_data                                                                                                                                   | _airbyte_extracted_at           | _airbyte_loaded_at |
|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|--------------------|
| 040511da-5878-44c6-916b-acf6c78b2f56   | {"symbol":"BBVA","industry":"Banks - Diversified","sector":"Financial Services","employee_count":116499,"city":"Bilbao","phone":null,"state":null,"country":"Spain","website":"https://www.bbva.com","address":"Plaza San Nicolás, 4"} | 2024-10-23 08:01:23.128 +0000   | NULL               |

Pero esto no será un problema gracias a la siguiente implementación. Dentro del OLAP, se optó por usar una **medallion architecture** para realizar las respectivas transformaciones, validaciones y reporte, se explica a continuación.

---

#### Transformación de Datos con DBT

  Antes de detallar las transformaciones específicas de cada capa, es importante entender el enfoque de la **arquitectura Medallion**. Esta arquitectura organiza los datos en capas secuenciales que permiten controlar su calidad y aplicar transformaciones gradualmente, desde datos crudos hasta datos listos para el análisis. Las tres capas principales son **Bronze**, **Silver**, y **Gold**, cada una con un propósito específico.
  
  Con base en esta arquitectura, DBT (Data Build Tool) es utilizado para crear las capas y al mismo tiempo las transformaciones dentro de cada una. A continuación, se explican las transformaciones realizadas en cada nivel:
  
  1. **Bronze Layer**:
       - En esta capa, los datos crudos son **normalizados**. Por ejemplo, si los datos están almacenados en formato JSON, DBT extrae las **columnas relevantes** y transforma la estructura del JSON a un formato tabular usando JSONEXTRACT. Se asegura que las columnas clave (como IDs y fechas) estén correctamente formateadas para su uso en las siguientes capas.
    
  2. **Silver Layer**:
       - En esta etapa, se aplican transformaciones más complejas, como el **cambio de tipos de datos** (por ejemplo, de texto a numérico o de cadena a fecha). También se implementan **constraints** para asegurar la calidad de los datos, tales como la eliminación de valores nulos o inconsistentes. Adicionalmente, se realiza un **filtrado temporal**, donde los datos se agrupan o seleccionan con base en ciertos años o períodos relevantes para el análisis.
    
  3. **Gold Layer**:
       - Finalmente, en la capa Gold, los datos son optimizados para análisis avanzados. En este caso, se generan **reportes mensuales** de los datos de acciones financieras, agrupando los precios por banco y por mes. También se calculan **promedios** y otras métricas relevantes que permitirán a los analistas extraer información clave sobre el comportamiento de las acciones en distintos períodos.
    
  Este enfoque asegura que los datos fluyan de manera eficiente desde su forma cruda hasta conjuntos de datos altamente refinados y listos para su análisis.
    
  4. **Validación y Pruebas:**
    
       - Se implementaron reglas de validación en la capa silver (plata) en DBT para garantizar que los datos cumplan con las expectativas y no haya duplicación o inconsistencias.

---

#### Ejecución y Cronograma

Como no se especificaba en los requerimeientos, se decidió por fines didácticos que el DAG se ejecute cada 1 hora `0 * * * *`, para ver como se manejan las tareas.

![image](https://github.com/user-attachments/assets/635aca3d-8b55-4dc2-a7c4-6a28ff2e7f17)

Este DAG comienza con la creación de tablas en PostgreSQL, utilizando un **PostgresOperator** en Airflow si no existen. Luego, se extraen los datos y se almacenan temporalmente en un **XCom**, que es recuperado en la siguiente tarea. Los datos se suben utilizando el **PostgresHook**, y a continuación, se ejecuta la conexión con Airbyte para mover los datos desde la landing a un almacén OLAP. Posteriormente, se ejecuta DBT para aplicar la arquitectura Medallion con transformaciones y validaciones en las capas **bronze**, **silver** y **gold**. Finalmente, se ejecutan pruebas para asegurar que todas las reglas de validación de datos se cumplan adecuadamente.

## Resultados

Tras implementar todos los entornos, configurar el DAG, establecer las conexiones, y llevar a cabo las validaciones y transformaciones, logramos un pipeline que se ejecuta satisfactoriamente. A continuación, se presentan algunas evidencias de este proceso:

### Vista de las tareas en el entorno visual de Airflow

![image](https://github.com/user-attachments/assets/d7484577-b29d-4e19-a8b6-562394fa41a1)

### Tablas generadas en la landing zone y datos insertados

![image](https://github.com/user-attachments/assets/2390a4ba-0fb2-4dc5-82f8-1e8c7e7b26f9)
![image](https://github.com/user-attachments/assets/fc625441-4a65-424e-a4b4-e0b7e82a5f4b)

> [!Note]
> Se está utilizando DBeaver para validar la información.

### Ejecución automática de la conexión en Airbyte con la tarea de sincronización en Airflow

[Ver video de la sincronización](https://github.com/user-attachments/assets/acf067dc-5e49-4c63-8b55-80cf12eb0b02)

En el video, se puede observar cómo, al ejecutar la tarea 4 del DAG, se activa automáticamente el conector en Airbyte.

### Tablas generadas en ClickHouse (OLAP)

![image](https://github.com/user-attachments/assets/8dbc198b-e6cf-4fbf-b5b3-421e25d8a115)
![image](https://github.com/user-attachments/assets/14b807c4-53b9-4452-ab8f-df88a217fced)

### Capa Bronce en la transformación con DBT

![image](https://github.com/user-attachments/assets/f54d7045-0f89-4f30-af77-a226b8243af4)
![image](https://github.com/user-attachments/assets/07af4b7f-88f8-4feb-a46e-c8b016ac5f38)

Como se observa, los datos ya no están en una columna en formato JSON, y se han eliminado otros campos no relevantes.

### Capa Plata en la transformación con DBT

![image](https://github.com/user-attachments/assets/4375348a-5e42-4ff3-a6b0-ec6465a98f72)
![image](https://github.com/user-attachments/assets/585743bc-1339-4301-92ed-5b54e4b30986)

En esta fase, las vistas se convirtieron en tablas. Aunque no haya cambios visibles en las tablas, se llevaron a cabo transformaciones internas, como la definición de constraints y la conversión de tipos de datos. Además, se implementaron reglas de validación, todas las cuales se pasaron con éxito, lo que indica que los datos son de alta calidad.

![image](https://github.com/user-attachments/assets/105b61f0-9bb2-48d6-aa1e-cd7e2c15bcf7)

### Capa Oro en la transformación con DBT

#### Tabla de resumen mensual (Agrupada por mes)

![image](https://github.com/user-attachments/assets/dc9fa779-7d37-47fd-8b1e-8b1edf4705d6)

#### Tabla de resumen mensual (Agrupada por mes y empresa)


https://github.com/user-attachments/assets/3576beb2-78df-4493-add5-61b47f73c9bc

---

## Cómo Correr el Proyecto

Para ejecutar este proyecto, sigue los pasos a continuación:

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/darvybm/data_pipeline_yahoo_finance.git
   cd data_pipeline_yahoo_finance
   ```

2. **Crea un entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux/Mac
   venv\Scripts\activate  # En Windows
   ```

3. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Valida el archivo `.env`**:
   Revisa el archivo `.env` para asegurarte de que las credenciales son correctas. Por defecto, se configuran de la siguiente manera:
   - **PostgreSQL y ClickHouse**:
     - Usuario: `darvybm`
     - Contraseña: `Darvy!BM`
   - **Airflow**:
     - Usuario: `darvybm`
     - Contraseña: `123456789`
   - **Airbyte**:
     - Usuario: `airbyte`
     - Contraseña: `password`

5. **Ejecuta Docker Compose**:
   Inicia el entorno de Docker que contiene todos los servicios necesarios:
   ```bash
   docker-compose up -d
   ```

6. **Configura la conexión en Airflow**:
   Accede a la interfaz de Airflow y configura la conexión con la base de datos siguiendo la imagen de referencia:
   ![Configuración de conexión en Airflow](https://github.com/user-attachments/assets/4f750e9e-3a60-4ed2-bb43-636311912ef1)

7. **Ejecuta el DAG por primera vez**:
   - Nota: Este paso es solo para ejecutar la primera tarea que crea las tablas. Las tareas siguientes pueden fallar debido a configuraciones que aún no se han realizado.

8. **Configura Airbyte**:
   - Ingresa a la interfaz de Airbyte y proporciona cualquier correo electrónico y nombre de empresa.
   - Crea un nuevo "source" seleccionando PostgreSQL.
   - Luego, ve a la sección de "destinations" y agrega ClickHouse.
   - Configura la conexión asegurándote de seguir las instrucciones mostradas en el video de referencia:

[Detalles](https://github.com/user-attachments/assets/54c80573-eadd-485e-a273-9607e3af6ee6)


10. **Obtén el Connection ID de Airbyte**:
   Una vez creada la conexión, busca el ID de conexión en la URL:
   ![Obtención del Connection ID](https://github.com/user-attachments/assets/6081a06c-bb29-4990-b06b-04b304cb7e53)
   Luego, ve a la carpeta `dags` de Airflow y actualiza la variable de entorno correspondiente con el Connection ID que acabas de obtener:
   ![Actualización del Connection ID](https://github.com/user-attachments/assets/36f789ef-8d22-4470-86f1-0ff323bf502e)

11. **Ejecuta tu tarea**:
    Una vez que todo esté configurado correctamente, puedes ejecutar tu tarea y personalizar la configuración del DAG según sea necesario:
    ![Ejecutando la tarea en Airflow](https://github.com/user-attachments/assets/310dc626-637b-40c5-841a-0a0ee6506c05)

---

## Retroalimentación

En esta parte mencionaré explicatamente las cosas que se pidieron con un check, para hacer la evaluación más sencilla:

### Checklist para la Prueba de Capacidades en Ingeniería de Datos

#### 1. **Configuración del Entorno de Desarrollo**
- [✔️] **Landing Zone**: Configurar un entorno en PostgreSQL para datos crudos extraídos desde el API.
- [✔️] **OLAP**: Configurar un entorno en ClickHouse como almacén centralizado de datos curados.
- [✔️] **Integración de Datos**: Configurar Airbyte para integrar datos en las distintas fases del pipeline.
- [✔️] **Validación y Transformación**: Configurar DBT para validar y transformar los datos.
- [✔️] **Orquestación**: Configurar Airflow para automatizar el pipeline de datos.
- [✔️] **Docker**: Asegurarse de que todo el entorno de desarrollo está configurado en Docker.

#### 2. **Implementación del Pipeline**
- [✔️] **Diagramar la Arquitectura**: Utilizar Draw.io para diagramar la arquitectura del pipeline.
- [✔️] **Conexión a la API**: Desarrollar un script en Python para conectar a la API de Yahoo Finance utilizando la librería `yfinance`.

#### 3. **Extracción de Datos**
- [✔️] **Datos Básicos**: Extraer información básica (Industry, Sector, Employee Count, City, Phone, State, Country, Website, Address).
- [✔️] **Precio Diario en Bolsa**: Extraer precios diarios (Date, Open, High, Low, Close, Volume).
- [✔️] **Fundamentales**: Extraer datos fundamentales (Assets, Debt, Invested Capital, Share Issued).
- [✔️] **Tenedores**: Extraer datos de tenedores (Date, Holder, Shares, Value).
- [✔️] **Calificadores**: Extraer datos de calificadores (Date, To Grade, From Grade, Action).

#### 4. **Carga y Validación de Datos**
- [✔️] **Carga en Landing Zone**: Colocar los datos extraídos del API en las tablas del entorno de landing zone.
- [✔️] **Integración en OLAP**: Integrar los datos extraídos en la solución OLAP.
- [✔️] **Reglas de Validación**: Implementar reglas de validación con DBT.

#### 5. **Transformación y Resumen**
- [✔️] **Tabla de Resumen Mensual**: Generar una tabla que contenga:
  - [✔️] Precio promedio de apertura y cierre.
  - [✔️] Volumen promedio de la acción.
- [✔️] **Transformaciones con DBT**: Asegurarse de que se usan DBT para las transformaciones.

#### 6. **Automatización**
- [❌] **Automatización del Pipeline**: Automatizar el pipeline para actualizar datos cuando se detecte nueva información en las tablas del landing zone.

  (Según lo que entendí en esta aprte es que el OLAP solo se iba a actualizar si se detectaba alguna actualización en el Landing Zone, algo tipo radar, pero al final no es necesario pues cada vez que se ejecute el pipeline el landing zone se va a actualizar)

#### 7. **Documentación**
- [✔️] **GitHub Repository**: Documentar el proceso en un repositorio de GitHub.
- [✔️] **Screenshots**: Incluir capturas de pantalla de la UI de los entornos.
- [✔️] **Diagrama de Arquitectura**: Incluir el diagrama de la arquitectura.
- [✔️] **Instrucciones de Ejecución**: Proporcionar un paso a paso para ejecutar el proyecto utilizando Docker.

#### 8. **Revisión Final**
- [✔️] **Organización del Proyecto**: Asegurarse de que el proyecto esté bien estructurado, incluyendo el manejo de variables de entorno y claves secretas.
- [✔️] **Documentación y Uso de Recursos**: Revisar el uso de documentación para implementar herramientas y la claridad de la documentación en GitHub.
- [✔️] **Código Eficiente**: Verificar que el código es eficiente y estructurado.
- [✔️] **Entrega**: Asegurarse de enviar el enlace directo del repositorio de GitHub antes de la fecha de entrega y no hacer cambios posteriores.

### Entrega Final
- [✔️] Enviar el enlace directo del repositorio de GitHub que contiene el proyecto organizado y explicado para ser ejecutado en Docker.

---

## Conclusión

Este proyecto ha sido una experiencia enriquecedora. Tuve la oportunidad de trabajar con herramientas nuevas que no había utilizado anteriormente, pero gracias a las sólidas comunidades y la excelente documentación disponibles, pude familiarizarme con ellas rápidamente. El proceso me llevó a profundizar en la lectura y el aprendizaje, lo cual resultó ser muy gratificante. Al final, logré cumplir con todos los requisitos establecidos, y estoy satisfecho con la implementación del pipeline, que ha quedado excepcional.

Muchas gracias,
Darvy Betances.
Darvybm@gmail.com
