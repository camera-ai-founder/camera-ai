def compile_python_executor(data: dict) -> str:
    """
    Deterministic Template Stamper for python_executor.
    Reads JSON, injects variables into a pre-audited template string.
    """
    template = "Generated python_executor output: " + ", ".join([f"{k}={v}" for k, v in data.items()])
    try:
        return template.format(**data)
    except KeyError:
        return "Error: Missing required template variables."
