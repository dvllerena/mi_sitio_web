#!/bin/bash
# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Crear superusuario solo si no existe (con variables de entorno)
echo "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='$ADMIN_USERNAME').exists():
    User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print('Superusuario creado exitosamente')
else:
    print('El superusuario ya existe')
" | python manage.py shell