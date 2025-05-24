# API/serializers.py
from rest_framework import serializers
from .models import UsuarioBiometrico, RegistroAsistencia, JornadaLaboral

class JornadaLaboralSerializer(serializers.ModelSerializer):
    class Meta:
        model = JornadaLaboral
        fields = '__all__'

class UsuarioBiometricoSerializer(serializers.ModelSerializer):
    turno = JornadaLaboralSerializer()

    class Meta:
        model = UsuarioBiometrico
        fields = ['user_id', 'nombre', 'privilegio', 'activo', 'turno']

class RegistroAsistenciaSerializer(serializers.ModelSerializer):
    usuario = UsuarioBiometricoSerializer()

    class Meta:
        model = RegistroAsistencia
        fields = ['id', 'usuario', 'timestamp', 'tipo']
