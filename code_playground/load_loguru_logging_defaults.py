# This file is the master template for my chosen Loguru setup
from loguru import logger
import sys

logger.remove()  # Remove the default handler

""" these lines were suggested by ChatGPT but have not proven useful for catching secrets in crash logs


# List of sensitive keys to obfuscate
sensitive_keys = ["password", "api_key", "token", "secret", "username", "self.password", "Conrad"]

def obfuscate_secrets(record):  # During a crash dump I witnessed API credential leakage and this is intended to protect against that
    
    for key in sensitive_keys:
        if key in record["message"]:
            record["message"] = record["message"].replace(record["extra"][key], "***REDACTED***")
    return record
# Example useage
# logger = logger.patch(obfuscate_secrets)


def redact_sensitive_data(record):
    for key in sensitive_keys:
        if key in record["message"]:
            record["message"] = record["message"].replace(record["extra"][key], "[REDACTED]")
        return True
# example useage
# logger.add("app.log", filter=redact_sensitive_data)


# Add a handler for the console that logs messages at the INFO level with colorization enabled and no live data exposure
logger.add(sys.stdout, level='INFO', 
           colorize=True, 
           format="<green>{time}</green> <level>{message}</level>", 
           diagnose=False)

"""

# Add a handler for the console that logs messages at the INFO level with colorization enabled and live data in crashes
logger.add(sys.stdout, level='INFO', 
           colorize=True, 
           format="<green>{time}</green> <level>{message}</level>", 
           diagnose=True)

# Add a handler for permanent storage with automatic rotation.  Caution; This will log sensitive data from crash reports
logger.add("LOGS/file_processing_{time:YYYY-MM-DD}.log", rotation="00:00", retention="9 days")
