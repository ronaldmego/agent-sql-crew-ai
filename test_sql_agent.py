# test_sql_agent.py

import os
from dotenv import load_dotenv
from agents.sql_agent import SQLAgent
from src.utils.database import init_database

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_init_database():
    """Prueba la inicialización de la conexión a la base de datos."""
    try:
        logger.info("Testing database initialization...")
        db = init_database()
        if db:
            logger.info("Database connection initialized successfully.")
            logger.info(f"Type of db: {type(db)}")
        else:
            logger.error("Database connection returned None.")
        return db
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def test_sql_agent():
    try:
        load_dotenv()
        db = test_init_database()
        sql_agent = SQLAgent()
        
        # Obtener información del esquema primero
        from src.utils.database import get_table_schema
        table_name = "sample_sales_data"  # O cualquier tabla que queramos consultar
        schema_info = get_table_schema(db._engine, table_name)
        
        logger.info(f"Testing with table: {table_name}")
        logger.info(f"Schema info: {schema_info}")
        
        # Probar diferentes tipos de consultas
        test_questions = [
            "What are the total sales by product?",
            "Who are the top 3 sellers by total sales?",
            "What is the average price per product?",
        ]
        
        for question in test_questions:
            logger.info(f"\nTesting question: {question}")
            result = sql_agent.generate_and_execute(question, schema_info)
            
            logger.info("-" * 50)
            logger.info(f"Generated SQL Query:\n{result['query']}")
            logger.info("Query Results:")
            logger.info(result['results'])
        
    except Exception as e:
        logger.error(f"An error occurred during testing: {str(e)}")

if __name__ == "__main__":
    test_sql_agent()