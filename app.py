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

import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            description=f"Analyze the structure of table {selected_table} and determine the best approach to answer the question: {question}",
            agent=agents['schema'],
            expected_output="Detailed schema analysis with suggested query approach"
        ),
        Task(
            description=f"""Based on the schema analysis, generate and execute an SQL query to answer: {question}
            Explain your reasoning for the query structure.""",
            agent=agents['sql'],
            expected_output="SQL query with explanation of approach"
        ),
        Task(
            description="""Analyze the query results and explain the findings in business terms.
            Highlight key insights and patterns.""",
            agent=agents['explain'],
            expected_output="Clear explanation of findings and insights"
        )
    ]
    
    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=True
    )

def process_analysis(question: str, selected_table: str) -> Dict[str, Any]:
    """Process the analysis using CrewAI agents"""
    try:
        # Crear y ejecutar el crew
        crew = create_crew(question, selected_table)
        crew_result = crew.kickoff()
        
        # Capturar el razonamiento de los agentes
        agent_reasoning = []
        query = None
        formatted_results = []
        
        # Procesar los resultados de cada tarea
        # La salida de crew.kickoff() es una tupla con los resultados
        for output in crew_result:
            # Extraer el contenido del output
            content = str(output)
            
            # Determinar el tipo de agente basado en el contenido
            agent_type = "Schema Analyst" if "structure" in content.lower() else \
                        "SQL Expert" if "sql" in content.lower() or "query" in content.lower() else \
                        "Data Analyst"
            
            # Agregar al razonamiento
            agent_reasoning.append({
                'agent': agent_type,
                'thoughts': [line.strip() for line in content.split('\n') if line.strip()],
                'task': f"Process {agent_type} analysis"
            })
            
            # Si es el output del SQL Agent, extraer la consulta
            if "SQL Expert" in agent_type:
                # Extraer la consulta SQL del output
                import re
                sql_match = re.search(r"```sql\s*(.*?)\s*```", content, re.DOTALL)
                if sql_match:
                    query = sql_match.group(1).strip()
                    # Ejecutar la consulta
                    sql_agent = SQLAgent()
                    result = sql_agent.generate_and_execute(question, {})
                    formatted_results = result['results']
        
        # Formatear la salida final
        formatted_output = {
            'query': query,
            'results': formatted_results,
            'reasoning': agent_reasoning,
            'question': question
        }
        
        return formatted_output
    
    except Exception as e:
        logger.error(f"Error processing analysis: {str(e)}")
        raise
    
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
                    # Mostrar el proceso de razonamiento de los agentes
                    st.subheader("🤖 Agent Reasoning Process")
                    for reasoning in result['reasoning']:
                        with st.expander(f"🔍 {reasoning['agent']}", expanded=True):
                            st.write("**Task:**", reasoning['task'])
                            st.write("**Thoughts:**")
                            for thought in reasoning['thoughts']:
                                if thought.strip() and not thought.startswith('```'):
                                    st.markdown(f"- {thought}")
                    
                    # Mostrar consulta SQL
                    st.subheader("Generated SQL Query")
                    st.code(result['query'], language='sql')
                    
                    # Mostrar resultados
                    st.subheader("Results")
                    if result['results']:
                        try:
                            df = pd.DataFrame(result['results'])
                            st.dataframe(df)
                        except Exception as e:
                            st.error(f"Error displaying results: {str(e)}")
                            st.write("Raw results:", result['results'])
                    
                    # Agregar a historial
                    st.session_state['history'].append({
                        'question': question,
                        'output': result,
                        'timestamp': pd.Timestamp.now()
                    })

if __name__ == "__main__":
    main()