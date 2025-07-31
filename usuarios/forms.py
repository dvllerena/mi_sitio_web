# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm



class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)
    
    
class PerfilForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        exclude = ['password']  # Excluimos el campo de contraseña