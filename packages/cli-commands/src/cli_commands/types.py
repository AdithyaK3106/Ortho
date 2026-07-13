from dataclasses import dataclass


@dataclass
class CliReport:
    title: str
    content: str
    format: str = "text"
    success: bool = True
