"""Conector unificado para IA local (Ollama) y BYO-key (APIs externas).

Adaptado del clon local de GenOffice (backend/ai_gateway.py), con correcciones:
- URL nativa de Ollama correcta (`/api/generate`, base sin `/v1`).
- Proveedores externos reales: OpenAI (chat completions), Anthropic (messages)
  y Google Gemini (generateContent) vía `requests`.
- `check_availability` intacto (patrón del clon).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AIConnector:
    """Conector unificado para múltiples proveedores de IA."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.local_client = None
        self.external_client = None

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Carga configuración de proveedores de IA."""
        default_config = {
            "local": {
                "enabled": True,
                "base_url": "http://localhost:11434",
                "default_model": "llama3",
                "available_models": ["llama3", "mistral", "phi3"],
            },
            "external": {
                "enabled": False,
                "providers": {
                    "openai": {"api_key": "", "model": "gpt-4o"},
                    "gemini": {"api_key": "", "model": "gemini-1.5-pro"},
                    "anthropic": {"api_key": "", "model": "claude-3-opus"},
                },
            },
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                if "local" in user_config:
                    default_config["local"].update(user_config["local"])
                if "external" in user_config:
                    externa = user_config["external"]
                    if isinstance(externa, dict):
                        if "enabled" in externa:
                            default_config["external"]["enabled"] = externa["enabled"]
                        proveedores = externa.get("providers", {})
                        for nombre, datos in proveedores.items():
                            default_config["external"]["providers"].setdefault(nombre, {})
                            default_config["external"]["providers"][nombre].update(datos)
            return default_config

        return default_config

    # ------------------------------------------------------------------
    # Generación
    # ------------------------------------------------------------------
    def generate_text(self, prompt: str, model: Optional[str] = None,
                      use_local: bool = True, **kwargs) -> str:
        """Genera texto con el proveedor especificado (local primero por defecto)."""
        model = model or self.config["local"]["default_model"]

        if use_local and self.config["local"].get("enabled", True):
            return self._generate_local(prompt, model, kwargs)

        externa = self.config["external"]
        if externa.get("enabled"):
            for nombre, prov in externa.get("providers", {}).items():
                if str(prov.get("api_key", "")).strip():
                    return self._generate_external(prompt, nombre, prov, kwargs)
            return "[Error: IA externa habilitada pero sin claves configuradas]"

        # Sin proveedor externo habilitado: reintenta local aunque use_local=False
        return self._generate_local(prompt, model, kwargs)

    def _generate_local(self, prompt: str, model: str, kwargs: Dict) -> str:
        """Genera texto usando Ollama local (API nativa /api/generate)."""
        import requests

        base_url = str(self.config["local"]["base_url"]).rstrip("/")
        payload = {"model": model, "prompt": prompt, "stream": False, **kwargs}
        try:
            response = requests.post(f"{base_url}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error("Error en generación local: %s", e)
            return f"[Error en modelo local: {str(e)}]"

    def _generate_external(self, prompt: str, proveedor: str,
                           prov: Dict[str, Any], kwargs: Dict) -> str:
        """Genera texto con una API externa BYO-key (OpenAI/Anthropic/Gemini)."""
        import requests

        clave = str(prov.get("api_key", "")).strip()
        modelo = prov.get("model", "")
        temperature = kwargs.get("temperature", 0.3)
        try:
            if proveedor == "openai":
                respuesta = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {clave}"},
                    json={"model": modelo or "gpt-4o",
                          "messages": [{"role": "user", "content": prompt}],
                          "temperature": temperature},
                    timeout=120,
                )
                respuesta.raise_for_status()
                return respuesta.json()["choices"][0]["message"]["content"]

            if proveedor == "anthropic":
                respuesta = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": clave, "anthropic-version": "2023-06-01"},
                    json={"model": modelo or "claude-3-opus",
                          "max_tokens": 2048,
                          "messages": [{"role": "user", "content": prompt}]},
                    timeout=120,
                )
                respuesta.raise_for_status()
                return respuesta.json()["content"][0]["text"]

            if proveedor == "gemini":
                respuesta = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{modelo or 'gemini-1.5-pro'}:generateContent?key={clave}",
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=120,
                )
                respuesta.raise_for_status()
                return respuesta.json()["candidates"][0]["content"]["parts"][0]["text"]

            return f"[Error: proveedor externo «{proveedor}» no soportado]"
        except Exception as e:
            logger.error("Error en generación externa (%s): %s", proveedor, e)
            return f"[Error en proveedor externo {proveedor}: {str(e)}]"

    # ------------------------------------------------------------------
    # Utilidades del clon (API compatible)
    # ------------------------------------------------------------------
    def enhance_markdown(self, markdown: str, operation: str = "improve",
                         model: Optional[str] = None) -> str:
        """Mejora o reescribe contenido Markdown usando IA."""
        prompt = self._build_enhancement_prompt(markdown, operation)
        return self.generate_text(prompt, model=model)

    def _build_enhancement_prompt(self, markdown: str, operation: str) -> str:
        """Construye el prompt según la operación solicitada."""
        base_prompt = (
            "Eres un asistente de redacción técnico. "
            "Mejora el siguiente contenido Markdown manteniendo el significado "
            "original pero mejorando la claridad, estructura y profesionalismo.\n\n"
            "Contenido original:\n"
        )
        return base_prompt + "\n\n" + markdown

    def check_availability(self) -> Dict[str, bool]:
        """Verifica qué proveedores de IA están disponibles."""
        result = {"local": False, "external": False}

        import requests
        try:
            base_url = str(self.config["local"]["base_url"]).rstrip("/")
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                result["local"] = True
        except Exception:
            pass

        has_keys = any(
            provider.get("api_key", "").strip()
            for provider in self.config["external"]["providers"].values()
        )
        result["external"] = has_keys

        return result
