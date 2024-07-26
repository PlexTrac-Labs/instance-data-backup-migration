from rich import print
import os
import json
import io

from tkinter import Tk
from tkinter.filedialog import askopenfilenames
import beaupy as binput

import settings
import utils.globals as globals
import utils.log_handler as logger
log = logger.log
from utils.auth_handler import Auth
import utils.data_utils as data
import utils.general_utils as utils
import api


class ReportsWorkflow:

    def create_report_ptrac_with_json_object(self, report, folder_path):
        # get PTRAC JSON
        try:
            response = api.reports.export_report_to_ptrac(globals.auth.base_url, globals.auth.get_auth_headers(), report['client_id'], report['id'])
            ptrac = response.json
        except Exception as e:
            log.exception(f'Could not download ptrac for report \'{report["name"]}\', skipping...')
            return
        
        # save PTRAC file
        file_name = utils.sanitize_file_name(f'{report["name"]}_{report["id"]}_{globals.script_time}.ptrac')
        json_buffer = io.StringIO()
        json.dump(ptrac, json_buffer)
        json_data = json_buffer.getvalue()
        with open(f'{folder_path}/{file_name}', 'w') as f:
            f.write(json_data)
        log.success(f'Created report PTRAC {folder_path}/{file_name}')


    def select_ptrac_files(self, initial_directory=None):
        """
        Prompt the user to select multiple ptrac files and return their paths.
        """
        print(f'Please select report PTRAC file(s) from file dialog popup...')
        root = Tk()
        root.withdraw()  # Hide the root window
        if not (os.path.exists(initial_directory) and os.path.isdir(initial_directory)):
            initial_directory = utils.get_script_root_path()
        file_paths = askopenfilenames(
            filetypes=[("Ptrac files", "*.ptrac")],
            initialdir=initial_directory
        )
        return file_paths
    

    def load_data_from_report_PTRAC(self, file_path) -> dict|None:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path) as file:
                ptrac = json.load(file)
                if utils.get_json_object_type(ptrac) == "ptrac":
                    return ptrac
                else:
                    log.exception(f'Encountered invalid PTRAC file \'{file_name}\'. Skipping...')
        except Exception as e:
            log.exception(f'Could not find or load report PTRAC file \'{file_path}\'\n{e}')
            return None


    def start(self):
        import main # importing here to prevent circular imports

        if globals.auth == None:
            log.info(f'Must authenticate to a Plextrac instance first')
            globals.auth = Auth()
            globals.auth.handle_authentication()

        binput.console.clear()
        log.debug(f'starting workflow \'reports\'')
        print(f'''[b u]Reports Workflow[/b u]

This workflow can import/export reports from Plextrac. Reports will be exported
as PTRAC files, which can be reimported to a client later.

Overview of Steps:
- Export reports
  - select which reports to export
- Import reports
  - select PTRAC files of reports to import
  - select an existing client in Plextrac to import reports to
  - choose whether to check if the client exists - TODO
              
[b]Would you like to import or exports reports[/b]''')
        action = binput.select([":import reports", ":export reports", ":main menu"], cursor=">", cursor_style='white')
        print(f'Selected {action[1:]}\n')
        log.debug(f'selected: {action}')

        if action == ":import reports":
            self.import_reports()
        elif action == ":export reports":
            self.export_reports()
        elif action == ":main menu":
            main.start()
        else:
            log.exception(f'Selected invalid option. Exiting to main menu')
            input(f'Press enter to continue...')
            main.start()


    def export_reports(self):
        import main # importing here to prevent circular imports

        # get reports from instance
        spinner = binput.spinners.Spinner(binput.spinners.DOTS, "Loading reports from instance...")
        spinner.start()
        reports = []
        data.get_page_of_reports(reports=reports, auth=globals.auth)
        spinner.stop()
        if len(reports) < 1:
            log.exception(f'Did not find any reports in Plextrac instance. Exiting to main menu')
            input(f'Press enter to continue...')
            main.start()

        # user selects reports
        print(f'[b]Loaded Report list:[/b]')
        selected_reports = binput.select_multiple(
            options=reports,
            # need to replace square brackets with something else since beaupy uses square brackets to define styles, effectively excluding them from allowed chars
            preprocessor=lambda report:f'Name: {report["name"]} | ID: {report["id"]} | Tags: {str(report.get("tags", [])).replace("[","<").replace("]", ">")} | Client ID: {report["client_id"]}',
            tick_character="x",
            tick_style="green",
            cursor_style="dark_goldenrod",
            minimal_count=1,
            pagination=True,
            page_size=10
        )
        print(f'Selected {len(selected_reports)} reports(s)\n')

        # create and export report PTRACs
        utils.create_directory("exported_data")
        utils.create_directory("exported_data/report_PTRACs")
        folder_path = "exported_data/report_PTRACs"

        for report in selected_reports:
            self.create_report_ptrac_with_json_object(report, folder_path)

        # return to main menu
        log.info(f'Finished exporting reports')
        input(f'Press enter to continue...')
        main.start()

        
    def import_reports(self):
        import main # importing here to prevent circular imports

        # have user select report PTRAC file(s) to import
        absolute_path = os.path.abspath("exported_data/report_PTRACs")
        ptrac_file_paths = self.select_ptrac_files(initial_directory=absolute_path)
        print(f'Selected {len(ptrac_file_paths)} PTRAC file(s)\n')
        log.debug(f'selected {len(ptrac_file_paths)} PTRAC file(s)')

        # get clients from instance
        spinner = binput.spinners.Spinner(binput.spinners.DOTS, "Loading clients from instance...")
        spinner.start()
        clients = []
        data.get_page_of_clients(clients=clients, auth=globals.auth)
        spinner.stop()
        if len(clients) < 1:
            log.exception(f'Did not find any clients in Plextrac instance. Exiting to main menu')
            input(f'Press enter to continue...')
            main.start()

        # user selects clients
        print(f'[b]Loaded Client list:[/b]')
        selected_client = binput.select(
            options=clients,
            # need to replace square brackets with something else since beaupy uses square brackets to define styles, effectively excluding them from allowed chars
            preprocessor=lambda client:f'Name: {client["name"]} | ID: {client["client_id"]} | Tags: {str(client.get("tags", [])).replace("[","<").replace("]", ">")}',
            cursor_style='white',
            pagination=True,
            page_size=10
        )
        print(f'Selected \'{selected_client["name"]}\'\n')
        
        # import data from report PTRACs to selected client
        print(f'All selected PTRACs will be imported to create a new report under the selected client.')
        spinner = binput.spinners.Spinner(binput.spinners.DOTS, "Importing reports from file(s)...")
        spinner.start()
        for file_path in ptrac_file_paths:
            # load ptrac dict from file
            ptrac = self.load_data_from_report_PTRAC(file_path)
            if ptrac == None:
                log.exception(f'Skipping invalid report PTRAC file \'{file_path}\'...')
                continue

            # TODO - add ability to add report tags at this step

            # import ptrac
            try:
                json_str = json.dumps(ptrac)
                json_file_like = io.BytesIO(json_str.encode('utf-8'))
                multipart_form_data = {
                    'file': json_file_like
                }
                response = api.reports.import_ptrac_report(globals.auth.base_url, globals.auth.get_auth_headers(), selected_client['client_id'], multipart_form_data)
                log.success(f'Created report \'{ptrac["report_info"]["name"]}\' for client \'{selected_client["name"]}\'')
            except Exception as e:
                log.exception(f'Could not create report. Skipping...')
                continue

        spinner.stop()

        # return to main menu
        log.info(f'Finished importing reports')
        input(f'Press enter to continue...')
        main.start()

