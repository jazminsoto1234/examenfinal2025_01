class Asignacion:
    def __init__(self, task_id, user_id):
        self.task_id = task_id
        self.user_id = user_id
        self.estado = "activo"  # Para tracking del estado de la asignación
        self.fecha_asignacion = None
        self.rol = None

    def set_rol(self, rol):
        """Establece el rol del usuario en la asignación"""
        if rol in ['programador', 'pruebas', 'infra']:
            self.rol = rol
            return True
        return False

    def desactivar(self):
        """Marca la asignación como inactiva"""
        self.estado = "inactivo"

    def get_assignment_details(self):
        """Retorna los detalles completos de la asignación"""
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "estado": self.estado,
            "rol": self.rol,
            "fecha_asignacion": self.fecha_asignacion
        }