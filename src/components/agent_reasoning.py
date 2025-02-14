import streamlit as st
from typing import List, Dict

def display_agent_reasoning_component(reasoning_steps: List[Dict]):
    """
    Componente de Streamlit para mostrar el razonamiento del agente
    
    Args:
        reasoning_steps: Lista de pasos de razonamiento con formato
        [{'agent': 'nombre', 'thoughts': ['pensamiento1', 'pensamiento2']}]
    """
    st.markdown("""
        <style>
        .agent-step {
            border-left: 3px solid #0066cc;
            padding-left: 10px;
            margin-bottom: 15px;
        }
        .agent-name {
            font-weight: bold;
            color: #0066cc;
        }
        .agent-thought {
            margin-left: 20px;
            color: #666666;
        }
        </style>
    """, unsafe_allow_html=True)

    for step in reasoning_steps:
        with st.container():
            st.markdown(f"""
                <div class="agent-step">
                    <div class="agent-name">🤖 {step['agent']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            for thought in step['thoughts']:
                if thought.strip():
                    st.markdown(f"""
                        <div class="agent-thought">
                            • {thought}
                        </div>
                    """, unsafe_allow_html=True)