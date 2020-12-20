import argparse
import logging
import os
import sys

from captchamonitor import (
    add,
    analyze,
    cloudflare,
    compose,
    export,
    md5,
    stats,
    worker,
)

logging.basicConfig(format="%(asctime)s %(module)s [%(levelname)s] %(message)s")

# get the root logger for this module
logger = logging.getLogger("captchamonitor")
logger.setLevel(logging.INFO)

env_vars = {
    "CM_DB_USER": "The database username",
    "CM_DB_PASS": "The database password",
    "CM_DB_NAME": "The database name",
    "CM_DB_HOST": "The IP address of the database server",
    "CM_DB_PORT": "The port number of the database server",
}

for env_var in env_vars:
    if env_var not in os.environ:
        logger.warning(
            "%s (%s) is not set in the environment",
            env_vars[env_var],
            env_var,
        )
        sys.exit()

os.environ["CM_TOR_HOST"] = "127.0.0.1"
os.environ["CM_TOR_DIR_PATH"] = "/home/cm/tor/data"

MAIN_DESC = """
CAPTCHA Monitor
"""

MAIN_HELP = """
Use 'captchamonitor <subcommand> --help' for more info
"""

WORKER_DESC = "Start in worker mode and process jobs"
WORKER_HELP = "Start in worker mode and process jobs"

ADD_JOB_DESC = "Add a new job to queue"
ADD_JOB_HELP = "Add a new job to queue"

COMPOSE_DESC = "Automatically add new jobs base on the job history"
COMPOSE_HELP = "Automatically add new jobs base on the job history"

ANALYZE_DESC = "Analyze the collected data"
ANALYZE_HELP = "Analyze the collected data"

MD5_DESC = "Returns the MD5 hash of a given URL"
MD5_HELP = "Returns the MD5 hash of a given URL"

EXPORT_DESC = (
    "Export the database tables to JSON files into a specified directory"
)
EXPORT_HELP = "Export the database tables to JSON files"

STATS_DESC = "Shows the stats of the remaining and completed jobs"
STATS_HELP = "Shows the stats of the remaining and completed jobs"

CLOUDFLARE_DESC = "Change Cloudflare security levels"
CLOUDFLARE_HELP = "Change Cloudflare security levels"


def formatter_class(prog):
    """
    Formats the arg parse menu
    """

    return argparse.HelpFormatter(prog, max_help_position=52)


class main:
    """
    Class the handles the command line arguments and running the requested module
    """

    def __init__(self):
        """
        Constructor
        """

        main_parser = argparse.ArgumentParser(description=MAIN_DESC)

        sub_parser = main_parser.add_subparsers(help=MAIN_HELP)

        ###########
        # ADD JOB #
        ###########
        add_job_parser = sub_parser.add_parser(
            "add",
            description=ADD_JOB_DESC,
            help=ADD_JOB_HELP,
            formatter_class=formatter_class,
        )

        add_job_parser.set_defaults(func=add, formatter_class=formatter_class)

        add_job_parser.add_argument(
            "-u",
            "--url",
            help="""the interesting URL to fetch""",
            metavar="URL",
            required="True",
            default="",
        )

        add_job_parser.add_argument(
            "-m",
            "--method",
            help="""the webrowser/tool to fetch the provided URL""",
            metavar="NAME",
            required="True",
            default="",
        )

        add_job_parser.add_argument(
            "-c",
            "--captcha_sign",
            help="""the text that will be searched for""",
            metavar="TEXT",
            default="| Cloudflare",
        )

        add_job_parser.add_argument(
            "-a",
            "--additional_headers",
            help="""specify additional headers for the job""",
            metavar="HEADER",
            default="",
        )

        add_job_parser.add_argument(
            "-e",
            "--exit_node",
            help="""specify the Tor exit node (if fetching over Tor)""",
            metavar="IP",
            default="",
        )

        add_job_parser.add_argument(
            "-s",
            "--tbb_security_level",
            help="""specify the Tor Browser security level, if using Tor Browser""",
            metavar="LEVEL",
            default="medium",
        )

        add_job_parser.add_argument(
            "-b",
            "--browser_version",
            help="""specify the version of the browser, if using a browser (leave empty to use the latest version)""",
            metavar="VERSION",
            default="",
        )

        add_job_parser.add_argument(
            "-d",
            "--data_hash",
            help="""md5 hash of the original data for checking data integrity""",
            metavar="HASH",
            default="",
        )

        add_job_parser.add_argument(
            "-x",
            "--all_exit_nodes",
            help="""use this argument if you want to add this current job for all exit nodes""",
            action="store_true",
        )

        add_job_parser.add_argument(
            "-v",
            "--verbose",
            help="""show all log messages""",
            action="store_true",
        )

        ##########
        # WORKER #
        ##########
        worker_parser = sub_parser.add_parser(
            "worker",
            description=WORKER_DESC,
            help=WORKER_HELP,
            formatter_class=formatter_class,
        )

        worker_parser.set_defaults(func=worker, formatter_class=formatter_class)

        worker_parser.add_argument(
            "-r",
            "--retry",
            help="""specify the number of retries for failed jobs""",
            metavar="N",
            type=int,
            default=1,
        )

        worker_parser.add_argument(
            "-t",
            "--timeout",
            help="""specify the number of seconds to allow each job to run""",
            metavar="N",
            type=int,
            default=30,
        )

        worker_parser.add_argument(
            "-l",
            "--loop",
            help="""use this argument to process jobs in a loop""",
            action="store_true",
            default=True,
        )

        worker_parser.add_argument(
            "-v",
            "--verbose",
            help="""show all log messages""",
            action="store_true",
        )

        ###########
        # COMPOSE #
        ###########
        compose_parser = sub_parser.add_parser(
            "compose",
            description=COMPOSE_DESC,
            help=COMPOSE_HELP,
            formatter_class=formatter_class,
        )

        compose_parser.set_defaults(
            func=compose, formatter_class=formatter_class
        )

        compose_parser.add_argument(
            "-m",
            "--match_relays_and_jobs",
            help="""specify the interval in minutes to update the job information related to relays""",
            metavar="N",
            type=int,
            default=15,
        )

        compose_parser.add_argument(
            "-d",
            "--dispatch_jobs",
            help="""specify the interval in minutes to dispatch a new batch of jobs""",
            metavar="N",
            type=int,
            default=30,
        )

        compose_parser.add_argument(
            "-b",
            "--batch_size",
            help="""specify the jobs to dispatch in a single batch""",
            metavar="N",
            type=int,
            default=150,
        )

        compose_parser.add_argument(
            "-n",
            "--new_relays",
            help="""specify the interval in minutes to update the relay list from consensus""",
            metavar="N",
            type=int,
            default=60,
        )

        compose_parser.add_argument(
            "-l",
            "--local_tor",
            help="""use local Tor's directory for fetching consensus""",
            action="store_true",
        )

        compose_parser.add_argument(
            "-v",
            "--verbose",
            help="""show all log messages""",
            action="store_true",
        )

        ###########
        # ANALYZE #
        ###########
        analyze_parser = sub_parser.add_parser(
            "analyze",
            description=ANALYZE_DESC,
            help=ANALYZE_HELP,
            formatter_class=formatter_class,
        )

        analyze_parser.set_defaults(
            func=analyze, formatter_class=formatter_class
        )

        analyze_parser.add_argument(
            "-v",
            "--verbose",
            help="""show all log messages""",
            action="store_true",
        )

        analyze_parser.add_argument(
            "-g",
            "--process_captcha_rates",
            help="""specify the interval in hours to analyze and recreate the graph data""",
            metavar="N",
            type=int,
            default=30,
        )

        #################
        # CALCULATE MD5 #
        #################
        md5_parser = sub_parser.add_parser(
            "md5",
            description=MD5_DESC,
            help=MD5_HELP,
            formatter_class=formatter_class,
        )

        md5_parser.set_defaults(func=md5, formatter_class=formatter_class)

        md5_parser.add_argument(
            "-u",
            "--url",
            help="""the website given URL will be hashed""",
            required="True",
            metavar="URL",
            default="",
        )

        md5_parser.add_argument(
            "-v",
            "--verbose",
            help="""show all log messages""",
            action="store_true",
        )

        ##########
        # EXPORT #
        ##########
        export_parser = sub_parser.add_parser(
            "export",
            description=EXPORT_DESC,
            help=EXPORT_HELP,
            formatter_class=formatter_class,
        )

        export_parser.set_defaults(func=export, formatter_class=formatter_class)

        export_parser.add_argument(
            "-p",
            "--path",
            help="""use this argument to process jobs in a loop""",
            required="True",
            metavar="PATH",
        )

        export_parser.add_argument(
            "-v",
            "--verbose",
            help="""show all log messages""",
            action="store_true",
        )

        #########
        # STATS #
        #########
        stats_parser = sub_parser.add_parser(
            "stats",
            description=STATS_DESC,
            help=STATS_HELP,
            formatter_class=formatter_class,
        )

        stats_parser.set_defaults(func=stats, formatter_class=formatter_class)

        stats_parser.add_argument(
            "-v",
            "--verbose",
            help="""show all log messages""",
            action="store_true",
        )

        ##############
        # CLOUDFLARE #
        ##############
        cloudflare_parser = sub_parser.add_parser(
            "cloudflare_change",
            description=CLOUDFLARE_DESC,
            help=CLOUDFLARE_HELP,
            formatter_class=formatter_class,
        )

        cloudflare_parser.set_defaults(
            func=cloudflare, formatter_class=formatter_class
        )

        cloudflare_parser.add_argument(
            "-e",
            "--email",
            help="""your Cloudflare email""",
            required="True",
            metavar="EMAIL",
        )

        cloudflare_parser.add_argument(
            "-t",
            "--token",
            help="""your Cloudflare API token""",
            required="True",
            metavar="TOKEN",
        )

        cloudflare_parser.add_argument(
            "-d",
            "--domain",
            help="""use this argument to process jobs in a loop""",
            required="True",
            metavar="NAME",
        )

        cloudflare_parser.add_argument(
            "-s",
            "--security_level",
            help="""use this argument to process jobs in a loop""",
            required="True",
            metavar="NAME",
        )

        cloudflare_parser.add_argument(
            "-v",
            "--verbose",
            help="""show all log messages""",
            action="store_true",
        )

        # Get args and call the command handler for the chosen mode
        if len(sys.argv) == 1:
            main_parser.print_help()
            sys.exit(1)
        else:
            args = main_parser.parse_args()
            args.func(args)


if __name__ == "__main__":
    main()
