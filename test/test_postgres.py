import os
from dotenv import load_dotenv
from crewai import Agent
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_debug(message):
    """Helper function to print debug messages"""
    print(f"\n>>> DEBUG: {message}")

def test_postgres_query():
    """Test PostgreSQL queries with QuerySQLDataBaseTool"""
    print_debug("Testing PostgreSQL connection and queries...")
    
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Verificar variables necesarias
        pg_password = os.getenv('POSTGRES_PASSWORD')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not all([pg_password, openai_key]):
            missing = []
            if not pg_password: missing.append('POSTGRES_PASSWORD')
            if not openai_key: missing.append('OPENAI_API_KEY')
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        
        # Construir URI de conexión
        pg_uri = (
            f"postgresql://postgres.klfwwypsvykenulckrwn:{pg_password}@"
            "aws-0-us-west-1.pooler.supabase.com:5432/postgres"
        )
        
        print_debug("Initializing components...")
        
        # Inicializar la base de datos
        db = SQLDatabase.from_uri(pg_uri)
        print_debug("Database connection established")
        
        # Crear el LLM
        llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        print_debug("LLM initialized")
        
        # Crear la cadena de consulta SQL
        write_query = create_sql_query_chain(llm, db)
        print_debug("SQL query chain created")
        
        # Crear la herramienta de ejecución
        execute_query = QuerySQLDataBaseTool(db=db)
        print_debug("Query execution tool created")
        
        # Definir algunas consultas de prueba
        test_queries = [
            "What tables exist in the database?",
            "Show me the structure of the table prueba",
            "How many records are in the prueba table?"
        ]
        
        # Probar cada consulta
        for question in test_queries:
            print_debug(f"\nTesting query: {question}")
            try:
                # Generar la consulta SQL
                query = write_query.invoke({"question": question})
                print_debug(f"Generated SQL: {query}")
                
                # Ejecutar la consulta
                result = execute_query.run(query)
                print_debug(f"Query result: {result}")
                
            except Exception as e:
                print_debug(f"Error with query '{question}': {str(e)}")
        
        return True
        
    except Exception as e:
        print_debug(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print_debug("Starting PostgreSQL query test...")
    
    # Verificar psycopg2
    try:
        import psycopg2
        print_debug("psycopg2 is installed")
    except ImportError:
        print_debug("Please run: pip install psycopg2-binary")
        exit(1)
    
    # Ejecutar pruebas
    success = test_postgres_query()
    print_debug(f"Test {'successful' if success else 'failed'}")