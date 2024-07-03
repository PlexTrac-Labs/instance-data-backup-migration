from rich import print

import beaupy as binput

import settings
import utils.globals as globals
import utils.log_handler as logger
log = logger.log
from utils.auth_handler import Auth


class TemplatesWorkflow:

    def start(self):
        import main

        if globals.auth == None:
            log.info(f'Must authenticate to a Plextrac instance first')
            globals.auth = Auth()
            globals.auth.handle_authentication()

        binput.console.clear()
        log.debug(f'starting workflow \'templates\'')
        print(f'''[b u]Report/Export Templates & Style Guides[/b u]

TODO: need to implement

returning to main menu''')

        input(f'Press enter to continue...')
        main.start()