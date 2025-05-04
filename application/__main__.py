from pydoover.docker import run_app

from .app_config import SampleConfig
from .application import SampleApplication

if __name__ == "__main__":
    run_app(SampleApplication(config=SampleConfig()))
