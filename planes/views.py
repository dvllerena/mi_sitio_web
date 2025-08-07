from django.shortcuts import render, redirect
from django.views import View
from .models import Plan, DatosMunicipio, DatosUEB
from .forms import PlanForm
import pandas as pd
from django.db import transaction
from datetime import datetime
from django.contrib import messages
from django.utils import timezone



class PlanesView(View):
    template_name = 'planes/listar.html'
    
    def get(self, request):
        # Obtener el plan seleccionado o el más reciente
        plan_id = request.GET.get('plan')
        if plan_id:
            plan_seleccionado = Plan.objects.get(id=plan_id)
        else:
            plan_seleccionado = Plan.objects.last()
        
        # Obtener todos los planes para el dropdown
        planes = Plan.objects.all().order_by('-fecha_carga')
        
        # Obtener datos para las tablas y gráfico
        datos_municipios = []
        datos_uebs = []
        datos_grafico_municipios = [0]*12
        datos_grafico_uebs = [0]*12
        
        if plan_seleccionado:
            # Datos para tablas
            datos_municipios = DatosMunicipio.objects.filter(plan=plan_seleccionado)
            datos_uebs = DatosUEB.objects.filter(plan=plan_seleccionado)
            
            # Preparar datos para gráfico (promedios mensuales)
            if datos_municipios.exists():
                meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
                         'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
                
                for i, mes in enumerate(meses):
                    valores = [getattr(m, mes) for m in datos_municipios if getattr(m, mes) is not None]
                    datos_grafico_municipios[i] = sum(valores)/len(valores) if valores else 0
                    
                    valores_ueb = [getattr(u, mes) for u in datos_uebs if getattr(u, mes) is not None]
                    datos_grafico_uebs[i] = sum(valores_ueb)/len(valores_ueb) if valores_ueb else 0
        
        context = {
            'planes': planes,
            'plan_seleccionado': plan_seleccionado,
            'datos_municipios': datos_municipios,
            'datos_uebs': datos_uebs,
            'datos_grafico_municipios': datos_grafico_municipios,
            'datos_grafico_uebs': datos_grafico_uebs,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = PlanForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    archivo = request.FILES['archivo']
                    periodo = form.cleaned_data['periodo']
                    
                    # Leer archivo Excel
                    xls = pd.ExcelFile(archivo)
                    
                    # Verificar hojas requeridas
                    if 'Acumulados' not in xls.sheet_names or 'Mensuales' not in xls.sheet_names:
                        messages.error(request, "El archivo debe contener las hojas 'Acumulados' y 'Mensuales'")
                        return redirect('planes:listar')
                    
                    # Crear nuevo plan
                    plan = Plan.objects.create(
                        periodo=periodo,
                        archivo=archivo,
                        fecha_carga=timezone.now()
                    )
                    
                    # Procesar datos de municipios (hoja Acumulados)
                    df_municipios = pd.read_excel(xls, sheet_name='Acumulados', header=2)  # Saltar 2 filas de encabezado
                    df_municipios = df_municipios[df_municipios['Municipio'].notna()]  # Filtrar filas vacías
                    
                    for _, row in df_municipios.iterrows():
                        if row['Municipio'] != 'Provincia' and pd.notna(row['Municipio']):
                            DatosMunicipio.objects.create(
                                plan=plan,
                                nombre=row['Municipio'],
                                enero=row.get('Enero'),
                                febrero=row.get('Febrero'),
                                marzo=row.get('Marzo'),
                                abril=row.get('Abril'),
                                mayo=row.get('Mayo'),
                                junio=row.get('Junio'),
                                julio=row.get('Julio'),
                                agosto=row.get('Agosto'),
                                septiembre=row.get('Septiembre'),
                                octubre=row.get('Octubre'),
                                noviembre=row.get('Noviembre'),
                                diciembre=row.get('Diciembre')
                            )
                    
                    # Procesar datos de UEBs (hoja Mensuales)
                    df_uebs = pd.read_excel(xls, sheet_name='Mensuales', header=2)  # Saltar 2 filas de encabezado
                    df_uebs = df_uebs[df_uebs['OBET o UEB'].notna()]  # Filtrar filas vacías
                    
                    for _, row in df_uebs.iterrows():
                        if row['OBET o UEB'] != 'Provincia' and pd.notna(row['OBET o UEB']):
                            DatosUEB.objects.create(
                                plan=plan,
                                nombre=row['OBET o UEB'],
                                enero=row.get('Enero'),
                                febrero=row.get('Febrero'),
                                marzo=row.get('Marzo'),
                                abril=row.get('Abril'),
                                mayo=row.get('Mayo'),
                                junio=row.get('Junio'),
                                julio=row.get('Julio'),
                                agosto=row.get('Agosto'),
                                septiembre=row.get('Septiembre'),
                                octubre=row.get('Octubre'),
                                noviembre=row.get('Noviembre'),
                                diciembre=row.get('Diciembre')
                            )
                    
                    messages.success(request, f"Plan '{periodo}' cargado exitosamente con {len(df_municipios)} municipios y {len(df_uebs)} UEBs")
                    return redirect('planes:listar')
            
            except Exception as e:
                messages.error(request, f"Error al procesar el archivo: {str(e)}")
                return redirect('planes:listar')
        
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        
        return redirect('planes:listar')
    
    
    
    
       