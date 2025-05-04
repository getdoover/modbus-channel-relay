import logging
import random
import time

from pydoover.docker import Application
from pydoover import ui

from .app_config import SampleConfig
from .app_ui import SampleUI
from .app_state import SampleState

# UI Will look like this

# Variable : Is Working : Bool
# Variable : Uptime : Int
# Parameter : Test Message
# Variable : Test Output
# Action : Send this text as an alert
# Submodule :
#      Variable : Battery Voltage
#      Parameter : Low Battery Voltage Alert
#            Once below this setpoint, send a text and show a warning
#      StateCommand : Charge Battery Mode
#           - Charge
#           - Discharge
#           - Idle

log = logging.getLogger()

class SampleApplication(Application):
    config: SampleConfig  # not necessary, but helps your IDE provide autocomplete!

    def setup(self):
        self.started = time.time()
        self.ui = SampleUI()
        self.state = SampleState()
        self.ui_manager.add_children(*self.ui.fetch())

    def main_loop(self):
        log.info(f"State is: {self.state.state}")
        self.ui.update(
            True,
            random.randint(900, 2100) / 100,
            time.time() - self.started,
        )

    @ui.callback("send_alert")
    def on_send_alert(self, new_value):
        log.info(f"Sending alert: {self.ui.test_output.current_value}")
        self.publish_to_channel("significantAlerts", self.ui.test_output.current_value)
        self.ui.send_alert.coerce(None)

    @ui.callback("test_message")
    def on_text_parameter_change(self, new_value):
        log.info(f"New value for test message: {new_value}")
        # Set the value as an output to the corresponding variable is this case
        self.ui.test_output.update(new_value)

    @ui.callback("charge_mode")
    def on_state_command(self, new_value):
        log.info(f"New value for state command: {new_value}")

