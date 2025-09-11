#!/bin/bash
# Script para iniciar el servidor biométrico
# Guarda este archivo como start_bioserver.sh

echo "🚀 Iniciando servidor biométrico..."
echo "📍 URL: http://186.31.35.24:8000"
echo "📱 Endpoint: /api/recibir-datos-biometrico/"
echo ""

cd "c:\ControlIngreso\BioData"

# Activar entorno virtual
source env/Scripts/activate

# Aplicar migraciones si es necesario
python manage.py migrate

# Iniciar servidor
echo "✅ Servidor iniciado en http://186.31.35.24:8000"
python manage.py runserver 0.0.0.0:8000
