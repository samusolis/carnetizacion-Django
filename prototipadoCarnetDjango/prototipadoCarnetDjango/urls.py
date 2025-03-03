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
    path("descargar_reporte_aprendices/", views.descargar_reporte_aprendices, name="descargar_reporte_aprendices"),
    path('admin/', admin.site.urls, name="admin_site"),
    path('',views.index,name="index"),
    path('instructor/', views.instructor, name="instructor"),
    
    path('administrador/', views.administrador, name="administrador"),
    path('admin_dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('admin-login/', views.admin_login, name="admin_login"),
    path('gestionar-usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('gestionar-fichas/', views.gestionar_fichas, name='gestionar_fichas'),
    path('gestionar-programas/', views.gestionar_programas, name="gestionar_programas"),
    path("subir_instructores/", views.subir_instructores, name="subir_instructores"),
    path('subir-fichas/', views.subir_fichas, name='subir_fichas'),
    
    path('instru-login/', views.instru_login, name="instru_login"),
    path("dashboard/", views.dashboard_instructor, name="dashboard_instructor"),
    
    path('reporte_aprendices/', views.reporte_aprendices, name='reporte_aprendices'),
    
    
    path("logout-instructor/", views.logout_instructor, name="logout_instructor"),

    
    path('mis-fichas/', views.mis_fichas, name="mis_fichas"),
    path('fichas-instru/', views.instru_fichas, name="fichas_instru"),
    path('crear-clave/', views.crear_clave, name="crear_clave"),
    path('upload/', views.upload_excel, name="upload_excel"),
    
    path('verificar-documento/', views.verificar_documento, name='verificar_documento'),
    path('carnet/<str:documento>/', views.carnet, name="carnet"),
    
    path('carnetInstru/', views.carnetInstru, name="carnetInstru"),
    path('carnetTras/', views.carnetTras, name="carnetTras"),
    path('ficha-select/<int:numero>', views.ficha_select, name="ficha_select"),
    path('editar-aprendiz/<int:numero_documento>/', views.editar_aprendiz, name="editar_aprendiz"),
    path('ficha-select/<int:numero>/', views.ficha_select, name="ficha_select"),
    path('configurar_permisos/', views.configurar_permisos, name='configurar_permisos'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

