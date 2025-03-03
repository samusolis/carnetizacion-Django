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
from django.core.files.base import ContentFile 
import base64
from django.utils import timezone
import unicodedata
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

#reportes

def reporte_aprendices(request):
    ficha_id = request.GET.get("ficha")  # Obtener el ID de la ficha seleccionada
    fichas = Ficha.objects.all()  # Obtener todas las fichas para el filtro

    if ficha_id:
        aprendices = Aprendiz.objects.filter(ficha_id=ficha_id)  # Filtrar por ficha seleccionada
    else:
        aprendices = Aprendiz.objects.all()  # Mostrar todos los aprendices si no se filtra

    # Datos para el gráfico (solo fechas con descargas)
    fechas = [aprendiz.fecha_descarga.strftime('%Y-%m-%d') for aprendiz in aprendices if aprendiz.fecha_descarga]
    cantidad = [1 for _ in fechas]

    context = {
        'aprendices': aprendices,
        'fichas': fichas,
        'ficha_id': ficha_id,  # Para mantener la selección en el formulario
        'fechas': fechas,
        'cantidad': cantidad,
    }

    return render(request, "reporte.html", context)


# subir excel Aprendices
def generar_correo(nombres, apellidos):
    # Normalizar nombres y apellidos (eliminar tildes y caracteres especiales)
    nombres = unicodedata.normalize('NFKD', nombres).encode('ascii', 'ignore').decode('ascii')
    apellidos = unicodedata.normalize('NFKD', apellidos).encode('ascii', 'ignore').decode('ascii')

    # Crear el correo electrónico
    correo = f"{nombres.lower().replace(' ', '.')}.{apellidos.lower().replace(' ', '.')}@soy.sena.edu.co"
    return correo

def upload_excel(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        instructor_id = request.POST.get("instructor_a_cargo")
        ficha_id = request.POST.get("ficha")

        try:
            # Leer el archivo Excel desde la fila 11 (skiprows=10)
            df = pd.read_excel(excel_file, header=None, skiprows=10)
        except Exception as e:
            return JsonResponse({"error": f"Error al leer el archivo: {str(e)}"})

        errores = []
        for index, row in df.iterrows():
            try:
                # Convertir la fila a una lista y procesar los valores
                row = row.tolist()  # Convertir la fila a una lista

                # Asegurarse de que la fila tenga al menos 5 columnas
                if len(row) < 5:
                    error_msg = f"❌ Error en fila {index + 11}: La fila no tiene suficientes columnas."
                    errores.append(error_msg)
                    continue

                # Asignar valores a las columnas correctas
                tipo_doc_str = str(row[0]).strip() if pd.notna(row[0]) else None
                numero_documento = str(row[1]).strip() if pd.notna(row[1]) else None
                nombres = str(row[2]).strip() if pd.notna(row[2]) else None
                apellidos = str(row[3]).strip() if pd.notna(row[3]) else None
                estado_str = str(row[4]).strip() if pd.notna(row[4]) else "EN FORMACION"  # Columna 4 es el estado

                # Validar que los campos obligatorios no estén vacíos
                if not all([tipo_doc_str, numero_documento, nombres, apellidos]):
                    error_msg = f"❌ Error en fila {index + 11}: Campos obligatorios vacíos."
                    errores.append(error_msg)
                    continue

                # Verificar referencias en la base de datos
                tipo_documento = TipoDoc.objects.filter(tipo__iexact=tipo_doc_str).first()
                estado = Estado.objects.filter(estado=estado_str).first()
                ficha = Ficha.objects.filter(ficha=ficha_id).first()
                instructor = Instructor.objects.filter(id=instructor_id).first()
                roll = Roll.objects.get(id=1)  # Siempre será 1

                # Validar que todas las referencias existan
                if not all([tipo_documento, estado, ficha, instructor]):
                    error_msg = f"❌ Error en fila {index + 11}: Referencias no encontradas."
                    errores.append(error_msg)
                    continue

                # Verificar si el número de documento ya existe en la base de datos
                if Aprendiz.objects.filter(numero_documento=numero_documento).exists():
                    error_msg = f"⚠️ Documento duplicado en fila {index + 11}: {numero_documento}"
                    errores.append(error_msg)
                    continue

                # Generar un correo electrónico automáticamente
                correo = generar_correo(nombres, apellidos)

                # Crear el objeto Aprendiz
                aprendiz = Aprendiz(
                    nombres=nombres,
                    apellidos=apellidos,
                    correo=correo,  # Correo generado automáticamente
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    instructor_cargo=instructor,
                    roll=roll,
                    ficha=ficha,
                    estado=estado,
                    rh=None,  # Se deja como NULL
                    fecha_descarga=timezone.now()  # Fecha y hora actual
                )
                aprendiz.save()
            except Exception as e:
                error_msg = f"⚠️ Error inesperado en fila {index + 11}: {str(e)}"
                errores.append(error_msg)

        if errores:
            return JsonResponse({"error": "\n".join(errores)})
        
        return JsonResponse({"success": "Archivo subido correctamente."})

    return render(request, "upload_excel.html")

#subir excel Instructores

def subir_instructores(request):
    if request.method == "POST" and request.FILES.get("instructores_file"):
        archivo_excel = request.FILES["instructores_file"]
        df = pd.read_excel(archivo_excel, header=None)  # Sin encabezado
        registros_exitosos = 0
        registros_fallidos = 0
        errores = []

        for index, row in df.iterrows():
            try:
                if Instructor.objects.filter(numero_identificacion=row[2]).exists():
                    registros_fallidos += 1  # Ya existe, no se sube
                    continue

                Instructor.objects.create(
                    nombres=row[0],
                    apellidos=row[1],
                    numero_identificacion=row[2],
                    correo_instructor=row[3],
                    password=None,  # Se sube como NULL
                    numero_telefono=None,  # Se sube como NULL
                    roll=Roll.objects.get(id=2)  # Siempre asignar roll=2 (Instructor)
                )
                registros_exitosos += 1
            except Exception as e:
                errores.append(str(e))
                registros_fallidos += 1

        mensaje = f"✅ {registros_exitosos} instructores subidos correctamente."
        if registros_fallidos > 0:
            mensaje += f" ❌ {registros_fallidos} instructores no se subieron por duplicados o errores."

        return JsonResponse({"success": True, "message": mensaje})

    return JsonResponse({"success": False, "message": "No se recibió ningún archivo."})

# verificar documento

def verificar_documento(request):
    mensaje = None  # Inicializamos el mensaje como None

    if request.method == "POST":
        numero_documento = request.POST.get('documento', None)

        if numero_documento:
            try:
                aprendiz = Aprendiz.objects.get(numero_documento=numero_documento)
                
                # Verificamos si tiene RH y foto asignados
                faltantes = []
                if not aprendiz.rh:  # Verifica si el campo de RH está vacío o es nulo
                    faltantes.append("RH")
                if not aprendiz.foto:  # Verifica si el campo de foto está vacío o es nulo
                    faltantes.append("foto")

                if faltantes:
                    mensaje = f"Falta asignar {', '.join(faltantes)} a este usuario."
                else:
                    return redirect('carnet', documento=aprendiz.numero_documento)  # Redirige a la vista del carnet
            
            except Aprendiz.DoesNotExist:
                mensaje = "El número de identificación no existe en nuestra base de datos."

    return render(request, 'index.html', {'mensaje': mensaje})  # Volvemos a cargar el mismo template

def carnet(request, documento):
    aprendiz = get_object_or_404(Aprendiz, numero_documento=documento)

    # Asegurar que la carpeta de códigos de barras existe
    barcode_dir = os.path.join(settings.MEDIA_ROOT, "barcodes")
    os.makedirs(barcode_dir, exist_ok=True)

    # Nombre del archivo de código de barras
    barcode_filename = os.path.join(barcode_dir, f"{aprendiz.numero_documento}")

    # Verificar si el archivo ya existe
    if not os.path.exists(f"{barcode_filename}.png"):
        ean = barcode.get('code128', str(aprendiz.numero_documento), writer=ImageWriter())
        ean.save(barcode_filename)

    # URL del código de barras
    barcode_url = f"/media/barcodes/{aprendiz.numero_documento}.png"

    # Obtener la ficha del aprendiz
    ficha = aprendiz.ficha.ficha  # Asegúrate de que `numero_ficha` es el campo correcto en tu modelo

    # Generar la URL de la imagen del aprendiz
    foto_url = f"/media/fotos/{ficha}/{aprendiz.numero_documento}.jpg"

    return render(request, 'carnetDel.html', {'aprendiz': aprendiz, 'barcode_url': barcode_url, 'foto_url': foto_url})


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

# administrador

def administrador(request):
    """Página de login para todos los administradores"""
    logout(request)  # Asegura que no haya sesión activa
    return render(request, "administrador.html")

def admin_login(request):
    """Proceso de autenticación"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_superuser:  
                login(request, user)
                return redirect("admin_dashboard")  # Redirige a la página del superadmin
            
            else:
                logout(request)  # Cierra sesión si no es superadmin
                return redirect("administrador")  # Redirige al login general

        else:
            logout(request)  # Cierra sesión si las credenciales son incorrectas
            return render(request, "administrador.html", {"error": "Credenciales incorrectas"})

    return render(request, "administrador.html") 

def admin_dashboard(request):
    """Panel de control del superadmin"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        logout(request)  # Cierra sesión si el usuario no es superadmin
        return redirect("administrador")  
    
    return render(request, "admin-log.html")  # Renderiza el panel de superadmi

def gestionar_usuarios(request):
    instructores = Instructor.objects.all()
    return render(request, "gestionar-usuarios.html", {"instructores":instructores})

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
#############################################################################################
        foto_base64 = request.POST.get("foto_base64")
        if foto_base64:
            formato, imgstr = foto_base64.split(";base64,")  # Separar metadatos
            ext = formato.split("/")[-1]  # Obtener extensión (png o jpg)
            img_data = base64.b64decode(imgstr)  # Decodificar la imagen

            # Guardar la imagen en la carpeta de aprendices dentro de MEDIA
            file_name = f"{numero_documento}.{ext}"
            file_path = os.path.join(settings.MEDIA_ROOT, "aprendices", file_name)

            # Guardar imagen en la carpeta correspondiente
            with open(file_path, "wb") as f:
                f.write(img_data)

            # Asignar la ruta de la imagen al campo del aprendiz
            aprendiz.foto.name = f"aprendices/{file_name}"
#############################################################################################
        aprendiz.save()
        return redirect('ficha_select', numero=aprendiz.ficha.ficha)

    grupos_sanguineos = Rh.objects.all()
    tipos_documento = TipoDoc.objects.all()

    return render(request, 'editar-aprendiz.html', {
        'aprendiz': aprendiz,
        'grupos_sanguineos': grupos_sanguineos,
        'tipos_documento': tipos_documento
    })




def carnetInstru(request):
    instructor_id = request.session.get("instructor_id")

    if not instructor_id:
        return redirect("instructor")  # Redirigir al login si no está autenticado

    instructor = get_object_or_404(Instructor, id=instructor_id)

    # Asegurar que la carpeta de códigos de barras existe
    barcode_dir = os.path.join(settings.MEDIA_ROOT, "barcodes")
    os.makedirs(barcode_dir, exist_ok=True)

    # Nombre del archivo de código de barras
    barcode_filename = os.path.join(barcode_dir, f"{instructor.numero_identificacion}")

    # Verificar si el archivo ya existe
    if not os.path.exists(f"{barcode_filename}.png"):
        ean = barcode.get('code128', str(instructor.numero_identificacion), writer=ImageWriter())
        ean.save(barcode_filename)

    # URL del código de barras
    barcode_url = f"/media/barcodes/{instructor.numero_identificacion}.png"

    return render(request, "carnetInstru.html", {"instructor": instructor, "barcode_url": barcode_url})



def carnetTras(request):
    instructor_id = request.session.get("instructor_id")  # Obtener el ID del instructor de la sesión

    if not instructor_id:
        return redirect("instructor")  # Redirigir al login si no está autenticado

    instructor = get_object_or_404(Instructor, id=instructor_id)  # Obtener el instructor logueado

    return render(request, "carnetTras.html", {"instructor": instructor})

def configurar_permisos(request):
    return render(request, 'admin/configurar_permisos.html')

#############indicador formato para tomar la foto############
    if request.method == "POST":
        aprendiz.nombres = request.POST["nombres"]
        aprendiz.apellidos = request.POST["apellidos"]

        if "foto" in request.FILES:
            aprendiz.foto = request.FILES["foto"]

        if "foto_base64" in request.POST:  # Si la imagen viene desde la cámara
            format, imgstr = request.POST["foto_base64"].split(";base64,")
            ext = format.split("/")[-1]
            aprendiz.foto.save(f"{aprendiz.numero_documento}.{ext}", ContentFile(base64.b64decode(imgstr)), save=True)

        aprendiz.save()
        return redirect("alguna_vista")

    return render(request, "editar_aprendiz.html", {"aprendiz": aprendiz})
#################################################################################################

