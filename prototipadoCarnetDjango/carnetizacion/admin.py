from django.contrib import admin
from .models import Ficha, Instructor, Aprendiz, ProgramaEnFormacion, Rh

# Register your models here.

# class FichaAdmin(admin.ModelAdmin):
#     list_display = ('ficha', 'nombre_ficha', 'fecha_inicio', 'base')
#     list_filter = ('nombre_ficha',)
# class InstructorAdmin(admin.ModelAdmin):
#     list_display = ('nombres', 'apellidos', 'correo_instructor','numero_identificacion', 'numero_telefono')
#     list_filter = ('nombres',)
# class AprendizAdmin(admin.ModelAdmin):
#     search_fields = ('nombres', 'apellidos', 'correo', 'numero_identificacion')
#     list_display = ('nombres', 'apellidos', 'correo', 'telefono', 'rh', 'numero_identificacion', 'foto', 'ficha_id', 'instructor_a_cargo_id')
#     list_filter = ('ficha_id',)
# class RhAdmin(admin.ModelAdmin):
#     list_display = ('nombre',)

# class ProgramaEnFormacionAdmin(admin.ModelAdmin):
#     list_display = ('ficha_id', 'nombre_ficha_id', 'nombre_instructor_id')
#     list_filter = ('ficha_id', 'nombre_instructor_id',)



admin.site.register(Ficha)
admin.site.register(Instructor)
admin.site.register(Aprendiz)
admin.site.register(Rh)
admin.site.register(ProgramaEnFormacion)