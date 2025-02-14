# agents/schema_agent.py

from typing import Dict
import logging
from crewai import Agent
from sqlalchemy import create_engine, inspect
import pandas as pd
from config.config import get_mysql_uri, get_agent_model

logger = logging.getLogger(__name__)

class SchemaAgent(Agent):
    def __init__(self):
        # Inicializar el engine antes del super().__init__
        try:
            engine = create_engine(get_mysql_uri())
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database engine: {str(e)}")
            raise

        model_config = get_agent_model('schema')
        
        # Llamar al constructor de la clase padre
        super().__init__(
            role='Database Schema Analyst',
            goal='Analyze database structure and provide clear schema understanding',
            backstory="""You are an expert in database analysis. You examine tables 
            and understand their structure, identifying patterns and relationships in the data.""",
            model=model_config['model'],
            verbose=True,
            allow_delegation=False
        )
        
        # Asignar el engine como atributo después de la inicialización
        self._engine = engine

    @property
    def engine(self):
        return self._engine

    def analyze_table(self, table_name: str) -> Dict:
        """
        Analiza la estructura y contenido de una tabla
        
        Args:
            table_name: Nombre de la tabla a analizar
            
        Returns:
            Dict con información relevante de la tabla
        """
        try:
            # Obtener información del esquema usando inspector
            inspector = inspect(self.engine)
            columns_info = inspector.get_columns(table_name)
            
            # Obtener muestra de datos
            query = f"SELECT * FROM {table_name} LIMIT 100"
            df = pd.read_sql(query, self.engine)
            
            # Preparar información de columnas en formato más amigable
            columns_data = [{
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable']
            } for col in columns_info]
            
            # Analizar la estructura usando el LLM
            prompt = f"""
            Analyze this table structure and sample data:
            
            Table: {table_name}
            Columns: {columns_data}
            Sample Data Stats: {df.describe().to_dict()}
            
            Provide a concise analysis of:
            1. Column types and their purpose
            2. Key patterns in the data
            3. Potential relationships between columns
            
            Return the analysis in a structured format.
            """
            
            analysis = self.llm.generate(prompt)
            
            return {
                'table_name': table_name,
                'analysis': analysis,
                'columns': columns_data,
                'sample_data': df.head(5).to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {str(e)}")
            raise