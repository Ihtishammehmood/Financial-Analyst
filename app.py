import streamlit as st
from pathlib import Path
import pandas as pd
import shutil
import yfinance as yf
from phi.agent.python import PythonAgent
from phi.agent import Agent
from phi.model.google import Gemini
from phi.file.local.csv import CsvFile
from phi.tools.yfinance import YFinanceTools
from Custom_tools import get_profit_and_loss, balance_sheet, cash_flow

# Set page config
st.set_page_config(
    page_title="Data Analysis Suite",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
def initialize_session_state():
    session_vars = {
        "csv_file_uploaded": False,
        "csv_messages": [],
        "finance_messages": [],
        "active_tab": "Data Analyst"
    }
    for key, value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# Configure paths and API keys
google_api_key = st.secrets["GOOGLE_API_KEY"]
cwd = Path(__file__).parent.resolve()
tmp = cwd.joinpath("tmp")

# Utility functions
def cleanup_temp_folder():
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(exist_ok=True, parents=True)

# Clean up the tmp folder at the start
cleanup_temp_folder()

# Sidebar configuration
st.sidebar.title("Navigation")
st.session_state.active_tab = st.sidebar.radio("Select Analyst", 
                                             ["Data Analyst", "Financial Analyst"])

st.sidebar.markdown("---")
st.sidebar.title("About This Suite")
st.sidebar.markdown("""
**Data Analysis Suite** combines powerful tools for:
- CSV data exploration
- Financial market analysis
- Interactive data visualization
- Automated insights generation
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### Useful Links")
st.sidebar.markdown("[GitHub Repository](https://github.com/Ihtishammehmood/Financial-Analyst.git)")
st.sidebar.markdown("[Company Website](https://www.deepmindcraft.online/)")
st.sidebar.markdown("[Personal Portfolio](https://ihtishammehmood.github.io/)")
st.sidebar.markdown("[Support](mailto:ihtisahm@deepmindcraft.online)")

# CSV Analyst Tab
if st.session_state.active_tab == "Data Analyst":
      
    st.markdown(
    """
    <div style="text-align: center;">
        <h1>📊 Data Analyst</h1>
        <h3>Interactive Data Exploration & Visualization</h3>
    </div>
    """,
    unsafe_allow_html=True
)

    # File upload section
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=["csv"],
        help="Maximum file size: 200MB"
    )

    if uploaded_file is not None:
        cleanup_temp_folder()
        file_path = tmp / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.session_state.csv_file_uploaded = True
        st.session_state.csv_file_path = file_path
        
        with st.expander("Preview Dataset"):
            df = pd.read_csv(file_path)
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Dataset Shape: {df.shape} | Columns: {', '.join(df.columns)}")

    if st.session_state.csv_file_uploaded:
        # Initialize Python Agent
        if "csv_agent" not in st.session_state:
            st.session_state.csv_agent = PythonAgent(
                model=Gemini(model=Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key)),
                base_dir=tmp,
                files=[CsvFile(path=str(st.session_state.csv_file_path), description="Uploaded dataset")],
                instructions=[
                    "As as data analyst,You only specialized in data analysis and visualization.Only generate response based on the uploaded dataset",
                    "Never display python code used to generate the output to user",
                    "Use plotly.express for visualizations",
                    "Never display executed code at all cost",
                    "Validate code before execution",
                    "Don't save plots and chart in .png or .html instead Use st.plotly_chart() for display",
                    "Include data quality checks",
                    "Provide actionable insights",
                    
                    
                ],
                pip_install=True,
                markdown=True
            )

        # Chat interface for CSV analysis
        st.divider()
        st.markdown("### Analysis Chat")

        for message in st.session_state.csv_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about your data..."):
            st.session_state.csv_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                try:
                    with st.spinner('Thinking...'):
                        response = st.session_state.csv_agent.run(prompt)
                        response_placeholder.markdown(response.content)
                        st.session_state.csv_messages.append(
                            {"role": "assistant", "content": response.content}
                        )
                except Exception as e:
                    st.error(f"Analysis error: {str(e)}")

        if st.button("Clear CSV Chat"):
            st.session_state.csv_messages = []
            st.rerun()

# Financial Analyst Tab
elif st.session_state.active_tab == "Financial Analyst":
    st.markdown(
    """
    <div style="text-align: center;">
        <h1>📈 Financial Analyst</h1>
        <h3>Real-time Market Analysis & Insights</h3>
    </div>
    """,
    unsafe_allow_html=True
)

    # Initialize Finance Agent
    if "finance_agent" not in st.session_state:
        st.session_state.finance_agent = Agent(
            name="Finance Expert",
            model=Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key),
            tools=[
                YFinanceTools(
                    stock_price=True,
                    analyst_recommendations=True,
                    company_info=True,
                    company_news=True
                ),
                get_profit_and_loss,
                balance_sheet,
                cash_flow
            ],
            instructions=[
                "As as financial analyst you only work with financial data.Never answer questions outside of finance.",
                "Use markdown tables for financial data",
                "Include key metrics in bold",
                "Compare historical performance",
                "Highlight risk factors",
                "Suggest comparable companies"
            ],
            markdown=True
        )

    # Financial chat interface
    st.divider()
    st.markdown("### Financial Insights Chat")

    for message in st.session_state.finance_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about stocks or companies..."):
        st.session_state.finance_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""
            
            try:
                with st.spinner('Thinking...'):
                    for delta in st.session_state.finance_agent.run(prompt, stream=True):
                        full_response += delta.content
                        response_container.markdown(full_response + "▌")
                    response_container.markdown(full_response)
                    st.session_state.finance_messages.append(
                        {"role": "assistant", "content": full_response}
                    )
            except Exception as e:
                st.error(f"Financial analysis error: {str(e)}")

    if st.button("Clear Finance Chat"):
        st.session_state.finance_messages = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown(" 📈 **Real-time Data** | 🤖 **AI-Powered Insights**")
st.markdown("---")
st.caption("Author: Ihtisham M | [linkedIn](www.linkedin.com/in/ihtishammehmood)")

# Style enhancements
st.markdown("""
<style>
    .stChatInput {position: fixed; bottom: 20px; width: 63%;}
    .stChatMessage {padding: 1.5rem;}
    [data-testid="stSidebar"] {background: #f5f9ff;}
</style>
""", unsafe_allow_html=True)