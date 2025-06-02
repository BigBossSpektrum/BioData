from django import forms
from .models import UsuarioBiometrico

class UsuarioBiometricoForm(forms.ModelForm):
    class Meta:
        model = UsuarioBiometrico
        fields = ['user_id', 'nombre', 'privilegio', 'activo', 'turno']
