"""
Sanitizing logging utility for SAP AI Master Data Automation Platform.
Ensures zero leaks of SAP passwords, NVIDIA API keys, or session tokens.
"""
import logging
import re
import sys
from typing import Any

# Patterns to sanitize
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(password["\':\s=]+)([\'"]?[^\'",\s}]+[\'"]?)'), r'\1***REDACTED***'),
    (re.compile(r'(?i)(api[_-]?key["\':\s=]+)([\'"]?[^\'",\s}]+[\'"]?)'), r'\1***REDACTED***'),
    (re.compile(r'(?i)(b1session["\':\s=]+)([\'"]?[^\'",\s}]+[\'"]?)'), r'\1***REDACTED***'),
    (re.compile(r'(?i)(routeid["\':\s=]+)([\'"]?[^\'",\s}]+[\'"]?)'), r'\1***REDACTED***'),
    (re.compile(r'(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{15,})'), r'\1***REDACTED***'),
]

class SanitizingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.sanitize(record.msg)
        if record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitized_args.append(self.sanitize(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        return True

    @staticmethod
    def sanitize(text: str) -> str:
        for pattern, replacement in SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

def setup_logger(name: str = "sap_ai", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SanitizingFilter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
