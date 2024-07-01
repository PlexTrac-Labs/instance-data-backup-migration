import yaml
import time

import beaupy as binput

import settings
import utils.globals as globals
import utils.log_handler as logger
log = logger.log
from utils.auth_handler import Auth
import utils.input_utils as input
from workflows.clients_reports import ClientReportsWorkflow
from workflows.templates import TemplatesWorkflow


def authentication_controller():
    binput.console.clear()
    # current status
    if globals.auth == None:
        log.info(f'Not currently authenticated to a Plextrac instance')
    elif time.time() - globals.auth.time_since_last_auth > 840:
        log.info(f'User session for \'{globals.auth.username}\' on \'{globals.auth.base_url}\' instance has expired')
    else:
        log.info(f'User \'{globals.auth.username}\' is authenticated to tenant {globals.auth.tenant_id} on \'{globals.auth.base_url}\'')

    if binput.confirm(
        f'Would you like to authenticate to a different Plextrac instance?\nSelect no to stay connected to current instance above, even if session is expired',
        cursor_style="white"
    ):
        globals.auth = Auth()
        globals.auth.handle_authentication()

def start():
    # select workflow
    log.info(f'''
Choose a workflow to start
 - Each workflow supports exporting and importing different data modules in Plextrac.
 - This allows for backup or migration of data. Different workflows can effectively
   migrate data between different parts of the platform, or between Plextrac instances.

Workflows:
----------''')
    workflows_options = [":authenticate to instance", ":clients and reports", ":report/export templates & style guides"]
    workflow_selection = binput.select(workflows_options, cursor_style='white')
    log.debug(f'selected: {workflow_selection}')

    if workflow_selection == ":authenticate to instance":
        authentication_controller()
        start()

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











