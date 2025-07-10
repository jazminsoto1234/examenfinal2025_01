class Usuario:
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email
        self.contactos = []
        self.tareas = []

    def add_contacto(self, contacto):
        if contacto not in self.contactos:
            self.contactos.append(contacto)

    def get_user_info(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "contactos": self.contactos,
            "tareas": self.tareas
        }