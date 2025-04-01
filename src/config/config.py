import os

from src.config.dev_config import DevConfig
from src.config.prod_config import ProdConfig

# basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    def __init__(self):
        self.dev_config = DevConfig()
        self.production_config = ProdConfig()
