import os
from django.db import models
from django.core.files.storage import default_storage
import base64
from django.core.files.base import ContentFile  # Import necesario para manejar archivos base64
from django.utils import timezone
from django.conf import settings

# Create your models here.

class Rh(models.Model):
    id = models.AutoField(primary_key=True)
    Rh = models.CharField(max_length=10)

class TipoDoc(models.Model):
    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=50)

class Roll(models.Model):
    id = models.AutoField(primary_key=True)
    roll = models.CharField(max_length=50)

class Estado(models.Model):
    id = models.AutoField(primary_key=True)
    estado = models.CharField(max_length=50)

class Modalidad(models.Model):
    id = models.AutoField(primary_key=True)
    modalidad = models.CharField(max_length=50)

class Ficha(models.Model):
    ficha = models.CharField(primary_key=True, max_length=20)  # Número de ficha como clave primaria
    nombre_ficha = models.CharField(max_length=100)
    fecha_inicio = models.CharField(max_length=50)
    modalidad = models.ForeignKey('Modalidad', on_delete=models.CASCADE)
    instructores = models.ManyToManyField('Instructor', related_name='fichas')  # Relación muchos a muchos

    def __str__(self):
        return f"{self.ficha} - {self.nombre_ficha}"

class Instructor(models.Model):
    id = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo_instructor = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    numero_identificacion = models.CharField(max_length=50, unique=True)
    numero_telefono = models.CharField(max_length=20, null=True, blank=True)
    rh = models.ForeignKey('Rh', on_delete=models.SET_NULL, null=True)
    roll = models.ForeignKey('Roll', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

#######################################################################################

def ruta_foto_aprendiz(instance, filename):
    """Guarda la imagen en media/fotos/{numero_de_ficha}/ con el nombre {numero_documento}.ext"""
    extension = filename.split('.')[-1]  # Obtener la extensión del archivo
    nombre_archivo = f"{instance.numero_documento}.{extension}"  # Guardar con el número de documento
    return os.path.join('fotos', str(instance.ficha.ficha), nombre_archivo)

class Aprendiz(models.Model):
    id = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    rh = models.ForeignKey(Rh, on_delete=models.SET_NULL, null=True, blank=True)
    correo = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    tipo_documento = models.ForeignKey(TipoDoc, on_delete=models.CASCADE)
    numero_documento = models.CharField(max_length=50, unique=True)
    instructor_cargo = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE)
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE)
    estado = models.ForeignKey('Estado', on_delete=models.SET_NULL, null=True, blank=True)
    foto = models.ImageField(upload_to=ruta_foto_aprendiz, null=True, blank=True)
    fecha_descarga = models.DateTimeField(default=timezone.now)
   

    # Modificación para permitir guardar imágenes en base64 desde el formulario de edición
    def save(self, *args, **kwargs):
        """Elimina la imagen anterior antes de guardar una nueva y maneja imágenes en base64"""
        if self.pk:  # Si el objeto ya existe en la base de datos
            try:
                obj = Aprendiz.objects.get(pk=self.pk)
                if obj.foto and self.foto and obj.foto != self.foto:
                    if os.path.isfile(obj.foto.path):
                        os.remove(obj.foto.path)
            except Aprendiz.DoesNotExist:
                pass  # Si no existe el objeto previo, no hacemos nada

        # Modificación: Guardar imagen desde base64 si se proporciona
        if isinstance(self.foto, str) and self.foto.startswith("data:image"):
            formato, imgstr = self.foto.split(';base64,')
            extension = formato.split('/')[-1]
            nombre_archivo = f"{self.numero_documento}.{extension}"
            self.foto = ContentFile(base64.b64decode(imgstr), name=nombre_archivo)

        super().save(*args, **kwargs)

################################################################

class ProgramaEnFormacion(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='programas')
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    

    


