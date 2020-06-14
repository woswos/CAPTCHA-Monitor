import logging
import argparse
import sys
import os

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('captchamonitor')
logger.setLevel(logging.INFO)

env_vars = {'CM_TBB_PATH': 'The path to Tor Browser bundle',
            'CM_TOR_HOST': 'The IP address of the Tor server',
            'CM_TOR_SOCKS_PORT': 'The port number of the Tor server',
            'CM_TOR_CONTROL_PORT': 'The control port number of the Tor server',
            'CM_DB_FILE_PATH': 'The path to the database file'}

for env_var in env_vars:
    if env_var not in os.environ:
        logger.warning('%s (%s) is not set in the environment' % (env_vars[env_var], env_var))
        sys.exit()


MAIN_DESC = """
CAPTCHA Monitor
"""

MAIN_HELP = """
Use 'captchamonitor <subcommand> --help' for more info
"""

ADD_JOB_DESC = 'Add a new job to queue'
ADD_JOB_HELP = 'Add a new job to queue'

RUN_DESC = 'Run jobs in the queue'
RUN_HELP = 'Run jobs in the queue'

EXPORT_DESC = 'Export the database tables to JSON files into a specified directory'
EXPORT_HELP = 'Export the database tables to JSON files'

CLOUDFLARE_DESC = 'Change Cloudflare security levels'
CLOUDFLARE_HELP = 'Change Cloudflare security levels'


def formatter_class(prog):
    return argparse.HelpFormatter(prog, max_help_position=52)


class main():
    def __init__(self):
        main_parser = argparse.ArgumentParser(description=MAIN_DESC)

        sub_parser = main_parser.add_subparsers(help=MAIN_HELP)

        ###########
        # ADD JOB #
        ###########
        add_job_parser = sub_parser.add_parser('add',
                                               description=ADD_JOB_DESC,
                                               help=ADD_JOB_HELP,
                                               formatter_class=formatter_class)

        add_job_parser.set_defaults(func=self.add_job, formatter_class=formatter_class)

        add_job_parser.add_argument('-u', '--url',
                                    help="""the interesting URL to fetch""",
                                    metavar='URL',
                                    required='True',
                                    default='')
        add_job_parser.add_argument('-m', '--method',
                                    help="""the webrowser/tool to fetch the provided URL""",
                                    metavar='NAME',
                                    required='True',
                                    default='')
        add_job_parser.add_argument('-c', '--captcha_sign',
                                    help="""the text that will be searched for""",
                                    metavar='TEXT',
                                    required='True',
                                    default='')
        add_job_parser.add_argument('-a', '--additional_headers',
                                    help="""specify additional headers for the job""",
                                    metavar='HEADER',
                                    default='')
        add_job_parser.add_argument('-e', '--exit_node',
                                    help="""specify the Tor exit node (if fetching over Tor)""",
                                    metavar='IP',
                                    default='')
        add_job_parser.add_argument('-s', '--tbb_security_level',
                                    help="""specify the Tor Browser security level (if using Tor Browser)""",
                                    metavar="LEVEL",
                                    default='medium')
        add_job_parser.add_argument('-x', '--all_exit_nodes',
                                    help="""use this argument if you want to add this current job for all exit nodes""",
                                    action='store_true')

        #######
        # RUN #
        #######
        run_parser = sub_parser.add_parser('run',
                                           description=RUN_DESC,
                                           help=RUN_HELP,
                                           formatter_class=formatter_class)

        run_parser.set_defaults(func=self.run, formatter_class=formatter_class)

        run_parser.add_argument('-r', '--retry',
                                help="""specify the number of retries for failed jobs""",
                                metavar='N',
                                type=int,
                                default=3)

        run_parser.add_argument('-t', '--timeout',
                                help="""specify the number of seconds to allow each job to run""",
                                metavar='N',
                                type=int,
                                default=60)

        run_parser.add_argument('-l', '--loop',
                                help="""use this argument to process jobs in a loop""",
                                action='store_true')

        ##########
        # EXPORT #
        ##########
        export_parser = sub_parser.add_parser('export',
                                              description=EXPORT_DESC,
                                              help=EXPORT_HELP,
                                              formatter_class=formatter_class)

        export_parser.set_defaults(func=self.export, formatter_class=formatter_class)

        export_parser.add_argument('-p', '--path',
                                   help="""use this argument to process jobs in a loop""",
                                   required='True',
                                   metavar="PATH")

        ##############
        # CLOUDFLARE #
        ##############
        cloudflare_parser = sub_parser.add_parser('cloudflare_change',
                                                  description=CLOUDFLARE_DESC,
                                                  help=CLOUDFLARE_HELP,
                                                  formatter_class=formatter_class)

        cloudflare_parser.set_defaults(func=self.cloudflare_change, formatter_class=formatter_class)

        cloudflare_parser.add_argument('-e', '--email',
                                       help="""your Cloudflare email""",
                                       required='True',
                                       metavar="EMAIL")

        cloudflare_parser.add_argument('-t', '--token',
                                       help="""your Cloudflare API token""",
                                       required='True',
                                       metavar="TOKEN")

        cloudflare_parser.add_argument('-d', '--domain',
                                       help="""use this argument to process jobs in a loop""",
                                       required='True',
                                       metavar="NAME")

        cloudflare_parser.add_argument('-s', '--security_level',
                                       help="""use this argument to process jobs in a loop""",
                                       required='True',
                                       metavar="NAME")

        # Get args and call the command handler for the chosen mode
        if len(sys.argv) == 1:
            main_parser.print_help()
            sys.exit(1)
        else:
            args = main_parser.parse_args()
            args.func(args)

    def add_job(self, args):
        """
        Add a new job to the queue
        """
        from captchamonitor.utils.queue import Queue

        queue = Queue()

        if args.all_exit_nodes:
            import captchamonitor.utils.tor_launcher as tor_launcher
            import time

            wait_time = 3
            logger.info(
                'I\'m going to replicate the specified job for all exit nodes. Use CTRL+C if you want to cancel.')
            logger.info('I\'ll wait for %d seconds before starting, just in case' % wait_time)

            for i in range(wait_time, 0, -1):
                logger.info('%s' % i)
                time.sleep(1)

            try:
                # Just all exit nodes
                tor = tor_launcher.TorLauncher()
                for exit in tor.get_exit_relays().keys():
                    data = {'method': args.method,
                            'url': args.url,
                            'captcha_sign': args.captcha_sign,
                            'additional_headers': args.additional_headers,
                            'exit_node': exit,
                            'tbb_security_level': args.tbb_security_level}
                    queue.add_job(data)

                logger.info('DONE!')

            except KeyboardInterrupt:
                logger.info('Stopping, bye!')

        else:
            data = {'method': args.method,
                    'url': args.url,
                    'captcha_sign': args.captcha_sign,
                    'additional_headers': args.additional_headers,
                    'exit_node': args.exit_node,
                    'tbb_security_level': args.tbb_security_level}

            queue.add_job(data)

        sys.exit()

    def run(self, args):
        from captchamonitor.utils.queue import Queue
        from captchamonitor.utils.fetch import fetch_via_method
        from captchamonitor.utils.captcha import detect
        from captchamonitor.utils.sqlite import SQLite
        import captchamonitor.utils.tor_launcher as tor_launcher
        import time
        import random
        import string

        # Silence the stem logger
        from stem.util.log import get_logger
        stem_logger = get_logger()
        stem_logger.propagate = False

        def randomString(size=10, chars=string.ascii_uppercase + string.digits):
            return ''.join(random.choice(chars) for _ in range(size))

        loop = args.loop
        retry_budget = args.retry
        timeout_value = int(args.timeout)

        # Generate a worker id
        worker_id = randomString(64)

        # Do setup
        db = SQLite()
        queue = Queue()

        # Start Tor
        tor = tor_launcher.TorLauncher()
        tor.start()

        # TODO: make this less confusing
        try:
            if loop:
                logger.info('Started running CAPTCHA Monitor in the continous mode')
            else:
                logger.info('Started running CAPTCHA Monitor')

            # The main loop for getting a new job and processing it
            while True:

                # Get the details of the first available job
                job_details = queue.get_job(worker_id)

                # Process the job if there is one in the queue
                if job_details is not None:
                    job_id = job_details['id']
                    success = False
                    exit_node_connection_success = False

                    try:
                        if (('tor' in job_details['method']) or (job_details['exit_node'] is not None)):
                            tor.new_circuit(job_details['exit_node'])
                            logger.info('Using %s as the exit node' % job_details['exit_node'])

                        # This will be run if circuit was created successfully or no exit node was provided
                        exit_node_connection_success = True

                    except Exception as err:
                        logger.info('Cloud not connect to the specified exit node: %s' % err)

                    # Retry fetching the same job up to the specified amount
                    for number_of_retries in range(retry_budget):
                        # Don't even try fetching if not connected to the exit node
                        # if 'tor' in job_details['method'] and not exit_node_connection_success:
                        #    break

                        # Fetch the URL using the method specified
                        fetched_data = fetch_via_method(job_details)

                        # Stop retry loop if a meaningful result was returned
                        if fetched_data is not None:
                            success = True
                            break

                    # Process the results if the fetch was successful
                    if success:
                        # Detect any CAPTCHAs
                        fetched_data['is_captcha_found'] = detect(job_details['captcha_sign'],
                                                                  fetched_data['html_data'])

                        # Delete columns that we don't want in the results table
                        del job_details['id']
                        del job_details['additional_headers']
                        del job_details['claimed_by']

                        # Combine the fetched data and job details
                        results = {**job_details, **fetched_data}

                        # Insert into the database
                        db.insert_result(results)

                    else:
                        logger.info('Job %s failed %s time(s), giving up...',
                                    job_id, retry_budget)

                    # Remove completed job from queue
                    queue.remove_job(job_id)

                elif not loop:
                    logger.info('No job found in the queue, exitting...')
                    break

                time.sleep(1)

        except KeyboardInterrupt:
            logger.info('Stopping, bye!')

        finally:
            tor.stop()
            sys.exit()

    def export(self, args):
        from captchamonitor.utils.db_export import export

        export_location = args.path

        try:
            logger.info('Exporting to %s', export_location)
            export(export_location)
            logger.info('Done!')

        except KeyboardInterrupt:
            logger.info('Stopping, bye!')

        finally:
            sys.exit()

    def cloudflare_change(self, args):
        from captchamonitor.utils.cloudflare import Cloudflare

        email = args.email
        api_token = args.token
        domain = args.domain
        security_level = args.security_level

        cloudflare = Cloudflare(email, api_token)
        zone_ids = cloudflare.get_zone_ids()
        cloudflare.set_zone_security_level(zone_ids[domain], security_level)

        sys.exit()


if __name__ == '__main__':
    main()
