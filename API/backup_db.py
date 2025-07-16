import os
import datetime
import subprocess

def export_mysql_backup(backup_dir=r'C:\\datos\\MySQL_backup'):
    """
    Exporta la base de datos MySQL configurada en settings.py a un archivo .sql para backup.
    El archivo se guarda en la carpeta C:\datos\MySQL_backup, con timestamp.
    """
    # Configuración de conexión (ajusta según settings.py)
    DB_NAME = 'Ligol'
    DB_USER = 'root'
    DB_PASSWORD = 'L0sm3j0r3s!'
    DB_HOST = 'localhost'
    DB_PORT = '3308'

    # Crear carpeta de backups si no existe
    backup_path = backup_dir
    os.makedirs(backup_path, exist_ok=True)

    # Nombre del archivo de backup
    fecha = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_path, f"backup_{DB_NAME}_{fecha}.sql")

    # Comando mysqldump
    cmd = [
        'mysqldump',
        f'-u{DB_USER}',
        f'-p{DB_PASSWORD}',
        f'-h{DB_HOST}',
        f'-P{DB_PORT}',
        DB_NAME,
    ]

    print(f"Exportando backup a: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        print(f"Backup exitoso: {backup_file}")
    else:
        print(f"Error al crear backup: {result.stderr}")

if __name__ == '__main__':
    export_mysql_backup()
