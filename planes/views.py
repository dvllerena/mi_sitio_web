from django.shortcuts import render, redirect
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
import pandas as pd
from .models import Plan, DatosMunicipio, DatosUEB
from .forms import PlanForm
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

# Configuración básica del logging (solo en desarrollo)
if settings.DEBUG:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
# Mapeo de municipios a OBETs (definido localmente para evitar dependencia)
MUNICIPIO_TO_OBET = {
    'Matanzas': 'OBET Matanzas',
    'Cárdenas': 'OBET Cárdenas',
    'Unión de Reyes': 'OBET Unión',
    'Limonar': 'OBET Unión',
    'Colón': 'OBET Colón',
    'Martí': 'OBET Colón',
    'Los Arabos': 'OBET Colón',
    'Calimete': 'OBET Colón',
    'Perico': 'OBET Jovellanos',
    'Pedro Betancourt': 'OBET Jagüey',
    'Jovellanos': 'OBET Jovellanos',
    'Jagúey Grande': 'OBET Jagüey',
    'Ciénaga de Zapata': 'OBET Jagüey',
    'Varadero': 'OBET Varadero',
    'Provincia': ''
}

class PlanesView(View):
    template_name = 'planes/listar.html'
    
    def get(self, request):
        plan_id = request.GET.get('plan')
        plan_seleccionado = Plan.objects.filter(id=plan_id).first() if plan_id else Plan.objects.last()
        
        if plan_seleccionado:
            # Organizar datos para el template
            datos_municipios_acum = DatosMunicipio.objects.filter(
                plan=plan_seleccionado, 
                es_mensual=False
            ).order_by('nombre')
            
            datos_municipios_mensual = DatosMunicipio.objects.filter(
                plan=plan_seleccionado, 
                es_mensual=True
            ).order_by('nombre')
            
            datos_uebs_acum = DatosUEB.objects.filter(
                plan=plan_seleccionado,
                es_mensual=False
            ).order_by('nombre')
            
            datos_uebs_mensual = DatosUEB.objects.filter(
                plan=plan_seleccionado,
                es_mensual=True
            ).order_by('nombre')
        else:
            datos_municipios_acum = datos_municipios_mensual = []
            datos_uebs_acum = datos_uebs_mensual = []
        
        context = {
            'planes': Plan.objects.all().order_by('-fecha_carga'),
            'plan_seleccionado': plan_seleccionado,
            'datos_municipios_acum': datos_municipios_acum,
            'datos_municipios_mensual': datos_municipios_mensual,
            'datos_uebs_acum': datos_uebs_acum,
            'datos_uebs_mensual': datos_uebs_mensual,
            'meses': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        logger.debug("Iniciando vista POST de Planes")
        form = PlanForm(request.POST, request.FILES)
        
        if not form.is_valid():
            logger.warning(f"Formulario inválido: {form.errors}")
            for error in form.errors.values():
                messages.error(request, error)
            return redirect('planes:listar')
        
        try:
            with transaction.atomic():
                logger.debug("Iniciando transacción atómica")
                archivo = request.FILES['archivo']
                periodo = form.cleaned_data['periodo']
                logger.debug(f"Procesando archivo: {archivo.name} para periodo: {periodo}")
                
                try:
                    xls = pd.ExcelFile(archivo)
                    logger.debug(f"Hojas encontradas en el Excel: {xls.sheet_names}")
                except Exception as e:
                    logger.error(f"Error al leer archivo Excel: {str(e)}", exc_info=True)
                    raise ValueError("El archivo no es un Excel válido")
                
                # Validar hojas requeridas
                if not all(sheet in xls.sheet_names for sheet in ['Acumulados', 'Mensuales']):
                    logger.error(f"Hojas faltantes. Esperadas: ['Acumulados', 'Mensuales'], Encontradas: {xls.sheet_names}")
                    raise ValueError("El archivo debe contener hojas 'Acumulados' y 'Mensuales'")
                
                # Crear plan
                plan = Plan.objects.create(
                    periodo=periodo,
                    archivo=archivo,
                    fecha_carga=timezone.now()
                )
                logger.debug(f"Plan creado: ID {plan.id}")
                
                # Procesar hojas
                logger.debug("Procesando hoja Acumulados")
                self.procesar_hoja(xls, 'Acumulados', plan, es_mensual=False)
                
                logger.debug("Procesando hoja Mensuales")
                self.procesar_hoja(xls, 'Mensuales', plan, es_mensual=True)
                
                logger.info(f"Plan '{periodo}' cargado exitosamente con ID {plan.id}")
                messages.success(request, f"Plan '{periodo}' cargado exitosamente!")
                return redirect('planes:listar')
                
        except Exception as e:
            logger.error(f"Error en POST: {str(e)}", exc_info=True)
            messages.error(request, f"Error al procesar: {str(e)}")
            return redirect('planes:listar')
    
    def procesar_hoja(self, xls, nombre_hoja, plan, es_mensual=False):
        try:
            df = pd.read_excel(xls, sheet_name=nombre_hoja, header=1)
            
            if len(df) < 24:
                raise ValueError(f"La hoja {nombre_hoja} no tiene el formato esperado (faltan filas)")

            # Procesar municipios
            municipios_data = []
            for i in range(0, 15):
                if i >= len(df):
                    break
                    
                row = df.iloc[i]
                municipio = str(row.iloc[0]).strip()
                if municipio and municipio.lower() != 'provincia' and municipio != 'nan':
                    municipios_data.append(DatosMunicipio(
                        plan=plan,
                        nombre=municipio,
                        obet=MUNICIPIO_TO_OBET.get(municipio, ''),
                        enero=self.validar_porcentaje(row.iloc[1]),
                        febrero=self.validar_porcentaje(row.iloc[2]),
                        marzo=self.validar_porcentaje(row.iloc[3]),
                        abril=self.validar_porcentaje(row.iloc[4]),
                        mayo=self.validar_porcentaje(row.iloc[5]),
                        junio=self.validar_porcentaje(row.iloc[6]),
                        julio=self.validar_porcentaje(row.iloc[7]),
                        agosto=self.validar_porcentaje(row.iloc[8]),
                        septiembre=self.validar_porcentaje(row.iloc[9]),
                        octubre=self.validar_porcentaje(row.iloc[10]),
                        noviembre=self.validar_porcentaje(row.iloc[11]),
                        diciembre=self.validar_porcentaje(row.iloc[12]),
                        es_mensual=es_mensual
                    ))

            # Procesar OBETs/UEBs
            uebs_data = []
            start_uebs = 17  # Fila 17 en Excel (OBET o UEB)
            
            for i in range(start_uebs, len(df)):
                row = df.iloc[i]
                obet = str(row.iloc[0]).strip()
                if obet and obet != 'nan':
                    if obet == 'Provincia':
                        obet = 'PROVINCIA'
                    
                    uebs_data.append(DatosUEB(
                        plan=plan,
                        nombre=obet,
                        enero=self.validar_porcentaje(row.iloc[1]),
                        febrero=self.validar_porcentaje(row.iloc[2]),
                        marzo=self.validar_porcentaje(row.iloc[3]),
                        abril=self.validar_porcentaje(row.iloc[4]),
                        mayo=self.validar_porcentaje(row.iloc[5]),
                        junio=self.validar_porcentaje(row.iloc[6]),
                        julio=self.validar_porcentaje(row.iloc[7]),
                        agosto=self.validar_porcentaje(row.iloc[8]),
                        septiembre=self.validar_porcentaje(row.iloc[9]),
                        octubre=self.validar_porcentaje(row.iloc[10]),
                        noviembre=self.validar_porcentaje(row.iloc[11]),
                        diciembre=self.validar_porcentaje(row.iloc[12]),
                        es_mensual=es_mensual
                    ))

            # Bulk create
            if municipios_data:
                DatosMunicipio.objects.bulk_create(municipios_data)
            if uebs_data:
                DatosUEB.objects.bulk_create(uebs_data)
                
        except Exception as e:
            raise
    
    def validar_porcentaje(self, valor):
        """Valida que el valor sea un porcentaje válido o lo convierte a None"""
        try:
            if pd.isna(valor):
                return None
            valor_float = float(valor)
            return valor_float if 0 <= valor_float <= 100 else None
        except (ValueError, TypeError):
            return None   

@login_required
def eliminar_plan(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Plan eliminado correctamente.')
        return redirect('planes:listar')
    # Opcional: puedes renderizar un template de confirmación para GET
    return render(request, 'planes/confirmar_eliminar.html', {'plan': plan})