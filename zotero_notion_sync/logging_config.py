"""
Module Name: logging_config.py
Description: 
    This module sets up a custom logging configuration that uses colored formatting for log messages. 
    It defines a `ColorFormatter` class that formats log messages using ANSI color codes to make log levels 
    more visually distinguishable. The module also configures the root logger to use the custom formatter 
    with a stream handler.

Classes:
    ColorFormatter(logging.Formatter):
        A custom logging formatter that adds ANSI color codes to log levels based on the log severity.

Usage:
    Import this module to enable colored logging for DEBUG, INFO, WARNING, ERROR, and CRITICAL levels.
    The color-coded logs help easily distinguish between different severity levels during debugging 
    and monitoring.

Example:
    ```python
    import logging
    import logging_config  # Import to configure logging with colors

    logger = logging.getLogger(__name__)
    logger.info("This is an info message.")
    logger.error("This is an error message.")
    ```

Attributes:
    COLORS (dict): A dictionary that maps logging levels to ANSI color codes.
    RESET (str): ANSI escape code to reset colors to default after each log message.

Notes:
    - This logging configuration is suitable for console output where colored log messages improve readability.
    - ANSI color codes may not render properly in non-ANSI compatible terminals.
"""

import logging


# pylint: disable=missing-class-docstring
class ColorFormatter(logging.Formatter):
    # ANSI escape sequences for colors
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[1;91m",  # Bright Red
    }
    RESET = "\033[0m"  # Reset to Default Color

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        return super().format(record)


# pylint: disable=missing-function-docstring
def configure_logging():
    # Create a custom formatter instance
    formatter = ColorFormatter("%(levelname)s - %(message)s\n")

    # Configure the root logger with a stream handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logging.basicConfig(level=logging.DEBUG, handlers=[handler])


# Configure logging when the module is imported
configure_logging()
