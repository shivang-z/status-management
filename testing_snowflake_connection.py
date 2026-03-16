import streamlit as st
import snowflake.connector
import pandas as pd

# Load connection config from secrets
conn_config = st.secrets["connections"]["my_example_connection"]

try:
    # Create Snowflake connection
    conn = snowflake.connector.connect(
        account=conn_config["account"],
        user=conn_config["user"],
        authenticator=conn_config["authenticator"],
        role=conn_config["role"],
        warehouse=conn_config["warehouse"],
        database=conn_config["database"],
        schema=conn_config["schema"],
    )

    st.success("✅ Connected to Snowflake")

    query = """
    SELECT *
    FROM rcm.rcm.UNITS_SUMMARY_PBI_INFLOW_BACKLOG
    LIMIT 10
    """

    # Execute query
    cur = conn.cursor()
    cur.execute(query)

    # Convert result to pandas dataframe
    df = cur.fetch_pandas_all()

    st.subheader("Query Result")
    st.dataframe(df, use_container_width=True)

    cur.close()
    conn.close()

except Exception as e:
    st.error(f"❌ Error: {e}")