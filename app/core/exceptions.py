class AppError(Exception):
    """Base de todas las excepciones de dominio."""
    pass

class NotFoundError(AppError):
    def __init__(self, entity: str, entity_id: int | str):
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} with id={entity_id} not found or inactive")

class AlreadyExistsError(AppError):
    def __init__(self, entity: str, field: str, value: str):
        self.entity = entity
        self.field = field
        self.value = value
        super().__init__(f"{entity} with {field}='{value}' already exists")
