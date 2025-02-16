import os
import streamlit as st
from dotenv import load_dotenv
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
import pandas as pd

# Cargar variables de entorno
load_dotenv()

def init_database():
    """Inicializar conexión a la base de datos"""
    pg_password = os.getenv('POSTGRES_PASSWORD')
    pg_uri = (
        f"postgresql://postgres.klfwwypsvykenulckrwn:{pg_password}@"
        "aws-0-us-west-1.pooler.supabase.com:5432/postgres"
    )
    return SQLDatabase.from_uri(pg_uri)

def process_query(question: str, db: SQLDatabase):
    """Procesar una consulta en lenguaje natural"""
    try:
        # Inicializar componentes
        llm = ChatOpenAI(temperature=0, model="gpt-4")
        write_query = create_sql_query_chain(llm, db)
        execute_query = QuerySQLDataBaseTool(db=db)
        
        # Generar y ejecutar la consulta
        query = write_query.invoke({"question": question})
        result = execute_query.run(query)
        
        return {
            "success": True,
            "query": query,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    st.title("💬 SQL Query Assistant")
    st.write("Ask questions about your database in natural language!")
    
    # Inicializar la base de datos
    db = init_database()
    
    # Input para la pregunta
    question = st.text_input(
        "Ask a question:",
        placeholder="e.g., What tables exist in the database?"
    )
    
    if question:
        with st.spinner("Processing your question..."):
            # Procesar la consulta
            result = process_query(question, db)
            
            if result["success"]:
                # Mostrar la consulta SQL generada
                with st.expander("Generated SQL Query", expanded=True):
                    st.code(result["query"], language="sql")
                
                # Mostrar los resultados
                st.write("### Results")
                if isinstance(result["result"], list):
                    # Convertir a DataFrame si es una lista de tuplas
                    if result["result"] and isinstance(result["result"][0], tuple):
                        df = pd.DataFrame(result["result"])
                        st.dataframe(df)
                    else:
                        st.write(result["result"])
                else:
                    st.write(result["result"])
            else:
                st.error(f"Error: {result['error']}")
                st.write("Please try rephrasing your question.")

if __name__ == "__main__":
    main()