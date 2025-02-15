from typing import Dict, Any
import logging
import pandas as pd
from crewai import Agent
from config.config import get_agent_model

logger = logging.getLogger(__name__)

class ExplainAgent(Agent):
    def __init__(self):
        """Initialize the Explanation Agent"""
        model_config = get_agent_model('explain')
        
        Agent.__init__(
            self,
            role='Data Insight Analyst',
            goal='Provide clear, insightful explanations of data analysis results',
            backstory="""You are an expert in data interpretation who excels at 
            explaining technical findings in clear, actionable terms. You understand 
            both business context and technical details.""",
            model=model_config['model'],
            verbose=True
        )
    
    def generate_explanation(self, question: str, sql_results: Dict, viz_info: Dict) -> Dict[str, str]:
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
            # Asegurarse de que los resultados sean un DataFrame
            if isinstance(sql_results.get('results', []), list):
                results_df = pd.DataFrame(sql_results['results'])
            else:
                results_df = pd.DataFrame([sql_results['results']])
            
            # Convertir todos los valores numéricos a strings para el prompt
            results_str = results_df.astype(str).to_dict('records')
            
            # Construir el prompt para el LLM
            prompt = f"""
            Analyze these results and provide insights:
            Original Question: {question}
            SQL Query: {sql_results.get('query', 'Query not available')}
            
            Data Summary:
            - Total Records: {len(results_df)}
            - Results Preview: {results_str[:5]}
            
            Visualization Info:
            - Type: {viz_info.get('visualization_type', 'Not specified')}
            - Title: {viz_info.get('title', 'Not specified')}
            
            Please provide:
            1. A clear explanation of the findings in business terms
            2. Key insights and patterns discovered
            3. Any notable outliers or unexpected results
            4. Potential business implications or recommendations
            
            Keep the explanation concise but informative, focusing on actionable insights.
            """
            
            # Intentar generar la explicación de diferentes maneras
            try:
                explanation = self.llm.predict(prompt)
            except AttributeError:
                try:
                    explanation = str(self.llm(prompt))
                except:
                    explanation = "Unable to generate detailed explanation at this moment."
            
            return {
                'explanation': explanation,
                'question': question,
                'total_records': len(results_df),
                'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return {
                'explanation': "Unable to generate explanation due to an error",
                'question': question,
                'total_records': 0,
                'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }