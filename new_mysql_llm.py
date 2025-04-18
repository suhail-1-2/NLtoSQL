#pip install --upgrade grpcio google-cloud-aiplatform


import os 
from dotenv import load_dotenv
from langchain_community.utilities.sql_database import SQLDatabase
from urllib.parse import quote_plus
from langchain.chains import create_sql_query_chain
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI  
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
import warnings
import re

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

# Initialize LLM
# llm = ChatGoogleGenerativeAI(
#         model="gemini-1.5-pro",
#         google_api_key=GORQ_API_KEY,
#         max_output_tokens=6000
#     )
llm = ChatGroq(model="mixtral-8x7b-32768", api_key= GORQ_API_KEY)
# SQL Query Generator
generate_sql_query = create_sql_query_chain(llm=llm, db=db)

def extract_sql_query(response: str) -> str:
    """Extracts only the valid SQL query from the LLM response and removes escape characters."""
    match = re.search(r"SELECT.*?;", response, re.IGNORECASE | re.DOTALL)
    if match:
        cleaned_query = match.group(0).strip()
        return cleaned_query.replace("\\", "")  # Remove unnecessary backslashes
    return ""
# Generate SQL Query
query_response = generate_sql_query.invoke({"question": "How many columns are there in the transactions table?"})
query = extract_sql_query(query_response)

if not query:
    raise ValueError(f"Failed to extract SQL query from response: {query_response}")

print("Generated SQL Query:", query)

# Execute SQL Query 
execute_query = QuerySQLDatabaseTool(db=db)
sql_result = execute_query.invoke(query)

print("SQL Query Result:", sql_result)

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
answer_chain = (
    RunnablePassthrough.assign(
        query=lambda x: extract_sql_query(generate_sql_query.invoke(x))
    )
    .assign(sql_result=lambda x: execute_query.invoke(x["query"]))
    | rephrase_answer
)

# Final Answer Generation
answer = answer_chain.invoke({"question": "How many 'Outgoing' transactions are there for the month of December 2024??"})

print("Final Answer:", answer)