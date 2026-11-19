"""Permite autenticación por correo sin reemplazar AUTH_USER_MODEL ni perder cuentas."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CorreoOUsuarioBackend(ModelBackend):
    """Correo para el portal; usuario tradicional para compatibilidad con Django Admin."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email') or kwargs.get('identificador')
        if not isinstance(username, str) or password is None:
            return None
        identificador = username.strip()
        if not identificador:
            return None
        Usuario = get_user_model()
        usuario = None
        if '@' in identificador:
            coincidencias = list(Usuario._default_manager.filter(email__iexact=identificador)[:2])
            if len(coincidencias) == 1:
                usuario = coincidencias[0]
            elif len(coincidencias) > 1:
                # No autenticar correos ambiguos que ya pudieran existir con distinta capitalización.
                return None
        if usuario is None:
            try:
                usuario = Usuario._default_manager.get_by_natural_key(identificador)
            except Usuario.DoesNotExist:
                # Mantiene un coste de hashing para identificadores inexistentes.
                Usuario().set_password(password)
                return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
