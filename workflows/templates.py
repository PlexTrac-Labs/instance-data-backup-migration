import time

import beaupy as binput

import settings
import utils.globals as globals
import utils.log_handler as logger
log = logger.log
from utils.auth_handler import Auth
import utils.input_utils as input


class TemplatesWorkflow:
    def __init__(self):
        pass

    def display_title_card(self):
        log.debug(f'starting workflow \'templates\'')
        title_card = [
            " Report/Export Templates & Style Guides",
            "------------------------------------------------------------------",
            """
    TODO: need to implement

    returning to main menu...
            """
        ]
        for i in title_card:
            print(i)


    def start(self):
        binput.console.clear()
        import main
        self.display_title_card()

        time.sleep(3)

        main.start()