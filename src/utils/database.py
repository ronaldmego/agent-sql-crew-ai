import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, MetaData
from typing import List, Optional, Dict
import logging
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def init_database():
    """Inicializar conexión a la base de datos"""
    load_dotenv()
    mysql_user = os.getenv('MYSQL_USER')
    mysql_password = os.getenv('MYSQL_PASSWORD')
    mysql_host = os.getenv('MYSQL_HOST')
    mysql_database = os.getenv('MYSQL_DATABASE')
    mysql_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_database}"
    return SQLDatabase.from_uri(mysql_uri)

def get_table_names(engine) -> List[str]:
    """Obtener lista de tablas de la base de datos"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return tables
    except Exception as e:
        logger.error(f"Error getting table names: {str(e)}")
        return []

def get_table_schema(engine, table_name: str) -> Dict:
    """Obtener esquema de una tabla específica"""
    try:
        inspector = inspect(engine)
        metadata = MetaData()
        metadata.reflect(bind=engine, only=[table_name])
        
        table = metadata.tables[table_name]
        
        # Obtener información de columnas
        columns = inspector.get_columns(table_name)
        
        # Obtener pk_constraint que incluye primary keys
        pk_constraint = inspector.get_pk_constraint(table_name)
        primary_keys = pk_constraint['constrained_columns'] if pk_constraint else []
        
        # Obtener foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        return {
            'columns': columns,
            'primary_key': primary_keys,
            'foreign_keys': foreign_keys,
            'table': table
        }
    except Exception as e:
        logger.error(f"Error getting schema for table {table_name}: {str(e)}")
        return {}