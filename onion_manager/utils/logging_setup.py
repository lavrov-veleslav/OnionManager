import logging
import os


def setup_logging(logfile: str | None = None):
    logfile = logfile or os.path.join(os.path.dirname(__file__), '..', '..', 'onion_manager.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(logfile),
            logging.StreamHandler()
        ]
    )
