# agents/viz_agent.py

from typing import Dict, Any
import logging
from crewai import Agent
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config.config import get_agent_model

logger = logging.getLogger(__name__)

class VizAgent(Agent):
    def __init__(self):
        model_config = get_agent_model('viz')
        
        super().__init__(
            role='Data Visualization Expert',
            goal='Create clear and insightful visualizations from SQL query results',
            backstory="""You are an expert in data visualization who knows how to 
            represent data in the most meaningful way. You understand how to choose 
            the right type of visualization based on the data and the question being asked.""",
            model=model_config['model'],
            verbose=True
        )

    def create_visualization(self, query_results: Dict, original_question: str) -> Dict[str, Any]:
        """
        Crea una visualización basada en los resultados de la consulta
        
        Args:
            query_results: Diccionario con los resultados de SQLAgent
            original_question: Pregunta original del usuario
        
        Returns:
            Dict con datos para visualización en Streamlit
        """
        try:
            # Convertir resultados a DataFrame
            df = pd.DataFrame(query_results['results'])
            
            # Consultar al LLM sobre el mejor tipo de visualización
            prompt = f"""
            Analyze these query results and the original question:
            
            Question: {original_question}
            Columns: {query_results['columns']}
            Data Sample: {df.head().to_dict('records')}
            
            Determine:
            1. Best visualization type (bar, line, pie, scatter)
            2. Which columns to use for x and y axes
            3. Any necessary data transformations
            4. Color scheme and styling suggestions
            
            Format response as a JSON-like structure.
            """
            
            viz_plan = self.llm.generate(prompt)
            
            # Preparar datos para visualización en Streamlit
            # Convertimos a formato esperado por el frontend
            viz_data = []
            
            # El agente usará las columnas que el LLM sugirió como mejores para la visualización
            for _, row in df.iterrows():
                # Generamos el formato estándar que espera el frontend
                viz_data.append({
                    "Categoría": str(row[viz_plan['x_column']]),
                    "Cantidad": float(row[viz_plan['y_column']])
                })

            return {
                'visualization_data': viz_data,
                'visualization_type': viz_plan['chart_type'],
                'title': viz_plan.get('title', original_question),
                'x_label': viz_plan.get('x_label', viz_plan['x_column']),
                'y_label': viz_plan.get('y_label', viz_plan['y_column'])
            }

        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            raise