# agents/viz_agent.py
from typing import Dict, Any
import logging
from crewai import Agent
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config.config import get_agent_model

logger = logging.getLogger(__name__)

class VizAgent:
    """A wrapper class that combines CrewAI Agent with visualization functionality"""
    
    def __init__(self):
        """Initialize the Visualization Agent"""
        model_config = get_agent_model('viz')
        
        self.agent = Agent(
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
            # Logging para debugging
            logger.info(f"Query results type: {type(query_results)}")
            logger.info(f"Query results content: {query_results}")
            
            # Obtener y procesar los resultados
            results = query_results.get('results', [])
            
            # Convertir tuplas a diccionarios
            if isinstance(results, list) and len(results) > 0:
                # Si es una lista de tuplas, convertir a lista de diccionarios
                if isinstance(results[0], tuple):
                    # Asumir que la primera columna es la categoría y la segunda el valor
                    results_list = [{'categoria': x[0], 'valor': x[1]} for x in results]
                else:
                    results_list = results
            else:
                results_list = []
                
            logger.info(f"Processed results: {results_list}")
            
            if not results_list:
                logger.warning("No results to visualize")
                raise ValueError("No data available for visualization")
            
            # Convertir a DataFrame
            df = pd.DataFrame(results_list)
            logger.info(f"DataFrame shape: {df.shape}")
            logger.info(f"DataFrame columns: {df.columns}")
            
            if df.empty:
                raise ValueError("No data available for visualization")
            
            # Crear la visualización
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")
            
            # Para este caso específico, usamos un gráfico de barras
            sns.barplot(data=df, x='categoria', y='valor')
            plt.xticks(rotation=45)
            plt.title(original_question)
            plt.tight_layout()
            
            return {
                'visualization_type': 'bar',
                'figure': plt.gcf(),
                'data': df.to_dict('records'),
                'columns_used': {
                    'x': 'categoria',
                    'y': 'valor'
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            raise
    
    def __getattr__(self, name):
        """Delegate unknown attributes to the agent"""
        return getattr(self.agent, name)