from rest_framework import serializers
from .models import UsuarioBiometrico, RegistroAsistencia

class UsuarioBiometricoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioBiometrico
        fields = '__all__'


class RegistroAsistenciaSerializer(serializers.ModelSerializer):
    nombre_usuario = serializers.CharField(source='usuario.nombre', read_only=True)
    user_id = serializers.CharField(source='usuario.user_id', read_only=True)

    class Meta:
        model = RegistroAsistencia
        fields = ['id', 'user_id', 'nombre_usuario', 'entrada', 'salida', 'timestamp', 'estado']

class ResumenAsistenciaSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    nombre = serializers.CharField(allow_null=True)
    privilegio = serializers.IntegerField()
    entrada = serializers.DateTimeField(allow_null=True)
    salida = serializers.DateTimeField(allow_null=True)
    tiempo_trabajado = serializers.CharField()

    class Meta:
        model = RegistroAsistencia
        fields = '__all__'