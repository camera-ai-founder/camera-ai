from pydantic import BaseModel
from typing import List, Dict, Any

class PythonExecutorDNA(BaseModel):
    code: str = ""
    timeout: int = 60