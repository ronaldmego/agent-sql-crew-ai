# agents/sql_agent.py
from typing import Dict
import logging
from crewai import Agent
from langchain.chains import create_sql_query_chain
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_openai import ChatOpenAI
from src.utils.database import init_database
from config.config import get_agent_model

logger = logging.getLogger(__name__)

class SQLAgent:
    """A wrapper class that combines CrewAI Agent with SQL functionality"""
    
    def __init__(self):
        # Inicializar la base de datos
        self.db = init_database()
        if not self.db:
            raise ValueError("Database initialization failed")
            
        # Configuración del modelo
        model_config = get_agent_model('sql')
        
        # Crear el agente base
        self.agent = Agent(
            role='SQL Analytics Expert',
            goal='Generate and execute SQL queries from natural language questions',
            backstory="""You are an expert SQL analyst who translates questions into 
            efficient SQL queries. You understand data types and analytics best practices.""",
            model=model_config['model'],
            verbose=True
        )
    
    def generate_and_execute(self, question: str) -> Dict:
        try:
            # Inicializar componentes
            llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
            write_query = create_sql_query_chain(llm, self.db)
            execute_query = QuerySQLDatabaseTool(db=self.db)
            
            # Generar la consulta
            query = write_query.invoke({"question": question})
            
            # Limpiar la consulta - remover "SQLQuery:" y otros elementos no deseados
            query = query.replace("SQLQuery:", "").replace("```sql", "").replace("```", "").strip()
            
            logger.info(f"Generated SQL Query: {query}")
            
            try:
                # Ejecutar la consulta
                result = execute_query.run(query)
                logger.info(f"SQL Result type: {type(result)}")
                logger.info(f"SQL Result: {result}")
                
                # Convertir tuplas a diccionarios
                if isinstance(result, str) and result.startswith("[('"):
                    # Evaluar el string como lista de tuplas
                    import ast
                    tuples_list = ast.literal_eval(result)
                    result = [
                        {'producto': t[0], 'total_ventas': float(t[1])} 
                        for t in tuples_list
                    ]
                
                return {
                    'query': query,
                    'results': result
                }
                
            except Exception as e:
                logger.error(f"SQL execution error: {str(e)}")
                return {
                    'query': query,
                    'results': [],
                    'error': str(e)
                }
                
        except Exception as e:
            logger.error(f"Error in SQL generation/execution: {str(e)}")
            raise
            
    def __getattr__(self, name):
        """Delegate unknown attributes to the agent"""
        return getattr(self.agent, name)