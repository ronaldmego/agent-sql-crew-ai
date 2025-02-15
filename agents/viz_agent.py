from typing import Dict, Any, Union, List, Tuple
import logging
from crewai import Agent
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config.config import get_agent_model

logger = logging.getLogger(__name__)

class VizAgent(Agent):
    def __init__(self):
        # Get model configuration
        model_config = get_agent_model('viz')
        
        # Initialize the Agent class properly
        Agent.__init__(
            self,
            role='Data Visualization Expert',
            goal='Create clear and insightful visualizations from SQL query results',
            backstory="""You are an expert in data visualization who knows how to 
            represent data in the most meaningful way. You understand how to choose 
            the right type of visualization based on the data and the question being asked.""",
            model=model_config['model'],
            verbose=True
        )
        
        super().__init__(
            role='Data Visualization Expert',
            goal='Create clear and insightful visualizations from SQL query results',
            backstory="""You are an expert in data visualization who knows how to 
            represent data in the most meaningful way. You understand how to choose 
            the right type of visualization based on the data and the question being asked.""",
            model=model_config['model'],
            verbose=True
        )

    def create_visualization(self, query_results: Union[List[Tuple], Dict], original_question: str) -> Dict[str, Any]:
        try:
            logger.info(f"Query results type: {type(query_results)}")
            logger.info(f"Query results content: {query_results}")
            
            # Convertir resultados a DataFrame
            if isinstance(query_results, list):
                df = pd.DataFrame(query_results)
            elif isinstance(query_results, dict):
                results = query_results.get('results', [])
                df = pd.DataFrame(results)
            else:
                raise ValueError(f"Unsupported query_results type: {type(query_results)}")
            
            logger.info(f"DataFrame shape: {df.shape}")
            logger.info(f"DataFrame columns: {df.columns}")
            
            if df.empty:
                raise ValueError("No data available for visualization")
            
            # Crear la visualización
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")
            
            # Asumimos que 'producto' es la columna de categorías y 'total_ventas' es la columna numérica
            sns.barplot(data=df, x='producto', y='total_ventas')
            plt.xticks(rotation=45)
            plt.title(original_question)
            plt.tight_layout()
            
            return {
                'visualization_type': 'bar',
                'figure': plt.gcf(),
                'data': df.to_dict('records'),
                'columns_used': {
                    'x': 'producto',
                    'y': 'total_ventas'
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            raise

    def __getattr__(self, name):
        """Delegate unknown attributes to the agent"""
        if name == 'agent':
            raise AttributeError(f"'VizAgent' object has no attribute 'agent'")
        return super().__getattr__(name)