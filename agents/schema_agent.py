# agents/schema_agent.py
from typing import Dict, Optional
import logging
import pandas as pd
import numpy as np
from crewai import Agent
from config.config import get_agent_model
from src.utils.database import init_database, get_table_schema

logger = logging.getLogger(__name__)

def convert_sqlalchemy_type(sql_type):
    """Convert SQLAlchemy types to Python types"""
    type_str = str(sql_type).upper()
    if 'INT' in type_str:
        return np.int64
    elif 'FLOAT' in type_str or 'DOUBLE' in type_str or 'DECIMAL' in type_str:
        return np.float64
    elif 'DATETIME' in type_str:
        return 'datetime64[ns]'
    else:
        return str

class SchemaAgent:
    """Schema Agent for analyzing database structure"""
    
    def __init__(self, table_name: Optional[str] = None):
        """Initialize the Schema Agent"""
        try:
            # Get model configuration
            model_config = get_agent_model('schema')
            
            # Initialize the database connection
            self.db = init_database()
            logger.info("Database connection initialized successfully")
            
            # Create the base agent
            self.agent = Agent(
                role='Database Schema Analyst',
                goal='Analyze database structure and provide clear schema understanding',
                backstory="""You are an expert in database analysis who examines tables 
                and understands their structure, identifying patterns and relationships in the data.""",
                model=model_config['model'],
                verbose=True
            )
            
        except Exception as e:
            logger.error(f"Error initializing SchemaAgent: {str(e)}")
            raise
    
    def analyze_table(self, table_name: str) -> Dict:
        """
        Analiza la estructura y contenido de una tabla
        
        Args:
            table_name: Nombre de la tabla a analizar
            
        Returns:
            Dict con información relevante de la tabla
        """
        try:
            # Obtener información del esquema
            schema_info = get_table_schema(self.db._engine, table_name)
            
            # Obtener una muestra pequeña de datos con tipos correctos
            try:
                query = f"SELECT * FROM {table_name} LIMIT 5"
                sample_df = pd.read_sql(query, self.db._engine)
                
                # Convertir tipos de datos
                for col in schema_info['columns']:
                    col_name = col['name']
                    if col_name in sample_df.columns:
                        py_type = convert_sqlalchemy_type(col['type'])
                        try:
                            sample_df[col_name] = sample_df[col_name].astype(py_type)
                        except (ValueError, TypeError):
                            # Si la conversión falla, mantener como string
                            sample_df[col_name] = sample_df[col_name].astype(str)
                
            except Exception as e:
                logger.warning(f"Could not get sample data: {str(e)}")
                sample_df = None
            
            # Preparar información de columnas
            columns_data = []
            for col in schema_info['columns']:
                column_info = {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col.get('nullable', True)
                }
                
                if schema_info.get('primary_key'):
                    column_info['primary_key'] = col['name'] in schema_info['primary_key']
                
                if schema_info.get('foreign_keys'):
                    column_info['foreign_key'] = any(
                        col['name'] in fk['constrained_columns'] 
                        for fk in schema_info['foreign_keys']
                    )
                
                columns_data.append(column_info)
            
            # Generar análisis usando el LLM
            analysis_prompt = f"""
            Analyze this table structure and provide insights:
            
            Table: {table_name}
            Columns: {columns_data}
            Primary Keys: {schema_info.get('primary_key', [])}
            Foreign Keys: {[(fk.get('constrained_columns', []), fk.get('referred_table', '')) 
                           for fk in schema_info.get('foreign_keys', [])]}
            Sample Data: {sample_df.to_dict('records') if sample_df is not None else 'Not available'}
            
            Provide a concise analysis focusing on:
            1. The purpose and role of each column
            2. Key relationships and constraints
            3. Data integrity considerations
            4. Potential use cases for this table
            
            Format the analysis in a clear, structured way.
            """
            
            analysis = self.agent.llm.generate(analysis_prompt)
            
            return {
                'table_name': table_name,
                'analysis': analysis,
                'schema': schema_info,
                'sample_data': sample_df.to_dict('records') if sample_df is not None else None,
                'columns': columns_data
            }
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {str(e)}")
            raise
    
    def __getattr__(self, name):
        """Delegate unknown attributes to the agent"""
        return getattr(self.agent, name)