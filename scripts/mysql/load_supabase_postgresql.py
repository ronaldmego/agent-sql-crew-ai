import pandas as pd
from sqlalchemy import create_engine
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_csv_to_postgresql(
    csv_path: str,
    connection_string: str,
    table_name: str = None,
    if_exists: str = 'replace'
) -> bool:
    """
    Carga un archivo CSV a PostgreSQL usando pandas
    
    Args:
        csv_path: Ruta al archivo CSV
        connection_string: String de conexión a PostgreSQL
        table_name: Nombre de la tabla (opcional, por defecto usa el nombre del archivo)
        if_exists: Comportamiento si la tabla existe ('fail', 'replace', 'append')
    """
    try:
        # Obtener nombre de tabla del archivo si no se especifica
        if not table_name:
            table_name = Path(csv_path).stem.lower()
        
        # Crear engine de SQLAlchemy
        engine = create_engine(connection_string)
        
        # Leer CSV
        logger.info(f"Leyendo archivo: {csv_path}")
        df = pd.read_csv(csv_path)
        
        # Convertir columnas de fecha si existen
        date_columns = [col for col in df.columns if 'fecha' in col.lower() or 'date' in col.lower()]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
        # Cargar a PostgreSQL
        logger.info(f"Cargando datos a la tabla: {table_name}")
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            index=False,
            chunksize=1000
        )
        
        logger.info("Carga completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error en la carga: {str(e)}")
        return False

if __name__ == "__main__":
    # Obtener ruta raíz del proyecto (2 niveles arriba de scripts/mysql)
    ROOT_PATH = Path(__file__).parent.parent.parent
    
    # Cargar variables de entorno
    load_dotenv(ROOT_PATH / '.env')
    
    # Configurar rutas y conexión
    CSV_PATH = ROOT_PATH / 'data' / 'sample_sales_data.csv'
    
    # Construir connection string con la contraseña del .env
    CONNECTION_STRING = f"postgresql://postgres.klfwwypsvykenulckrwn:{os.getenv('SUPABASE_PASSWORD')}@aws-0-us-west-1.pooler.supabase.com:5432/postgres"
    
    # Ejecutar carga
    load_csv_to_postgresql(str(CSV_PATH), CONNECTION_STRING)