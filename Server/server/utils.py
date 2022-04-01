import logging

def setup_logger(name: str, level: int) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(format)
    logger.addHandler(handler)
    return logger