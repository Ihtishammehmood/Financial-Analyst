import streamlit as st
import os
import base64
import pandas as pd
import google.generativeai as genai

from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
# import io


# --- Configuration & Setup ---
st.set_page_config(
    page_title="Data Analyst AI",
    page_icon="📊",
    layout="wide"
)

# Load environment variables (support for .env file or st.secrets)
load_dotenv()

# Helper to get API keys safely
def get_api_key(key_name):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name)

GEMINI_API_KEY = get_api_key("GEMINI_API_KEY")
E2B_API_KEY = get_api_key("E2B_API_KEY")

if not GEMINI_API_KEY or not E2B_API_KEY:
    st.error("🚨 API Keys missing! Please set GEMINI_API_KEY and E2B_API_KEY in your .env file or Streamlit secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "sandbox" not in st.session_state:
    # We store the sandbox object in session state to persist it across reruns
    try:
        st.session_state.sandbox = Sandbox.create(api_key=E2B_API_KEY)
    except Exception as e:
        st.error(f"Failed to create sandbox: {e}")
        st.stop()

if "dataset_info" not in st.session_state:
    st.session_state.dataset_info = None

# --- Helper Functions ---

def upload_to_sandbox(uploaded_file):
    """Uploads the Streamlit file object to the E2B sandbox."""
    try:
        # Read file as bytes
        file_bytes = uploaded_file.getvalue()
        
        # Save to sandbox
        remote_path = st.session_state.sandbox.files.write("dataset.csv", file_bytes)
        
        # Extract metadata (columns, etc) for the prompt context
        df = pd.read_csv(uploaded_file)
        columns = list(df.columns)
        head = df.head(3).to_markdown(index=False)
        
        info = {
            "path": remote_path,
            "columns": columns,
            "preview": head,
            "rows": len(df)
        }
        st.session_state.dataset_info = info
        return info
    except Exception as e:
        st.error(f"Error uploading file to sandbox: {e}")
        return None

def run_code_in_sandbox(code):
    """Executes Python code in the E2B sandbox and processes results."""
    sbx = st.session_state.sandbox
    
    try:
        execution = sbx.run_code(code)
    except Exception as e:
        return {"error": str(e), "text_output": "", "images": []}

    if execution.error:
        error_msg = f"{execution.error.name}: {execution.error.value}\n{execution.error.traceback}"
        return {"error": error_msg, "text_output": "", "images": []}

    images = []
    for result in execution.results:
        if result.png:
            # Decode base64 image
            img_data = base64.b64decode(result.png)
            images.append(img_data)
    
    # Capture standard output (print statements)
    text_output = "".join(execution.logs.stdout)
    
    return {"error": None, "text_output": text_output, "images": images}

def generate_response(user_query, dataset_info):
    """Interacts with Gemini to generate code or text."""
    
    # 1. Define Tools
    tools = [
        {
            "function_declarations": [
                {
                    "name": "run_python_code",
                    "description": "Executes Python code to analyze data or generate charts. Use matplotlib/seaborn for plots. The dataset is at 'dataset.csv'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The Python code to run."
                            }
                        },
                        "required": ["code"],
                    },
                }
            ]
        }
    ]

    # 2. Construct Prompt
    system_context = f"""
    You are an expert Python Data Analyst.
    A CSV file is loaded in the environment at path: '{dataset_info['path']}'.
    It has {dataset_info['rows']} rows.
    
    Here is a preview of the data:
    {dataset_info['preview']}
    
    Columns: {', '.join(dataset_info['columns'])}

    When asked to visualize, use Matplotlib or Seaborn. 
    ALWAYS save charts using `plt.show()` (the environment captures this) or print textual analysis.
    Do NOT open files using `os.startfile` or `plt.savefig` unless asked.
    
    If the user's request requires code, call the `run_python_code` function.
    If it's a general question, just answer.
    """
    
    model = genai.GenerativeModel("gemini-3-flash-preview", tools=tools, system_instruction=system_context)
    
    chat = model.start_chat(enable_automatic_function_calling=False) # We handle execution manually
    
    try:
        response = chat.send_message(user_query)
        return response
    except Exception as e:
        return f"Error communicating with AI: {e}"

# --- UI Layout ---

st.sidebar.title("📁 Data Setup")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# --- Main Logic ---

st.title("Data Analysis Suite")
st.markdown("Here to help you with data analysis and visualization.")

# Handle File Upload
if uploaded_file:
    # Check if this is a new file or if we haven't processed it yet
    current_file_name = uploaded_file.name
    if (st.session_state.dataset_info is None) or (st.session_state.get("last_uploaded") != current_file_name):
        with st.spinner("Uploading and analyzing dataset..."):
            info = upload_to_sandbox(uploaded_file)
            if info:
                st.session_state.last_uploaded = current_file_name
                st.sidebar.success(f"Loaded: {current_file_name}")
                # Add a system message indicating success
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I've loaded **{current_file_name}**. It has {info['rows']} rows. How can I help you?"
                })
    else:
        st.sidebar.info(f"Active: {current_file_name}")

else:
    st.info("Please upload a CSV file in the sidebar to begin.")
    st.stop()


# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "content" in msg and msg["content"]:
            st.markdown(msg["content"])
        if "images" in msg:
            for img in msg["images"]:
                st.image(img)
        if "code" in msg:
            with st.expander("View Code"):
                st.code(msg["code"], language="python")

# Chat Input
if prompt := st.chat_input("Ask a question about your data (e.g., 'Plot vote_average over time')"):
    
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Process with AI
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt, st.session_state.dataset_info)
            
            # Check for function call
            function_call = None
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if part.function_call:
                        function_call = part.function_call
                        break
            
            if function_call and function_call.name == "run_python_code":
                code_to_run = function_call.args["code"]
                
                # Show status
                message_placeholder = st.empty()
                message_placeholder.markdown("⚙️ *Generating and running code...*")
                
                # Execute Code
                result = run_code_in_sandbox(code_to_run)
                
                message_placeholder.empty() # Clear status
                
                # Prepare response content
                response_content = ""
                
                if result["error"]:
                    response_content = f"**Error executing code:**\n```\n{result['error']}\n```"
                else:
                    if result["text_output"]:
                        response_content += f"**Output:**\n```\n{result['text_output']}\n```\n"
                
                # Update Session State
                assistant_message = {
                    "role": "assistant",
                    "content": response_content,
                    "code": code_to_run,
                    "images": result["images"]
                }
                
                # Display Immediately
                if response_content:
                    st.markdown(response_content)
                
                if result["images"]:
                    for img in result["images"]:
                        st.image(img)
                    if not response_content:
                        st.markdown("*Chart generated successfully.*")

                with st.expander("View Code"):
                    st.code(code_to_run, language="python")
                
                st.session_state.messages.append(assistant_message)
                
            else:
                # Text-only response
                text_response = response.text if hasattr(response, 'text') else "I couldn't generate a response."
                st.markdown(text_response)
                st.session_state.messages.append({"role": "assistant", "content": text_response})