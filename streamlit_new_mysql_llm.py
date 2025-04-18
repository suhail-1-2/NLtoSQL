

import os
import re
import warnings
import streamlit as st
from urllib.parse import quote_plus
from dotenv import load_dotenv
from langchain.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
# from langchain.sql_database import SQLDatabase
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq

# Suppress warnings
warnings.simplefilter("ignore", DeprecationWarning)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('google_api_key')
GORQ_API_KEY = os.getenv('gorq_api_key')

# Database Connection
db_user = "root"
db_password = quote_plus("5252300@Ej")
db_host = "127.0.0.1"
db_name = "blockchain_database"

db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

# # Initialize LLM
# llm = ChatGoogleGenerativeAI(
#     model="gemini-1.5-pro",
#     google_api_key=GORQ_API_KEY,
#     max_output_tokens=6000
# )
llm = ChatGroq(model="mixtral-8x7b-32768", api_key= GORQ_API_KEY)
# SQL Query Generator
def extract_sql_query(response: str) -> str:
    """Extracts only the valid SQL query from the LLM response and removes escape characters."""
    match = re.search(r"SELECT.*?;", response, re.IGNORECASE | re.DOTALL)
    if match:
        cleaned_query = match.group(0).strip()
        return cleaned_query.replace("\\", "")  # Remove unnecessary backslashes
    return ""

# Initialize SQL Query Execution
execute_query = QuerySQLDatabaseTool(db=db)

# Answer Formatting
answer_prompt = PromptTemplate.from_template(
    '''
    Given the following user question, corresponding SQL query, and SQL result, answer the user question.
    Question: {question}
    SQL Query: {query} 
    SQL Result: {sql_result}
    Answer: 
    '''
)

rephrase_answer = answer_prompt | llm | StrOutputParser()

# Answer Chain
def answer_question(user_question):
    generate_sql_query = create_sql_query_chain(llm=llm, db=db)
    
    query_response = generate_sql_query.invoke({"question": user_question})
    query = extract_sql_query(query_response)

    if not query:
        return f"Failed to extract SQL query from response: {query_response}"

    sql_result = execute_query.invoke(query)

    answer_chain = (
        RunnablePassthrough.assign(query=lambda x: extract_sql_query(generate_sql_query.invoke(x)))
        .assign(sql_result=lambda x: execute_query.invoke(x["query"]))
        | rephrase_answer
    )

    answer = answer_chain.invoke({"question": user_question})
    return answer

# Streamlit UI
st.title("Blockchain Database Query System")
st.write("Enter a natural language question about blockchain transactions, and get an AI-powered SQL response.")

# User input
user_question = st.text_input("Enter your question:", "")

if st.button("Get Answer"):
    if user_question:
        with st.spinner("Fetching answer..."):
            answer = answer_question(user_question)
            st.subheader("Final Answer:")
            st.write(answer)
    else:
        st.warning("Please enter a question.")

