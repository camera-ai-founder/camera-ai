# packages/core/security_engine.py
import json
import os
from string import Template
from typing import Any, Dict, Type
from pydantic import BaseModel, ValidationError

# Import our DNA models and the new Security rules
from .models import SecurityDNA, AppDNA

def truncate_strings(obj: Any, max_length: int = 2000) -> Any:
    """
    THE SCISSORS: 
    Recursively searches through the JSON data. If it finds a massive string, 
    it snips it down to prevent memory overload attacks.
    """
    if isinstance(obj, str):
        return obj[:max_length]
    elif isinstance(obj, dict):
        return {k: truncate_strings(v, max_length) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [truncate_strings(i, max_length) for i in obj]
    return obj

def sanitize_dna(
    raw_json_string: str, 
    target_model: Type[BaseModel], 
    security_config: SecurityDNA = None
) -> dict:
    """
    THE ZERO-TRUST DNA SANITIZER.
    This is the only way raw data is allowed to enter our compilers.
    """
    # If no specific security rules are passed, use the default safe vault rules
    if not security_config:
        security_config = SecurityDNA()

    # 1. THE BOUNCER: Check raw size before we even parse it
    # This protects your i3 laptop's RAM from being instantly flooded.
    if len(raw_json_string) > security_config.max_payload_size:
        raise ValueError(
            f"THREAT BLOCKED: Payload size ({len(raw_json_string)} bytes) "
            f"exceeds the strict limit of {security_config.max_payload_size} bytes."
        )

    # 2. THE METAL DETECTOR: Try to read the JSON
    try:
        raw_dict = json.loads(raw_json_string)
    except json.JSONDecodeError:
        raise ValueError("THREAT BLOCKED: Malformed, corrupted JSON detected.")

    # 3. THE SCISSORS: Snip any overly long strings
    safe_dict = truncate_strings(raw_dict, max_length=2000)

    # 4. THE VAULT: Hand the safe data to Pydantic to strip unauthorized keys
    try:
        # Pydantic checks every single rule we defined in models.py
        validated_model = target_model.model_validate(safe_dict)
        
        # Return the perfectly clean, mathematically verified dictionary
        return validated_model.model_dump()
        
    except ValidationError as e:
        # If the AI or a user tried to sneak in bad data, we catch it here
        raise ValueError(f"THREAT BLOCKED: DNA structure violated. Details: {str(e)}")

# ==========================================
# DAY 22 STEP 4: THE COMPILER SANDBOX
# ==========================================

def safe_template_render(template_string: str, variables: dict) -> str:
    """
    THE SAFE INJECTOR:
    Prevents Template Injection Attacks. We use Python's built-in safe Template
    engine. It treats everything as plain text. It NEVER executes code.
    """
    # We replace any double braces {{ }} with single braces { } to neutralize Jinja2 attacks
    sanitized_template = template_string.replace('{{', '{').replace('}}', '}')
    
    # Use the safest string substitution method in Python
    safe_template = Template(sanitized_template)
    try:
        return safe_template.safe_substitute(variables)
    except Exception as e:
        raise ValueError(f"THREAT BLOCKED: Template injection attempt detected. Details: {str(e)}")

def secure_file_path(base_dir: str, requested_path: str) -> str:
    """
    THE VAULT LOCK:
    Prevents Path Traversal Attacks. Ensures the compiler can ONLY read files
    inside our pre-audited templates folder. It cannot read system files like /etc/passwd.
    """
    # Get the absolute, real paths
    abs_base = os.path.abspath(base_dir)
    abs_requested = os.path.abspath(os.path.join(base_dir, requested_path))
    
    # Check if the requested path is actually inside the base directory
    if not abs_requested.startswith(abs_base + os.sep) and abs_requested != abs_base:
        raise ValueError(f"THREAT BLOCKED: Path traversal attack detected. Access denied to {requested_path}")
        
    return abs_requested