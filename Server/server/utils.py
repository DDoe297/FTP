import logging

def setup_logger(name: str, console_handler_level: int, file_handler_level: int) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('server.log')
    console_handler.setLevel(console_handler_level)
    file_handler.setLevel(file_handler_level)
    format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(format)
    file_handler.setFormatter(format)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger