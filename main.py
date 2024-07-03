import yaml
import time
from rich import print

import beaupy as binput

import settings
import utils.globals as globals
import utils.log_handler as logger
log = logger.log
from utils.auth_handler import Auth
from workflows.clients_reports import ClientReportsWorkflow
from workflows.templates import TemplatesWorkflow


def authentication_controller():
    binput.console.clear()
    log.debug(f'starting main.py authentication_controller() - confirm session or auth to new session')
    # authentication status
    print(f'''[b u]Authentication Workflow[/b u]
          
Plextrac uses JWT tokens to manage authentication sessions. Each session lasts 15 minutes
before requiring the token to be refreshed.
          
This script automatically refreshes a token if it expires. If the authentication status
below shows expired, but was previously authenticated, you don't need to use this workflow
to re-authenticate.
          
This workflow is only required for changing the authentication to a different instance of
Plextrac. This is useful in the case where data needs to be exported from one instance and
imported into a separate instance.

[b]Current status of authentication[/b]''')
    if globals.auth == None:
        log.info(f'Not currently authenticated to a Plextrac instance')
    else:
        globals.auth.get_auth_details()

    # continue with workflow and auth to new instance
    if binput.confirm(
        f'\nWould you like to authenticate to a different Plextrac instance?\nSelect no to stay connected to current instance above, even if session is expired',
        cursor_style="white"
    ):
        globals.auth = Auth()
        globals.auth.handle_authentication()

    input(f'Press enter to continue...')
    start()

def start():
    binput.console.clear()
    log.debug(f'starting main.py start() - main menu')
    # select workflow
    print(f'''[b u]Main Menu:[/b u]
          
This script is broken up into multiple workflows that manage different modules of data.

 - Each workflow supports exporting and importing different data modules in Plextrac.
 - This allows for backup or migration of data. Different workflows can effectively
   migrate data between different parts of the platform, or between Plextrac instances.

[b]Choose a workflow to start[/b]''')
    workflows_options = [
        f":authenticate to instance {globals.auth.get_auth_status() if globals.auth!=None else '(no authentication session)'}",
        ":clients and reports",
        # ":report/export templates & style guides",
        ":exit"
    ]
    workflow_selection = binput.select(workflows_options, cursor_style='white')
    log.debug(f'selected: {workflow_selection}')

    if " ".join(workflow_selection.split()[0:3]) == ":authenticate to instance":
        authentication_controller()
    if workflow_selection == ":exit":
        exit()

    workflows = {
        ":clients and reports": ClientReportsWorkflow,
        ":report/export templates & style guides": TemplatesWorkflow,
    }
    workflows[workflow_selection]().start()

if __name__ == '__main__':
    binput.console.clear()
    for i in settings.script_info:
        print(i)

    with open("config.yaml", 'r') as f:
        args = yaml.safe_load(f)

    globals.auth = Auth(args)
    globals.auth.handle_authentication()

    input(f'Press enter to continue...')
    start()

    # select PT instance to interact with, allows for export/import to different instance within the same running instance of the script

    # clients and reports
    # export all clients and reports > recreate in new instance

    # reports
    # export all reports under a client > load into new client

    # users

    # report templates, export templates, style guides

    # writeups

    # tags

    



    # spinner = binput.spinners.Spinner(binput.spinners.DOTS, "Loading...")
    # spinner.start()
    # time.sleep(5)
    # spinner.stop()

