from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from .forms import CargaConsumoForm, EditarConsumoForm
from .models import ConsumoEnergia
from datetime import date



def _agrupar_por_obet(datos):
    """Función auxiliar para agrupar datos por OBET"""
    agrupados = {}
    for dato in datos:
        if dato['obet'] not in agrupados:
            agrupados[dato['obet']] = []
        agrupados[dato['obet']].append(dato)
    return agrupados

@login_required
def guardar_consumo(request):
    if request.method == 'POST' and 'datos_consumo' in request.session:
        datos_consumo = request.session['datos_consumo']
        fecha = date.fromisoformat(datos_consumo['fecha'])
        
        try:
            # Eliminar registros existentes para este mes/año
            ConsumoEnergia.objects.filter(fecha__year=fecha.year, fecha__month=fecha.month).delete()
            
            # Crear nuevos registros
            consumos = [
                ConsumoEnergia(
                    obet=item['obet'],
                    municipio=item['municipio'],
                    fecha=fecha,
                    consumo=item['consumo']
                ) for item in datos_consumo['datos']
            ]
            ConsumoEnergia.objects.bulk_create(consumos)
            
            messages.success(request, 'Datos guardados exitosamente!')
            del request.session['datos_consumo']
        except Exception as e:
            messages.error(request, f'Error al guardar datos: {str(e)}')
    
    return redirect('perdidas:calculo')

@login_required 
class EditarConsumoView(UpdateView):
    model = ConsumoEnergia
    form_class = EditarConsumoForm
    template_name = 'perdidas/editar_consumo.html'
    success_url = reverse_lazy('perdidas:calculo')

    def form_valid(self, form):
        messages.success(self.request, 'Consumo actualizado correctamente')
        return super().form_valid(form)

@login_required
def facmayor_view(request):
    return render(request, 'facturacion/facmayor.html')

@login_required
def infoperdidas_view(request):
    return render(request, 'infoperdidas/informe.html')

@login_required
def lventas_view(request):
    return render(request, 'perdidas/lventas.html')

@login_required
def carga_consumo(request):
    consumos_existentes = None  # Definir siempre al inicio
    if request.method == 'POST':
        form = CargaConsumoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                resultado = form.procesar_archivo()
                request.session['datos_consumo'] = {
                    'datos': resultado['datos'],
                    'fecha': resultado['fecha'].strftime('%Y-%m-%d')
                }
                consumos_existentes = ConsumoEnergia.objects.filter(
                    fecha__year=form.cleaned_data['año'],
                    fecha__month=form.cleaned_data['mes']
                ).order_by('obet', 'municipio')
                return render(request, 'perdidas/calculo.html', {
                    'form': form,
                    'datos_agrupados': _agrupar_por_obet(resultado['datos']),
                    'total_consumo': resultado['total_consumo'],
                    'fecha': resultado['fecha'],
                    'consumos_existentes': consumos_existentes,
                    'mostrar_resultados': True,
                    'mostrar_existentes': True
                })
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = CargaConsumoForm()
        consumos_existentes = None

    # Cargar datos existentes si se proporciona mes/año
    año = request.GET.get('año')
    mes = request.GET.get('mes')
    if año and mes:
        consumos_existentes = ConsumoEnergia.objects.filter(
            fecha__year=año,
            fecha__month=mes
        ).order_by('obet', 'municipio')

    return render(request, 'perdidas/calculo.html', {
        'form': form,
        'consumos_existentes': consumos_existentes,
        'mostrar_existentes': consumos_existentes is not None
    })