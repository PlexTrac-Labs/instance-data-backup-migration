import json
import io
import zipfile
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilenames

import beaupy as binput

import utils.globals as globals
import utils.log_handler as logger
log = logger.log
from utils.auth_handler import Auth
import utils.data_utils as data
import utils.general_utils as utils
import api

class ClientReportsWorkflow:

    def __init__(self):
        pass


    def display_title_card(self):
        title_card = [
            " Clients and Reports Workflow                                     ",
            "------------------------------------------------------------------",
            """
    This workflow can import/export clients from Plextrac. You can choose whether
    reports under a client should be moved as well. For each client exported, a ZIP
    file is created. This ZIP file can be used to reimport the client into a
    different Plextrac instance.

    Overview of Next Steps:
    - Export clients
      - select which clients to export
      - choose whether to export reports with client
    - Import clients
      - add ZIP files of clients to import
      - choose whether to check if the client exists
      - choose whether to export reports with client
      """]
        for i in title_card:
            print(i)

    
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

        zip_file_name = utils.sanitize_file_name(f'{client["name"]}_{client["client_id"]}_{globals.script_time}.zip')
        with open(f'{folder_path}/{zip_file_name}', 'wb') as f:
            f.write(zip_buffer.getvalue())

    
    def get_json_object_type(self, loaded_json):
        """
        :return: ["client", "report", "ptrac"]
        :rtype: str
        """
        if self._json_is_client(loaded_json): return "client"
        if self._json_is_report(loaded_json): return "report"
        if self._json_is_ptrac(loaded_json): return "ptrac"
    

    def _json_is_client(self, json_object) -> bool:
        if "poc" not in list(json_object.keys()): return False
        if "poc_email" not in list(json_object.keys()): return False
        if "users" not in list(json_object.keys()): return False
        if "doc_type" not in list(json_object.keys()): return False
        if json_object['doc_type'] != "client": return False
        return True


    def _json_is_report(self, json) -> bool:
        if "template" not in list(json.keys()): return False
        if "fields_template" not in list(json.keys()): return False
        if "reviewers" not in list(json.keys()): return False
        if "operators" not in list(json.keys()): return False
        if "includeEvidence" not in list(json.keys()): return False
        return True
    

    def _json_is_ptrac(self, json) -> bool:
        if "report_info" not in list(json.keys()): return False
        if "flaws_array" not in list(json.keys()): return False
        if "summary" not in list(json.keys()): return False
        if "evidence" not in list(json.keys()): return False
        if "client_info" not in list(json.keys()): return False
        if "procedures" not in list(json.keys()): return False
        return True
    

    # TODO move to utils file
    def get_script_root_path(self, start_path=None):
        if start_path is None:
            start_path = os.path.abspath(os.path.dirname(__file__))

        # Specify a distinctive file or directory that identifies the project root
        project_root_identifier = '.git'

        current_path = start_path

        while current_path != os.path.dirname(current_path):
            if project_root_identifier in os.listdir(current_path):
                return current_path
            current_path = os.path.dirname(current_path)

        return None


    # TODO verify initial_directory exists
    # TODO move to utils file
    def select_zip_files(self, initial_directory=None):
        """
        Prompt the user to select multiple zip files and return their paths.
        """
        root = Tk()
        root.withdraw()  # Hide the root window
        file_paths = askopenfilenames(
            filetypes=[("Zip files", "*.zip")],
            initialdir=initial_directory
        )
        return file_paths
    

    # TODO create defined object that holds response
    def extract_data_from_client_ZIP(self, zip_path):
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
                            if self.get_json_object_type(json_data) == "client":
                                client_json = json_data
                            elif self.get_json_object_type(json_data) == "ptrac":
                                report_json_list.append(json_data)
            if client_json == None:
                log.exception(f'client ZIP file \'{zip_path}\' did not contain a valid client JSON')
                return None, None
            return client_json, report_json_list
        except Exception as e:
            log.exception(f'Could not find or load client ZIP file \'{zip_path}\'\n{e}')
            return None, None


    def start(self):
        binput.console.clear()
        log.debug(f'starting workflow \'client_reports\'')
        self.display_title_card()

        log.info(f'Would you like to import or exports clients')
        action = binput.select([":import clients", ":export clients"], cursor=">", cursor_style='white')
        log.debug(f'selected: {action}')

        if action == "import clients":
            self.import_clients()
        elif action == "export clients":
            self.export_clients()


    def export_clients(self):
        import main # importing here to prevent circular imports

        # get clients from instance
        spinner = binput.spinners.Spinner(binput.spinners.DOTS, "Loading clients from instance...")
        spinner.start()
        clients = []
        data.get_page_of_clients(clients=clients, auth=globals.auth)
        spinner.stop()
        if len(clients) < 1:
            log.exception(f'Did not find any clients in Plextrac instance... Exiting to main menu')
            main.start()

        # user selects clients
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

        # prompt user for action details
        export_clients_options = binput.select_multiple(
            options=["include client reports", "exclude user data"], # TODO add option to exclude user, sensitivity
            tick_character="x",
            tick_style="green",
            cursor_style="dark_goldenrod"
        )

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
        folder_path = "exported_client_ZIPs"
        try:
            os.mkdir(folder_path)
        except FileExistsError as e:
            log.debug(f'Could not create directory {folder_path}, already exists')

        for i, client in enumerate(selected_clients):
            self.create_client_zip_with_json_objects(client, sorted_client_reports[i], folder_path)

        # return to main menu
        main.start()


    def import_clients(self):
        import main # importing here to prevent circular imports

        # have user select client ZIP files to import
        absolute_path = os.path.abspath("exported_client_ZIPs")
        if not (os.path.exists(absolute_path) and os.path.isdir(absolute_path)):
            absolute_path = self.get_script_root_path()
        zip_file_paths = self.select_zip_files(initial_directory=absolute_path)
        log.debug(f'selected {len(zip_file_paths)} ZIP files')
        
        # import data from client ZIPs
        for file_path in zip_file_paths:
            client, report_list = self.extract_data_from_client_ZIP(file_path)
            if client == None:
                log.exception(f'Skipping invalid client ZIP file \'{file_path}\'...')
                continue

            # create client
            payload = client
            payload.pop("cuid")
            payload.pop("tenant_id")
            payload.pop("client_id")
            # TODO figure out how to handle logo
            payload.pop("logo")
            payload.pop("doc_type")
            # TODO figure out how to handle users
            payload.pop("users")
            payload['name'] = "Green Testing import" # TODO remove - only for testing
            try:
                response = api.clients.create_client(globals.auth.base_url, globals.auth.get_auth_headers(), payload)
                client_id = response.json['client_id']
            except Exception as e:
                log.exception(f'Could not create client. Skipping client and {len(report_list)} subsequent report(s)...')
                continue

            # # import ptracs
            # def request_import_report_from_ptrac(base_url, headers, client_id, file):
            #     name = "Import Ptrac Report"
            #     root = "/api/v1"
            #     path = f'/client/{client_id}/report/import'
            #     multipart_form_data = {
            #         'file': file
            #     }
            #     return request_post_multipart(base_url, root, path, name, headers, multipart_form_data)


            for ptrac in report_list:
                try:
                    json_str = json.dumps(ptrac)
                    json_file_like = io.BytesIO(json_str.encode('utf-8'))
                    multipart_form_data = {
                        'file': json_file_like
                    }
                    response = api.reports.import_ptrac_report(globals.auth.base_url, globals.auth.get_auth_headers(), client_id, multipart_form_data)
                except Exception as e:
                    log.exception(f'Could not create report. Skipping...')
                    continue

        # return to main menu
        main.start()

        