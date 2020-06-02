from captchamonitor.chef import CaptchaMonitor
from captchamonitor.utils.db_export import export
import logging
import time
import argparse
import sys
import os

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('captchamonitor')
logger.setLevel(logging.INFO)


class main():
    def __init__(self):
        self.default_config_file_path = os.path.join(os.getcwd(), 'config.ini')
        parser = argparse.ArgumentParser(description='CAPTCHA Monitor',
                                         usage='''captchamonitor <command> [<args>]

Available commands:
run     Run the CAPTCHA Monitor in loop until stopped by the user
export  Export the captured data to a JSON file
add     Add a new job to the database
                                        ''')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            sys.exit()
        # Run the corresponding command
        getattr(self, args.command)()

    def run(self):
        if os.path.isfile(self.default_config_file_path) and os.access(self.default_config_file_path, os.R_OK):
            config_file = self.default_config_file_path
            logger.info('Using the configuration file found in the current working directory')
        else:
            parser = argparse.ArgumentParser(description='Path to the configuration file')
            parser.add_argument('config_file')
            args = parser.parse_args(sys.argv[2:])
            config_file = args.config_file
            logger.info('Running CAPTCHA Monitor with the given configuration file')

        try:
            while True:
                CaptchaMonitor.run(config_file)
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info('Stopping, bye!')
            sys.exit()

    def export(self):
        if os.path.isfile(self.default_config_file_path) and os.access(self.default_config_file_path, os.R_OK):
            config_file = self.default_config_file_path
            logger.info('Using the configuration file found in the current working directory')
        else:
            parser = argparse.ArgumentParser(description='Path to the configuration file')
            parser.add_argument('config_file')
            args = parser.parse_args(sys.argv[2:])
            config_file = args.config_file
            logger.info('Running CAPTCHA Monitor with the given configuration file')

        try:
            logger.info('Exporting...')
            export(config_file)
            logger.info('Done!')
            sys.exit()

        except KeyboardInterrupt:
            logger.info('Stopping, bye!')
            sys.exit()


if __name__ == '__main__':
    main()
