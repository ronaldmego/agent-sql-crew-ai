import os
from dotenv import load_dotenv
from crewai import Agent
from crewai_tools import NL2SQLTool
import logging
from sqlalchemy import create_engine, text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_debug(message):
    """Helper function to print debug messages"""
    print(f"\n>>> DEBUG: {message}")

def test_postgres_connection():
    """Test PostgreSQL connection with NL2SQLTool"""
    print_debug("Testing PostgreSQL connection...")
    
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Construir el URI de conexión para Supabase
        pg_password = os.getenv('POSTGRES_PASSWORD')
        if not pg_password:
            raise ValueError("POSTGRES_PASSWORD not found in environment variables")
            
        pg_uri = (
            f"postgresql://postgres.klfwwypsvykenulckrwn:{pg_password}@"
            "aws-0-us-west-1.pooler.supabase.com:5432/postgres"
        )
        
        print_debug(f"PostgreSQL URI (masked): postgresql://postgres.klfwwypsvykenulckrwn:***@aws-0-us-west-1.pooler.supabase.com:5432/postgres")
        
        # Primero probar la conexión directa con SQLAlchemy
        print_debug("Testing direct connection with SQLAlchemy...")
        engine = create_engine(pg_uri)
        with engine.connect() as connection:
            # Consulta para listar tablas en PostgreSQL
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print_debug(f"Tables found: {tables}")
        
        # Ahora probar NL2SQLTool
        print_debug("Creating NL2SQLTool instance...")
        nl2sql = NL2SQLTool(db_uri=pg_uri)
        print_debug("NL2SQLTool instance created successfully")
        
        # Crear agente de prueba
        print_debug("Creating test agent...")
        agent = Agent(
            role='Test SQL Agent',
            goal='Test database queries',
            backstory='I am a test agent for database queries',
            tools=[nl2sql],
            verbose=True
        )
        print_debug("Test agent created successfully")
        
        # Probar una consulta simple en una tabla específica
        if tables:
            test_table = tables[0]  # Usar la primera tabla encontrada
            test_question = f"What columns are in the table {test_table}?"
            print_debug(f"Testing query about table: {test_table}")
            
            result = nl2sql.run(test_question)
            print_debug(f"Query result: {result}")
        else:
            print_debug("No tables found to query")
        
        return True
        
    except Exception as e:
        print_debug(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print_debug("Starting PostgreSQL test with Supabase...")
    
    # Verificar que psycopg2 está instalado
    try:
        import psycopg2
        print_debug("psycopg2 is installed")
    except ImportError:
        print_debug("psycopg2 is not installed. Installing...")
        print_debug("Please run: pip install psycopg2-binary")
        exit(1)
    
    # Probar conexión
    success = test_postgres_connection()
    print_debug(f"PostgreSQL test {'successful' if success else 'failed'}")
    
    print_debug("Tests completed")