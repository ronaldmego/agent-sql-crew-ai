# test_agents.py
import os
from dotenv import load_dotenv
from agents.schema_agent import SchemaAgent
from agents.sql_agent import SQLAgent
from src.utils.database import init_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agents_interaction():
    try:
        # 1. Cargar configuración
        load_dotenv()
        db = init_database()
        
        # 2. Crear instancias de los agentes
        schema_agent = SchemaAgent()
        sql_agent = SQLAgent()
        
        # 3. Analizar la tabla
        table_name = "sample_sales_data"
        logger.info(f"\nAnalyzing table: {table_name}")
        schema_analysis = schema_agent.analyze_table(table_name)
        
        # 4. Mostrar el análisis del esquema
        logger.info("\nSchema Analysis:")
        logger.info("-" * 50)
        logger.info(f"Metrics available: {schema_analysis['column_roles']['metrics']}")
        logger.info(f"Dimensions available: {schema_analysis['column_roles']['dimensions']}")
        logger.info(f"Temporal columns: {schema_analysis['column_roles']['temporal']}")
        
        # 5. Probar diferentes tipos de preguntas
        test_questions = [
            "What are the total sales by product?",
            "Who are the top 3 sellers by total sales?",
            "What is the average price per product?",
            "How many units were sold of each product per month?",
            "What is the total revenue per customer?"
        ]
        
        # 6. Ejecutar consultas usando el contexto del esquema
        for question in test_questions:
            logger.info(f"\nTesting question: {question}")
            result = sql_agent.generate_and_execute(question, schema_analysis['raw_schema'])
            
            logger.info("-" * 50)
            logger.info(f"Generated SQL Query:\n{result['query']}")
            logger.info("Query Results:")
            logger.info(result['results'])
            
        print("\nTest completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred during testing: {str(e)}")

if __name__ == "__main__":
    test_agents_interaction()