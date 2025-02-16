from typing import Dict
import logging
from crewai import Agent
import pandas as pd
from config.config import get_agent_model
from langchain.chains import create_sql_query_chain
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_openai import ChatOpenAI
from src.utils.database import init_database

logger = logging.getLogger(__name__)

class SQLAgent:
    """SQL Agent for generating and executing database queries"""
    
    def __init__(self):
        """Initialize the SQL Agent"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error initializing SQLAgent: {str(e)}")
            raise
    
    def generate_and_execute(self, question: str, schema_info: Dict) -> Dict:
        try:
            # Inicializar componentes
            llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
            
            # Generar la consulta
            write_query = create_sql_query_chain(llm, self.db)
            query = write_query.invoke({"question": question})
            query = query.replace("SQLQuery:", "").replace("```sql", "").replace("```", "").strip()
            
            logger.info(f"Generated SQL Query: {query}")
            
            # Ejecutar la consulta
            execute_query = QuerySQLDatabaseTool(db=self.db)
            result = execute_query.run(query)
            
            # Procesar los resultados
            if isinstance(result, str):
                # Si el resultado es un string, intentar convertirlo
                if result.startswith("[('") and result.endswith("')]"):
                    try:
                        # Extraer nombres de columnas de la consulta
                        import re
                        select_match = re.search(r"SELECT\s+(.*?)\s+FROM", query, re.IGNORECASE | re.DOTALL)
                        if select_match:
                            columns_part = select_match.group(1)
                            # Extraer nombres/alias de columnas
                            column_names = []
                            for col in re.findall(r'(?:`[\w\s]+`|[\w\s]+(?=\s*,|\s*FROM|$))', columns_part):
                                # Buscar alias
                                alias_match = re.search(r'AS\s+`?(\w+)`?', col, re.IGNORECASE)
                                if alias_match:
                                    column_names.append(alias_match.group(1))
                                else:
                                    # Limpiar nombre de columna
                                    clean_col = col.strip('` ').split('.')[-1]
                                    column_names.append(clean_col)
                        else:
                            # Si no podemos extraer nombres, usar genéricos
                            column_names = ['column_1', 'column_2', 'column_3']

                        # Convertir string a lista de tuplas
                        import ast
                        data = ast.literal_eval(result)
                        # Convertir tuplas a diccionarios
                        processed_results = []
                        for row in data:
                            row_dict = {}
                            for i, value in enumerate(row):
                                if i < len(column_names):
                                    row_dict[column_names[i]] = value
                            processed_results.append(row_dict)
                        
                        result = processed_results

                    except Exception as e:
                        logger.error(f"Error processing results: {str(e)}")
                        raise
            
            return {
                'query': query,
                'results': result
            }

        except Exception as e:
            logger.error(f"Error in SQL generation/execution: {str(e)}")
            raise
    
    def __getattr__(self, name):
        """Delegate unknown attributes to the agent"""
        return getattr(self.agent, name)