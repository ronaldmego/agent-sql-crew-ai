# agents/schema_agent.py
from typing import Dict, Optional
import logging
from crewai import Agent
from config.config import get_agent_model
from src.utils.database import init_database, get_table_schema
from pydantic import PrivateAttr

logger = logging.getLogger(__name__)

class SchemaAgent(Agent):
    # Usar PrivateAttr para almacenar la db
    _db = PrivateAttr()
    
    def __init__(self):
        # Obtener configuración del modelo
        model_config = get_agent_model('schema')
        
        # Llamar al constructor de Agent primero
        super().__init__(
            role='Database Schema Analyst',
            goal='Analyze database structure and provide schema understanding',
            backstory="""You are an expert in database analysis who examines tables 
            and their relationships to understand patterns and suggest optimal query approaches.""",
            model=model_config['model'],
            verbose=True
        )
        
        # Inicializar la base de datos usando PrivateAttr
        self._db = init_database()

    def analyze_table(self, table_name: str) -> Dict:
        """Analiza la estructura y proporciona insights sobre la tabla"""
        try:
            # Obtener el esquema usando _db
            raw_schema = get_table_schema(self._db._engine, table_name)
            
            # Analizar columnas para determinar sus roles
            metrics = []
            dimensions = []
            temporal = []
            identifiers = []
            
            for col in raw_schema['columns']:
                col_type = str(col['type']).upper()
                col_name = col['name']
                
                if col_name in raw_schema.get('primary_key', []):
                    identifiers.append(col_name)
                elif 'INT' in col_type or 'FLOAT' in col_type or 'DOUBLE' in col_type or 'DECIMAL' in col_type:
                    metrics.append(col_name)
                elif 'DATE' in col_type or 'TIME' in col_type:
                    temporal.append(col_name)
                else:
                    dimensions.append(col_name)

            return {
                'table_name': table_name,
                'raw_schema': raw_schema,
                'column_roles': {
                    'metrics': metrics,
                    'dimensions': dimensions,
                    'temporal': temporal,
                    'identifiers': identifiers
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {str(e)}")
            raise