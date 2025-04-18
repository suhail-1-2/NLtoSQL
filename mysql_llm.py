import os
import streamlit as st
import mysql.connector
from dotenv import  load_dotenv
from langchain_groq import ChatGroq
import pandas as pd 
import re

# for requirments download the requirements.txt. -- 
# pip install -r requirements.txt run this command in command prompt or terminal
load_dotenv()
GORQ_API_KEY = os.getenv('groq_api_key')

def generate_SQL_query(human_query):

    prompt = f"""Always respond with an SQL query for the 'Transactions' table, which has columns: transaction_ID, Address_id, Amount, counteraddress_id, date, time TIME (ensuring the time is represented in full as HH:MM:SS), and Type.
                \nUse appropriate SQL clauses (WHERE, ORDER BY, LIMIT) and aggregations as needed. Output only the query without explanations.

                \nHuman Query: {human_query} """

    llm = ChatGroq(model="mixtral-8x7b-32768", api_key= GORQ_API_KEY)
    generated_query = llm.invoke(prompt)

    # Extract the actual query string from the AIMessage object
    if hasattr(generated_query, 'content'):
        query_string = generated_query.content
    else:
        query_string = str(generated_query)

    
    # while running a model (mixtral) it will add \ to the query string, to troubleshoot that issue the below logic is written.
    cleared_query_string = query_string.replace("\\", "") 
    return cleared_query_string


#the function to read the sql query, which hits the database and returns the result.
def read_sql_query(sql):
    # connection = sqlite3.connect("blockchain_suhail.db")
    connection = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='5252300@Ej',
    database='blockchain_database'
)
    cursor =  connection.cursor()
    cursor.execute(sql)
    rows =  cursor.fetchall()
    connection.commit()
    connection.close()
    for row in  rows:
        return rows
def extract_columns_from_query(query):
    
    Transaction_columns = ["transaction_ID", "Address_id", "Amount", "counteraddress_id", "date", "time", "Type"]
   
    # Regex to match column names in the SELECT part of the query this extracts the column names form the query
    match = re.search(r"select\s+(.*?)\s+from", query, re.IGNORECASE)
    
    if match:
        columns_part = match.group(1).strip()
        if columns_part == "*":
            # If the query has `*`, return all predefined columns
            return Transaction_columns
        else:
            # Split the columns by comma and strip whitespace
            column_names = [col.strip() for col in columns_part.split(",")]
            return column_names
        
    else:
        raise ValueError("Invalid SQL query or no columns found in the SELECT part.")
    
    
    

# human_query = str(input("ask your question: "))
# respose_query = generate_SQL_query(human_query)
# column_names = extract_columns_from_query(respose_query)
# data = read_sql_query(respose_query)
# formatted_data = [{column_names[i]: row[i] for i in range(len(row))} for row in data]
# df = pd.DataFrame(data, columns=column_names)
# print(df)

st.set_page_config(page_title= "SQL NL Query")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.header("LLama SQL Interface")

# Input for the natural language query

human_query = st.text_input("Ask your question:",placeholder="Type your question here...")
if st.button("Submit"):
    respose_query = generate_SQL_query(human_query)
    column_names = extract_columns_from_query(respose_query)
    data = read_sql_query(respose_query)
    df = pd.DataFrame(data, columns=column_names)
    if isinstance(df,str):
        st.session_state.chat_history.insert(0,({"user": human_query, "bot": df}))  
    else:
        st.session_state.chat_history.insert(0,({"user": human_query, "bot": df}))


st.subheader("Chat History")
for chat in st.session_state.chat_history:
    st.write(f"<div style='background-color: #f1f1f1; padding: 10px; border-radius: 5px;'><strong>You:</strong> {chat['user']}</div>",unsafe_allow_html=True)
    st.write("  ")
    st.write(chat['bot']) 
    st.markdown("---")








