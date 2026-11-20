"""
users/brevo_service.py — Servicio de correos transaccionales vía Brevo API v3.
Plataforma: Literatus Novelist Infantil.
"""
import os
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def build_registration_html(recipient_name: str, verify_url: str) -> str:
    """
    Genera una plantilla HTML amigable, atractiva y responsiva
    diseñada para la plataforma Literatus Novelist Infantil.
    """
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmación de Registro - Literatus Novelist Infantil</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 10px;">
        <tr>
            <td align="center">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);">
                    <!-- Cabecera Temática Infantil -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%); padding: 36px 20px; text-align: center;">
                            <div style="font-size: 40px; line-height: 1; margin-bottom: 8px;">🏰 ✨ 📖</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 800; letter-spacing: 0.5px;">Literatus Novelist</h1>
                            <p style="margin: 4px 0 0 0; color: #fdf2f8; font-size: 15px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;">Mundo Infantil</p>
                        </td>
                    </tr>
                    <!-- Contenido Principal -->
                    <tr>
                        <td style="padding: 36px 32px;">
                            <h2 style="margin-top: 0; margin-bottom: 16px; color: #0f172a; font-size: 22px; font-weight: 700;">¡Hola, {recipient_name}! 🌟</h2>
                            <p style="font-size: 16px; line-height: 1.7; color: #334155; margin-bottom: 20px;">
                                ¡Qué alegría tenerte con nosotros! Te damos la bienvenida a <strong>Literatus Novelist Infantil</strong>, el rincón donde los libros cobran vida.
                            </p>
                            <p style="font-size: 15px; line-height: 1.7; color: #475569; margin-bottom: 28px;">
                                Estás a un solo paso de explorar cuentos mágicos, divertirte con minijuegos interactivos y conversar con los personajes de tus historias favoritas. Para activar tu cuenta, confirma tu correo electrónico:
                            </p>
                            <!-- Botón de Confirmación -->
                            <div style="text-align: center; margin: 32px 0;">
                                <a href="{verify_url}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 700; padding: 14px 34px; border-radius: 50px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4); text-transform: uppercase; letter-spacing: 0.5px;">
                                    🚀 Confirmar mi registro
                                </a>
                            </div>
                            <!-- Enlace Alternativo de Respaldo -->
                            <div style="background-color: #f1f5f9; border-radius: 8px; padding: 16px; margin-top: 28px;">
                                <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b; font-weight: 600;">¿El botón no funciona? Copia y pega este enlace en tu navegador:</p>
                                <a href="{verify_url}" target="_blank" style="font-size: 12px; color: #6366f1; word-break: break-all; text-decoration: underline;">{verify_url}</a>
                            </div>
                        </td>
                    </tr>
                    <!-- Pie de Página -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 32px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 6px 0; font-size: 12px; color: #94a3b8;">
                                Si no creaste una cuenta en Literatus Novelist Infantil, puedes ignorar este mensaje de forma segura.
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #cbd5e1;">
                                &copy; Literatus Novelist Infantil — Fomentando la magia de la lectura
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def send_registration_email(user, verify_url: str | None = None) -> dict:
    """
    Envía el correo de confirmación de registro utilizando la API v3 de Brevo.
    
    Args:
        user: Instancia del modelo User o entidad que contenga 'email' y 'username'.
        verify_url: URL opcional de confirmación. Si no se provee, se genera
                    automáticamente con el token de verificación y la URL del frontend.

    Returns:
        dict: Respuesta en formato JSON devuelta por Brevo con el 'messageId'.
    """
    # 1. Configuración de Entorno
    api_key = getattr(settings, 'BREVO_API_KEY', '') or os.environ.get('BREVO_API_KEY', '')
    if not api_key:
        error_msg = "BREVO_API_KEY no está configurada en settings ni en .env."
        logger.error(f"❌ [Brevo Service] {error_msg}")
        raise ValueError(error_msg)

    sender_email = (
        getattr(settings, 'BREVO_SENDER_EMAIL', '') or
        os.environ.get('BREVO_SENDER_EMAIL', '') or
        getattr(settings, 'DEFAULT_FROM_EMAIL', '') or
        'no-reply@literatusnovelist.com'
    )
    sender_name = (
        getattr(settings, 'BREVO_SENDER_NAME', '') or
        os.environ.get('BREVO_SENDER_NAME', '') or
        'Literatus Novelist Infantil'
    )

    # 2. Obtención de datos del destinatario
    recipient_email = getattr(user, 'email', str(user))
    recipient_name = (
        (getattr(user, 'get_full_name', lambda: '')() or getattr(user, 'username', 'Lector'))
    ).strip()

    # 3. Generación automática del enlace de confirmación si no se suministró
    if not verify_url:
        from .utils import email_verification_token
        uid = str(user.pk).strip()
        token = email_verification_token.make_token(user)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:4200').rstrip('/')
        verify_url = f"{frontend_url}/verify-email?uid={uid}&token={token}"

    logger.info(f"🔗 [Brevo Service] Enlace de confirmación generado para {recipient_email}: {verify_url}")

    # 4. Formateo de Payload y Headers según especificación de Brevo API v3
    subject = "¡Bienvenido a Literatus Novelist Infantil! Confirma tu registro"
    html_content = build_registration_html(recipient_name, verify_url)

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": recipient_email,
                "name": recipient_name
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    # 5. Petición HTTP POST al endpoint de Brevo
    try:
        response = requests.post(
            BREVO_API_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
    except requests.RequestException as exc:
        logger.error(f"❌ [Brevo Service] Error de conexión al invocar Brevo API para {recipient_email}: {exc}")
        raise

    if response.status_code in (200, 201):
        result = response.json()
        logger.info(f"✅ [Brevo Service] Correo de registro enviado exitosamente a {recipient_email}. ID: {result.get('messageId')}")
        return result
    else:
        error_detail = response.text
        logger.error(
            f"❌ [Brevo Service] Falló el envío a {recipient_email}. "
            f"Código HTTP: {response.status_code} - Detalle: {error_detail}"
        )
        raise RuntimeError(f"Error Brevo API ({response.status_code}): {error_detail}")


# Alias con nomenclatura camelCase para compatibilidad
sendRegistrationEmail = send_registration_email

