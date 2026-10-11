# Taller: API REST de vehículos con Flask, MongoDB y Redis

CRUD sobre una colección de vehículos (MongoDB) con caché en Redis y tiempos de
expiración según las reglas del taller.

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `app.py` | API Flask: rutas CRUD y consulta con caché |
| `cache.py` | Política de expiración y operaciones con Redis |
| `db.py` | Conexión a MongoDB (`automoviles` / `vehiculos`) |
| `seed.py` | Carga los 10 vehículos de la tabla de referencia |
| `test_cache.py` | Pruebas de la política de expiración |
| `postman_collection.json` | Colección de Postman lista para importar |

## Requisitos

- Python 3.10 o superior
- MongoDB en `localhost:27017`
- Redis en `localhost:6379`, instalado en Ubuntu (WSL)

### Redis en Ubuntu (WSL)

Instalación (una sola vez), en la terminal de Ubuntu:

```bash
sudo apt update && sudo apt install -y redis-server
```

Uso: abrir una terminal de Ubuntu y dejarla abierta. El servicio arranca solo; se
comprueba con:

```bash
redis-cli ping    # responde PONG
```

> WSL apaga Ubuntu (y Redis con él) unos segundos después de cerrar la última
> terminal. Mantén abierta la terminal de Ubuntu mientras usas la API y durante el
> video. Si Redis no responde, la API sigue funcionando con MongoDB, pero sin caché.

El puerto 6379 no puede compartirse: si tienes otro Redis en Docker, detenlo antes
con `docker stop redis`.

### Alternativa: Redis en Docker

```bash
docker run -d --name redis -p 6379:6379 redis
```

Si el contenedor ya existe pero está detenido: `docker start redis`. En ese caso los
comandos `redis-cli` de más abajo se ejecutan con `docker exec -it redis redis-cli`.

## Instalación y ejecución (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python seed.py     # crea la BD «automoviles» y carga los 10 vehículos
python app.py      # API en http://localhost:5000
```

Variables de entorno opcionales: `MONGO_URI`, `MONGO_DB`, `MONGO_COLLECTION`,
`REDIS_HOST`, `REDIS_PORT`, `PORT`.

## Estructura de un documento

```json
{
  "_id": "665f...",
  "vehiculo": "Automóvil",
  "categoria": "Terrestre (motorizado)",
  "peso_toneladas": 1.5,
  "descripcion": "Vehículo común para transporte personal."
}
```

`vehiculo` es el campo que identifica al vehículo (índice único) y es el que se
usa en las URLs.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/vehiculos` | Registrar un vehículo (requiere los 4 campos) |
| GET | `/vehiculos` | Listar todos (siempre desde MongoDB) |
| GET | `/vehiculos/<vehiculo>` | Consultar uno; incluye `"fuente": "mongodb"` o `"redis"` |
| PUT | `/vehiculos/<vehiculo>` | Actualizar `categoria`, `peso_toneladas` y/o `descripcion` |
| DELETE | `/vehiculos/<vehiculo>` | Eliminar |
| GET | `/cache` | Apoyo para la demo: claves vigentes en Redis y su TTL |

Ejemplo de consulta:

```json
{
  "_id": "665f...",
  "vehiculo": "Barco",
  "categoria": "Acuático",
  "peso_toneladas": 500,
  "descripcion": "Embarcación grande usada para transporte marítimo.",
  "fuente": "mongodb"
}
```

## Reglas de caché

El tiempo de vida depende de los caracteres del campo `vehiculo`:

| Condición | Expiración |
|---|---|
| 5 caracteres o menos | 15 segundos |
| Más de 5 y hasta 10 | 20 segundos |
| Más de 10 | 40 segundos |
| `descripcion` de más de 20 caracteres | **No se cachea** (tiene prioridad) |

- Si el vehículo no está en Redis se consulta MongoDB y, si corresponde, se guarda en Redis.
- `PUT` y `DELETE` invalidan la entrada de caché del vehículo.
- Si Redis no responde, la API sigue funcionando contra MongoDB.

### Importante: los datos de la tabla no se cachean

Las 10 descripciones de la tabla de referencia tienen **más de 20 caracteres**, así
que, por la regla de prioridad, esos vehículos siempre responden con
`"fuente": "mongodb"`. Para demostrar Redis hay que registrar vehículos con
descripción corta (la colección de Postman ya incluye tres):

| Vehículo | Caracteres | Descripción | Expiración |
|---|---|---|---|
| Tren | 4 | Va sobre rieles | 15 s |
| Patineta | 8 | Tabla con ruedas | 20 s |
| Transbordador | 13 | Nave reutilizable | 40 s |

## Demostración de Redis

1. Importar `postman_collection.json` y ejecutar los pasos 03 a 09 en orden.
2. Consultar dos veces seguidas el mismo vehículo: la 1ª responde `mongodb`, la 2ª `redis`.
3. Ver las claves y los segundos restantes, en Postman (`GET /cache`) o en Redis
   (desde la terminal de Ubuntu):

   ```bash
   redis-cli
   ```

   ```
   KEYS vehiculo:*
   TTL vehiculo:Tren
   GET vehiculo:Tren
   ```

4. Esperar el tiempo de expiración y volver a consultar: la clave desaparece de
   Redis y la respuesta vuelve a ser `mongodb`.
5. Hacer un `PUT` o `DELETE` y comprobar que la clave se elimina al instante.

## Pruebas

```powershell
python -m unittest -v test_cache
```

## Publicar en GitHub

```bash
git init
git add .
git commit -m "Taller Flask + MongoDB + Redis"
git branch -M main
git remote add origin https://github.com/<usuario>/<repositorio>.git
git push -u origin main
```
