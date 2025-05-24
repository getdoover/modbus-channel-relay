from pydoover.docker import run_app

from .app_config import SampleConfig
from .application import SampleApplication

def main():
    run_app(SampleApplication(config=SampleConfig()))
