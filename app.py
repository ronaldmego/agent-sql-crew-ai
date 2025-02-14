import streamlit as st
from crewai import Crew, Task
from sqlalchemy import create_engine
import pandas as pd
from src.utils.database import get_mysql_uri, get_table_names, get_table_schema
from src.utils.agent_output_handler import AgentOutputHandler
from src.components.agent_reasoning import display_agent_reasoning_component
from typing import Dict, Any
from agents.schema_agent import SchemaAgent
from agents.sql_agent import SQLAgent
from agents.viz_agent import VizAgent
from agents.explain_agent import ExplainAgent
import matplotlib.pyplot as plt
import re

def initialize_session_state() -> None:
    """Initialize session state variables"""
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'selected_table' not in st.session_state:
        st.session_state['selected_table'] = None
    if 'schema_info' not in st.session_state:
        st.session_state['schema_info'] = None
    if 'current_table_schema' not in st.session_state:
        st.session_state['current_table_schema'] = None

def create_agents(table_name: str):
    """Create instances of all agents with table context"""
    return {
        'schema': SchemaAgent(table_name=table_name),
        'sql': SQLAgent(table_name=table_name),
        'viz': VizAgent(table_name=table_name),
        'explain': ExplainAgent(table_name=table_name)
    }

def create_crew(question: str, selected_table: str) -> Crew:
    """Create and configure the CrewAI crew"""
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

# Justo después de las importaciones en app.py, antes de initialize_session_state()
def convert_df_types(df):
    """Convert DataFrame types to be compatible with Streamlit"""
    for col in df.columns:
        # Convert any problematic types to string
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
        elif 'datetime' in str(df[col].dtype):
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

def display_query_results(results: Dict):
    """Display query results in a structured way"""
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
            st.info(f"Total records: {results['row_count']}")
            
        except Exception as e:
            st.error(f"Error displaying results: {str(e)}")
            st.write("Raw results:")
            st.write(results['results'])

def display_table_schema(schema_info: Dict):
    """Display table schema information in a structured way"""
    if not schema_info:
        st.warning("No schema information available")
        return
        
    st.write("### Table Structure")
    
    try:
        # Display columns
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
        
        # Display keys
        if schema_info.get('primary_key'):
            st.write("#### Primary Key")
            st.write(", ".join(schema_info['primary_key']))
        
        if schema_info.get('foreign_keys'):
            st.write("#### Foreign Keys")
            for fk in schema_info['foreign_keys']:
                st.write(f"- {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}")
                
    except Exception as e:
        st.error(f"Error displaying schema: {str(e)}")
        st.write("Raw schema:")
        st.write(schema_info)

def main():
    initialize_session_state()
    
    # Header
    st.title("📊 SQL Query Assistant with CrewAI")
    st.write("Ask questions about your data in natural language")
    
    # Sidebar - Database Configuration
    with st.sidebar:
        st.header("Configuration")
        
        try:
            engine = create_engine(get_mysql_uri())
            tables = get_table_names(engine)
            
            selected_table = st.selectbox(
                "Select a table to analyze:",
                options=tables,
                key='table_selector'
            )
            
            if selected_table != st.session_state.get('selected_table'):
                st.session_state['selected_table'] = selected_table
                st.session_state['current_table_schema'] = get_table_schema(engine, selected_table)
                
                # Display schema information
                if st.session_state['current_table_schema']:
                    display_table_schema(st.session_state['current_table_schema'])
                
        except Exception as e:
            st.error(f"Database connection error: {str(e)}")
            st.stop()
    
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
                    # Process analysis with CrewAI
                    crew = create_crew(question, selected_table)
                    result = crew.kickoff()
                    
                    # Format and display results
                    formatted_output = AgentOutputHandler.format_agent_output(result)
                    
                    if formatted_output:
                        # Display the reasoning process
                        with st.expander("Agent Reasoning Process", expanded=True):
                            display_agent_reasoning_component(formatted_output['reasoning'])
                        
                        # Display SQL Query
                        if 'query' in formatted_output:
                            st.subheader("Generated SQL Query")
                            st.code(formatted_output['query'], language='sql')
                        
                        # Display Results
                        if 'results' in formatted_output:
                            display_query_results(formatted_output)
                        
                        # Display Visualization
                        if 'visualization_fig' in formatted_output:
                            st.subheader("Data Visualization")
                            st.pyplot(formatted_output['visualization_fig'])
                        
                        # Add to history
                        st.session_state['history'].append({
                            'question': question,
                            'output': formatted_output,
                            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.error("Please try again with a different question.")
        
        # Display History
        if st.session_state['history']:
            st.subheader("Question History")
            for item in reversed(st.session_state['history']):
                with st.expander(f"Q: {item['question']} ({item['timestamp']})"):
                    if 'reasoning' in item['output']:
                        display_agent_reasoning_component(item['output']['reasoning'])
                    if 'query' in item['output']:
                        st.code(item['output']['query'], language='sql')
                    if 'results' in item['output']:
                        display_query_results(item['output'])

if __name__ == "__main__":
    main()