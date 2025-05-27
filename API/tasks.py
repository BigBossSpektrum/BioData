from celery import shared_task
from . import Biometricos_connections

@shared_task
def sync_biometricos():
    Biometricos_connections.ejecutar_sync()

@shared_task
def sync_biometricos():
    print(">> Ejecutando tarea de sincronización de biométricos...")
    Biometricos_connections.ejecutar_sync()
