# agents/schema_agent.py
from typing import Dict, Optional
import logging
import pandas as pd
from crewai import Agent
from config.config import get_agent_model
from src.utils.database import init_database, get_table_schema

logger = logging.getLogger(__name__)

class SchemaAgent:
    def __init__(self):
        try:
            # Inicializar la base de datos
            self.db = init_database()
            if not self.db:
                raise ValueError("Database initialization failed")
            
            # Configuración del modelo
            model_config = get_agent_model('schema')
            
            # Crear el agente base
            self.agent = Agent(
                role='Database Schema Analyst',
                goal='Analyze database structure and provide schema understanding',
                backstory="""You are an expert in database analysis who examines tables 
                and their relationships to understand patterns and suggest optimal query approaches.""",
                model=model_config['model'],
                verbose=True
            )
            
        except Exception as e:
            logger.error(f"Error initializing SchemaAgent: {str(e)}")
            raise

    def analyze_table(self, table_name: str) -> Dict:
        """Analiza la estructura y proporciona insights sobre la tabla"""
        try:
            # Obtener el esquema crudo primero
            raw_schema = get_table_schema(self.db._engine, table_name)  # Esta es la estructura original
            
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

            # Enriquecer el análisis
            analysis = {
                'table_name': table_name,
                'raw_schema': raw_schema,  # Incluimos el esquema crudo
                'structure': {
                    'columns': raw_schema['columns'],
                    'primary_keys': raw_schema.get('primary_key', []),
                    'foreign_keys': raw_schema.get('foreign_keys', [])
                },
                'column_roles': {
                    'metrics': metrics,
                    'dimensions': dimensions,
                    'temporal': temporal,
                    'identifiers': identifiers
                },
                'suggested_queries': {
                    'aggregations': [
                        f"SUM({metric})" for metric in metrics
                    ],
                    'grouping': dimensions,
                    'time_analysis': temporal
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {str(e)}")
            raise

    def __getattr__(self, name):
        """Delegate unknown attributes to the agent"""
        return getattr(self.agent, name)