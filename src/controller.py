from flask import Flask, jsonify, request
from data_handler import DataHandler
from models.tarea import Tarea
from models.usuario import Usuario
from models.asignacion import Asignacion

import uuid

app = Flask(__name__)
data_handler = DataHandler()

class ControladorTareas:
    def __init__(self, data_handler):
        self.data_handler = data_handler

@app.route('/dummy', methods=['GET'])
def dummy_endpoint():
    # Example dummy response
    return jsonify({"message": "This is a dummy endpoint!"})

@app.route('/tasks', methods=['POST'])
def crear_tarea():
    # ...existing code...
    
    task_id = str(uuid.uuid4())
    tarea = Tarea(task_id, data['nombre'], data['descripcion'])
    
    # Crear asignación al crear la tarea
    asignacion = Asignacion(task_id, data['usuario'])
    tarea.add_user(data['usuario'], data['rol'])
    
    # Convertir a diccionario y agregar detalles de asignación
    tarea_dict = tarea.__dict__
    if 'users' in tarea_dict and tarea_dict['users']:
        for user in tarea_dict['users']:
            user.update(asignacion.get_assignment_details())
    
    data_handler.tasks.append(tarea_dict)
    data_handler.save_data()
    
    return jsonify({"id": task_id}), 201


@app.route('/tasks/<task_id>', methods=['POST'])
def actualizar_estado_tarea(task_id):
    """
    Actualiza el estado de una tarea
    Entrada esperada:
    {
        "estado": "nuevo_estado"
    }
    """
    data = request.json
    if 'estado' not in data:
        return jsonify({"error": "Falta el campo estado"}), 400

    tarea = next((t for t in data_handler.tasks if t['id'] == task_id), None)
    if not tarea:
        return jsonify({"error": "Tarea no encontrada"}), 404

    tarea['status'] = data['estado']
    data_handler.save_data()
    
    return jsonify({"mensaje": "Estado actualizado exitosamente"}), 200

@app.route('/tasks/<task_id>/users', methods=['POST'])
def gestionar_usuarios_tarea(task_id):
    """
    Gestiona usuarios de una tarea
    Entrada esperada:
    {
        "usuario": "alias",
        "rol": "programador|pruebas|infra",
        "accion": "adicionar|remover"
    }
    """
    data = request.json
    if not all(k in data for k in ['usuario', 'rol', 'accion']):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    if data['rol'] not in ['programador', 'pruebas', 'infra']:
        return jsonify({"error": "Rol no válido"}), 400

    if data['accion'] not in ['adicionar', 'remover']:
        return jsonify({"error": "Acción no válida"}), 400

    tarea = next((t for t in data_handler.tasks if t['id'] == task_id), None)
    if not tarea:
        return jsonify({"error": "Tarea no encontrada"}), 404

    # Crear asignación
    if data['accion'] == 'adicionar':
        asignacion = Asignacion(task_id, data['usuario'])
        if 'users' not in tarea:
            tarea['users'] = []
        tarea['users'].append({
            "usuario": data['usuario'], 
            "rol": data['rol'],
            **asignacion.get_assignment_details()
        })
    else:
        if 'users' in tarea:
            tarea['users'] = [u for u in tarea['users'] 
                            if not (u['usuario'] == data['usuario'] and u['rol'] == data['rol'])]

    data_handler.save_data()
    return jsonify({"mensaje": "Usuarios actualizados exitosamente"}), 200


@app.route('/tasks/<task_id>/dependencies', methods=['POST'])
def gestionar_dependencias_tarea(task_id):
    """
    Gestiona dependencias de una tarea
    Entrada esperada:
    {
        "dependencytaskid": "id_tarea_dependencia",
        "accion": "adicionar|remover"
    }
    """
    data = request.json
    if not all(k in data for k in ['dependencytaskid', 'accion']):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    if data['accion'] not in ['adicionar', 'remover']:
        return jsonify({"error": "Acción no válida"}), 400

    tarea = next((t for t in data_handler.tasks if t['id'] == task_id), None)
    if not tarea:
        return jsonify({"error": "Tarea no encontrada"}), 404

    tarea_dependencia = next((t for t in data_handler.tasks if t['id'] == data['dependencytaskid']), None)
    if not tarea_dependencia:
        return jsonify({"error": "Tarea dependiente no encontrada"}), 404

    if data['accion'] == 'adicionar':
        if data['dependencytaskid'] not in tarea.get('dependencies', []):
            if 'dependencies' not in tarea:
                tarea['dependencies'] = []
            tarea['dependencies'].append(data['dependencytaskid'])
    else:
        if 'dependencies' in tarea and data['dependencytaskid'] in tarea['dependencies']:
            tarea['dependencies'].remove(data['dependencytaskid'])
    
    data_handler.save_data()
    return jsonify({"mensaje": "Dependencias actualizadas exitosamente"}), 200




@app.route('/usuarios/<alias>', methods=['GET'])
def get_usuario(alias):
    """
    Obtiene información del usuario y sus tareas asignadas
    """
    usuario = next((u for u in data_handler.users if u['id'] == alias), None)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Buscar tareas asignadas al usuario
    tareas_usuario = [
        t for t in data_handler.tasks 
        if any(u['usuario'] == alias for u in t['users'])
    ]
    
    response = usuario.copy()
    response['tareas'] = tareas_usuario
    return jsonify(response)

@app.route('/usuarios', methods=['POST'])
def crear_usuario():
    """
    Crea un nuevo usuario
    Entrada esperada:
    {
        "contacto": "alias del contacto",
        "nombre": "nombre del usuario"
    }
    """
    data = request.json
    if not all(k in data for k in ['contacto', 'nombre']):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    # Verificar si el usuario ya existe
    if any(u['id'] == data['contacto'] for u in data_handler.users):
        return jsonify({"error": "El alias ya está en uso"}), 400

    nuevo_usuario = Usuario(data['contacto'], data['nombre'], None)
    data_handler.users.append(nuevo_usuario.get_user_info())
    data_handler.save_data()
    
    return jsonify({"mensaje": "Usuario creado exitosamente", "id": data['contacto']}), 201




if __name__ == '__main__':
    app.run(debug=True)