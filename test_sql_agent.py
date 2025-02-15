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
        # 1. Cargar variables de entorno
        load_dotenv()

        # 2. Probar la inicialización de la base de datos
        db = test_init_database()

        # 3. Crear una instancia del SQLAgent
        logger.info("Initializing SQLAgent...")
        sql_agent = SQLAgent()
        
        # 4. Mostrar todos los atributos del objeto SQLAgent
        logger.info(f"Attributes of SQLAgent: {dir(sql_agent)}")

        # 5. Verificar que el atributo 'db' esté disponible
        if not hasattr(sql_agent, 'db'):
            logger.error("SQLAgent has no attribute 'db'. Initialization failed.")
            return

        logger.info("SQLAgent 'db' attribute is available.")
        logger.info(f"Type of SQLAgent.db: {type(sql_agent.db)}")

        # 6. Definir una pregunta simple
        question = "What are the total sales by product?"

        # 7. Generar y ejecutar la consulta SQL
        logger.info(f"Generating and executing SQL query for question: '{question}'")
        result = sql_agent.generate_and_execute(question)

        # 8. Mostrar los resultados
        logger.info("\nResults:")
        logger.info("-" * 50)
        logger.info(f"Generated SQL Query:\n{result['query']}")
        logger.info("-" * 50)
        logger.info("Query Results:")
        logger.info(result['results'])

        print("\nTest completed successfully!")
        print("Generated SQL Query:")
        print(result['query'])
        print("\nQuery Results:")
        print(result['results'])

    except Exception as e:
        logger.error(f"An error occurred during testing: {str(e)}")

if __name__ == "__main__":
    test_sql_agent()