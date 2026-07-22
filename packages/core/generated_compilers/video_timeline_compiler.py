def compile_video_timeline(data: dict) -> str:
    """
    Deterministic Template Stamper for video_timeline.
    Reads JSON, injects variables into a pre-audited template string.
    """
    template = "Generated video_timeline output: " + ", ".join([f"{k}={v}" for k, v in data.items()])
    try:
        return template.format(**data)
    except KeyError:
        return "Error: Missing required template variables."
