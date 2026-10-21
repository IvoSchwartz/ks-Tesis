"""Error de regla de negocio: se convierte en una respuesta JSON con mensaje en español."""


class ErrorNegocio(Exception):
    def __init__(self, estado: int, mensaje: str):
        super().__init__(mensaje)
        self.estado = estado
        self.mensaje = mensaje
