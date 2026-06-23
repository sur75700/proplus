import logging
import json
import sys

class JSONLogger:
    def __init__(self, name="proplus"):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler(sys.stdout)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def log(self, data: dict):
        self.logger.info(json.dumps(data, default=str))
