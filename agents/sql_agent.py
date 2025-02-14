# agents/sql_agent.py

from typing import Dict
import logging
from crewai import Agent
from sqlalchemy import create_engine
import pandas as pd
from config.config import get_mysql_uri, get_agent_model

logger = logging.getLogger(__name__)

class SQLAgent(Agent):
    def __init__(self):
        model_config = get_agent_model('sql')
        
        super().__init__(
            role='SQL Analytics Expert',
            goal='Generate SQL queries from natural language questions',
            backstory="""You are an expert SQL analyst who translates questions into 
            efficient SQL queries. You understand data types and analytics best practices.""",
            model=model_config['model'],
            verbose=True
        )
        
        # Inicializar el engine como atributo protegido
        self._engine = create_engine(get_mysql_uri())

    @property
    def engine(self):
        """Property para acceder al engine de manera segura"""
        return self._engine

    def generate_and_execute(self, question: str, schema_info: Dict) -> Dict:
        """
        Genera y ejecuta una consulta SQL basada en la pregunta y el esquema
        
        Args:
            question: Pregunta en lenguaje natural
            schema_info: Información del esquema proporcionada por SchemaAgent
            
        Returns:
            Dict con la consulta y sus resultados
        """
        try:
            # Formar el prompt para el LLM incluyendo el contexto del esquema
            prompt = f"""
            Based on this database schema:
            {schema_info}
            
            Generate a SQL query to answer: {question}
            
            Consider:
            - Use appropriate aggregations when needed
            - Include relevant columns for visualization
            - Return only the SQL query, no explanations
            """
            
            # Generar la consulta usando el LLM
            query = self.llm.generate(prompt).strip()
            
            # Ejecutar la consulta usando el property engine
            results = pd.read_sql(query, self.engine)
            
            return {
                'query': query,
                'results': results.to_dict('records'),
                'columns': list(results.columns),
                'row_count': len(results)
            }

        except Exception as e:
            logger.error(f"Error in SQL generation/execution: {str(e)}")
            raise