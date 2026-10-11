"""Caché de vehículos en Redis: política de expiración y operaciones básicas.

Si Redis no responde, la API sigue funcionando consultando MongoDB. Tras un
fallo no se vuelve a intentar durante unos segundos para no frenar cada petición.
"""
import json
import logging
import os
import time
import unicodedata

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

log = logging.getLogger(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
PREFIJO = "vehiculo:"

DESCRIPCION_MAX_CACHEABLE = 20
PAUSA_TRAS_FALLO = 10  # segundos sin consultar Redis después de un error

_redis = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
    retry=Retry(NoBackoff(), 0),
)
_sin_redis_hasta = 0.0


def _largo(texto: str) -> int:
    return len(unicodedata.normalize("NFC", texto.strip()))


def _disponible() -> bool:
    return time.monotonic() >= _sin_redis_hasta


def _fallo(accion: str, exc: Exception) -> None:
    global _sin_redis_hasta
    _sin_redis_hasta = time.monotonic() + PAUSA_TRAS_FALLO
    log.warning("Redis no disponible al %s: %s", accion, exc)


def ttl_para(vehiculo: str, descripcion: str) -> int | None:
    """Segundos que debe vivir el vehículo en caché, o None si no se cachea.

    La descripción tiene prioridad: más de 20 caracteres no se almacena.
    Si no, el tiempo depende de los caracteres del identificador («vehiculo»).
    """
    if _largo(descripcion) > DESCRIPCION_MAX_CACHEABLE:
        return None
    largo = _largo(vehiculo)
    if largo <= 5:
        return 15
    if largo <= 10:
        return 20
    return 40


def clave(vehiculo: str) -> str:
    return PREFIJO + vehiculo


def leer(vehiculo: str) -> dict | None:
    """Devuelve el vehículo cacheado, o None si no está (o Redis falla)."""
    if not _disponible():
        return None
    try:
        valor = _redis.get(clave(vehiculo))
    except redis.RedisError as exc:
        _fallo("leer", exc)
        return None
    return json.loads(valor) if valor else None


def guardar(doc: dict) -> int | None:
    """Guarda el vehículo con su expiración. Devuelve el TTL aplicado o None."""
    ttl = ttl_para(doc["vehiculo"], doc["descripcion"])
    if ttl is None or not _disponible():
        return None
    try:
        _redis.set(clave(doc["vehiculo"]), json.dumps(doc, ensure_ascii=False), ex=ttl)
    except redis.RedisError as exc:
        _fallo("guardar", exc)
        return None
    return ttl


def invalidar(vehiculo: str) -> None:
    """Elimina el vehículo de la caché (tras actualizar o eliminar).

    Siempre se intenta, aunque Redis haya fallado hace poco, para no dejar datos viejos.
    """
    try:
        _redis.delete(clave(vehiculo))
    except redis.RedisError as exc:
        _fallo("invalidar", exc)


def listar() -> list[dict]:
    """Claves de vehículos vigentes en Redis con los segundos que les quedan."""
    entradas = []
    for key in _redis.scan_iter(match=PREFIJO + "*"):
        ttl = _redis.ttl(key)
        if ttl >= 0:
            entradas.append({"clave": key, "ttl_segundos": ttl})
    return entradas
