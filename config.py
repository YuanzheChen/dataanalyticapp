class Config(object):
    # openai credential
    OPENAI_API_KEY = ''
    OPENAI_API_BASE = ''
    OPENAI_API_TYPE = 'azure'
    OPENAI_API_VERSION = '2023-05-15'

    # llm config
    DEPLOYMENT_NAME = 'gpt-35-turbo'
    MODEL_NAME = 'gpt-35-turbo'

    # app config
    MAX_RETRY_NUM = 1
    FILE_PATH = './data/data.csv'