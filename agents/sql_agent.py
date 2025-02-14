from typing import Dict
import logging
from crewai import Agent
from sqlalchemy import create_engine
import pandas as pd
from config.config import get_agent_model
from src.utils.database import get_mysql_uri, get_crewai_tools

logger = logging.getLogger(__name__)

class SQLAgent(Agent):
    def __init__(self, table_name: str = None):
        model_config = get_agent_model('sql')
        
        super().__init__(
            role='SQL Analytics Expert',
            goal='Generate and execute SQL queries from natural language questions',
            backstory="""You are an expert SQL analyst who translates questions into 
            efficient SQL queries. You understand data types and analytics best practices.""",
            model=model_config['model'],
            tools=get_crewai_tools(table_name),  # Usar las herramientas de CrewAI
            verbose=True
        )

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
            # Usar NL2SQLTool para generar y ejecutar la consulta
            nl2sql_tool = next(tool for tool in self.tools if tool.__class__.__name__ == 'NL2SQLTool')
            results = nl2sql_tool.run(question)
            
            # Convertir resultados a DataFrame si no lo están ya
            if not isinstance(results, pd.DataFrame):
                results = pd.DataFrame(results)
            
            return {
                'query': nl2sql_tool.last_query,  # Obtener la última consulta ejecutada
                'results': results.to_dict('records'),
                'columns': list(results.columns),
                'row_count': len(results)
            }

        except Exception as e:
            logger.error(f"Error in SQL generation/execution: {str(e)}")
            raise