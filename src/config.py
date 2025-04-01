import os

class Config:
    def __init__(self):
        self.db_name = os.environ["POSTGRES_DB"]
        self.db_user = os.environ["POSTGRES_USER"]
        self.db_password = os.environ["POSTGRES_PASSWORD"]
        self.db_host = os.environ["POSTGRES_HOST"]
        self.db_port = os.environ["POSTGRES_PORT"]
        self.db_connect_retries = 5
        self.db_retry_delay_s = 10


