from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import RegistroForm, LoginForm
from .forms import PerfilForm 



def home(request):
    """Vista principal de la aplicación"""
    return render(request, 'usuarios/home.html')

@login_required
def perfil(request):
    """Vista del perfil de usuario"""
    return render(request, 'usuarios/perfil.html', {'user': request.user})

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso! Bienvenido/a.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistroForm()     
    return render(request, 'usuarios/registro.html', {'form': form})                 
def login_view(request):
    """Vista personalizada de login"""
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Configuración de "Recordarme"
            if not form.cleaned_data['remember_me']:
                request.session.set_expiry(0)  # Sesión se cierra al cerrar el navegador
                
            messages.success(request, f'Bienvenido/a {user.username}!')
            return redirect('home')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})

@require_POST
def logout_view(request):
    """Vista para cerrar sesión"""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('home')

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'usuarios/editar_perfil.html', {'form': form})

@login_required
def cambiar_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        # Accede al perfil a través del related_name 'perfil'
        perfil = request.user.perfil  # Usa el related_name definido
        perfil.avatar = request.FILES['avatar']
        perfil.save()
        messages.success(request, 'Avatar actualizado correctamente')
    return redirect('perfil')

@login_required
def dashboard_view(request):
    return render(request, 'usuarios/dashboard.html')