from typing import Dict, Any
import logging
from crewai import Agent
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config.config import get_agent_model
from src.utils.database import get_crewai_tools

logger = logging.getLogger(__name__)

class VizAgent(Agent):
    def __init__(self, table_name: str = None):
        model_config = get_agent_model('viz')
        
        super().__init__(
            role='Data Visualization Expert',
            goal='Create clear and insightful visualizations from SQL query results',
            backstory="""You are an expert in data visualization who knows how to 
            represent data in the most meaningful way. You understand how to choose 
            the right type of visualization based on the data and the question being asked.""",
            model=model_config['model'],
            tools=get_crewai_tools(table_name),
            verbose=True
        )

    def create_visualization(self, 
                           query_results: Dict, 
                           original_question: str) -> Dict[str, Any]:
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
            
            # Analizar las columnas para determinar el mejor tipo de visualización
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            
            prompt = f"""
            Analyze this data and suggest the best visualization:
            
            Question: {original_question}
            Data Structure:
            - Numeric columns: {list(numeric_cols)}
            - Categorical columns: {list(categorical_cols)}
            - Total records: {len(df)}
            
            Suggest:
            1. Best visualization type (bar, line, scatter, pie, etc.)
            2. Which columns to use for x and y axes
            3. Any data transformations needed
            4. Color scheme and styling suggestions
            
            Consider the question context and data characteristics.
            """
            
            viz_plan = self.llm.generate(prompt)
            
            # Crear la visualización
            plt.figure(figsize=(10, 6))
            
            # Aplicar estilo seaborn
            sns.set_style("whitegrid")
            
            # Determinar el tipo de gráfico basado en el plan
            if "bar" in viz_plan.lower():
                chart_type = "bar"
                if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                    sns.barplot(data=df, x=categorical_cols[0], y=numeric_cols[0])
            elif "line" in viz_plan.lower():
                chart_type = "line"
                if len(numeric_cols) >= 2:
                    sns.lineplot(data=df, x=numeric_cols[0], y=numeric_cols[1])
            elif "scatter" in viz_plan.lower():
                chart_type = "scatter"
                if len(numeric_cols) >= 2:
                    sns.scatterplot(data=df, x=numeric_cols[0], y=numeric_cols[1])
            elif "pie" in viz_plan.lower():
                chart_type = "pie"
                if len(numeric_cols) >= 1:
                    plt.pie(df[numeric_cols[0]], labels=df.index if len(categorical_cols) == 0 else df[categorical_cols[0]])
            else:
                chart_type = "bar"  # Default to bar chart
                if len(numeric_cols) >= 1:
                    df[numeric_cols[0]].plot(kind='bar')
            
            plt.title(original_question)
            plt.tight_layout()
            
            return {
                'visualization_type': chart_type,
                'figure': plt.gcf(),
                'data': df.to_dict('records'),
                'columns_used': {
                    'numeric': list(numeric_cols),
                    'categorical': list(categorical_cols)
                }
            }

        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            raise