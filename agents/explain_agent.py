from typing import Dict, Any
import logging
import pandas as pd
from crewai import Agent
from config.config import get_agent_model
from src.utils.database import get_crewai_tools

logger = logging.getLogger(__name__)

class ExplainAgent(Agent):
    def __init__(self, table_name: str = None):
        model_config = get_agent_model('explain')
        
        super().__init__(
            role='Data Insight Analyst',
            goal='Provide clear, insightful explanations of data analysis results',
            backstory="""You are an expert in data interpretation who excels at 
            explaining technical findings in clear, actionable terms. You understand 
            both business context and technical details.""",
            model=model_config['model'],
            tools=get_crewai_tools(table_name),
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
            # Convertir resultados a DataFrame si es necesario
            results_df = pd.DataFrame(sql_results['results'])
            
            # Calcular estadísticas básicas si hay datos numéricos
            stats = {}
            for column in results_df.select_dtypes(include=['int64', 'float64']).columns:
                stats[column] = {
                    'mean': results_df[column].mean(),
                    'min': results_df[column].min(),
                    'max': results_df[column].max(),
                    'std': results_df[column].std()
                }
            
            prompt = f"""
            Analyze these results and provide insights:

            Original Question: {question}
            SQL Query: {sql_results.get('query', 'Query not available')}
            
            Data Summary:
            - Total Records: {sql_results['row_count']}
            - Columns Analyzed: {', '.join(sql_results['columns'])}
            
            Statistical Summary: {stats if stats else 'No numerical data available'}
            
            Visualization Info:
            - Type: {viz_info.get('visualization_type', 'Not specified')}
            - Title: {viz_info.get('title', 'Not specified')}
            
            Please provide:
            1. A clear explanation of the findings in business terms
            2. Key insights and patterns discovered
            3. Any notable outliers or unexpected results
            4. Potential business implications or recommendations
            5. Data quality considerations (if any)
            
            Keep the explanation concise but informative, focusing on actionable insights.
            """
            
            explanation = self.llm.generate(prompt)
            
            return {
                'explanation': explanation,
                'question': question,
                'statistics': stats,
                'total_records': sql_results['row_count'],
                'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            raise