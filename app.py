"""API REST de vehículos: Flask + MongoDB + caché en Redis."""
import math
import os

import redis
from flask import Flask, jsonify, request
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError
from werkzeug.exceptions import HTTPException

import cache
from db import get_collection

app = Flask(__name__)
app.json.ensure_ascii = False  # mostrar tildes tal cual
app.json.sort_keys = False

vehiculos = get_collection()

CAMPOS = ("vehiculo", "categoria", "peso_toneladas", "descripcion")


def serializar(doc: dict) -> dict:
    return {**doc, "_id": str(doc["_id"])}


def error(mensaje: str, estado: int):
    return jsonify(error=mensaje), estado


def validar(datos, parcial: bool):
    """Devuelve (campos, mensaje_de_error). Con parcial=True no exige todos los campos."""
    if not isinstance(datos, dict):
        return None, "El cuerpo de la petición debe ser un objeto JSON"
    campos = {}
    for campo in ("vehiculo", "categoria", "descripcion"):
        if campo in datos:
            valor = datos[campo]
            if not isinstance(valor, str) or not valor.strip():
                return None, f"'{campo}' debe ser un texto no vacío"
            campos[campo] = valor.strip()
    if "peso_toneladas" in datos:
        peso = datos["peso_toneladas"]
        if (
            isinstance(peso, bool)
            or not isinstance(peso, (int, float))
            or not math.isfinite(peso)
            or peso < 0
        ):
            return None, "'peso_toneladas' debe ser un número mayor o igual a 0"
        campos["peso_toneladas"] = peso
    if not parcial:
        faltantes = [c for c in CAMPOS if c not in campos]
        if faltantes:
            return None, f"Faltan campos: {', '.join(faltantes)}"
    return campos, None


@app.get("/")
def inicio():
    return jsonify(
        servicio="API de vehículos (Flask + MongoDB + Redis)",
        endpoints=[
            "POST   /vehiculos",
            "GET    /vehiculos",
            "GET    /vehiculos/<vehiculo>",
            "PUT    /vehiculos/<vehiculo>",
            "DELETE /vehiculos/<vehiculo>",
            "GET    /cache",
        ],
    )


@app.post("/vehiculos")
def crear_vehiculo():
    campos, mensaje = validar(request.get_json(silent=True), parcial=False)
    if mensaje:
        return error(mensaje, 400)
    documento = {c: campos[c] for c in CAMPOS}
    try:
        resultado = vehiculos.insert_one(documento)
    except DuplicateKeyError:
        return error(f"Ya existe el vehículo '{documento['vehiculo']}'", 409)
    return jsonify(serializar({"_id": resultado.inserted_id, **documento})), 201


@app.get("/vehiculos")
def listar_vehiculos():
    docs = [serializar(d) for d in vehiculos.find().sort("_id")]
    return jsonify(total=len(docs), fuente="mongodb", vehiculos=docs)


@app.get("/vehiculos/<nombre>")
def obtener_vehiculo(nombre):
    doc = cache.leer(nombre)
    if doc is not None:
        return jsonify({**doc, "fuente": "redis"})

    doc = vehiculos.find_one({"vehiculo": nombre})
    if doc is None:
        return error(f"No existe el vehículo '{nombre}'", 404)
    doc = serializar(doc)
    cache.guardar(doc)
    return jsonify({**doc, "fuente": "mongodb"})


@app.put("/vehiculos/<nombre>")
def actualizar_vehiculo(nombre):
    campos, mensaje = validar(request.get_json(silent=True), parcial=True)
    if mensaje:
        return error(mensaje, 400)
    if campos.get("vehiculo", nombre) != nombre:
        return error("'vehiculo' identifica al registro y no se puede modificar", 400)
    campos.pop("vehiculo", None)
    if not campos:
        return error("Envíe al menos un campo a actualizar", 400)

    doc = vehiculos.find_one_and_update(
        {"vehiculo": nombre}, {"$set": campos}, return_document=ReturnDocument.AFTER
    )
    cache.invalidar(nombre)
    if doc is None:
        return error(f"No existe el vehículo '{nombre}'", 404)
    return jsonify(serializar(doc))


@app.delete("/vehiculos/<nombre>")
def eliminar_vehiculo(nombre):
    resultado = vehiculos.delete_one({"vehiculo": nombre})
    cache.invalidar(nombre)
    if resultado.deleted_count == 0:
        return error(f"No existe el vehículo '{nombre}'", 404)
    return jsonify(mensaje=f"Vehículo '{nombre}' eliminado")


@app.get("/cache")
def ver_cache():
    """Apoyo para la demostración: qué hay en Redis y cuánto le queda de vida."""
    claves = cache.listar()
    return jsonify(total=len(claves), claves=claves)


@app.errorhandler(HTTPException)
def error_http(exc):
    return error(exc.description, exc.code)


@app.errorhandler(PyMongoError)
def error_mongo(exc):
    return error("MongoDB no está disponible", 503)


@app.errorhandler(redis.RedisError)
def error_redis(exc):
    return error("Redis no está disponible", 503)


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", "5000")))
