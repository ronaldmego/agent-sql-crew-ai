# config/config.py

from dotenv import load_dotenv
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

load_dotenv()

class Config:
    @staticmethod
    def get_env(key: str, default: str = None) -> str:
        """Obtiene variable de entorno con valor por defecto"""
        return os.getenv(key, default)

# Database Config
MYSQL_USER = Config.get_env("MYSQL_USER")
MYSQL_PASSWORD = Config.get_env("MYSQL_PASSWORD")
MYSQL_HOST = Config.get_env("MYSQL_HOST")
MYSQL_DATABASE = Config.get_env("MYSQL_DATABASE")

# Agent Models Config (Principales y por defecto)
SCHEMA_AGENT_MODEL = Config.get_env("SCHEMA_AGENT_MODEL", "gpt-4o-mini")
SQL_AGENT_MODEL = Config.get_env("SQL_AGENT_MODEL", "gpt-4o-mini")
VIZ_AGENT_MODEL = Config.get_env("VIZ_AGENT_MODEL", "gpt-4o-mini")
EXPLAIN_AGENT_MODEL = Config.get_env("EXPLAIN_AGENT_MODEL", "gpt-4o-mini")

# OpenAI Config
OPENAI_API_KEY = Config.get_env("OPENAI_API_KEY")

# Ollama Config (para modelos locales)
OLLAMA_BASE_URL = Config.get_env("OLLAMA_BASE_URL", "http://localhost:11434")

def get_agent_model(agent_type: str) -> Dict[str, str]:
    """
    Obtiene la configuración del modelo para un tipo específico de agente
    
    Args:
        agent_type: Tipo de agente ('schema', 'sql', 'viz', 'explain')
    
    Returns:
        Dict con provider y nombre del modelo
    """
    model_mapping = {
        'schema': SCHEMA_AGENT_MODEL,
        'sql': SQL_AGENT_MODEL,
        'viz': VIZ_AGENT_MODEL,
        'explain': EXPLAIN_AGENT_MODEL
    }
    
    model = model_mapping.get(agent_type)
    if not model:
        raise ValueError(f"Tipo de agente no válido: {agent_type}")
    
    # Determinar si es un modelo de OpenAI o local
    if model.startswith('gpt'):
        return {
            'provider': 'openai',
            'model': model
        }
    else:
        return {
            'provider': 'ollama',
            'model': model
        }

# Database Connection String
def get_mysql_uri() -> str:
    """Retorna el URI de conexión para MySQL"""
    return f'mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}'