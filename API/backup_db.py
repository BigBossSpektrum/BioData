import os
import datetime
import subprocess

def export_mysql_backup(backup_dir=r'C:\\datos\\MySQL_backup'):
    r"""
    Exporta la base de datos MySQL configurada en settings.py a un archivo .sql para backup.
    El archivo se guarda en la carpeta C:\datos\MySQL_backup, con timestamp.
    """
    # Configuración de conexión (ajusta según settings.py)
    DB_NAME = 'ligol'
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

    # Buscar mysqldump en PATH o usar ruta común de Windows
    mysqldump_path = 'mysqldump'
    from shutil import which
    if not which('mysqldump'):
        # Intenta ruta común de Windows (ajusta si es necesario)
        default_path = r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe'
        if os.path.exists(default_path):
            mysqldump_path = default_path
        else:
            print('ERROR: No se encontró mysqldump en el PATH ni en la ruta por defecto.')
            print('Por favor, instala MySQL o ajusta la variable mysqldump_path en el script.')
            return

    cmd = [
        mysqldump_path,
        f'-u{DB_USER}',
        f'-p{DB_PASSWORD}',
        f'-h{DB_HOST}',
        f'-P{DB_PORT}',
        DB_NAME,
    ]

    print(f"Exportando backup a: {backup_file}")
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"Backup exitoso: {backup_file}")
        else:
            print(f"Error al crear backup: {result.stderr}")
    except FileNotFoundError as e:
        print(f"ERROR: No se encontró el ejecutable mysqldump.\nDetalles: {e}")
    except Exception as e:
        print(f"ERROR inesperado al crear el backup: {e}")

if __name__ == '__main__':
    export_mysql_backup()
