import barcode
from barcode.writer import ImageWriter
import os
from django.conf import settings
import pandas as pd
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib import messages
from .models import Aprendiz, Rh, Instructor, Ficha, TipoDoc, Roll, Estado, Modalidad, ProgramaEnFormacion
from .forms import UploadFileForm
from django.http import JsonResponse



# Create your views here.
#########################################################################
def upload_excel(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]
            instructor_id = request.POST.get("instructor_a_cargo")  # Obtener ID del instructor
            ficha_id = request.POST.get("ficha")  # Obtener ID de la ficha

            try:
                df = pd.read_excel(file, engine="openpyxl", skiprows=10)
                df.columns = ["tipo_documento", "numero_documento", "nombres", "apellidos", "correo", "estado"]
                # df.columns = ["tipo_documento", "numero_documento", "nombres", "apellidos", "estado", "correo"]
                df = df.iloc[1:].reset_index(drop=True)

                aprendices = []
                instructor = Instructor.objects.filter(id=instructor_id).first()
                ficha = Ficha.objects.get(ficha=ficha_id)  # Buscar ficha por ID

                for _, row in df.iterrows():
                    # Obtener el ID del tipo de documento
                    tipo_doc = TipoDoc.objects.filter(tipo=row["tipo_documento"]).first()
                    if not tipo_doc:
                        return JsonResponse({"error": f"Tipo de documento '{row['tipo_documento']}' no encontrado."}, status=400)

                    # Obtener el ID del estado
                    estado = Estado.objects.filter(estado=row["estado"]).first()
                    if not estado:
                        return JsonResponse({"error": f"Estado '{row['estado']}' no encontrado."}, status=400)

                    aprendiz = Aprendiz(
                        tipo_documento=tipo_doc,
                        numero_documento=row["numero_documento"],
                        nombres=row["nombres"],
                        apellidos=row["apellidos"],
                        correo=row["correo"],
                        instructor_cargo=instructor,
                        ficha=ficha,
                        estado=estado,
                        roll_id=1  # Asignando roll_id = 1 automáticamente
                    )
                    aprendices.append(aprendiz)

                Aprendiz.objects.bulk_create(aprendices)
                return JsonResponse({"mensaje": "Archivo subido correctamente"})

            except Exception as e:
                return JsonResponse({"error": f"Error al procesar el archivo: {e}"}, status=400)

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
    if request.method == "POST":
        correo = request.POST.get("email")
        contraseña = request.POST.get("password")

        try:
            # Comparación directa porque las contraseñas NO están encriptadas
            instructor = Instructor.objects.get(correo_instructor=correo, password=contraseña)

            # Guardar información en la sesión
            request.session["nombre"] = instructor.nombres
            request.session["id_instructor"] = instructor.id

            return redirect("instru_login")  # Redirigir a la misma página o al dashboard
        except Instructor.DoesNotExist:
            messages.error(request, "Correo o contraseña incorrectos")  

    return render(request, "instru-login.html")


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
        aprendiz.tipo_documento = request.POST['tipoDoc']
        aprendiz.nombres = request.POST['nombres']
        aprendiz.apellidos = request.POST['apellidos']
        
        # Buscar la instancia de Rh correcta antes de asignarla
        rh_id = request.POST['rh']
        aprendiz.rh = get_object_or_404(Rh, id=rh_id)

        aprendiz.save()
        return redirect('ficha_select', numero=aprendiz.ficha.ficha)

    # Obtener todos los grupos sanguíneos para el formulario
    grupos_sanguineos = Rh.objects.all()
    
    return render(request, 'editar-aprendiz.html', {
        'aprendiz': aprendiz,
        'grupos_sanguineos': grupos_sanguineos  # Pasar la lista de grupos sanguíneos a la plantilla
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

