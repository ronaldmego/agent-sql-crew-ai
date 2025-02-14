import streamlit as st
from crewai import Crew, Task
from sqlalchemy import create_engine
from src.utils.database import get_mysql_uri, get_table_names
from src.utils.agent_output_handler import AgentOutputHandler
from src.components.agent_reasoning import display_agent_reasoning_component
from typing import Dict, Any
# Importar los agentes
from agents.schema_agent import SchemaAgent
from agents.sql_agent import SQLAgent
from agents.viz_agent import VizAgent
from agents.explain_agent import ExplainAgent

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
    """Process the analysis using CrewAI and return formatted results"""
    try:
        # Crear el crew con la pregunta y tabla específica
        crew = create_crew(question, selected_table)
        
        # Obtener la respuesta de CrewAI
        result = crew.kickoff()
        
        # Formatear la salida usando el handler
        formatted_output = AgentOutputHandler.format_agent_output(result)
        
        return formatted_output
    except Exception as e:
        st.error(f"Error processing analysis: {str(e)}")
        return None

def main():
    initialize_session_state()
    
    # Header
    st.title("📊 SQL Query Assistant with CrewAI")
    st.write("Ask questions about your data in natural language")
    
    # Sidebar - Selección de tabla
    with st.sidebar:
        st.header("Configuration")
        
        # Obtener lista de tablas
        engine = create_engine(get_mysql_uri())
        tables = get_table_names(engine)
        
        selected_table = st.selectbox(
            "Select a table to analyze:",
            options=tables,
            key='table_selector'
        )
        
        if selected_table != st.session_state.get('selected_table'):
            st.session_state['selected_table'] = selected_table
            st.session_state['schema_info'] = None
    
    # Main area
    if selected_table:
        # Input para la pregunta
        question = st.text_input(
            "Ask a question about your data:",
            placeholder="e.g., What are the total sales by product?"
        )
        
        if question:
            with st.spinner("Processing your question..."):
                try:
                    # Procesar análisis
                    formatted_output = process_analysis(question, selected_table)
                    
                    if formatted_output:
                        # Mostrar el proceso de razonamiento
                        display_agent_reasoning_component(formatted_output['reasoning'])
                        
                        # Mostrar la consulta SQL
                        if formatted_output['query']:
                            st.subheader("Generated SQL Query")
                            st.code(formatted_output['query'], language='sql')
                            
                            # Ejecutar la consulta y mostrar resultados
                            if 'execute_query' in formatted_output:
                                results = formatted_output['execute_query']
                                st.subheader("Query Results")
                                st.dataframe(results)
                        
                        # Mostrar visualización si existe
                        if formatted_output.get('visualization'):
                            st.subheader("Data Visualization")
                            st.plotly_chart(formatted_output['visualization'])
                        
                        # Agregar a historial
                        st.session_state['history'].append({
                            'question': question,
                            'output': formatted_output
                        })
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.error("Please try again with a different question.")
        
        # Mostrar historial
        if st.session_state['history']:
            st.subheader("Question History")
            for item in reversed(st.session_state['history']):
                with st.expander(f"Q: {item['question']}"):
                    if 'reasoning' in item['output']:
                        display_agent_reasoning_component(item['output']['reasoning'])
                    if 'query' in item['output']:
                        st.code(item['output']['query'], language='sql')

if __name__ == "__main__":
    main()