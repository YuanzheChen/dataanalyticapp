import streamlit as st
import pandas as pd
import os
import re
import subprocess
import sys
import matplotlib.pyplot as plt
from langchain.llms import AzureOpenAI
from langchain.agents import create_csv_agent
from langchain.agents.agent_types import AgentType
from io import StringIO
from contextlib import redirect_stdout
from config import Config


class DataAnalyticApp:
    """
        excel数据分析demo
    """

    def __init__(self):
        self.init_env()
        self.llm = AzureOpenAI(deployment_name=Config.DEPLOYMENT_NAME, model_name=Config.MODEL_NAME)
        self.csv_agent = create_csv_agent(
            self.llm,
            Config.FILE_PATH,
            verbose=True,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
        )
        self.is_self_debugging = False
        self.retry_num = 0

    def init_env(self):
        os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY
        os.environ["OPENAI_API_BASE"] = Config.OPENAI_API_BASE
        os.environ["OPENAI_API_TYPE"] = Config.OPENAI_API_TYPE
        os.environ["OPENAI_API_VERSION"] = Config.OPENAI_API_VERSION

    def extract_code_from_response(self, response):
        """Extracts Python code from response."""
        """Return answer and code separately."""

        if isinstance(response, str):
            # workaround approach to handle langchain exception, better revise langchain source code instead
            response = response.split('::')
            if len(response) > 1:
                response = response[1]
                res = response.split('\n\n')[0]
                arr = res.split('PYTHON')
                if len(arr) > 1:
                    answer = arr[0]
                    code = arr[1]
                    code = code.lstrip()
                    return answer, code
                else:
                    return response, None
            else:
                return response[0], None
        else:
            res = response['output']
            res = res.split('<|im_end|>')[0]
            res = res.split('<|im_sep|>')[0]
            arr = res.split('PYTHON')
            if len(arr) > 1:
                answer = arr[0]
                code = arr[1]
                code = code.lstrip()
                return answer, code
            else:
                return response['output'], None

    def call_csv_agent(self, user_message):
        """Run the CSV agent with user message."""
        try:
            # Properly format the user's input and wrap it with the required "input" key
            tool_input = {
                "input": {
                    "name": "python",
                    "arguments": user_message + ' write the entire code you generated in a single string, and add the word PYTHON before this string.'
                }
            }
            response = self.csv_agent(tool_input)
            return response
        except Exception as e:
            rs = e.args[0]
            return rs

    def call_python_debug_agent(self, code, err_msg):
        """Ask python agent to generate correct python code."""
        try:
            tool_input = {
                "input": {
                    "name": "python",
                    "arguments": 'Error "' + err_msg + '"occurs when execute the following code: ' + code + 'write the corrected code in a single string, and add the word PYTHON before this string.'
                }
            }
            response = self.csv_agent(tool_input)
            return response
        except Exception as e:
            rs = e.args[0]
            return rs

    def response_handler(self, response, df):
        # Extracting code from the response
        answer, code_to_execute = self.extract_code_from_response(response)

        if code_to_execute:
            try:
                # Making df available for execution in the context
                exec(code_to_execute, globals(), {"df": df, "plt": plt})
                st.write(answer)
                if len(plt.get_fignums()) > 0:  # If fig is generated
                    fig = plt.gcf()  # Get current figure
                    st.pyplot(fig)  # Display using Streamlit
                else:
                    f = StringIO()
                    with redirect_stdout(f):
                        exec('print(' + code_to_execute + ')', globals(), {"df": df, "plt": plt})
                    output = f.getvalue()
                    if output:
                        st.write(output)
                    else:
                        st.write(code_to_execute)
            except Exception as e:
                if isinstance(e, ModuleNotFoundError):
                    # install missing package
                    if package := re.search(
                            r"No module named '(.*)'",
                            e.msg
                    ):
                        try:
                            subprocess.check_call([sys.executable, "-m", "pip", "install", package.group(1)])
                            st.write(
                                f"package {package.group(1)} was missing but installed now. Please try again.")
                        except Exception as ee:
                            st.write(
                                f"package {package.group(1)} was missing and failed to install as following: ")
                            st.write(f"{ee}")
                else:
                    st.write(f"Error executing code: {e}")
                    if self.is_self_debugging:
                        # with self debugging mode, send the code and error message to llm for debugging.
                        # retry at most Config.MAX_RETRY_NUM times
                        self.retry_num += 1
                        if self.retry_num <= Config.MAX_RETRY_NUM:
                            st.write("Retrying...")
                            res = self.call_python_debug_agent(code_to_execute, str(e))
                            self.response_handler(res, df)
        else:
            st.write(answer)

    def run(self):
        """Main Streamlit application for EXCEL analysis."""

        st.title('Data Analyzer')
        self.is_self_debugging = st.checkbox('self-debugging')
        st.write('Please upload your excel file and enter your query below:')

        uploaded_file = st.file_uploader("Choose a file", type="xlsx")

        if uploaded_file is not None:
            file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                            "FileSize": uploaded_file.size}
            st.write(file_details)

            # change format to csv and save to disk
            data = pd.read_excel(uploaded_file, engine='openpyxl')
            file_path = "./data/data.csv"
            data.to_csv(file_path, index=False)

            df = pd.read_csv(file_path)
            st.dataframe(df)

            user_input = st.text_input("Your query")
            # user_input = 'draw a scatter plot to show the distribution of X1 and X2.'

            if st.button('Run'):
                self.retry_num = 0
                response = self.call_csv_agent(user_input)
                self.response_handler(response, df)

        st.divider()
