# Data Analytic App
using langchain and streamlit

## three step to run the code

step 1: install the package.

note: langchain agent is only supported by python 3.9 or above.
```bash
pip install -r requirement.txt
```
step 2: add your openai credential in `config.py`.

step 3: run the app.
```bash
streamlit run .\main.py
```
Note: When you select the `self-debugging` check box, 
the app will retry automatically if the task fails. 