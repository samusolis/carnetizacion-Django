import barcode
from barcode.writer import ImageWriter
import os
from django.conf import settings
import pandas as pd
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib import messages
from .models import Aprendiz, Rh, Instructor, Ficha, TipoDoc, Roll, Estado, Modalidad, ProgramaEnFormacion
from .forms import UploadFileForm
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse



# Create your views here.
#########################################################################
def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            # Leer archivo Excel desde la celda 11
            df = pd.read_excel(request.FILES['file'], skiprows=10)

            # Renombrar columnas según la base de datos
            df.columns = ['tipo_documento', 'numero_documento', 'nombres', 'apellidos', 'correo', 'estado']

            # Verificar que las columnas esperadas estén presentes
            expected_columns = {'tipo_documento', 'numero_documento', 'nombres', 'apellidos', 'correo', 'estado'}
            if not expected_columns.issubset(set(df.columns)):
                return JsonResponse({"error": "Las columnas del archivo no coinciden con las esperadas"}, status=400)

            # Obtener IDs de las relaciones foráneas
            tipo_doc_map = {td.tipo: td.id for td in TipoDoc.objects.all()}
            estado_map = {e.estado: e.id for e in Estado.objects.all()}

            # Convertir valores a los IDs correspondientes
            df['tipo_documento_id'] = df['tipo_documento'].map(tipo_doc_map)
            df['estado_id'] = df['estado'].map(estado_map)

            # Rellenar valores faltantes y asignar roll_id = 1 (aprendiz)
            df['rh_id'] = 1  # Si RH es obligatorio, modificar aquí
            df['roll_id'] = 1  # Siempre será aprendiz
            df['ficha_id'] = request.POST.get('ficha')
            df['instructor_cargo_id'] = request.POST.get('instructor_a_cargo')

            # Verificar que no haya valores nulos en claves foráneas
            if df[['tipo_documento_id', 'estado_id', 'roll_id', 'ficha_id', 'instructor_cargo_id']].isnull().any().any():
                return JsonResponse({"error": "Error en los valores de referencia. Verifica tipo de documento, estado, ficha o instructor."}, status=400)

            # Crear objetos en la base de datos
            registros = [
                Aprendiz(
                    nombres=row['nombres'],
                    apellidos=row['apellidos'],
                    correo=row['correo'],
                    numero_documento=row['numero_documento'],
                    tipo_documento_id=row['tipo_documento_id'],
                    estado_id=row['estado_id'],
                    ficha_id=row['ficha_id'],
                    instructor_cargo_id=row['instructor_cargo_id'],
                    roll_id=row['roll_id'],
                )
                for _, row in df.iterrows()
            ]
            Aprendiz.objects.bulk_create(registros)

            return JsonResponse({"mensaje": "Archivo subido con éxito"}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Error al procesar el archivo: {str(e)}"}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

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
  
def editar_aprendiz(request, numero_documento):
    aprendiz = get_object_or_404(Aprendiz, numero_documento=numero_documento)

    if request.method == 'POST':
        tipo_doc_id = request.POST['tipoDoc']
        aprendiz.tipo_documento = get_object_or_404(TipoDoc, id=tipo_doc_id)  # Asignar tipo de documento correcto
        aprendiz.nombres = request.POST['nombres']
        aprendiz.apellidos = request.POST['apellidos']
        
        # Buscar la instancia de Rh correcta antes de asignarla
        rh_id = request.POST['rh']
        aprendiz.rh = get_object_or_404(Rh, id=rh_id)

        aprendiz.save()
        return redirect('ficha_select', numero=aprendiz.ficha.ficha)

    # Obtener todos los grupos sanguíneos y tipos de documento
    grupos_sanguineos = Rh.objects.all()
    tipos_documento = TipoDoc.objects.all()

    return render(request, 'editar-aprendiz.html', {
        'aprendiz': aprendiz,
        'grupos_sanguineos': grupos_sanguineos,
        'tipos_documento': tipos_documento  # Pasar lista de tipos de documento
    })

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

