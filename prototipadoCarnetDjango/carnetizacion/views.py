import barcode
from barcode.writer import ImageWriter
import os
from django.conf import settings
import pandas as pd
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib import messages
from .models import Aprendiz, Rh, Instructor, Ficha, TipoDoc, Roll, Estado, Modalidad, ProgramaEnFormacion
from .forms import UploadFileForm
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.core.files.storage import default_storage



# Create your views here.
#########################################################################
def upload_excel(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        instructor_id = request.POST.get("instructor_a_cargo")
        ficha_id = request.POST.get("ficha")

        try:
            df = pd.read_excel(excel_file, header=None, skiprows=10)  # Leer desde la fila 11
        except Exception as e:
            return JsonResponse({"error": f"Error al leer el archivo: {str(e)}"})

        errores = []
        for index, row in df.iterrows():
            try:
                tipo_doc_str = str(row[0]).strip()
                numero_documento = str(row[1]).strip()
                nombres = str(row[2]).strip()
                apellidos = str(row[3]).strip()
                correo = str(row[4]).strip()
                estado_str = str(row[5]).strip()

                tipo_documento = TipoDoc.objects.filter(tipo__iexact=tipo_doc_str.strip()).first()
                estado = Estado.objects.filter(estado=estado_str).first()
                ficha = Ficha.objects.filter(ficha=ficha_id).first()
                instructor = Instructor.objects.filter(id=instructor_id).first()
                roll = Roll.objects.get(id=1)  # Siempre será 1

                if not all([tipo_documento, estado, ficha, instructor]):
                    errores.append(f"❌ Error en fila {index + 11}: Referencias no encontradas.")
                    continue

                aprendiz = Aprendiz(
                    nombres=nombres,
                    apellidos=apellidos,
                    correo=correo,
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    instructor_cargo=instructor,
                    roll=roll,
                    ficha=ficha,
                    estado=estado,
                    rh=None  # Se deja como NULL
                )
                aprendiz.save()
            except IntegrityError:
                errores.append(f"⚠️ Documento duplicado en fila {index + 11}: {numero_documento}")
            except Exception as e:
                errores.append(f"⚠️ Error inesperado en fila {index + 11}: {str(e)}")

        if errores:
            return JsonResponse({"error": "\n".join(errores)})
        
        return JsonResponse({"success": "Archivo subido correctamente."})

    return render(request, "upload_excel.html")


##########################################################################

def verificar_documento(request):
    mensaje = None  # Inicializamos el mensaje como None

    if request.method == "POST":
        numero_documento = request.POST.get('documento', None)

        if numero_documento:
            try:
                aprendiz = Aprendiz.objects.get(numero_documento=numero_documento)
                return redirect('carnet', documento=aprendiz.numero_documento)  # Redirige a la vista del carnet
            except Aprendiz.DoesNotExist:
                mensaje = "El número de identificación no existe en nuestra base de datos."

    return render(request, 'index.html', {'mensaje': mensaje})  # Volvemos a cargar el mismo template

def carnet(request, documento):
    aprendiz = get_object_or_404(Aprendiz, numero_documento=documento)

    # Asegurar que la carpeta de códigos de barras existe
    barcode_dir = os.path.join(settings.MEDIA_ROOT, "barcodes")
    os.makedirs(barcode_dir, exist_ok=True)

    # Nombre del archivo SIN EXTENSIÓN
    barcode_filename = os.path.join(barcode_dir, f"{aprendiz.numero_documento}")

    # Verificar si el archivo ya existe para no generarlo de nuevo
    if not os.path.exists(f"{barcode_filename}.png"):
        # Generar el código de barras
        ean = barcode.get('code128', str(aprendiz.numero_documento), writer=ImageWriter())
        ean.save(barcode_filename)  # Guarda la imagen sin doble extensión

    # Pasar la ruta relativa para mostrarla en la plantilla
    barcode_url = f"/media/barcodes/{aprendiz.numero_documento}.png"

    return render(request, 'carnetDel.html', {'aprendiz': aprendiz, 'barcode_url': barcode_url})

##########################################################################
def index(request):
    return render(request, 'index.html')

def instructor(request):
    return render (request, 'instructor.html')

def instru_login(request):
    if "instructor_id" in request.session:
        return redirect("dashboard_instructor")  # Redirigir al dashboard si ya está autenticado

    if request.method == "POST":
        correo_instructor = request.POST.get("email")
        password = request.POST.get("password")

        try:
            instructor = Instructor.objects.get(correo_instructor=correo_instructor)
        except Instructor.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
            return redirect("instructor")

        if not instructor.password or instructor.password.strip() == "":
            request.session["user_email"] = correo_instructor  
            return redirect("crear_clave")

        if password != instructor.password:
            messages.error(request, "Contraseña incorrecta.")
            return redirect("instructor")

        # Guardar datos en la sesión
        request.session["instructor_id"] = instructor.id  
        request.session["nombre"] = instructor.nombres  # Asegurar que el nombre se almacena

        return redirect("dashboard_instructor")  # Redirigir al dashboard

    return render(request, "instructor.html")

def dashboard_instructor(request):
    if "instructor_id" not in request.session:
        return redirect("instructor")  # Si no hay sesión, devolver al login

    return render(request, "instru-login.html")  # Renderizar el dashboard

def crear_clave(request):
    if request.method == "POST":
        nueva_password = request.POST.get("password")
        correo_instructor = request.session.get("user_email")

        if correo_instructor:
            try:
                instructor = Instructor.objects.get(correo_instructor=correo_instructor)
                instructor.password = nueva_password  # ⚠️ Mejor usar hashing aquí
                instructor.save()

                # Cerrar sesión completamente
                logout(request)  
                request.session.flush()  

                messages.success(request, "Contraseña creada con éxito. Ahora puedes iniciar sesión.")
                return redirect("instructor")  # Redirigir a la página de inicio de sesión
            except Instructor.DoesNotExist:
                messages.error(request, "Error al crear la contraseña.")
                return redirect("crear_clave")

    return render(request, "crear_clave.html")

def logout_instructor(request):
    request.session.flush()  # Elimina toda la sesión
    messages.success(request, "Sesión cerrada correctamente.")  # Mensaje opcional
    return redirect("instructor")  # Asegúrate de que este nombre de URL sea correcto

###############################################################################

def administrador(request):
    return render (request, 'administrador.html')

def admin_login(request):
    return render(request, 'admin-log.html')

def mis_fichas(request):
    return render (request, 'mis_fichas.html')

def instru_fichas(request):
    fichas = Ficha.objects.all()
    instructores = Instructor.objects.all()
    return render(request, "fichas-instru.html",{"fichas": fichas, "instructores":instructores})

def ficha_select(request, numero):
    
    aprendices = Aprendiz.objects.filter(ficha=numero)

    return render(request, 'ficha-select.html', {'aprendices': aprendices, 'numero': numero})
    # aprendices = Aprendiz.objects.all()
    # return render(request, "ficha-select.html", {"aprendices": aprendices})
#####################################################################################

def editar_aprendiz(request, numero_documento):
    aprendiz = get_object_or_404(Aprendiz, numero_documento=numero_documento)

    if request.method == 'POST':
        tipo_doc_id = request.POST['tipoDoc']
        aprendiz.tipo_documento = get_object_or_404(TipoDoc, id=tipo_doc_id)
        aprendiz.nombres = request.POST['nombres']
        aprendiz.apellidos = request.POST['apellidos']
        
        rh_id = request.POST['rh']
        aprendiz.rh = get_object_or_404(Rh, id=rh_id)

        # Manejo de la imagen
        if 'foto' in request.FILES:
            aprendiz.foto = request.FILES['foto']

        aprendiz.save()
        return redirect('ficha_select', numero=aprendiz.ficha.ficha)

    grupos_sanguineos = Rh.objects.all()
    tipos_documento = TipoDoc.objects.all()

    return render(request, 'editar-aprendiz.html', {
        'aprendiz': aprendiz,
        'grupos_sanguineos': grupos_sanguineos,
        'tipos_documento': tipos_documento
    })

#############################################################################################

def carnetTras(request):
    return render (request, 'carnetTras.html')

def ver_fichas_admin(request):
    return render(request, 'admin/ver_fichas.html')

def gestionar_usuarios(request):
    return render(request, 'admin/gestionar_usuarios.html')

def aprobar_registros(request):
    return render(request, 'admin/aprobar_registros.html')

def configurar_permisos(request):
    return render(request, 'admin/configurar_permisos.html')

def ver_fichas_admin(request):
    return render(request, 'admin/ver_fichas_admin.html')

def gestionar_usuarios(request):
    return render(request, 'admin/gestionar_usuarios.html')

def aprobar_registros(request):
    return render(request, 'admin/aprobar_registros.html')

def configurar_permisos(request):
    return render(request, 'admin/configurar_permisos.html')

def carnetInstru(request):
    instructor = Instructor.objects.all()
    return render(request, 'carnetInstru.html', {"instructor": instructor})

