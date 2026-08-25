"""
Structured logging configuration with automatic secret masking.
"""

import logging
import os
import re
import sys
from typing import Optional


class SensitiveFilter(logging.Filter):
    """Filter that masks sensitive substrings such as passwords and tokens."""

    SENSITIVE_RULES = [
        (re.compile(r'(password[:=]\s*)([^\s,;&]+)', re.IGNORECASE), r'\1***'),
        (re.compile(r'(auth[:=]\s*)([^\s,;&]+)', re.IGNORECASE), r'\1***'),
        (re.compile(r'(token[:=]\s*)([^\s,;&]+)', re.IGNORECASE), r'\1***'),
        (re.compile(r'((?:bolt|redis|rediss)[^\:]*://[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1***\3'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, repl in self.SENSITIVE_RULES:
                try:
                    msg = pattern.sub(repl, msg)
                except Exception:
                    pass
            record.msg = msg
        return True


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Configures application-wide structured logging."""
    if level is None:
        level = os.getenv("BENCHMARK_LOG_LEVEL", "INFO").upper()

    numeric_level = getattr(logging, level, logging.INFO)
    logger = logging.getLogger("benchmark")
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers on re-initialization
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveFilter())
    logger.addHandler(console_handler)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveFilter())
        logger.addHandler(file_handler)

    return logger
