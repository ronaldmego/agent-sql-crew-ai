# agents/sql_agent.py
from typing import Dict
import logging
from crewai import Agent
from config.config import get_agent_model
from langchain.chains import create_sql_query_chain
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_openai import ChatOpenAI
from src.utils.database import init_database
from pydantic import PrivateAttr

logger = logging.getLogger(__name__)

class SQLAgent(Agent):
    # Usar PrivateAttr para almacenar la db
    _db = PrivateAttr()
    
    def __init__(self):
        # Obtener configuración del modelo
        model_config = get_agent_model('sql')
        
        # Llamar al constructor de Agent primero
        super().__init__(
            role='SQL Analytics Expert',
            goal='Generate and execute SQL queries from natural language questions',
            backstory="""You are an expert SQL analyst who translates questions into 
            efficient SQL queries. You understand data types and analytics best practices.""",
            model=model_config['model'],
            verbose=True
        )
        
        # Inicializar la base de datos usando PrivateAttr
        self._db = init_database()
    
    def generate_and_execute(self, question: str, schema_info: Dict) -> Dict:
        try:
            llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
            write_query = create_sql_query_chain(llm, self._db)  # Usar _db
            query = write_query.invoke({"question": question})
            query = query.replace("SQLQuery:", "").replace("```sql", "").replace("```", "").strip()
            
            logger.info(f"Generated SQL Query: {query}")
            
            execute_query = QuerySQLDatabaseTool(db=self._db)  # Usar _db
            result = execute_query.run(query)
            
            return {
                'query': query,
                'results': result
            }

        except Exception as e:
            logger.error(f"Error in SQL generation/execution: {str(e)}")
            raise