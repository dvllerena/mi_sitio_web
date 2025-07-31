#!/bin/bash
# build.sh - Script para despliegue en Render.com

# 1. Configuración inicial
set -e  # Detener el script ante cualquier error
echo "🟢 Iniciando proceso de build..." 

# 2. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 3. Aplicar migraciones
echo "🔄 Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate

# 4. Recolectar archivos estáticos
echo "🖼️ Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# 5. Crear superusuario (solo si no existe)
echo "👑 Configurando superusuario..."
cat <<EOF | python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USERNAME').exists():
    User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print('✅ Superusuario creado exitosamente')
else:
    print('ℹ️ El superusuario ya existe')
EOF

# 6. Verificación final
echo "🔍 Resumen del build:"
python manage.py check --deploy
echo "🏁 Build completado con éxito!"