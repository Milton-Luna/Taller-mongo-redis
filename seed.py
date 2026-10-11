"""Carga en MongoDB los 10 vehículos de la tabla de referencia.

Es idempotente: se puede ejecutar varias veces (restablece estos 10 registros).
"""
from db import get_collection

VEHICULOS = [
    {"vehiculo": "Automóvil", "categoria": "Terrestre (motorizado)", "peso_toneladas": 1.5,
     "descripcion": "Vehículo común para transporte personal."},
    {"vehiculo": "Motocicleta", "categoria": "Terrestre (motorizado)", "peso_toneladas": 0.2,
     "descripcion": "Vehículo de dos ruedas impulsado por motor."},
    {"vehiculo": "Camión", "categoria": "Terrestre (motorizado)", "peso_toneladas": 10,
     "descripcion": "Vehículo grande para carga pesada."},
    {"vehiculo": "Bicicleta", "categoria": "Terrestre (no motorizado)", "peso_toneladas": 0.015,
     "descripcion": "Vehículo de dos ruedas impulsado por pedales."},
    {"vehiculo": "Monopatín", "categoria": "Terrestre (no motorizado)", "peso_toneladas": 0.005,
     "descripcion": "Tabla con ruedas impulsada por el usuario."},
    {"vehiculo": "Barco", "categoria": "Acuático", "peso_toneladas": 500,
     "descripcion": "Embarcación grande usada para transporte marítimo."},
    {"vehiculo": "Lancha", "categoria": "Acuático", "peso_toneladas": 2,
     "descripcion": "Embarcación pequeña usada en ríos o mares."},
    {"vehiculo": "Avión", "categoria": "Aéreo", "peso_toneladas": 70,
     "descripcion": "Aeronave comercial para transporte de pasajeros."},
    {"vehiculo": "Helicóptero", "categoria": "Aéreo", "peso_toneladas": 3,
     "descripcion": "Aeronave de despegue vertical con rotores."},
    {"vehiculo": "Cohete", "categoria": "Espacial", "peso_toneladas": 500,
     "descripcion": "Vehículo propulsado para viajes espaciales."},
]


def main():
    coleccion = get_collection()
    for vehiculo in VEHICULOS:
        coleccion.update_one({"vehiculo": vehiculo["vehiculo"]}, {"$set": vehiculo}, upsert=True)
    print(f"{coleccion.count_documents({})} vehículos en {coleccion.full_name}")


if __name__ == "__main__":
    main()
