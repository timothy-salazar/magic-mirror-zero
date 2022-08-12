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
    config = read_config()
    replace_crontab(config)
    make_command_file(config)

def replace_crontab(config):
    """ Input:
            config: configparser.ConfigParser - a configparser object containing
                the information in the configuration file (which should be
                located at magic-mirror-zero/magicmirror/config)
        Output:
            None

    Deletes user crontab, creates new crontab text (which is saved as a file in
    the project root directory), and then installs the new crontab file.
    """
    # this gets the path to where we're going to save our crontab file
    project_dir = get_project_dir()
    crontab_path = project_dir.joinpath('crontab.txt')

    # remove the existing user crontab
    subprocess.run(['crontab', '-r'], check=True)

    # saves valid crontab as crontab.txt, then installs it
    crontab = cron_formatter(config)
    with open(crontab_path, 'w+') as f:
        f.write(crontab)
    subprocess.run(['crontab', crontab_path], check=True)

def make_command_file(config):
    """ Input:
            config: configparser.ConfigParser - a configparser object containing
                the information in the configuration file (which should be
                located at magic-mirror-zero/magicmirror/config)
        Output:
            None

        If the user has specified that they want any commands run when the
        mirror starts up (this is specified by setting the 'run_at_startup'
        setting in 'magicmirror/config' to True), then a file is generated
        containing these commands.

    """
    # this gets the path to where we're going to save the command file
    project_dir = get_project_dir()
    command_path = project_dir.joinpath('commands.sh')

    # We write the commands the user has specified that they want run
    # on startup to a file called 'commands.sh' in the project root directory.
    # They will be run by the start_mirror.sh script.
    command_text = command_formatter(config)
    with open(command_path, 'w+') as f:
        f.write(command_text)


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

def command_formatter(config):
    """ Input:
            config: configparser.ConfigParser - a configparser object containing
                the information in the configuration file (which should be
                located at magic-mirror-zero/magicmirror/config)
        Output:
            command_text: string - the information from the variables in our
                config file formatted in such a way that they can be saved as a
                bash script in the project root directory.
    """
    template = assemble_template(as_crontab=False)
    sections = config.sections()
    command_text = ''
    command_text += '# !/bin/bash\n'
    for section_name in sections:
        section = dict(config[section_name])
        if section_name == 'environment':
            continue
        if section['run_at_startup'].lower() != 'true':
            continue
        command = section['command']
        # Any '%' symbols in the command need to be backslash escaped if they're
        # going to be run by cron. We need to undo that in order to run the
        # command here.
        section['command'] = command.replace('\%', '%')

        # command_text should be a command that we can run
        command_text += template.format(**section)
    return command_text

def cron_formatter(config):
    """ Input:
            None
        Output:
            crontab: string - the information from the config file formatted in
                such a way as to be interpretable as a valid crontab file.
    """
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

def assemble_template(as_crontab = True):
    """ Input:
            as_crontab: bool - if 'as_crontab' is true, we'll make a template
                we can use to assemble our crontab file.
                if as_crontab is false, we'll get a template we can use to run
                'command' immediately.
        Output:
            template: string - a template that will take the variables in our
                config file and format them as a valid crontab entry
    """
    # We need to use absolute paths if we want to be sure that cron will do its
    # job reliably, so this is just getting the absolute path to the
    # update_mirror.py script.
    project_dir = get_project_dir()
    script_path = project_dir.joinpath(
        'magicmirror', 'mirror', 'update_mirror.py')
    template = ''
    if as_crontab:
        template += '{timing} '
    template += '{command} | '
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
    main()
