"""Adaptador SmtpEmailService: implementa IEmailService con SMTP y branding UTPL.

Envía correos HTML con la identidad visual de la UTPL (azul #003B71, naranja
#F39C12). Es el único punto del sistema que depende de smtplib.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from domain.ports.outbound.email_service import IEmailService

logger = logging.getLogger(__name__)

# Colores institucionales UTPL.
_AZUL = "#003B71"
_NARANJA = "#F39C12"


class SmtpEmailService(IEmailService):
    """Implementación de IEmailService basada en SMTP."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        from_email: str,
        from_name: str = "UTPL - Evaluación DigComp",
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from_email = from_email
        self._from_name = from_name

    # ------------------------------------------------------------------ #
    # API pública (IEmailService)
    # ------------------------------------------------------------------ #
    def send_verification_email(self, to_email: str, user_name: str, code: str) -> bool:
        body = self._code_template(
            title="Verifica tu cuenta",
            user_name=user_name,
            intro="Usa el siguiente código para verificar tu cuenta:",
            code=code,
            footer="El código expira en 15 minutos.",
        )
        return self._send(to_email, "Verificación de cuenta - UTPL DigComp", body)

    def send_password_reset_email(self, to_email: str, user_name: str, code: str) -> bool:
        body = self._code_template(
            title="Restablecer contraseña",
            user_name=user_name,
            intro="Usa el siguiente código para restablecer tu contraseña:",
            code=code,
            footer="Si no solicitaste este cambio, ignora este correo.",
        )
        return self._send(to_email, "Recuperación de contraseña - UTPL DigComp", body)

    def send_unlock_account_email(self, to_email: str, user_name: str, code: str) -> bool:
        body = self._code_template(
            title="Desbloquear cuenta",
            user_name=user_name,
            intro="Tu cuenta fue bloqueada por varios intentos fallidos. "
            "Usa este código para desbloquearla:",
            code=code,
            footer="El código expira en 15 minutos.",
        )
        return self._send(to_email, "Desbloqueo de cuenta - UTPL DigComp", body)

    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        body = self._wrap(
            title="¡Bienvenido/a!",
            inner=(
                f"<p>Hola <strong>{user_name}</strong>,</p>"
                "<p>Tu cuenta ha sido verificada correctamente. "
                "Ya puedes iniciar sesión en la plataforma de evaluación "
                "de competencias digitales DigComp 2.2.</p>"
            ),
        )
        return self._send(to_email, "Bienvenido/a - UTPL DigComp", body)

    # ------------------------------------------------------------------ #
    # Plantillas HTML
    # ------------------------------------------------------------------ #
    def _code_template(
        self, title: str, user_name: str, intro: str, code: str, footer: str
    ) -> str:
        inner = (
            f"<p>Hola <strong>{user_name}</strong>,</p>"
            f"<p>{intro}</p>"
            f'<div style="text-align:center;margin:32px 0;">'
            f'<span style="display:inline-block;font-size:34px;letter-spacing:10px;'
            f"font-weight:bold;color:{_AZUL};background:#F5F6FA;border:2px dashed "
            f'{_NARANJA};border-radius:10px;padding:16px 28px;">{code}</span></div>'
            f'<p style="color:#666;font-size:13px;">{footer}</p>'
        )
        return self._wrap(title=title, inner=inner)

    @staticmethod
    def _wrap(title: str, inner: str) -> str:
        """Envuelve el contenido en el layout HTML con branding UTPL."""
        return f"""\
<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#F5F6FA;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:560px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;
              box-shadow:0 2px 8px rgba(0,0,0,.08);">
    <div style="background:{_AZUL};padding:24px 32px;">
      <h1 style="margin:0;color:#fff;font-size:18px;">UTPL · Evaluación DigComp 2.2</h1>
    </div>
    <div style="padding:28px 32px;color:#222;font-size:15px;line-height:1.6;">
      <h2 style="color:{_AZUL};margin-top:0;">{title}</h2>
      {inner}
    </div>
    <div style="padding:16px 32px;background:#F0F2F5;color:#888;font-size:12px;text-align:center;">
      Universidad Técnica Particular de Loja · Este es un mensaje automático, no responder.
    </div>
  </div>
</body>
</html>"""

    # ------------------------------------------------------------------ #
    # Envío
    # ------------------------------------------------------------------ #
    def _send(self, to_email: str, subject: str, html_body: str) -> bool:
        """Envía un correo HTML vía SMTP (STARTTLS). Devuelve True si tuvo éxito."""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self._from_name} <{self._from_email}>"
        message["To"] = to_email
        message.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP(self._host, self._port, timeout=15) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._from_email, [to_email], message.as_string())
            logger.info("Correo enviado a %s (%s).", to_email, subject)
            return True
        except Exception:  # pragma: no cover - depende del entorno SMTP
            logger.exception("Fallo al enviar correo a %s.", to_email)
            return False
