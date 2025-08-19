from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import RegistroForm, LoginForm
from .forms import PerfilForm 
from django.db import models 
from django.utils import timezone
from datetime import datetime, timedelta
from facturacion.models import FacturacionMunicipio
from infoperdidas.models import ResultadoPerdidas
from planes.models import Plan, DatosMunicipio, DatosUEB
from django.core.exceptions import ObjectDoesNotExist
from infoperdidas.services import CalculadorPerdidas
def _obtener_valor_mes(datos_obj, mes):
    """Obtiene el valor del mes usando nombres de campos en español"""
    MESES_ESPANOL = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio',
        7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    mes_espanol = MESES_ESPANOL[mes]
    return getattr(datos_obj, mes_espanol, 0) if datos_obj else 0

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
    año_actual = datetime.now().year
    mes_actual = datetime.now().month
    
    # 1. OBTENER DATOS DE TODOS LOS MUNICIPIOS PARA LA PROVINCIA
    resultados_municipios = ResultadoPerdidas.objects.filter(
        año=año_actual,
        mes=mes_actual
    )
    
    # Calcular totales provinciales sumando todos los municipios
    datos_municipios_list = []
    for resultado in resultados_municipios:
        datos_municipios_list.append({
            'energia_barra': resultado.energia_barra,
            'fact_mayor': resultado.facturacion_mayor,
            'fact_menor': resultado.facturacion_menor,
        })
    
    # 2. CALCULAR DATOS PROVINCIALES (réplica de _calcular_datos_provincia)
    try:
        estacion_cabecera = FacturacionMunicipio.objects.get(
            municipio='CAR',
            mes=mes_actual,
            año=año_actual
        ).consumo_transmision or 0
    except ObjectDoesNotExist:
        estacion_cabecera = 0
    
    # Datos consolidados del MES
    datos_provincia_mes = {
        'energia_barra': sum(m['energia_barra'] for m in datos_municipios_list),
        'fact_mayor': sum(m['fact_mayor'] for m in datos_municipios_list),
        'fact_menor': sum(m['fact_menor'] for m in datos_municipios_list),
        'estacion_cabecera': estacion_cabecera,
    }
    
    datos_provincia_mes['total_ventas'] = (
        datos_provincia_mes['fact_mayor'] +
        datos_provincia_mes['fact_menor'] +
        datos_provincia_mes['estacion_cabecera']
    )
    datos_provincia_mes['perdidas_mwh'] = (
        datos_provincia_mes['energia_barra'] -
        datos_provincia_mes['total_ventas']
    )
    datos_provincia_mes['perdidas_pct'] = (
        (datos_provincia_mes['perdidas_mwh'] / datos_provincia_mes['energia_barra'] * 100)
        if datos_provincia_mes['energia_barra'] > 0 else 0
    )
    
    # 3. CALCULAR ACUMULADOS PROVINCIALES
    acumulado_provincial = CalculadorPerdidas.calcular_acumulado_provincial(año_actual, mes_actual)
    
    # 4. OBTENER DATOS DEL PLAN PROVINCIAL
    plan_pct_mes = 0
    plan_pct_acumulado = 0
    
    plan_anual = Plan.objects.filter(periodo__contains=str(año_actual)).first()
    if plan_anual:
        try:
            # Plan mensual
            datos_plan_mensual = DatosUEB.objects.filter(
                plan=plan_anual,
                nombre__icontains='PROVINCIA',
                es_mensual=True
            ).first()
            if datos_plan_mensual:
                plan_pct_mes = _obtener_valor_mes(datos_plan_mensual, mes_actual)
            
            # Plan acumulado
            datos_plan_acumulado = DatosUEB.objects.filter(
                plan=plan_anual,
                nombre__icontains='PROVINCIA',
                es_mensual=False
            ).first()
            if datos_plan_acumulado:
                plan_pct_acumulado = _obtener_valor_mes(datos_plan_acumulado, mes_actual)
                
        except Exception as e:
            print(f"Error obteniendo planes: {e}")
    
    # 5. PREPARAR DATOS PARA GRÁFICO (acumulados por mes)
    meses_grafico = []
    perdidas_reales_acumuladas = []
    plan_acumulado_grafico = []
    
    for mes in range(1, mes_actual + 1):
        meses_grafico.append(f"{mes:02d}/{año_actual}")
        
        # Obtener acumulado real hasta este mes
        acumulado_mes = CalculadorPerdidas.calcular_acumulado_provincial(año_actual, mes)
        perdidas_reales_acumuladas.append(round(acumulado_mes['acumulado_pct'], 1))
        
        # Obtener plan acumulado hasta este mes
        if datos_plan_acumulado:
            plan_acumulado_grafico.append(_obtener_valor_mes(datos_plan_acumulado, mes))
        else:
            plan_acumulado_grafico.append(0)
    
    # 6. ÚLTIMOS PLANES CARGADOS
    ultimos_planes = Plan.objects.order_by('-fecha_carga')[:5]
    
    
    # 7. CONTEXTO COMPLETO
    context = {
        'año_actual': año_actual,
        'mes_actual': mes_actual,
        
        # DATOS DEL MES ACTUAL
        'energia_mes': round(datos_provincia_mes['energia_barra'], 1),
        'facturacion_mes': round(datos_provincia_mes['total_ventas'], 1),
        'perdidas_pct_mes': round(datos_provincia_mes['perdidas_pct'], 1),
        'plan_pct_mes': round(plan_pct_mes, 1),
        
        # DATOS ACUMULADOS (CORREGIDOS para que coincidan con el template)
        'energia_total': round(acumulado_provincial['acumulado_energia'], 1),
        'facturacion_total': round(acumulado_provincial['acumulado_ventas'], 1),
        'perdidas_pct_acumulado': round(acumulado_provincial['acumulado_pct'], 1),
        'plan_pct_acumulado': round(plan_pct_acumulado, 1),
        
        # AÑADIR PROMEDIOS (calcula el promedio de los meses disponibles)
        'plan_promedio': round(plan_pct_acumulado, 1) if plan_pct_acumulado else 0,
        'perdidas_promedio': round(acumulado_provincial['acumulado_pct'], 1),
        
        # DATOS PARA GRÁFICO
        'meses_grafico': meses_grafico,
        'perdidas_reales': perdidas_reales_acumuladas,
        'plan_perdidas': plan_acumulado_grafico,
        
        # ACTIVIDAD RECIENTE
        'ultimos_planes': ultimos_planes,
    }
    
    return render(request, 'usuarios/dashboard.html', context)