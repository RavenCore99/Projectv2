import re

class AutomataValidador:
    _re_nit = re.compile(r"^\d{6,10}-\d$")
    _re_fecha = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
    _re_valor = re.compile(r"^\d+(\.\d{1,2})?$")
    _re_usuario = re.compile(r"^[a-zA-Z0-9_]{4,20}$")

    @staticmethod
    def nit(nit: str) -> bool:
        return bool(AutomataValidador._re_nit.fullmatch(nit))

    @staticmethod
    def fecha(fecha: str) -> bool:
        return bool(AutomataValidador._re_fecha.fullmatch(fecha))

    @staticmethod
    def valor(valor: str) -> bool:
        return bool(AutomataValidador._re_valor.fullmatch(valor))

    @staticmethod
    def usuario(usuario: str) -> bool:
        return bool(AutomataValidador._re_usuario.fullmatch(usuario))