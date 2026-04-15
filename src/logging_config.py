import logging

# Create or get the logger
logger = logging.getLogger('shared_logger')
logger.setLevel(logging.INFO)  # Log everything (DEBUG level or higher)

# Prevent multiple handlers if the logger is configured multiple times
if not logger.handlers:
    # Create a file handler to log to a file
    file_handler = logging.FileHandler('logs\shared_log_file.log')
    file_handler.setLevel(logging.INFO)  # Log INFO level and above to the file

    # Create a console handler to log to the console for real-time feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Log INFO level and above to the console


    # Define log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    # Add file handler to logger
    logger.addHandler(file_handler)
    # Add console handler to logger
    logger.addHandler(console_handler)