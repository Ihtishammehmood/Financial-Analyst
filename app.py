
import streamlit as st
from pathlib import Path
import pandas as pd
import shutil
from phi.model.google import Gemini
from phi.agent.python import PythonAgent
from phi.agent import Agent
from phi.tools.yfinance import YFinanceTools
from phi.file.local.csv import CsvFile
from typing import Optional, Dict, List
from Custom_tools import get_profit_and_loss, balance_sheet, cash_flow

# Constants and Configuration
class Config:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    CWD = Path(__file__).parent.resolve()
    TMP_DIR = CWD / "tmp"
    PAGE_CONFIG = {
        "page_title": "Analysis Suite",
        "page_icon": ":bar_chart:",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    AGENT_INSTRUCTIONS = {
        "csv": [
            "As as data analyst,You only specialized in data analysis and visualization.Only generate response based on the uploaded dataset",
            "Always generate python code to perform the analysis and visualization",
            "use pandas for data manipulation and analysis",
            "Never display python code used to generate the output to user",
            # "The uploaded .csv file is always stored in tmp folder",
            "Use plotly.express for visualizations",
            # "Validate code before execution",
            "Don't save plots and chart in .png or .html instead Use st.plotly_chart() for display",
            "Include data quality checks",
            # "Only Provide actionable insights when not generating any visualization",
        ],
        
        "finance": [
            "As a financial analyst, only respond to financial questions",
            "Use markdown tables for financial data",
            "Highlight key metrics and Actional Insights",
            "Suggest comparable companies"
        ]
    }

# Utility Functions
def manage_temp_directory() -> None:
    """Manage temporary directory with cleanup and recreation."""
    try:
        if Config.TMP_DIR.exists():
            shutil.rmtree(Config.TMP_DIR)
        Config.TMP_DIR.mkdir(exist_ok=True, parents=True)
    except OSError as e:
        st.error(f"Directory management error: {str(e)}")
        raise

def initialize_session_state() -> None:
    """Initialize all session state variables."""
    session_defaults = {
        "csv_file_uploaded": False,
        "csv_messages": [],
        "finance_messages": [],
        "active_tab": "Data Analyst"
    }
    for key, value in session_defaults.items():
        st.session_state.setdefault(key, value)

def setup_sidebar() -> None:
    """Configure the sidebar navigation and information."""
    st.sidebar.title("Navigation")
    st.session_state.active_tab = st.sidebar.radio(
        "Select Analyst", 
        ["Data Analyst", "Financial Analyst"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.title("About This Suite")
    st.sidebar.markdown("""
    **Analysis Suite** combines powerful tools for:
    - CSV data exploration
    - Financial market analysis
    - Interactive visualization
    - AI-powered insights
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Useful Links")
    links = {
        "GitHub Repository": "https://github.com/Ihtishammehmood/Financial-Analyst.git",
        "Company Website": "https://www.deepmindcraft.online/",
        "Personal Portfolio": "https://ihtishammehmood.github.io/",
        "Support": "mailto:ihtisahm@deepmindcraft.online"
    }
    for text, url in links.items():
        st.sidebar.markdown(f"[{text}]({url})")

# Agent Management
def create_csv_agent(file_path: Path) -> PythonAgent:
    """Create and configure CSV analysis agent."""
    return PythonAgent(
        model=Gemini(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=Config.GOOGLE_API_KEY)
        ),
        base_dir=Config.TMP_DIR,
        files=[CsvFile(path=str(file_path), description="Uploaded dataset")],
        instructions=Config.AGENT_INSTRUCTIONS["csv"],
        pip_install=True,
        markdown=True
    )

def create_finance_agent() -> Agent:
    """Create and configure financial analysis agent."""
    return Agent(
        name="Finance Expert",
        model=Gemini(id="gemini-2.0-flash-exp", api_key=Config.GOOGLE_API_KEY),
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
        instructions=Config.AGENT_INSTRUCTIONS["finance"],
        markdown=True
    )

# Chat Handlers
def handle_chat_interface(
    agent: Agent,
    session_key: str,
    empty_state_message: str
) -> None:
    """Generic handler for chat interfaces."""
    messages = st.session_state.get(session_key, [])
    
    if not messages:
        st.info(empty_state_message)
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your question..."):
        messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response_container = st.empty()
                full_response = ""
                
                with st.spinner('Analyzing...'):
                    for delta in agent.run(prompt, stream=True):
                        full_response += delta.content
                        response_container.markdown(full_response + "▌")
                    
                    response_container.markdown(full_response)
                    messages.append({"role": "assistant", "content": full_response})
                    st.session_state[session_key] = messages
                    
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")
                messages.pop()  # Remove failed prompt

# Main Application
def main() -> None:
    """Main application entry point."""
    st.set_page_config(**Config.PAGE_CONFIG)
    initialize_session_state()
    manage_temp_directory()
    setup_sidebar()
    
    # Header Section
    st.markdown(f"""
    <div style="text-align: center;">
        <h1>{'📊' if st.session_state.active_tab == 'Data Analyst' else '📈'} 
        {st.session_state.active_tab}</h1>
        <h3>{'Interactive Data Exploration & Analysis' if st.session_state.active_tab == 'Data Analyst' else 'Real-time Market Analysis'}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab-Specific Logic
    if st.session_state.active_tab == "Data Analyst":
        handle_data_analyst_tab()
    else:
        handle_financial_analyst_tab()
    
    # Footer Section
    # st.markdown("---")
    # st.markdown("📈 **Real-time Data** | 🤖 **AI-Powered Insights**")
    st.markdown("---")
    st.caption("Author: Ihtisham M | [LinkedIn](https://www.linkedin.com/in/ihtishammehmood)")

def handle_data_analyst_tab() -> None:
    """Handle CSV data analysis tab."""
    uploaded_file = st.file_uploader(
        "Upload CSV File", 
        type=["csv"],
        help="Maximum file size: 200MB"
    )
    
    if uploaded_file:
        process_uploaded_file(uploaded_file)
        
        if st.session_state.csv_file_uploaded:
            if "csv_agent" not in st.session_state:
                st.session_state.csv_agent = create_csv_agent(
                    st.session_state.csv_file_path
                )
            
            st.divider()
            handle_chat_interface(
                agent=st.session_state.csv_agent,
                session_key="csv_messages",
                empty_state_message="Ask questions about your CSV data to get started"
            )

def process_uploaded_file(uploaded_file) -> None:
    """Process and validate uploaded CSV file."""
    try:
        file_path = Config.TMP_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Validate CSV
        df = pd.read_csv(file_path)
        if df.empty:
            st.error("Uploaded file is empty")
            return
        
        st.session_state.csv_file_uploaded = True
        st.session_state.csv_file_path = file_path
        
        with st.expander("Dataset Preview"):
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Dataset Shape: {df.shape} | Columns: {', '.join(df.columns)}")
            
    except pd.errors.ParserError:
        st.error("Invalid CSV file format")
    except Exception as e:
        st.error(f"File processing error: {str(e)}")

def handle_financial_analyst_tab() -> None:
    """Handle financial analysis tab."""
    if "finance_agent" not in st.session_state:
        st.session_state.finance_agent = create_finance_agent()
    
    st.divider()
    handle_chat_interface(
        agent=st.session_state.finance_agent,
        session_key="finance_messages",
        empty_state_message="Ask about stocks, companies, or market trends"
    )

# Run the application
if __name__ == "__main__":
    main()