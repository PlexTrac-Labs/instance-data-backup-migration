import json
import io
import zipfile
import os
from typing import List, Union
from dataclasses import dataclass
from rich import print

from tkinter import Tk
from tkinter.filedialog import askopenfilenames
import beaupy as binput

import utils.globals as globals
import utils.log_handler as logger
log = logger.log
from utils.log_handler import IterationMetrics
from utils.auth_handler import Auth
import utils.data_utils as data
import utils.general_utils as utils
import api


@dataclass
class ClientZIP:
    client: Union[dict, None]
    reports: List[dict]
    
class ClientReportsWorkflow:
    
    def create_client_zip_with_json_objects(self, client, reports, folder_path):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # add client json to ZIP buffer
            json_buffer = io.StringIO()
            json.dump(client, json_buffer)
            json_data = json_buffer.getvalue()
            zip_file.writestr(utils.sanitize_file_name(f'{client["name"]}_{client["client_id"]}_{globals.script_time}.json'), json_data)

            # add report jsons to ZIP buffer
            for report in reports:
                if report['ptrac'] == None:
                    continue # report doesn't have ptrac, request to get ptrac must have failed
                json_obj = report['ptrac']
                json_buffer = io.StringIO()
                json.dump(json_obj, json_buffer)
                json_data = json_buffer.getvalue()
                zip_file.writestr(utils.sanitize_file_name(f'{report["report_data"]["name"]}_{report["report_data"]["id"]}_{globals.script_time}.ptrac'), json_data)

        # save ZIP file
        zip_file_name = utils.sanitize_file_name(f'{client["name"]}_{client["client_id"]}_{globals.script_time}.zip')
        with open(f'{folder_path}/{zip_file_name}', 'wb') as f:
            f.write(zip_buffer.getvalue())
        log.success(f'Created client ZIP for \'{client["name"]}\' with {len(reports)} report(s)')


    def select_zip_files(self, initial_directory=None):
        """
        Prompt the user to select multiple zip files and return their paths.
        """
        print(f'Please select client ZIP file(s) from file dialog popup...')
        root = Tk()
        root.withdraw()  # Hide the root window
        if not (os.path.exists(initial_directory) and os.path.isdir(initial_directory)):
            initial_directory = utils.get_script_root_path()
        file_paths = askopenfilenames(
            filetypes=[("Zip files", "*.zip")],
            initialdir=initial_directory
        )
        return file_paths
    

    def extract_data_from_client_ZIP(self, zip_path) -> ClientZIP:
        """
        Extract JSON files from a zip file and return them as a list of dictionaries.
        """
        client_json = None
        report_json_list = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_name in zip_ref.namelist():
                    if file_name.endswith('.json') or file_name.endswith('.ptrac'):
                        with zip_ref.open(file_name) as file:
                            json_data = json.load(file)
                            if utils.get_json_object_type(json_data) == "client":
                                client_json = json_data
                            elif utils.get_json_object_type(json_data) == "ptrac":
                                report_json_list.append(json_data)
                            else:
                                log.exception(f'Encountered invalid file in client ZIP \'{file_name}\'.')
                    else:
                        log.exception(f'Encountered unknown file in client ZIP \'{file_name}\'.')
            if client_json == None:
                log.exception(f'Client ZIP file \'{zip_path}\' did not contain a valid client JSON')
                return ClientZIP(None, [])
            return ClientZIP(client_json, report_json_list)
        except Exception as e:
            log.exception(f'Could not find or load client ZIP file \'{zip_path}\'\n{e}')
            return ClientZIP(None, [])


    def start(self):
        import main # importing here to prevent circular imports

        if globals.auth == None:
            log.info(f'Must authenticate to a Plextrac instance first')
            globals.auth = Auth()
            globals.auth.handle_authentication()

        binput.console.clear()
        log.debug(f'starting workflow \'client_reports\'')
        print(f'''[b u]Clients and Reports Workflow[/b u]

This workflow can import/export clients from Plextrac. You can choose whether
reports under a client should be moved as well. For each client exported, a ZIP
file is created. This ZIP file can be used to reimport the client into a
different Plextrac instance.

Overview of Steps:
- Export clients
  - select which clients to export
  - choose whether to export reports with client
- Import clients
  - select ZIP files of clients to import
  - choose whether to import reports with client - TODO
  - choose whether to check if the client exists - TODO
              
[b]Would you like to import or exports clients[/b]''')
        action = binput.select([":import clients", ":export clients", ":main menu"], cursor=">", cursor_style='white')
        print(f'Selected {action[1:]}\n')
        log.debug(f'selected: {action}')

        if action == ":import clients":
            self.import_clients()
        elif action == ":export clients":
            self.export_clients()
        elif action == ":main menu":
            main.start()
        else:
            log.exception(f'Selected invalid option. Exiting to main menu')
            input(f'Press enter to continue...')
            main.start()


    def export_clients(self):
        import main # importing here to prevent circular imports

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
        selected_clients = binput.select_multiple(
            options=clients,
            # need to replace square brackets with something else since beaupy uses square brackets to define styles, effectively excluding them from allowed chars
            preprocessor=lambda client:f'Name: {client["name"]} | ID: {client["client_id"]} | Tags: {str(client.get("tags", [])).replace("[","<").replace("]", ">")}',
            tick_character="x",
            tick_style="green",
            cursor_style="dark_goldenrod",
            minimal_count=1,
            pagination=True,
            page_size=10
        )
        print(f'Selected {len(selected_clients)} client(s)\n')

        # prompt user for action details
        print(f'Select options for exporting client(s)')
        export_clients_options = binput.select_multiple(
            options=["include client reports", "exclude user data - TODO need to implement"], # TODO add option to exclude user, sensitivity
            tick_character="x",
            tick_style="green",
            cursor_style="dark_goldenrod"
        )
        print("- including reports in client export" if "include client reports" in export_clients_options else "- ignoring reports under client(s)")
        print("- excluding user data from client export" if "exclude user data" in export_clients_options else "- keeping user data in client export")
        print("")


        # get and sort reports from instance
        sorted_client_reports = [[] for client in selected_clients]
        if "include client reports" in export_clients_options:
            spinner = binput.spinners.Spinner(binput.spinners.DOTS, "Loading reports from instance...")
            spinner.start()
            reports = []
            data.get_page_of_reports(reports=reports, auth=globals.auth)
            # sort reports into groups related to clients
            for i, report_group in enumerate(sorted_client_reports):
                for report in reports:
                    if report['client_id'] == clients[i]['client_id']:
                        # get ptrac for each report
                        ptrac = None
                        try:
                            response = api.reports.export_report_to_ptrac(globals.auth.base_url, globals.auth.get_auth_headers(), report['client_id'], report['id'])
                            ptrac = response.json
                        except Exception as e:
                            log.exception(f'Could not download ptrac for report \'{report["name"]}\' under client \'{clients[i]["name"]}\', skipping...')
                        report_group.append({"report_data":report, "ptrac":ptrac})
            spinner.stop()

        # create and export client ZIPs
        utils.create_directory("exported_data")
        utils.create_directory("exported_data/client_ZIPs")
        folder_path = "exported_data/client_ZIPs"

        for i, client in enumerate(selected_clients):
            self.create_client_zip_with_json_objects(client, sorted_client_reports[i], folder_path)

        # return to main menu
        log.info(f'Finished exporting clients')
        input(f'Press enter to continue...')
        main.start()


    def import_clients(self):
        import main # importing here to prevent circular imports

        # have user select client ZIP files to import
        absolute_path = os.path.abspath("exported_data/client_ZIPs")
        zip_file_paths = self.select_zip_files(initial_directory=absolute_path)
        print(f'Selected {len(zip_file_paths)} ZIP file(s)\n')
        log.debug(f'selected {len(zip_file_paths)} ZIP file(s)')
        
        # import data from client ZIPs
        spinner = binput.spinners.Spinner(binput.spinners.DOTS, "Importing clients from file(s)...")
        spinner.start()
        for file_path in zip_file_paths:
            zip = self.extract_data_from_client_ZIP(file_path)
            if zip.client == None:
                log.exception(f'Skipping invalid client ZIP file \'{file_path}\'...')
                continue

            # create client
            payload = zip.client
            payload.pop("cuid")
            payload.pop("tenant_id")
            payload.pop("client_id")
            # TODO figure out how to handle logo
            payload.pop("logo")
            payload.pop("doc_type")
            # TODO figure out how to handle users
            payload.pop("users")
            # payload['name'] = "Green Testing import" # TODO remove - only for testing
            payload["tags"].append("green_delete") # TODO remove - only for testing
            try:
                response = api.clients.create_client(globals.auth.base_url, globals.auth.get_auth_headers(), payload)
                client_id = response.json['client_id']
                log.success(f'Created client \'{payload["name"]}\'')
            except Exception as e:
                log.exception(f'Could not create client. Skipping client and {len(zip.reports)} subsequent report(s)...')
                continue

            # import ptracs
            for ptrac in zip.reports:
                try:
                    json_str = json.dumps(ptrac)
                    json_file_like = io.BytesIO(json_str.encode('utf-8'))
                    multipart_form_data = {
                        'file': json_file_like
                    }
                    response = api.reports.import_ptrac_report(globals.auth.base_url, globals.auth.get_auth_headers(), client_id, multipart_form_data)
                    log.success(f'Created report \'{ptrac["report_info"]["name"]}\' for client \'{zip.client["name"]}\'')
                except Exception as e:
                    log.exception(f'Could not create report. Skipping...')
                    continue

        spinner.stop()

        # return to main menu
        log.info(f'Finished importing clients')
        input(f'Press enter to continue...')
        main.start()
