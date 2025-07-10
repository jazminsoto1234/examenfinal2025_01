class Tarea:
    def __init__(self, id, title, description, status='pending'):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.users = []
        self.dependencies = [] # Lista de IDs de tareas dependientes

    def mark_complete(self):
        self.status = 'completed'

    def update_status(self, new_status):
        self.status = new_status
        return True

    def add_user(self, usuario, rol):
        self.users.append({"usuario": usuario, "rol": rol})

    def remove_user(self, usuario, rol):
        self.users = [u for u in self.users if not (u["usuario"] == usuario and u["rol"] == rol)]

    def add_dependency(self, task_id):
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def remove_dependency(self, task_id):
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)