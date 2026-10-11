"""Conexión a MongoDB: base de datos «automoviles», colección «vehiculos»."""
import os

from pymongo import ASCENDING, MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", "automoviles")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "vehiculos")

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)


def get_collection():
    """Devuelve la colección de vehículos.

    El campo «vehiculo» identifica a cada documento, por eso tiene índice único.
    """
    coleccion = _client[MONGO_DB][MONGO_COLLECTION]
    coleccion.create_index([("vehiculo", ASCENDING)], unique=True)
    return coleccion
