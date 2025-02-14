import streamlit as st
from typing import Dict, Any
import re

class AgentOutputHandler:
    @staticmethod
    def format_agent_output(crew_output: Any) -> Dict[str, Any]:
        """Formatea la salida del agente para su visualización"""
        formatted_output = {
            'question': '',
            'reasoning': [],
            'query': '',
            'visualization': None,
            'insights': ''
        }
        
        try:
            # Verificamos si crew_output es una tupla
            if isinstance(crew_output, tuple):
                # Procesamos cada elemento de la tupla
                for output in crew_output:
                    # Verificamos si el output tiene el formato esperado
                    if hasattr(output, 'task'):
                        agent_name = output.task.description
                        content = str(output.output)  # Convertimos el output a string
                    else:
                        # Si no tiene el formato esperado, usamos str() directamente
                        agent_name = "Agent"
                        content = str(output)
                    
                    # Identificar si es una consulta SQL
                    if "SQL query for:" in agent_name:
                        sql_match = re.search(r"```sql\s*(.*?)\s*```", content, re.DOTALL)
                        if sql_match:
                            formatted_output['query'] = sql_match.group(1).strip()
                    
                    # Agregar al razonamiento
                    formatted_output['reasoning'].append({
                        'agent': agent_name,
                        'thoughts': content.split('\n')
                    })
            else:
                # Si no es una tupla, agregamos directamente como un solo resultado
                formatted_output['reasoning'].append({
                    'agent': "Analysis Result",
                    'thoughts': [str(crew_output)]
                })
            
            return formatted_output
            
        except Exception as e:
            st.error(f"Error formatting agent output: {str(e)}")
            raise  # Agregamos raise para ver el error completo en desarrollo
            return formatted_output

    @staticmethod
    def display_agent_reasoning(reasoning_data: list):
        """Muestra el proceso de razonamiento en Streamlit"""
        st.subheader("🤖 Agent Reasoning Process")
        
        for step in reasoning_data:
            with st.expander(f"🔍 {step['agent']}", expanded=False):
                for thought in step['thoughts']:
                    if thought.strip():
                        # Remover marcadores markdown y limpiar el texto
                        cleaned_thought = re.sub(r'#+ ', '', thought).strip()
                        if cleaned_thought and not cleaned_thought.startswith('Agent:'):
                            st.markdown(f"- {cleaned_thought}")

    @staticmethod
    def display_results(formatted_output: Dict[str, Any]):
        """Muestra los resultados en Streamlit"""
        # Mostrar el proceso de razonamiento
        AgentOutputHandler.display_agent_reasoning(formatted_output['reasoning'])

        # Mostrar la consulta SQL si existe
        if formatted_output['query']:
            st.subheader("🔍 Generated SQL Query")
            st.code(formatted_output['query'], language='sql')