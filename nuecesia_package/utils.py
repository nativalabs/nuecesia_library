import pandas as pd
import streamlit as st
from sqlalchemy import text
from datetime import datetime, timedelta

@st.cache_data(ttl=60)
def fetch_data(query,_connection):
    data = pd.read_sql(query,_connection)
    return data

def test_function():
    print('Function working correctly')
    return True, False, None

def update_sql_table(connection, table_name, edited_data, original_data, identifier_column, value_column):
    indexes_edited = original_data.compare(edited_data).index
    update_queries = []
    for index in indexes_edited:
        ID_value = edited_data.loc[index, identifier_column]
        new_value = edited_data.loc[index, value_column]
        
        update_query = f"""UPDATE {table_name} SET {value_column} = '{new_value}' WHERE {identifier_column} = '{ID_value}'"""
        update_queries.append(update_query)

    if update_queries:
        try:
            with connection.connect() as conn:
                with conn.begin():
                    for query in update_queries:
                        conn.execute(text(query))
            return True
        except Exception as e:
            print(e)
            return False

def convert_utc_to_chilean_time(utc_timestamp):    
    utc_timestamp = str(utc_timestamp)
    # Parse the UTC timestamp
    utc_time = datetime.strptime(utc_timestamp, "%Y-%m-%d %H:%M:%S")
    # Subtract 4 hours to UTC time for Chilean time
    chilean_time = utc_time - timedelta(hours=4)
    # Format the Chilean time
    formatted_time = chilean_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


