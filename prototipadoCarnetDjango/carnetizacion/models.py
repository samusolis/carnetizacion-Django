from django.db import models
# Create your models here.

class Ficha(models.Model):
    ficha = models.CharField(max_length=191, primary_key=True)  
    nombre_ficha = models.CharField(max_length=255)
    fecha_inicio = models.CharField(max_length=255)
    base = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre_ficha


# Model for the Instructores table
class Instructor(models.Model):
    id = models.AutoField(primary_key=True)
    correo_instructor = models.EmailField()
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    numero_identificacion = models.CharField(max_length=50)
    clave = models.CharField(max_length=255, null=True, blank=True)  # Permitir null y vacío

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'


# Model for the Rh table 
class Rh(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre


# Model for the Aprendices table
class Aprendiz(models.Model):
    id = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(max_length=50)
    numero_identificacion = models.CharField(max_length=50)
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    rh = models.ForeignKey(Rh, on_delete=models.SET_NULL, null=True, blank=True, related_name='aprendices')  # Permitir null
    clave = models.CharField(max_length=255, null=True, blank=True)  # Permitir null y vacío
    instructor_a_cargo = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, related_name='aprendices')
    ficha = models.ForeignKey(Ficha, on_delete=models.SET_NULL, null=True, to_field='ficha', related_name='aprendices')  # Apunta a ficha como clave primaria

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'

# Model for the ProgramaEnFormacion table
class ProgramaEnFormacion(models.Model):
    id = models.AutoField(primary_key=True)
    nombre_ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE)
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='programas')
    nombre_instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.nombre_ficha.nombre_ficha} - {self.nombre_instructor.nombres}'