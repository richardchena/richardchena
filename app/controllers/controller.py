#aqui van los controladores, encargados de la logica del negocio
#se pueden agregar mas archivos
from datetime import date
from app.models.usuario_proyecto_model import UsuarioProyectoModel
from django.urls.base import resolve
from django import http
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
import json
import datetime
from sys import path as path
path.append('./')
from app.models.personas_model import PersonaModel
from app.models.proyectos_model import ProyectoModel
from app.models.permisos_model import PermisosModel
from app.models.usuarios_model import UserModel
from app.models.roles_model import RolesModel
from app.models.usuario_roles_model import UsuarioRolModel
from app.models.rol_permiso_model import RolPermisoModel
from app.models.us_model import USModel
from app.models.sprints_model import SprintModel

class ViewRequest:
    def __init__(self):
        self.usuario_logueado = None
        self.mensaje_error = []
        self.titulo_error = None
        self.id_proyecto = None
        self.id_sprint = None
        self.permisos = None

    def enviar_sms_error(self, templade):        
        view = loader.get_template(templade)
        html_reponse = view.render({'titulo': self.titulo_error, 'errors': self.mensaje_error})

        self.mensaje_error = []
        return HttpResponse(html_reponse)

    #-------------------------LOGIN-------------------------------#
    def iniciar_sesion(self, request):
        return render(request, 'login.html')

    def sitio_en_construccion(self, request):
        return render(request, 'construccion.html')

    def logeado(self, request):
        modelo = UserModel()
        usuario = request.GET["usuario"]
        psw = request.GET["contrasena"]
        base_password = modelo.consult_persona(usuario)
        if base_password is not None:
            if base_password[1] == psw:
                self.usuario_logueado = usuario
                ids = self.obtener_roles_usuario(usuario)
                permisos = []
                if ids is not None:
                    for id in ids:
                        rol_permisos = RolPermisoModel().consult_permisos(id)
                        if rol_permisos is not None:
                            for per in rol_permisos:
                                permisos.append(per[0])

                self.permisos = permisos
                #view = loader.get_template('home.html')
                #html = view.render({'user': self.usuario_logueado, 'permisos': self.permisos})                
                #return HttpResponse(html)
                return redirect('/home/')

        #sino redirecciona, entonces es un error de credenciales
        self.titulo_error = 'Credenciales Inválidas'
        self.mensaje_error.append('El nombre de usuario y/o la contraseña que ingresaste no coinciden con nuestros registros.')
        self.mensaje_error.append('Por favor, revisa e inténtalo de nuevo.')

        return self.enviar_sms_error('login.html')  

    def home(self, request):
        view = loader.get_template('home.html')
        html = view.render({'user': self.usuario_logueado, 'permisos': self.permisos})
        return HttpResponse(html)

    def proyectos(self, request):
        view = loader.get_template('proyectos.html')
        html = view.render({'user': self.usuario_logueado})
        return HttpResponse(html)

    #-------------------------USUARIOS-------------------------------#
    def crear_usuario(self, request):
        today = date.today()
        hoy = today.strftime("%Y-%m-%d")
        view = loader.get_template('signup.html')
        html_reponse = view.render({'lista_roles': self.obtener_roles(), 'current_date': hoy})
        return HttpResponse(html_reponse)

    def guardar_roles_selected(self, request):
        self.rol_select = request.GET.getlist('rol_select')
        return HttpResponse()
    
    def validar_datos_signup(self, request):
        password = request.GET['password']
        password2 = request.GET['password2']
        if password != password2:
            response = HttpResponse(
                json.dumps({ 'mensaje': 'Las contraseñas no coinciden'}), 
                content_type='application/json'
            )
            response.status_code = 400
            return response

        username = request.GET['username']
        print(username)
        if UserModel().consult_persona_exists(username) is not None:
            response = HttpResponse(
                json.dumps({ 'mensaje': 'Ya existe un usuario con ese "USERNAME"'}), 
                content_type='application/json'
            )
            response.status_code = 400
            return response

        return HttpResponse()
        
    def registrar_usuario(self, request):
        #datos de la persona
        persona = {}
        persona['p_nombre'] = request.GET['p_nombre']
        persona['s_nombre'] = request.GET['s_nombre']
        persona['p_apellido'] = request.GET['p_apellido']
        persona['s_apellido'] = request.GET['s_apellido']
        persona['fec_nac'] = request.GET['fec_nacimiento']
        print(persona)
        #datos del usuario
        usuario = {}
        usuario['username'] = request.GET['username']
        usuario['correo'] = request.GET['correo']
        usuario['password'] = request.GET['password']
        usuario['password2'] = request.GET['password_rep']
        print(usuario)
        persona['id'] = PersonaModel().insert_persona(
            persona['p_nombre'],
            persona['s_nombre'],
            persona['p_apellido'],
            persona['s_apellido'],
            persona['fec_nac']
        )

        UserModel().insert_user(usuario['username'], usuario['password'], persona['id'], usuario['correo'])
        #datos de los roles
        for rol in self.rol_select:
            UsuarioRolModel().insert_rol_usuario2(rol,usuario['username'])

        return redirect('/signup/')

    def modificar_usuario(self, request):
        #datos de la persona
        persona = {}
        persona['p_nombre'] = request.GET['p_nombre']
        persona['s_nombre'] = request.GET['s_nombre']
        persona['p_apellido'] = request.GET['p_apellido']
        persona['s_apellido'] = request.GET['s_apellido']
        persona['fec_nac'] = request.GET['fec_nacimiento']
        print(persona)
        #datos del usuario
        usuario = {}
        usuario['username'] = request.GET['username2']
        usuario['correo'] = request.GET['correo']
        usuario['password'] = request.GET['password']
        print(usuario)
        modelo_usuario = UserModel()
        persona['id'] = modelo_usuario.consult_id_persona(usuario['username'])
        PersonaModel().update_persona(
            persona['p_nombre'],
            persona['s_nombre'],
            persona['p_apellido'],
            persona['s_apellido'],
            persona['fec_nac'],
            persona['id']
        )

        modelo_usuario.update_user(usuario['password'], usuario['correo'], usuario['username'])
        #datos de los roles
        roles = self.obtener_roles_usuario(usuario['username'])
        if roles :
            for rol in roles:
                UsuarioRolModel().delete_rol_usuario(rol,usuario['username'])

        for rol in self.rol_select:
            UsuarioRolModel().insert_rol_usuario2(rol,usuario['username'])

        return redirect('/user_settings/')
    def modificar_user(self, request):
        view = loader.get_template('modificar_user.html')
        html_reponse = view.render({'lista_roles': self.obtener_roles()})
        return HttpResponse(html_reponse)
    
    def obtener_usuario(self, request):
        username = request.GET.get('username')
        usuario = UserModel().consult_persona(username)
        if usuario is None:
            return HttpResponse(status=400) ##VER
        
        persona = PersonaModel().consult_per(usuario[2])
        datos_persona={}
        datos_persona['p_nombre'] = persona[1]
        datos_persona['s_nombre'] = persona[2]
        datos_persona['p_apellido'] = persona[3]
        datos_persona['s_apellido'] = persona[4]
        datos_persona['nacimiento'] = persona[5].strftime("%Y-%m-%d")
        datos_persona['correo'] = usuario[3]
        datos_persona['pass'] = usuario[1]
        datos_persona['permisos'] = self.obtener_roles_usuario(username)
        print(datos_persona['permisos'])
        datos_persona['username'] = username

        return HttpResponse(json.dumps(datos_persona), content_type='application/json')
    
    def eliminar_user(self, request):
        return render(request, 'delete_user.html')

    def del_user(self, request):
        usuario = request.GET['username2']        
        ids_proyecto = UsuarioProyectoModel().consult_usuarios_proyecto_fin(usuario)
        if ids_proyecto is not None:
            for id_proyecto in ids_proyecto:
                UsuarioProyectoModel().update_fecha_salida(usuario, id_proyecto)

        UsuarioRolModel().delete_roles_usuario(usuario)
        UserModel().delete_user(usuario)
        if self.usuario_logueado == usuario:
            return redirect('/login/')
        
        return redirect('/delete_user/')

    def buscar_user_elm(self, request):
        username = request.GET.get('username')
        usuario = UserModel().consult_persona(username)

        if usuario is None:
            self.titulo_error = "ERROR"
            self.mensaje_error.append("No existe ese usuario")
            return HttpResponse(self.enviar_sms_error('modificar_user.html'), status=400) ##VER
        
        persona = PersonaModel().consult_per(usuario[2])
        datos_persona = {}
        pers = ''
        for ind in range(len(persona)):
            if persona[ind] is not None and ind > 0 and ind < 5:
                pers = pers + ' ' + str(persona[ind])

        datos_persona['nombre'] = pers
        datos_persona['correo'] = usuario[3]
        datos_persona['username'] = username
        return HttpResponse(json.dumps(datos_persona), content_type='application/json')

    #-------------------------ROLES-------------------------------#
    def obtener_roles_usuario(self, usuario_user):
        return UsuarioRolModel().consult_id_roles(usuario_user)
    
    def seguridad(self, request):
        return render(request, 'seguridad.html')
    
    def rol_nombre(self, request):
        return render(request, 'asignar_nombre_rol.html')

    def modificar_rol(self, request):
        view = loader.get_template('modificar_rol.html')
        html_reponse = view.render({'lista_roles': self.obtener_roles(), 'lista_permisos': self.obtener_permisos()})
        return HttpResponse(html_reponse)

    def updt_rol(self, request):
        id_rol = request.GET['rol_selected']
        p = RolPermisoModel().consult_permisos2(id_rol)
        
        desc = request.GET['desc']
        RolesModel().update_descripcion(desc, id_rol)
        if (p):
            for permiso in p:
                RolPermisoModel().update_rol_permiso(False, id_rol, permiso)
        
        for permiso in self.permisos_selected:
            existe_registro = RolPermisoModel().consult_estado(id_rol, permiso)
            if (existe_registro is None):
                RolPermisoModel().insert_rol_permiso(id_rol, permiso, True)
            else:
                RolPermisoModel().update_rol_permiso(True, id_rol, permiso)

        RolesModel().update_descripcion(desc, id_rol)    
        return redirect('/seguridad/')

    def eliminar_rol(self, request):
        view = loader.get_template('delete_rol.html')
        html_reponse = view.render({'lista_roles': self.obtener_roles()})
        return HttpResponse(html_reponse)
    
    def del_rol(self, request):
        id_rol = request.GET['rol_selected']
        rol = UsuarioRolModel().consult_rol_user(self.usuario_logueado, id_rol)
        RolesModel().delete_rol(id_rol)
        if rol is not None:
            return redirect('/login/')
        
        return redirect('/delete_rol/')
    
    def rol_permisos(self, request):
        view = loader.get_template('asignar_permisos.html')
        html_reponse = view.render({'lista_permisos': self.obtener_permisos(), 'nombre_rol': self.nombre_rol, 'descripcion': self.descripcion})
        return HttpResponse(html_reponse)
    
    def guardar_nombre_rol(self, request):
        self.nombre_rol = request.GET.get('nombre')
        self.descripcion = request.GET.get('descripcion')
        return HttpResponse()
    
    def registrar_rol(self, request):
        nombre_rol = request.GET.get('nombre_rol')
        descripcion = request.GET.get('desc_rol')
        if (descripcion):
            rol_id = RolesModel().insert_rol(nombre_rol, descripcion)
        else:
            rol_id = RolesModel().insert_rol(nombre_rol, None)
        
        for permiso in self.permisos_selected:
            RolPermisoModel().insert_rol_permiso(rol_id, permiso, True)
            
        return render(request, 'seguridad.html')

    #-------------------------PERMISOS-------------------------------#
    def guardar_permisos_selected(self, request):
        self.permisos_selected = request.GET.getlist('permisos_selected')
        return HttpResponse()
   
    def obtener_permisos_rol(self, request):
        id_rol = request.GET.get('rol_selected')
        permisos = RolPermisoModel().consult_permisos2(id_rol)
        desc = RolesModel().consult_rol_desc(id_rol)
        datos={}
        datos['permisos'] = permisos
        datos['descripcion'] = desc
        return HttpResponse(json.dumps(datos), content_type='application/json')

    def crear_permisos(self, request):
        return render(request, 'crear_permiso.html')

    def reg_permiso(self, request):
        nombre = request.GET['nombre_permiso']
        descripcion = request.GET['desc_permiso']
        PermisosModel().insert_permiso(nombre, descripcion)
        return redirect('/crear_permiso/')

    def modificar_permisos(self, request):
        view = loader.get_template('modificar_permiso.html')
        html_reponse = view.render({'lista_permisos': self.obtener_permisos()})
        return HttpResponse(html_reponse)

    def eliminar_permisos(self, request):
        view = loader.get_template('eliminar_permiso.html')
        html_reponse = view.render({'lista_permisos': self.obtener_permisos()})
        return HttpResponse(html_reponse)
        
    def obt_permiso(self, request):
        id_permiso = request.GET['id_permiso']
        campos_permiso = PermisosModel().consult_permiso_by_id(id_permiso)
        permiso = { 
            'nombre': campos_permiso[0], 
            'descripcion': campos_permiso[1],
            'id_permiso': id_permiso 
        }
        return HttpResponse(json.dumps(permiso), content_type='application/json')
    
    def mod_permiso(self, request):
        nuevo_nombre = request.GET['nombre']
        descripcion = request.GET['descripcion']
        id_permiso = request.GET['id_permiso']
        PermisosModel().update_permiso(nuevo_nombre, descripcion, id_permiso)
        return redirect('/modificar_permiso/')

    def del_permiso(self, request):
        id_permiso = request.GET['id_permiso']
        ids_roles = RolPermisoModel().consult_roles_permiso(id_permiso)
        PermisosModel().delete_permiso(id_permiso)
        if ids_roles is not None:
            for id_rol in ids_roles:
                rol = UsuarioRolModel().consult_rol_user(self.usuario_logueado, id_rol)
                if rol is not None:
                    return redirect('/login/')
        
        return redirect('/eliminar_permiso/')

    #-------------------------PROYECTOS-------------------------------#
    def proyecto(self, request):
        lista_proyectos = ProyectoModel().consult_proyectos()
        if lista_proyectos is None:
            print('No hay proyectos')
 
        view = loader.get_template('proyecto.html')
        html_reponse = view.render({'lista_proyectos': lista_proyectos})
        return HttpResponse(html_reponse)
    
    def guardar_proyecto_id(self, request):
        self.id_proyecto = request.GET['id_proyecto']
        return HttpResponse()

    def modificar_proyecto(self, request):
        view = loader.get_template('modificar_proyecto.html')
        res = SprintModel().sprint_activo(self.id_proyecto)
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        html_reponse = view.render({'respuesta': res, 'nombre_proyecto': nombre_proyecto})
        return HttpResponse(html_reponse)     

    def mod_proyecto(self, request):
        nuevo_nombre = request.GET['proy_nombre']
        estado = request.GET.get('estado')
        
        if nuevo_nombre == '':
            ProyectoModel().update_estado_fin(estado, self.id_proyecto)
        else:
            if estado == 'false':
                ProyectoModel().update_nombre(nuevo_nombre, self.id_proyecto)
            else:
                ProyectoModel().update_project(nuevo_nombre, False, self.id_proyecto)
                ProyectoModel().update_estado_fin(estado, self.id_proyecto)

                usuarios_proyecto = UsuarioProyectoModel().consult_usuarios_asignados_fin(self.id_proyecto)
                if usuarios_proyecto is not None:
                    for usuario in usuarios_proyecto:
                        UsuarioProyectoModel().update_fecha_salida(usuario[0], self.id_proyecto)
      
        return HttpResponse()

    def crear_proyecto(self, request):
        return render(request, 'crear_proyecto.html')

    def reg_proyecto(self, request):
        ProyectoModel().insert_project(request.GET['pro_nombre'])
        return redirect('/proyects') 
    
    def del_proyecto(self, request):
        ProyectoModel().delete_project(request.GET['id_proyecto'])
        return HttpResponse()

    def equipo(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        view = loader.get_template('equipo.html')
        html_reponse = view.render({'nombre_proyecto':nombre_proyecto})
        return HttpResponse(html_reponse)

    #-------------------------EQUIPOS-------------------------------#
    def add_miembro(self, request):
        lista_miembros = UsuarioProyectoModel().consult_usuarios_disponibles()
        if lista_miembros is None:
            print('No hay miembros')
 
        view = loader.get_template('add_miembro.html')
        html_reponse = view.render({'lista_miembros': lista_miembros})
        return HttpResponse(html_reponse)

    def add_miembro_proyect(self, request):
        UsuarioProyectoModel().insert_usuario_proyecto(request.GET['username'], self.id_proyecto)
        return redirect('/add_miembro/') 

    def delete_miembro(self, request):
        lista_miembros = UsuarioProyectoModel().consult_usuarios_asignados(self.id_proyecto)
        if lista_miembros is None:
            print('No hay miembros')
 
        view = loader.get_template('delete_miembro.html')
        html_reponse = view.render({'lista_miembros': lista_miembros})
        return HttpResponse(html_reponse)
    
    def del_miembro(self, request):
        UsuarioProyectoModel().update_fecha_salida(request.GET['username'], self.id_proyecto)
        return redirect('/delete_miembro/') 
    
    def lista_miembro(self, request):
        lista_miembros = UsuarioProyectoModel().consult_usuarios(self.id_proyecto)
        if lista_miembros is None:
            print('No hay miembros')
 
        view = loader.get_template('lista_miembro.html')
        html_reponse = view.render({'lista_miembros': lista_miembros})
        return HttpResponse(html_reponse)

    def lista_miembro2(self, request):
        lista_miembros = UsuarioProyectoModel().consult_usuarios(self.id_proyecto)
        if lista_miembros is None:
            print('No hay miembros')
 
        view = loader.get_template('lista_miembro2.html')
        html_reponse = view.render({'lista_miembros': lista_miembros})
        return HttpResponse(html_reponse)

    #-------------------------BACKLOG-------------------------------#
    def desarrollo(self, request):
        lista_proyectos = ProyectoModel().consult_proyectos()
        if lista_proyectos is None:
            print('No hay proyectos')
 
        view = loader.get_template('desarrollo.html')
        html_reponse = view.render({'lista_proyectos': lista_proyectos})
        return HttpResponse(html_reponse)

    def backlog(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        lista_us = USModel().consult_us_by_proyect_backlog(self.id_proyecto)
        view = loader.get_template('backlog.html')
        html_reponse = view.render({'lista_us': lista_us,'nombre_proyecto':nombre_proyecto})
        return HttpResponse(html_reponse)

    def del_us_h(self, request):
        USModel().update_backlog_state(True, request.GET['id_us'])
        return HttpResponse()
    
    def del_us_backlog(self, request):
        USModel().delete_us(request.GET['id_us'])
        return HttpResponse()

    def eliminar_us(self, request):
        return render(request, 'eliminar_us.html')

    def guardar_us_id(self, request):
        self.id_us = request.GET['id_us']
        return HttpResponse()

    def modificar_us(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        nombre_us = USModel().consult_nombre_us(self.id_us)
        descripcion_us = USModel().consult_descripcion_us(self.id_us)

        if descripcion_us is None:
            descripcion_us = ''

        view = loader.get_template('modificar_us.html')
        html = view.render({'nombre_us': nombre_us,'descripcion_us': descripcion_us,'proy':nombre_proyecto})
        return HttpResponse(html) 
    
    def mod_us(self, request):
        nuevo_nombre = request.GET['nombre']
        descripcion = request.GET['descripcion']
        if nuevo_nombre:
            USModel().update_nombre(nuevo_nombre, self.id_us)     

        USModel().update_descripcion(descripcion, self.id_us)    
        return redirect('/modificar_us/')

    def obt_us(self, request):
        id_us= request.GET['id_us']
        campos_us = USModel().consult_us_by_id(id_us)
        us = { 
            'username': campos_us[2],
        }
        return HttpResponse(json.dumps(us), content_type='application/json')     

    #-------------------------SPRINTS-------------------------------#
    def sprint(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        lista = SprintModel().consult(self.id_proyecto)
        view = loader.get_template('sprint.html')
        html_reponse = view.render({'lista_sprint': lista,'nombre_proyecto':nombre_proyecto})
        return HttpResponse(html_reponse)

    def crear_sprint(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        view = loader.get_template('crear_sprint.html')
        html_reponse = view.render({'proy': nombre_proyecto})
        return HttpResponse(html_reponse)        

    def reg_sprint(self, request):
        SprintModel().insert_sprint_short(request.GET['spr_nombre'], self.id_proyecto)
        return redirect('/sprint')
    
    def fin_sprint(self, request):
        id_sprint = request.GET['id_sprint']
        print(request.GET['id_sprint'])
        print(self.id_proyecto)
        us_estados_sprint = USModel().consult_us_by_id_sprint(id_sprint)
        print(us_estados_sprint)
        if us_estados_sprint is not None:
            response = HttpResponse(
                json.dumps({ 'mensaje': 'Existen US sin finalizar correspondientes a ese Sprint'}), 
                content_type='application/json'
            )
            response.status_code = 400
            return response
        
        SprintModel().update_estado(False, id_sprint)
        SprintModel().update_fecha_fin(id_sprint)
        return HttpResponse()
    
    def iniciar_sprint(self, request):
        today = date.today()
        hoy = today.strftime("%Y-%m-%d")
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        sprint = SprintModel().consult_sprint(self.id_sprint)
        nombre_sprint = sprint[0]
        view = loader.get_template('iniciar_sprint.html')
        html = view.render({'nombre': nombre_sprint,'proy':nombre_proyecto, 'current_date': hoy})
        return HttpResponse(html)

    def calcular_fecha_duracion_sprint(self, request):
        fecha1 = datetime.datetime.strptime(request.GET['fecha_inicio'], '%Y-%m-%d').date()
        duracion = int(request.GET['duracion'])
        fecha2 = fecha1 + datetime.timedelta(days = duracion)
        response = HttpResponse(
            json.dumps({ 'fecha_fin_sprint': str(fecha2)}),
            content_type='application/json'
        )
        return response

    def ini_sprint(self, request):
        nombre_sprint = request.GET['nombre']
        fecha_inicio = request.GET['fecha_inicio']
        fecha_fin = request.GET['fecha_fin']
        SprintModel().update_sprint(nombre_sprint, fecha_inicio, fecha_fin, self.id_sprint)
        return HttpResponse()

    def comprobar_us_sprint(self, request):
        id_sprint = request.GET['id_sprint']
        us_backlog_sprint = USModel().consult_backlog_by_id_sprint(id_sprint)
        if us_backlog_sprint is None:
            response = HttpResponse(
                json.dumps({ 'mensaje': 'No se encuentra ningun US en el sprint'}), 
                content_type='application/json'
            )
            response.status_code = 400
            return response
        return HttpResponse()

    def guardar_sprint_id(self, request):
        self.id_sprint = request.GET['id_sprint']
        return HttpResponse()

    def modificar_sprint(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        sprint = SprintModel().consult_sprint(self.id_sprint)
        nombre_sprint = sprint[0]        
        lista_us = USModel().consult_us_by_sprint(self.id_sprint)
        view = loader.get_template('modificar_sprint.html')
        html_reponse = view.render({'lista_us': lista_us,'proy':nombre_proyecto,'sprint':nombre_sprint})
        return HttpResponse(html_reponse)
    
    def sprint_historico(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        lista = SprintModel().consult(self.id_proyecto)
        view = loader.get_template('sprint_historico.html')
        html_reponse = view.render({'lista_sprint': lista, 'proy':nombre_proyecto})
        return HttpResponse(html_reponse)

    #-------------------------US-------------------------------#
    def crear_us(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        view = loader.get_template('crear_us.html')
        html_reponse = view.render({'proy':nombre_proyecto})
        return HttpResponse(html_reponse)

    def crear_us2(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        view = loader.get_template('crear_us2.html')
        html_reponse = view.render({'proy':nombre_proyecto})
        return HttpResponse(html_reponse) 
    
    def agregar_us(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        sprint = SprintModel().consult_sprint(self.id_sprint)  
        nombre_sprint = sprint[0]        
        lista_us = USModel().consult_us_by_proyect_backlog(self.id_proyecto)
        view = loader.get_template('agregar_us.html')
        html_reponse = view.render({'lista_us': lista_us,'proy': nombre_proyecto, 'sprint': nombre_sprint})
        return HttpResponse(html_reponse)        
       
    def asignar_user(self, request):
        print(self.id_proyecto)
        lista_miembros = UsuarioProyectoModel().consult_usuarios_asignados(self.id_proyecto)
        if lista_miembros is None:
            print('No hay miembros')
 
        view = loader.get_template('asignar_user.html')
        html_reponse = view.render({'lista_miembros': lista_miembros})
        return HttpResponse(html_reponse)   

    def add_us(self, request):
        nombre = request.GET['nombre']
        descripcion = request.GET['descripcion']
        id_proyecto = self.id_proyecto
        if not descripcion:
            descripcion = None

        USModel().insert_us(nombre, descripcion, "TODO", None, id_proyecto, None, True)
        return redirect('/crear_us/')

    def add_us2(self, request):
        nombre = request.GET['nombre']
        descripcion = request.GET['descripcion']
        id_proyecto = self.id_proyecto
        if not descripcion:
            descripcion = None

        USModel().insert_us(nombre, descripcion, "TODO", None, id_proyecto, None, True)
        return redirect('/crear_us2/')

    def add_incidencia(self, request):
        id_us = request.GET['id_us']
        id_sprint = self.id_sprint
        USModel().update_backlog_state(False, id_us)
        USModel().update_sprint_us(id_sprint,id_us)
        return redirect('/agregar_us/')

    def add_user_sprint(self, request):
        USModel().update_username(request.GET['username'], self.id_us)
        return redirect('/modificar_sprint/')  

    def sprint_us_historico(self, request):
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        sprint = SprintModel().consult_sprint(self.id_sprint)
        nombre_sprint = sprint[0]         
        lista_us = USModel().consult_us_by_sprint(self.id_sprint)
        view = loader.get_template('sprint_us_historico.html')
        html_reponse = view.render({'lista_us': lista_us,'proy': nombre_proyecto, 'sprint': nombre_sprint})

        return HttpResponse(html_reponse)
        
    #-------------------------KANBAN-------------------------------#
    def kanban(self, request):
        lista_us = USModel().consult_us_by_proyect_kanban(self.id_proyecto)
        nombre_proyecto = ProyectoModel().consult_proyecto_nom(self.id_proyecto)
        sprint = SprintModel().consult_sprint_activo(self.id_proyecto)
        nombre = UserModel().consultar_nombre(self.usuario_logueado)
        if(sprint==None):
            sprint='Ningún sprint activo'
        view = loader.get_template('kanban.html')
        html_reponse = view.render({'lista_us': lista_us,'proy': nombre_proyecto, 'sprint': sprint, 'current_user': nombre})
        return HttpResponse(html_reponse)

    def actualizar_estado_us(self, request):
        id_us = request.GET['id_us']
        estado = request.GET['estado']

        USModel().update_estado(estado, id_us)
        return redirect('/kanban/')

    #-------------------------OTRAS FUNCIONES-------------------------------#
    def obtener_roles(self):
        return RolesModel().consult_roles()

    def obtener_permisos(self):
        return PermisosModel().consult_permiso()

    def obtener_us(self):
        return USModel().consult_us()

    def obtener_username(self):
        return USModel().consult_username()
  