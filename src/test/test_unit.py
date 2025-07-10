import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Agregar el directorio padre al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller import app, data_handler
from models.tarea import Tarea
from models.usuario import Usuario
from models.asignacion import Asignacion


class TestControllerEndpoints(unittest.TestCase):
    """
    Pruebas unitarias para los endpoints del controlador de tareas
    """
    
    def setUp(self):
        """
        Configuración inicial para cada prueba
        """
        self.app = app.test_client()
        self.app.testing = True
        
        # Mock del data_handler para evitar operaciones reales de archivo
        self.mock_data_handler = Mock()
        self.mock_data_handler.tasks = []
        self.mock_data_handler.users = []
        self.mock_data_handler.save_data = Mock()
        
        # Reemplazar el data_handler global
        import controller
        controller.data_handler = self.mock_data_handler

    def tearDown(self):
        """
        Limpieza después de cada prueba
        """
        self.mock_data_handler.tasks.clear()
        self.mock_data_handler.users.clear()

    # ========== PRUEBAS PARA CREAR TAREA ==========
    
    def test_crear_tarea_exitoso(self):
        """
        Caso de éxito: Crear una tarea con todos los datos válidos
        Verifica que la tarea se crea correctamente con ID único y se guarda
        """
        # Datos de entrada válidos
        task_data = {
            "nombre": "Implementar API REST",
            "descripcion": "Desarrollar endpoints para el sistema de tareas",
            "usuario": "dev001",
            "rol": "programador"
        }
        
        # Realizar petición POST
        response = self.app.post('/tasks', 
                            data=json.dumps(task_data),
                            content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('id', response_data)
        self.assertTrue(len(response_data['id']) > 0)
        
        # Verificar que la tarea se agregó al data_handler
        self.assertEqual(len(self.mock_data_handler.tasks), 1)
        self.mock_data_handler.save_data.assert_called_once()
        
        # Verificar estructura de la tarea creada
        created_task = self.mock_data_handler.tasks[0]
        self.assertEqual(created_task['title'], task_data['nombre'])  # Cambiar 'nombre' por 'title'
        self.assertEqual(created_task['description'], task_data['descripcion'])  # Cambiar 'descripcion' por 'description'
        self.assertIn('users', created_task)

    def test_crear_tarea_datos_faltantes(self):
        """
        Caso de error: Intentar crear tarea sin campos requeridos
        Verifica que se retorne error 400 cuando faltan datos obligatorios
        """
        # Datos incompletos (falta descripción)
        task_data = {
            "nombre": "Tarea incompleta",
            "usuario": "dev001",
            "rol": "programador"
        }
        
        # Realizar petición POST
        response = self.app.post('/tasks', 
                               data=json.dumps(task_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 400)
        
        # Verificar que no se creó ninguna tarea
        self.assertEqual(len(self.mock_data_handler.tasks), 0)
        self.mock_data_handler.save_data.assert_not_called()

    # ========== PRUEBAS PARA ACTUALIZAR ESTADO TAREA ==========
    
    def test_actualizar_estado_tarea_exitoso(self):
        """
        Caso de éxito: Actualizar estado de una tarea existente
        Verifica que el estado se actualiza correctamente
        """
        # Configurar tarea existente
        task_id = "task-123"
        existing_task = {
            "id": task_id,
            "nombre": "Tarea de prueba",
            "descripcion": "Descripción de prueba",
            "status": "pendiente"
        }
        self.mock_data_handler.tasks.append(existing_task)
        
        # Datos para actualizar
        update_data = {"estado": "en_progreso"}
        
        # Realizar petición POST
        response = self.app.post(f'/tasks/{task_id}', 
                               data=json.dumps(update_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['mensaje'], "Estado actualizado exitosamente")
        
        # Verificar que el estado se actualizó
        self.assertEqual(existing_task['status'], "en_progreso")
        self.mock_data_handler.save_data.assert_called_once()

    def test_actualizar_estado_tarea_no_encontrada(self):
        """
        Caso de error: Intentar actualizar estado de tarea inexistente
        Verifica que se retorne error 404 cuando la tarea no existe
        """
        # ID de tarea que no existe
        task_id = "task-inexistente"
        update_data = {"estado": "completado"}
        
        # Realizar petición POST
        response = self.app.post(f'/tasks/{task_id}', 
                               data=json.dumps(update_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], "Tarea no encontrada")
        
        # Verificar que no se llamó save_data
        self.mock_data_handler.save_data.assert_not_called()

    def test_actualizar_estado_tarea_campo_faltante(self):
        """
        Caso de error: Intentar actualizar estado sin proporcionar el campo estado
        Verifica que se retorne error 400 cuando falta el campo requerido
        """
        # Configurar tarea existente
        task_id = "task-123"
        existing_task = {
            "id": task_id,
            "nombre": "Tarea de prueba",
            "status": "pendiente"
        }
        self.mock_data_handler.tasks.append(existing_task)
        
        # Datos sin campo estado
        update_data = {"otro_campo": "valor"}
        
        # Realizar petición POST
        response = self.app.post(f'/tasks/{task_id}', 
                               data=json.dumps(update_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], "Falta el campo estado")
        
        # Verificar que el estado no cambió
        self.assertEqual(existing_task['status'], "pendiente")
        self.mock_data_handler.save_data.assert_not_called()

    # ========== PRUEBAS PARA GESTIONAR USUARIOS EN TAREA ==========
    
    def test_gestionar_usuarios_tarea_adicionar_exitoso(self):
        """
        Caso de éxito: Adicionar usuario a una tarea existente
        Verifica que el usuario se agrega correctamente con su rol
        """
        # Configurar tarea existente
        task_id = "task-123"
        existing_task = {
            "id": task_id,
            "nombre": "Tarea de prueba",
            "users": []
        }
        self.mock_data_handler.tasks.append(existing_task)
        
        # Datos para adicionar usuario
        user_data = {
            "usuario": "dev002",
            "rol": "programador",
            "accion": "adicionar"
        }
        
        # Realizar petición POST
        response = self.app.post(f'/tasks/{task_id}/users', 
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['mensaje'], "Usuarios actualizados exitosamente")
        
        # Verificar que el usuario se agregó
        self.assertEqual(len(existing_task['users']), 1)
        self.assertEqual(existing_task['users'][0]['usuario'], "dev002")
        self.assertEqual(existing_task['users'][0]['rol'], "programador")
        self.mock_data_handler.save_data.assert_called_once()

    def test_gestionar_usuarios_tarea_rol_invalido(self):
        """
        Caso de error: Intentar adicionar usuario con rol inválido
        Verifica que se retorne error 400 cuando el rol no es válido
        """
        # Configurar tarea existente
        task_id = "task-123"
        existing_task = {
            "id": task_id,
            "nombre": "Tarea de prueba",
            "users": []
        }
        self.mock_data_handler.tasks.append(existing_task)
        
        # Datos con rol inválido
        user_data = {
            "usuario": "dev002",
            "rol": "rol_inexistente",
            "accion": "adicionar"
        }
        
        # Realizar petición POST
        response = self.app.post(f'/tasks/{task_id}/users', 
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], "Rol no válido")
        
        # Verificar que no se agregó el usuario
        self.assertEqual(len(existing_task['users']), 0)
        self.mock_data_handler.save_data.assert_not_called()

    # ========== PRUEBAS PARA GESTIONAR DEPENDENCIAS ==========
    
    def test_gestionar_dependencias_tarea_adicionar_exitoso(self):
        """
        Caso de éxito: Adicionar dependencia entre tareas existentes
        Verifica que la dependencia se establece correctamente
        """
        # Configurar tareas existentes
        task_id = "task-123"
        dependency_id = "task-456"
        
        main_task = {
            "id": task_id,
            "nombre": "Tarea principal",
            "dependencies": []
        }
        
        dependency_task = {
            "id": dependency_id,
            "nombre": "Tarea dependiente"
        }
        
        self.mock_data_handler.tasks.extend([main_task, dependency_task])
        
        # Datos para adicionar dependencia
        dependency_data = {
            "dependencytaskid": dependency_id,
            "accion": "adicionar"
        }
        
        # Realizar petición POST
        response = self.app.post(f'/tasks/{task_id}/dependencies', 
                               data=json.dumps(dependency_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['mensaje'], "Dependencias actualizadas exitosamente")
        
        # Verificar que la dependencia se agregó
        self.assertIn(dependency_id, main_task['dependencies'])
        self.mock_data_handler.save_data.assert_called_once()

    def test_gestionar_dependencias_tarea_dependiente_no_encontrada(self):
        """
        Caso de error: Intentar adicionar dependencia con tarea dependiente inexistente
        Verifica que se retorne error 404 cuando la tarea dependiente no existe
        """
        # Configurar solo tarea principal
        task_id = "task-123"
        main_task = {
            "id": task_id,
            "nombre": "Tarea principal",
            "dependencies": []
        }
        self.mock_data_handler.tasks.append(main_task)
        
        # Datos con tarea dependiente inexistente
        dependency_data = {
            "dependencytaskid": "task-inexistente",
            "accion": "adicionar"
        }
        
        # Realizar petición POST
        response = self.app.post(f'/tasks/{task_id}/dependencies', 
                               data=json.dumps(dependency_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], "Tarea dependiente no encontrada")
        
        # Verificar que no se agregó la dependencia
        self.assertEqual(len(main_task['dependencies']), 0)
        self.mock_data_handler.save_data.assert_not_called()

    # ========== PRUEBAS PARA CREAR USUARIO ==========
    
    def test_crear_usuario_exitoso(self):
        """
        Caso de éxito: Crear un nuevo usuario con datos válidos
        Verifica que el usuario se crea correctamente
        """
        # Datos de usuario válidos
        user_data = {
            "contacto": "dev003",
            "nombre": "Juan Pérez"
        }
        
        # Realizar petición POST
        response = self.app.post('/usuarios', 
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['mensaje'], "Usuario creado exitosamente")
        self.assertEqual(response_data['id'], "dev003")
        
        # Verificar que el usuario se agregó
        self.assertEqual(len(self.mock_data_handler.users), 1)
        self.mock_data_handler.save_data.assert_called_once()

    def test_crear_usuario_alias_duplicado(self):
        """
        Caso de error: Intentar crear usuario con alias ya existente
        Verifica que se retorne error 400 cuando el alias ya está en uso
        """
        # Configurar usuario existente
        existing_user = {
            "id": "dev003",
            "nombre": "Usuario Existente"
        }
        self.mock_data_handler.users.append(existing_user)
        
        # Datos con alias duplicado
        user_data = {
            "contacto": "dev003",
            "nombre": "Nuevo Usuario"
        }
        
        # Realizar petición POST
        response = self.app.post('/usuarios', 
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        # Verificaciones
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], "El alias ya está en uso")
        
        # Verificar que no se agregó el usuario
        self.assertEqual(len(self.mock_data_handler.users), 1)
        self.mock_data_handler.save_data.assert_not_called()

    # ========== PRUEBAS PARA OBTENER USUARIO ==========
    
    def test_get_usuario_exitoso(self):
        """
        Caso de éxito: Obtener información de usuario existente con sus tareas
        Verifica que se retorne la información completa del usuario
        """
        # Configurar usuario existente
        user_alias = "dev001"
        existing_user = {
            "id": user_alias,
            "nombre": "Desarrollador Uno",
            "contacto": "dev001@empresa.com"
        }
        self.mock_data_handler.users.append(existing_user)
        
        # Configurar tarea asignada al usuario
        task_with_user = {
            "id": "task-123",
            "nombre": "Tarea asignada",
            "users": [{"usuario": user_alias, "rol": "programador"}]
        }
        self.mock_data_handler.tasks.append(task_with_user)
        
        # Realizar petición GET
        response = self.app.get(f'/usuarios/{user_alias}')
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['id'], user_alias)
        self.assertEqual(response_data['nombre'], "Desarrollador Uno")
        self.assertIn('tareas', response_data)
        self.assertEqual(len(response_data['tareas']), 1)
        self.assertEqual(response_data['tareas'][0]['id'], "task-123")

    def test_get_usuario_no_encontrado(self):
        """
        Caso de error: Intentar obtener información de usuario inexistente
        Verifica que se retorne error 404 cuando el usuario no existe
        """
        # Realizar petición GET para usuario inexistente
        response = self.app.get('/usuarios/usuario_inexistente')
        
        # Verificaciones
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], "Usuario no encontrado")

    # ========== PRUEBA PARA ENDPOINT DUMMY ==========
    
    def test_dummy_endpoint(self):
        """
        Caso de éxito: Verificar que el endpoint dummy funciona correctamente
        Prueba de conectividad básica de la API
        """
        # Realizar petición GET
        response = self.app.get('/dummy')
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], "This is a dummy endpoint!")


if __name__ == '__main__':
    # Configurar el runner de pruebas
    unittest.main(verbosity=2)