import os
from dotenv import load_dotenv
from typing import Union

# Load environment vars
load_dotenv()

def env(key: str) -> Union[str, int, float, bool, complex]:
    return os.getenv(key)