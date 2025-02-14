import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import pandas as pd
import logging
from pathlib import Path

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleCSVLoader:
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        self.config = {
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'host': os.getenv('MYSQL_HOST'),
            'database': os.getenv('MYSQL_DATABASE')
        }
        
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establece conexión con la base de datos"""
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor()
            logger.info("Conexión exitosa a MySQL")
            return True
        except Error as e:
            logger.error(f"Error de conexión: {str(e)}")
            return False

    def create_table_from_df(self, table_name: str, df: pd.DataFrame) -> bool:
        """Crea una tabla basada en la estructura del DataFrame"""
        try:
            # Mapeo simple de tipos de datos
            type_mapping = {
                'int64': 'BIGINT',
                'float64': 'DOUBLE',
                'object': 'VARCHAR(255)',
                'datetime64[ns]': 'DATETIME',
                'bool': 'BOOLEAN'
            }
            
            # Crear la definición de columnas
            columns = []
            for col in df.columns:
                col_type = str(df[col].dtype)
                sql_type = type_mapping.get(col_type, 'TEXT')
                columns.append(f"`{col}` {sql_type}")
            
            # SQL para crear la tabla
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                {', '.join(columns)}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            logger.info(f"Tabla {table_name} creada exitosamente")
            return True
            
        except Error as e:
            logger.error(f"Error creando tabla: {str(e)}")
            return False

    def load_csv_to_table(self, csv_path: str) -> bool:
        """Carga un archivo CSV a una tabla en MySQL"""
        try:
            # Obtener nombre de tabla del archivo
            table_name = Path(csv_path).stem
            
            # Leer CSV
            df = pd.read_csv(csv_path)
            
            # Convertir columnas de fecha si existen
            date_columns = [col for col in df.columns if 'fecha' in col.lower() or 'date' in col.lower()]
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Crear tabla
            if not self.create_table_from_df(table_name, df):
                return False
            
            # Preparar la inserción
            columns = df.columns
            placeholders = ', '.join(['%s'] * len(columns))
            
            # Insertar por lotes
            batch_size = 1000
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                values = [tuple(x) for x in batch.replace({pd.NA: None}).values]
                
                insert_sql = f"""
                INSERT INTO `{table_name}` 
                (`{'`, `'.join(columns)}`) 
                VALUES ({placeholders})
                """
                
                self.cursor.executemany(insert_sql, values)
                self.conn.commit()
                logger.info(f"Insertados registros {i} a {i + len(batch)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cargando CSV: {str(e)}")
            return False

    def process_directory(self, directory: str = 'data'):
        """Procesa todos los CSVs en un directorio"""
        try:
            # Obtener ruta raíz del proyecto (2 niveles arriba de scripts/mysql)
            root_path = Path(__file__).parent.parent.parent
            data_dir = root_path / directory
            if not data_dir.exists():
                raise Exception(f"El directorio {directory} no existe")
            
            # Obtener CSVs
            csv_files = list(data_dir.glob('*.csv'))
            if not csv_files:
                logger.warning(f"No se encontraron CSVs en {directory}")
                return
            
            # Conectar a la base de datos
            if not self.connect():
                return
            
            # Procesar cada archivo
            for csv_file in csv_files:
                logger.info(f"Procesando {csv_file}")
                if self.load_csv_to_table(str(csv_file)):
                    logger.info(f"Archivo {csv_file} procesado exitosamente")
                else:
                    logger.error(f"Error procesando {csv_file}")
                    
        except Exception as e:
            logger.error(f"Error en el proceso: {str(e)}")
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn and self.conn.is_connected():
                self.conn.close()
                logger.info("Conexión cerrada")

def main():
    loader = SimpleCSVLoader()
    loader.process_directory()

if __name__ == "__main__":
    main()