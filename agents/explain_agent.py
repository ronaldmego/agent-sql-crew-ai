# agents/explain_agent.py

from typing import Dict, Any
import logging
import pandas as pd
from crewai import Agent
from config.config import get_agent_model

logger = logging.getLogger(__name__)

class ExplainAgent(Agent):
    def __init__(self):
        model_config = get_agent_model('explain')
        
        super().__init__(
            role='Data Insight Analyst',
            goal='Provide clear, insightful explanations of data analysis results',
            backstory="""You are an expert in data interpretation who excels at 
            explaining technical findings in clear, actionable terms. You understand 
            both business context and technical details.""",
            model=model_config['model'],
            verbose=True
        )

    def generate_explanation(self, 
                           question: str, 
                           sql_results: Dict, 
                           viz_info: Dict) -> Dict[str, str]:
        """
        Genera una explicación clara de los resultados
        
        Args:
            question: Pregunta original
            sql_results: Resultados del SQLAgent
            viz_info: Información de visualización del VizAgent
            
        Returns:
            Dict con la explicación y análisis adicional
        """
        try:
            prompt = f"""
            Analyze and explain these analysis results:

            Original Question: {question}
            SQL Query: {sql_results['query']}
            Data Results: {sql_results['results'][:5]}  # Muestra primeros 5 resultados
            Visualization Type: {viz_info['visualization_type']}
            
            Please provide:
            1. A clear explanation of the findings
            2. Key insights from the data
            3. Any notable patterns or trends
            4. Potential business implications
            
            Keep the explanation concise but informative.
            Focus on what would be most valuable to understand.
            """
            
            explanation = self.llm.generate(prompt)
            
            return {
                'explanation': explanation,
                'question': question,
                'total_records': sql_results['row_count'],
                'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            raise