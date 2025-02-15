import streamlit as st
from crewai import Crew, Task
from sqlalchemy import create_engine, inspect
import pandas as pd
from src.utils.database import init_database, get_table_names, get_table_schema
from src.utils.agent_output_handler import AgentOutputHandler
from src.components.agent_reasoning import display_agent_reasoning_component
from agents.schema_agent import SchemaAgent
from agents.sql_agent import SQLAgent
from agents.viz_agent import VizAgent
from agents.explain_agent import ExplainAgent
import matplotlib.pyplot as plt
from typing import Dict

# Inicializar variables de sesión
def initialize_session_state() -> None:
    """Inicializa las variables de estado de la sesión"""
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'selected_table' not in st.session_state:
        st.session_state['selected_table'] = None
    if 'schema_info' not in st.session_state:
        st.session_state['schema_info'] = None
    if 'current_table_schema' not in st.session_state:
        st.session_state['current_table_schema'] = None

# Crear instancias de agentes
def create_agents(table_name: str):
    """Crea instancias de todos los agentes con el contexto de la tabla"""
    return {
        'schema': SchemaAgent(),
        'sql': SQLAgent(),
        'viz': VizAgent(),
        'explain': ExplainAgent()
    }

# Crear y configurar el equipo (crew)
def create_crew(question: str, selected_table: str) -> Crew:
    """Crea y configura el equipo de CrewAI"""
    agents = create_agents(selected_table)
    tasks = [
        Task(
            description=f"Analyze the structure of table {selected_table}",
            agent=agents['schema'],
            expected_output="Detailed table schema analysis"
        ),
        Task(
            description=f"Generate and execute SQL query for: {question}",
            agent=agents['sql'],
            expected_output="SQL query results with actual data"
        ),
        Task(
            description="Create visualization from the actual query results",
            agent=agents['viz'],
            expected_output="Data visualization with insights"
        ),
        Task(
            description="Explain the analysis results with actual data insights",
            agent=agents['explain'],
            expected_output="Clear explanation of findings based on real data"
        )
    ]
    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=True
    )

# Convertir tipos de datos del DataFrame para compatibilidad con Streamlit
def convert_df_types(df):
    """Convierte los tipos de datos del DataFrame para ser compatibles con Streamlit"""
    for col in df.columns:
        # Convertir tipos problemáticos a string
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
        elif 'datetime' in str(df[col].dtype):
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

# Mostrar los resultados de la consulta
def display_query_results(results: Dict):
    """Muestra los resultados de la consulta de manera estructurada"""
    if 'results' in results and results['results']:
        st.write("### Query Results")
        try:
            # Convertir resultados a DataFrame
            df = pd.DataFrame(results['results'])
            # Convertir tipos de datos para compatibilidad con Streamlit
            df = convert_df_types(df)
            # Mostrar resumen estadístico si hay datos numéricos
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if not numeric_cols.empty:
                with st.expander("Statistical Summary"):
                    summary_df = df[numeric_cols].describe()
                    summary_df = convert_df_types(summary_df)
                    st.dataframe(summary_df)
            # Mostrar los datos completos
            st.dataframe(df)
            # Mostrar información sobre el número de registros
            st.info(f"Total records: {len(df)}")
        except Exception as e:
            st.error(f"Error displaying results: {str(e)}")
            st.write("Raw results:")
            st.write(results['results'])

# Mostrar el esquema de la tabla
def display_table_schema(schema_info: Dict):
    """Muestra la información del esquema de la tabla de manera estructurada"""
    if not schema_info:
        st.warning("No schema information available")
        return
    st.write("### Table Structure")
    try:
        # Mostrar columnas
        if 'columns' in schema_info:
            st.write("#### Columns")
            cols_data = []
            for col in schema_info['columns']:
                cols_data.append({
                    'Name': col['name'],
                    'Type': str(col['type']),
                    'Nullable': 'Yes' if col.get('nullable', True) else 'No'
                })
            cols_df = pd.DataFrame(cols_data)
            st.dataframe(cols_df)
        # Mostrar claves primarias
        if schema_info.get('primary_key'):
            st.write("#### Primary Key")
            st.write(", ".join(schema_info['primary_key']))
        # Mostrar claves foráneas
        if schema_info.get('foreign_keys'):
            st.write("#### Foreign Keys")
            for fk in schema_info['foreign_keys']:
                st.write(f"- {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}")
    except Exception as e:
        st.error(f"Error displaying schema: {str(e)}")
        st.write("Raw schema:")
        st.write(schema_info)

# Función principal
def main():
    initialize_session_state()

    # Título de la aplicación
    st.title("📊 SQL Query Assistant with CrewAI")
    st.write("Ask questions about your data in natural language")

    # Inicializar conexión a la base de datos
    db = init_database()

    # Obtener la lista de tablas disponibles
    try:
        inspector = inspect(db._engine)
        tables = inspector.get_table_names()
    except Exception as e:
        st.error(f"Error fetching table names: {str(e)}")
        st.stop()

    # Selector de tablas
    selected_table = st.selectbox(
        "Select a table to analyze:",
        options=tables,
        key='table_selector'
    )

    if selected_table:
        # Mostrar información sobre la tabla seleccionada
        try:
            schema_info = get_table_schema(db._engine, selected_table)
            if schema_info:
                st.write("### Table Structure")
                st.write(f"Selected table: `{selected_table}`")
                # Mostrar columnas
                if 'columns' in schema_info:
                    st.write("#### Columns")
                    cols_data = []
                    for col in schema_info['columns']:
                        cols_data.append({
                            'Name': col['name'],
                            'Type': str(col['type']),
                            'Nullable': 'Yes' if col.get('nullable', True) else 'No'
                        })
                    cols_df = pd.DataFrame(cols_data)
                    st.dataframe(cols_df)
                # Mostrar claves primarias
                if schema_info.get('primary_key'):
                    st.write("#### Primary Key")
                    st.write(", ".join(schema_info['primary_key']))
                # Mostrar claves foráneas
                if schema_info.get('foreign_keys'):
                    st.write("#### Foreign Keys")
                    for fk in schema_info['foreign_keys']:
                        st.write(f"- {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}")
        except Exception as e:
            st.error(f"Error displaying schema: {str(e)}")

    # Input para la pregunta
    question = st.text_input(
        "Ask a question about your data:",
        placeholder="e.g., What are the total sales by product?"
    )

    if question and selected_table:
        with st.spinner("Processing your question..."):
            try:
                # Crear agentes con la tabla seleccionada
                agents = create_agents(selected_table)
                
                # Procesar la pregunta
                sql_result = agents['sql'].generate_and_execute(question)
                viz_result = agents['viz'].create_visualization(sql_result['results'], question)
                explain_result = agents['explain'].generate_explanation(question, sql_result, viz_result)
                
                # Mostrar resultados
                st.subheader("Generated SQL Query")
                st.code(sql_result['query'], language='sql')
                
                st.subheader("Query Results")
                df = pd.DataFrame(sql_result['results'])
                st.dataframe(df)
                
                st.subheader("Data Visualization")
                st.pyplot(viz_result['figure'])
                
                st.subheader("Explanation")
                st.write(explain_result['explanation'])
                
                # Agregar al historial
                st.session_state['history'].append({
                    'question': question,
                    'output': {
                        'query': sql_result['query'],
                        'results': sql_result['results'],
                        'visualization': viz_result,
                        'explanation': explain_result
                    },
                    'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Mostrar historial
    if st.session_state['history']:
        st.subheader("Question History")
        for item in reversed(st.session_state['history']):
            with st.expander(f"Q: {item['question']} ({item['timestamp']})"):
                st.code(item['output']['query'], language='sql')
                st.dataframe(pd.DataFrame(item['output']['results']))
                st.pyplot(item['output']['visualization']['figure'])
                st.write(item['output']['explanation'])

if __name__ == "__main__":
    main()