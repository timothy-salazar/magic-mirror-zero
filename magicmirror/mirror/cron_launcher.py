""" This will read in the config file, pass the results as a dictionary to
cron_formatter(), which formats each entry so they can be entered into the
user crontab file.
The cron_launcher() function then adds or updates each entry to the user
crontab file.
"""
import subprocess
import configparser
from update_mirror import get_project_dir

def main():
    crontab = cron_formatter()
    subprocess.run(['crontab', '-r'])
    

def read_config():
    """ Input:
            None
        Output:
            config: configparser.ConfigParser - a configparser object containing
                the information in the configuration file (which should be
                located at magic-mirror-zero/magicmirror/config)
    """
    project_dir = get_project_dir()
    config_path = project_dir.joinpath('magicmirror', 'config')
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def cron_formatter():
    """ Input:
            None
        Output:
    """
    config = read_config()
    crontab = ''
    template = assemble_template()
    sections = config.sections()
    for section_name in sections:
        section = config[section_name]
        if section_name == 'environment':
            crontab += environment_formatter(section)
            continue
        crontab += template.format(**dict(section))
    return crontab

def assemble_template():
    """ Input:
            None
        Output:
            template: string - a template that will take the variables in our
                config file and format them as a valid crontab entry
    """
    project_dir = get_project_dir()
    script_path = project_dir.joinpath(
        'magicmirror', 'mirror', 'update_mirror.py')
    template = '{timing} {command} | '
    template += f'python {script_path} '
    template += '{box_column} {box_row} {box_width} {box_height}\n'
    return template

def environment_formatter(section):
    """ Input:
            section: configparser.Section - the 'environment' configparser
                section object. Contains the environment settings we want to
                add to the crontab file.
        Output:
            environment_settings: string - the environment settings, formatted
                such that they can be understood by cron.
    """
    environment_settings = ''
    for name, value in section.items():
        environment_settings += f'{name} = {value}\n'
    return environment_settings



if __name__ == "__main__":
    read_config()
