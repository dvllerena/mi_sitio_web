from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Páginas principales
    path('', views.home, name='home'),
    path('perfil/', views.perfil, name='perfil'),
    
    # Autenticación personalizada
    path('registro/', views.registro, name='registro'),
    path('accounts/login/', 
            auth_views.LoginView.as_view(
                template_name='usuarios/login.html'  # Ruta exacta a tu template
            ),
            name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Recuperación de contraseña (con templates en usuarios/registration/)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='usuarios/registration/password_reset_form.html',
             email_template_name='usuarios/registration/password_reset_email.html',
             subject_template_name='usuarios/registration/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='usuarios/registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='usuarios/registration/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='usuarios/registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Cambio de contraseña (para usuarios logueados)
    path('password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name='usuarios/registration/password_change_form.html',
             success_url='/password-change/done/'
         ),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='usuarios/registration/password_change_done.html'
         ),
         name='password_change_done'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/cambiar-avatar/', views.cambiar_avatar, name='cambiar_avatar'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]