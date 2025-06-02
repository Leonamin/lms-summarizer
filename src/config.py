import os
from dotenv import load_dotenv

config = {}

def load_config():
    load_dotenv()
    config["USERNAME"] = os.getenv("USERNAME")
    config["PASSWORD"] = os.getenv("PASSWORD")
    
    if not config["USERNAME"]:
        config["USERNAME"] = input("아이디를 입력하세요: ")
    if not config["PASSWORD"]:
        config["PASSWORD"] = input("비밀번호를 입력하세요: ")
