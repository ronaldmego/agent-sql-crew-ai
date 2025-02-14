import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from typing import List
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def get_mysql_uri() -> str:
    """Obtener URI de conexión MySQL desde variables de entorno"""
    try:
        # Obtener credenciales de las variables de entorno
        MYSQL_USER = os.getenv('MYSQL_USER')
        MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
        MYSQL_HOST = os.getenv('MYSQL_HOST')
        MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
        
        if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE]):
            raise ValueError("Missing required database configuration in .env file")
        
        # Construir URI de conexión
        return f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}'
    
    except Exception as e:
        logger.error(f"Error getting MySQL URI: {str(e)}")
        raise

def get_table_names(engine) -> List[str]:
    """Obtener lista de tablas de la base de datos"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return tables
    except Exception as e:
        logger.error(f"Error getting table names: {str(e)}")
        return []

def get_table_schema(engine, table_name: str) -> dict:
    """Obtener esquema de una tabla específica"""
    try:
        inspector = inspect(engine)
        return {
            'columns': inspector.get_columns(table_name),
            'primary_key': inspector.get_primary_keys(table_name),
            'foreign_keys': inspector.get_foreign_keys(table_name)
        }
    except Exception as e:
        logger.error(f"Error getting schema for table {table_name}: {str(e)}")
        return {}

def execute_query(engine, query: str) -> List[tuple]:
    """Ejecutar una consulta SQL y retornar resultados"""
    try:
        with engine.connect() as connection:
            result = connection.execute(query)
            return result.fetchall()
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise

def test_connection(engine) -> bool:
    """Probar la conexión a la base de datos"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False