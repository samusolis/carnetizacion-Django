"""
URL configuration for prototipadoCarnetDjango project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
#importar app con mis vistas
from carnetizacion import views

urlpatterns = [
    path('admin/', admin.site.urls, name="admin_site"),
    path('',views.index,name="index"),
    path('instructor/', views.instructor, name="instructor"),
    path('administrador/', views.administrador, name="administrador"),
    
    path('instru-login/', views.instru_login, name="instru_login"),
    path("logout-instructor/", views.logout_instructor, name="logout_instructor"),

    path('admin-login/', views.admin_login, name="admin_login"),
    path('mis-fichas/', views.mis_fichas, name="mis_fichas"),
    path('fichas-instru/', views.instru_fichas, name="fichas_instru"),
    path('upload/', views.upload_excel, name="upload_excel"),
    
    path('verificar-documento/', views.verificar_documento, name='numero_documento'),
    
    path('carnet/<str:documento>/', views.carnet, name="carnet"),
    path('carnetInstru/', views.carnetInstru, name="carnetInstru"),
    path('carnetTras/', views.carnetTras, name="carnetTras"),
    path('ficha-select/<int:numero>', views.ficha_select, name="ficha_select"),
    path('editar-aprendiz/<int:numero_documento>/', views.editar_aprendiz, name="editar_aprendiz"),
    path('ficha-select/<int:numero>/', views.ficha_select, name="ficha_select"),
    path('admin/ver-fichas/', views.ver_fichas_admin, name='ver_fichas_admin'),
    path('admin/gestionar-usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('admin/aprobar-registros/', views.aprobar_registros, name='aprobar_registros'),
    path('admin/configurar-permisos/', views.configurar_permisos, name='configurar_permisos'),
    path('ver_fichas_admin/', views.ver_fichas_admin, name='ver_fichas_admin'),
    path('gestionar_usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('aprobar_registros/', views.aprobar_registros, name='aprobar_registros'),
    path('configurar_permisos/', views.configurar_permisos, name='configurar_permisos'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
