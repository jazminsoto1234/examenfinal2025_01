from flask import Flask, jsonify, request
from data_handler import DataHandler
from models.tarea import Tarea
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
    """
    Crea una nueva tarea
    Entrada esperada:
    {
        "nombre": "nombre de la tarea",
        "descripcion": "descripción de la tarea",
        "usuario": "alias",
        "rol": "programador|pruebas|infra"
    }
    """
    data = request.json
    if not all(k in data for k in ['nombre', 'descripcion', 'usuario', 'rol']):
        return jsonify({"error": "Faltan campos requeridos"}), 400
    
    if data['rol'] not in ['programador', 'pruebas', 'infra']:
        return jsonify({"error": "Rol no válido"}), 400

    task_id = str(uuid.uuid4())
    tarea = Tarea(task_id, data['nombre'], data['descripcion'])
    tarea.add_user(data['usuario'], data['rol'])
    
    data_handler.tasks.append(tarea.__dict__)
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

    if data['accion'] == 'adicionar':
        if not any(u['usuario'] == data['usuario'] and u['rol'] == data['rol'] for u in tarea['users']):
            tarea['users'].append({"usuario": data['usuario'], "rol": data['rol']})
    else:
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

if __name__ == '__main__':
    app.run(debug=True)