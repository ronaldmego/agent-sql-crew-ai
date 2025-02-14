import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, MetaData
from typing import List, Optional, Dict
import logging
from crewai_tools import MySQLSearchTool, NL2SQLTool

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def get_mysql_uri() -> str:
    """Obtener URI de conexión MySQL desde variables de entorno"""
    try:
        MYSQL_USER = os.getenv('MYSQL_USER')
        MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
        MYSQL_HOST = os.getenv('MYSQL_HOST')
        MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
        
        if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE]):
            raise ValueError("Missing required database configuration in .env file")
        
        return f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}'
    
    except Exception as e:
        logger.error(f"Error getting MySQL URI: {str(e)}")
        raise

def get_crewai_tools(table_name: Optional[str] = None) -> List:
    """Obtener las herramientas de CrewAI configuradas para MySQL"""
    try:
        # Obtener el URI de conexión
        db_uri = get_mysql_uri()
        
        tools = []
        
        # Crear NL2SQLTool con el URI completo
        nl2sql_tool = NL2SQLTool(db_uri=db_uri)
        tools.append(nl2sql_tool)
        
        # Si se especifica una tabla, agregar MySQLSearchTool
        if table_name:
            mysql_search = MySQLSearchTool(
                db_uri=db_uri,
                table_name=table_name
            )
            tools.append(mysql_search)
        
        return tools
        
    except Exception as e:
        logger.error(f"Error configuring CrewAI tools: {str(e)}")
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