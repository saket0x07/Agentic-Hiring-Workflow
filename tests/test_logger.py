from app.core.logger import logger

def test_logger():
    logger.info("Application Started")
    logger.success("Logger Working Successfully")
    logger.error("Error Occurred")
    logger.warning("Something went wrong")
    logger.debug("Debug Mode")