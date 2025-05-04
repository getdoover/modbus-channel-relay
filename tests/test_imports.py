"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from application.application import SampleApplication
    assert SampleApplication

def test_config():
    from application.app_config import SampleConfig

    config = SampleConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from application.app_ui import SampleUI
    assert SampleUI

def test_state():
    from application.app_state import SampleState
    assert SampleState