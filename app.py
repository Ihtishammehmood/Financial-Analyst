from Custom_tools import get_profit_and_loss,balance_sheet,cash_flow
import streamlit as st
import pandas as pd
import logging
import yfinance as yf
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.yfinance import YFinanceTools
# from dotenv import load_dotenv

# load_dotenv()
google_api_key = st.secrets["GOOGLE_API_KEY"]

# Initialize the finance agent if not already in session state
if "finance_agent" not in st.session_state:
    st.session_state.finance_agent = Agent(
        name="Finance Agent",
        model=Gemini(id="gemini-2.0-flash-exp",api_key=google_api_key),
        tools=[
            YFinanceTools(
                stock_price=True,
                analyst_recommendations=True,
                company_info=True,
                company_news=True
            ),get_profit_and_loss,balance_sheet,cash_flow
        ],
        instructions=["Always Use tables to display data",
            "Only provide information related to financial analysis",
            "If asked about non-financial topics, respond with 'This is outside of my expertise.'",
            "Use 'get_profit_and_loss' function to get income statement or profit and loss statement of a given stock symbol."
            "Use 'balance_sheet' function to get balance sheet of a given stock symbol."
            "Use 'cash_flow' function to get cash flow statement of a given stock symbol."],
        # show_tool_calls=True,
        markdown=True,
        # debug_mode=True  # Uncomment for debugging
    )

st.set_page_config(
    page_title="Financial Analyst",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",  
    initial_sidebar_state="expanded"  
)

st.title("Financial Analyst")
st.markdown("##### :chart_with_upwards_trend: Interact with the Finance Agent to get stock analysis and insights.")


st.sidebar.title("About This App")
st.sidebar.markdown("""
This web application serves as a Financial Analyst Agent, providing users with insights and analysis on stock prices, analyst recommendations, company information, and news. It leverages advanced models and tools to deliver accurate and up-to-date financial data. Please note that the agent is specialized in financial topics and will indicate if a query is outside its expertise.
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### Links")
st.sidebar.markdown("[GitHub Repository ](https://github.com/Ihtishammehmood/Financial-Analyst.git)")
st.sidebar.markdown("[LinkedIn Profile](https://www.linkedin.com/in/ihtishammehmood/)")
st.sidebar.markdown("[Company Website](https://www.deepmindcraft.online/)")
st.sidebar.markdown("[Portfolio Website](https://ihtishammehmood.github.io//)")



if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages in a container
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Ask about stocks..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display assistant's response
    with st.chat_message("assistant"):
        response_container = st.empty()
        response = ""
        try:
            with st.spinner("Thinking..."):
                for delta in st.session_state.finance_agent.run(message=prompt, stream=True):
                    response += delta.content  # Append each response delta to the response string
                    response_container.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Add footer or additional information
st.markdown("---")
st.markdown("Created by Ihtisham.M with :heart:")

