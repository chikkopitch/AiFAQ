import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(module)s | %(message)s"


def setup_logger() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
    )
    return logging.getLogger("construction_faq_bot")
