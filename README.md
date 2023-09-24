# Data Analytic App
Use langchain and streamlit

## Three step to run the code

Step 1: install the package.

Note: langchain agent is only supported by python 3.9 or above.
```bash
pip install -r requirement.txt
```
Step 2: add your openai credential in `config.py`.

Step 3: run the app.
```bash
streamlit run .\main.py
```
Note: When you select the `self-debugging` check box, 
the app will retry automatically if the task fails. 
