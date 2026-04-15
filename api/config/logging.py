# import logging
# import sys


# def setup_logging() -> None:
#     """Set up logging configuration."""
#     format_string = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
#     logging.basicConfig(
#         level=logging.INFO,
#         format=format_string,
#         datefmt="%H:%M:%S",
#         stream=sys.stdout,
#     )
#     logging.getLogger("passlib").setLevel(logging.INFO)


# def get_logger(name: str) -> logging.Logger:
#     """Get a logger instance."""
#     return logging.getLogger(name)

import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)


def get_logger(name: str):
    """Get a logger instance."""
    return structlog.get_logger(name)
