"""
Professional Logging Module for Kasparro AI Content Engine
==========================================================
Provides structured logging with both console and file output.
Logs are written to 'logs/system.log' for complete observability.
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOG_DIR / "system.log"

# Check if Windows terminal supports UTF-8
IS_WINDOWS = os.name == 'nt'


class SafeStreamHandler(logging.StreamHandler):
    """Stream handler that safely handles encoding issues on Windows."""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Replace emojis with text alternatives for Windows console
            if IS_WINDOWS:
                msg = msg.replace('💭', '[THOUGHT]')
                msg = msg.replace('🤖', '[LLM]')
                msg = msg.replace('📄', '[FILE]')
                msg = msg.replace('✓', '[OK]')
                msg = msg.replace('✗', '[FAIL]')
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Add color to levelname
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def setup_logger(name: str = "kasparro") -> logging.Logger:
    """
    Sets up a professional logger with console and file handlers.
    
    Args:
        name: Logger name (default: "kasparro")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # === File Handler (Detailed logs with UTF-8 encoding) ===
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # === Console Handler (User-friendly output with safe encoding) ===
    console_formatter = ColoredFormatter(
        fmt='%(levelname)s | %(message)s'
    )
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_agent_logger(agent_name: str) -> logging.Logger:
    """
    Get a logger for a specific agent with agent name in logs.
    
    Args:
        agent_name: Name of the agent (e.g., "ParserAgent", "StrategyAgent")
        
    Returns:
        Logger instance for the agent
    """
    return setup_logger(f"kasparro.{agent_name}")


# Pre-configured loggers for each component
main_logger = setup_logger("kasparro.main")
parser_logger = get_agent_logger("ParserAgent")
strategy_logger = get_agent_logger("StrategyAgent")
builder_logger = get_agent_logger("BuilderAgent")
llm_logger = get_agent_logger("LLMClient")


def log_pipeline_start():
    """Log the start of the content generation pipeline."""
    main_logger.info("=" * 60)
    main_logger.info("KASPARRO AI CONTENT ENGINE - Pipeline Started")
    main_logger.info(f"Timestamp: {datetime.now().isoformat()}")
    main_logger.info("=" * 60)


def log_pipeline_complete():
    """Log the completion of the pipeline."""
    main_logger.info("=" * 60)
    main_logger.info("PIPELINE COMPLETE - All content generated successfully")
    main_logger.info(f"Logs saved to: {LOG_FILE.absolute()}")
    main_logger.info("=" * 60)


def log_agent_thought(agent_name: str, thought: str, details: dict = None):
    """
    Log an agent's "thought" or decision process.
    
    Args:
        agent_name: Name of the agent
        thought: What the agent is thinking/doing
        details: Optional dict with additional context
    """
    logger = get_agent_logger(agent_name)
    logger.info(f"💭 {thought}")
    
    if details:
        for key, value in details.items():
            logger.debug(f"   - {key}: {value}")


def log_llm_call(prompt_summary: str, model: str):
    """Log an LLM API call."""
    llm_logger.debug(f"🤖 Calling {model}")
    llm_logger.debug(f"   - Prompt: {prompt_summary[:100]}...")


def log_llm_response(success: bool, tokens: int = None):
    """Log LLM response status."""
    if success:
        llm_logger.debug(f"✓ LLM response received successfully")
    else:
        llm_logger.error(f"✗ LLM call failed")


def log_file_saved(filepath: str):
    """Log when a file is saved."""
    main_logger.info(f"📄 Saved: {filepath}")
