import os
import requests
from django.conf import settings
from .models import ChatMessage

class AIService:
    def __init__(self, avatar, session):
        self.avatar = avatar
        self.session = session
        self.openrouter_key = getattr(settings, 'OPENROUTER_API_KEY', os.environ.get('OPENROUTER_API_KEY'))
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def generate_reply(self, new_message_content):
        if not self.openrouter_key:
            return {
                "text": "Error: Falta OPENROUTER_API_KEY en el .env",
                "provider": "none",
                "cost": 0,
                "status": "error"
            }
        try:
            text = self._call_openrouter(new_message_content)
            return {
                "text": text,
                "provider": "openrouter",
                "cost": 1,
                "status": "ok"
            }
        except Exception as e:
            print(f"OpenRouter failed: {e}")
            return {
                "text": "Lo siento, mi conexión con el mundo espiritual está débil ahora mismo. (Error de API)",
                "provider": "none",
                "cost": 0,
                "status": "error"
            }

    def _call_openrouter(self, content):
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://literatus.app",
            "X-Title": "Literatus Novelist"
        }
        # Priorizamos 'openrouter/free' ya que enruta automáticamente al modelo gratuito activo y funcional
        models_to_try = [
            "openrouter/free",
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-3-8b-instruct:free"
        ]
        messages = [{"role": "system", "content": self._build_system_prompt()}]
        
        # Historial de la sesión
        history = self.session.messages.order_by('-created_at')[:10]
        for msg in reversed(list(history)):
            role = "user" if msg.role == ChatMessage.RoleChoices.USER else "assistant"
            messages.append({"role": role, "content": msg.content})
        messages.append({"role": "user", "content": content})

        last_error = None
        for model in models_to_try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": float(self.avatar.temperature)
            }
            try:
                response = requests.post(self.url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
                else:
                    last_error = f"Modelo {model} falló: {response.status_code}"
                    print(last_error)
            except Exception as e:
                last_error = str(e)
                print(f"Excepción con {model}: {e}")
        raise Exception(last_error or "Todos los modelos fallaron")

    def _build_system_prompt(self):
        base_prompt = f"Eres {self.avatar.name}. \n\nDirectrices:\n{self.avatar.system_prompt}\n"
        if getattr(self.avatar, 'behavioral_context', None):
            base_prompt += f"\nContexto emocional:\n{self.avatar.behavioral_context}\n"
        base_prompt += "\nREGLA: No digas que eres IA. Mantén la inmersión total."
        return base_prompt
