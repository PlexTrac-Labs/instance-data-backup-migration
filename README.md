# instance-data-backup-migration
Since there are limited options to bulk export data from Plextrac within the platform, this script offers a solution to getting large amounts of data out of Plextrac. This is generally with the intent to reimport it into another instance, but it could be stored for backup as well.

This script is broken up into multiple workflows that manage exporting and reimporting certain modules of data.

Current modules include:
- Authentication to an instance
- Clients and reports

#### Limitations
One other backup option is to backup the entire DB. This backup can then be restored to a new instance, effectively cloning all data to the new instance. This method is preferred and this script is only meant for backing up and restoring smaller sections of data in the platform.

There are limitations with this script's approach, which are generally related to IDs. This script will read and backup data from one instance then create new data in a separate instance with the same values. However, you can't specific the IDs of objects on creation. This becomes problematic when you're trying to create new data that relates to other objects. There won't be a way to maintain a relationship between 2 objects, if the relationship is, that one objects stores the ID of another object, since the second object will have a different ID when it's recreated. Specific limitations will be noted in the info block that is display during scrip execution when a certain workflow is selected.

# Requirements
- [Python 3+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [pipenv](https://pipenv.pypa.io/en/latest/install/)

# Installing
After installing Python, pip, and pipenv, run the following commands to setup the Python virtual environment.
```bash
git clone this_repo
cd path/to/cloned/repo
pipenv install
```

# Setup
After setting up the Python environment the script will run in, you will need to setup a few things to configure the script before running.

## Credentials
In the `config.yaml` file you should add the full URL to your instance of Plextrac.

The config also can store your username and password. Plextrac authentication lasts for 15 mins before requiring you to re-authenticate. The script is set up to do this automatically through the authentication handler. If these 3 values are set in the config, and MFA is not enabled for the user, the script will take those values and authenticate automatically, both initially and every 15 mins. If any value is not saved in the config, you will be prompted when the script is run and during re-authentication.

# Usage
After setting everything up you can run the script with the following command. You should run the command from the folder where you cloned the repo.
```bash
pipenv run python main.py
```
You can also add values to the `config.yaml` file to simplify providing the script with custom parameters needed to run.

## Required Information
The following values can either be added to the `config.yaml` file or entered when prompted for when the script is run.
- PlexTrac Top Level Domain e.g. https://yourapp.plextrac.com
- Username
- Password

## Script Execution Flow
The script has a main menu and follows a state-like flow passing off execution to whichever workflow is selected. Any critical errors will return you to the main menu. Completing a workflow will also return you to the main menu. From here, you could continue exporting another data module, or authenticating to a different instance and starting to reimport data.
