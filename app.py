import pandas as pd
import streamlit as st
from crewai import Crew, Task
from sqlalchemy import create_engine
from src.utils.database import init_database, get_table_names
from src.utils.agent_output_handler import AgentOutputHandler
from src.components.agent_reasoning import display_agent_reasoning_component
from typing import Dict, Any
from agents.schema_agent import SchemaAgent
from agents.sql_agent import SQLAgent
from agents.viz_agent import VizAgent
from agents.explain_agent import ExplainAgent

from sqlalchemy import create_engine
from src.utils.database import init_database

# Crear engine como variable global
db = init_database()
engine = db._engine

def initialize_session_state() -> None:
    """Initialize session state variables"""
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'selected_table' not in st.session_state:
        st.session_state['selected_table'] = None
    if 'schema_info' not in st.session_state:
        st.session_state['schema_info'] = None

def create_agents():
    """Create instances of all agents"""
    return {
        'schema': SchemaAgent(),
        'sql': SQLAgent(),
        'viz': VizAgent(),
        'explain': ExplainAgent()
    }

def create_crew(question: str, selected_table: str) -> Crew:
    """Create and configure the CrewAI crew"""
    agents = create_agents()
    
    tasks = [
        Task(
            description=f"Analyze the structure of table {selected_table}",
            agent=agents['schema'],
            expected_output="Table schema analysis"
        ),
        Task(
            description=f"Generate and execute SQL query for: {question}",
            agent=agents['sql'],
            expected_output="SQL query results"
        ),
        Task(
            description="Create visualization from query results",
            agent=agents['viz'],
            expected_output="Visualization data"
        ),
        Task(
            description="Explain the analysis results",
            agent=agents['explain'],
            expected_output="Clear explanation of findings"
        )
    ]
    
    return Crew(
        agents=list(agents.values()),
        tasks=tasks
    )

def process_analysis(question: str, selected_table: str) -> Dict[str, Any]:
    """Process the analysis using CrewAI agents"""
    try:
        # 1. Inicializar agentes
        schema_agent = SchemaAgent()
        sql_agent = SQLAgent()
        
        # 2. Obtener análisis del esquema
        schema_analysis = schema_agent.analyze_table(selected_table)
        
        # 3. Generar y ejecutar consulta SQL
        result = sql_agent.generate_and_execute(question, schema_analysis['raw_schema'])
        
        # 4. Formatear la salida
        formatted_output = {
            'query': result['query'],
            'results': result['results'],
            'schema_analysis': {
                'metrics': schema_analysis['column_roles']['metrics'],
                'dimensions': schema_analysis['column_roles']['dimensions'],
                'temporal': schema_analysis['column_roles']['temporal']
            }
        }
        
        return formatted_output
    
    except Exception as e:
        st.error(f"Error processing analysis: {str(e)}")
        return None
    
def suggest_questions(schema_analysis):
    """Generate suggested questions based on schema analysis"""
    suggestions = []
    
    # Sugerencias básicas
    if schema_analysis['column_roles']['metrics']:
        metric = schema_analysis['column_roles']['metrics'][0]
        dimension = schema_analysis['column_roles']['dimensions'][0]
        suggestions.append(f"What is the total {metric} by {dimension}?")
    
    # Sugerencias temporales
    if schema_analysis['column_roles']['temporal']:
        suggestions.append("How have sales changed over time?")
        suggestions.append("What are the monthly totals?")
    
    return suggestions

def handle_query_error(error: Exception):
    """Handle and display errors in a user-friendly way"""
    if "syntax error" in str(error).lower():
        st.error("The question couldn't be converted to a valid SQL query. Try rephrasing it.")
    elif "column not found" in str(error).lower():
        st.error("One or more columns mentioned in the question don't exist in the table.")
    else:
        st.error(f"An error occurred: {str(error)}")

def main():
    initialize_session_state()
    
    st.title("📊 SQL Query Assistant with CrewAI")
    st.write("Ask questions about your data in natural language")
    
    # Selección de tabla
    selected_table = st.selectbox(
        "Select a table to analyze:",
        options=get_table_names(engine)
    )
    
    if selected_table:
        schema_analysis = SchemaAgent().analyze_table(selected_table)
        suggestions = suggest_questions(schema_analysis)
        # Mostrar información del esquema
        with st.expander("Table Structure Analysis", expanded=False):
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("📊 Metrics")
                st.write(schema_analysis['column_roles']['metrics'])
            with col2:
                st.write("🔍 Dimensions")
                st.write(schema_analysis['column_roles']['dimensions'])
            with col3:
                st.write("📅 Time Columns")
                st.write(schema_analysis['column_roles']['temporal'])
        
        # Input para la pregunta
        question = st.text_input(
            "Ask a question about your data:",
            placeholder="e.g., What are the total sales by product?"
        )
        
        if question:
            with st.spinner("Processing your question..."):
                result = process_analysis(question, selected_table)
                
                if result:
                    # Mostrar consulta SQL
                    st.subheader("Generated SQL Query")
                    st.code(result['query'], language='sql')
                    
                    # Mostrar resultados
                    st.subheader("Results")
                    df = pd.DataFrame(result['results'])
                    st.dataframe(df)
                    
                    # Agregar a historial
                    st.session_state['history'].append({
                        'question': question,
                        'output': result,
                        'timestamp': pd.Timestamp.now()
                    })

if __name__ == "__main__":
    main()