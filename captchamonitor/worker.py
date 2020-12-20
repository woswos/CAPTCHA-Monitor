import logging
import os
import time

import port_for
from stem.util.log import get_logger

import captchamonitor.utils
import captchamonitor.utils.tor_launcher as tor_launcher
from captchamonitor.utils.detect import captcha, diff
from captchamonitor.utils.fetch_via import fetch_via_method
from captchamonitor.utils.queue import Queue


def worker(args):
    """
    Initialize CAPTCHA Monitor in the worker mode and process jobs in the queue

    :param args: Arguments parsed by argparse
    :type args: argparse
    """

    logger = logging.getLogger(__name__)

    fetchers_dir = "/home/cm/browsers"

    # Silence the stem logger
    stem_logger = get_logger()
    stem_logger.propagate = False

    # Get the args
    retry_budget = args.retry
    loop = args.loop
    timeout_value = int(args.timeout)

    # Set logging level depending on the verbosity
    if args.verbose:
        logging.getLogger("captchamonitor").setLevel(logging.DEBUG)
    else:
        logging.getLogger("connectionpool").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)

    # Use Docker container ID as the worker id
    worker_id = os.environ["HOSTNAME"]

    # Obtain CAPTCHA Monitor version
    captchamonitor_version = captchamonitor.__version__

    logger.info("Worker #%s has started", worker_id)

    # The loop for running the worker in a loop unless closed explicitly
    try:
        # Do setup
        queue = Queue()

        # Determine the unused ports right before launching Tor
        #   to decrease the chance of any collisions
        os.environ["CM_TOR_SOCKS_PORT"] = str(port_for.select_random())
        os.environ["CM_TOR_CONTROL_PORT"] = str(port_for.select_random())

        tor = tor_launcher.TorLauncher()
        tor.start()

        # The main loop for getting a new job and processing it
        while True:

            # Get the details of the first available job
            job_details = queue.get_job(worker_id)

            # Process the job if there is one in the queue
            if job_details is not None:
                job_details = job_details[0]

                job_id = job_details["id"]
                success = False
                fail_reason = ""

                if job_details["exit_node"]:
                    exit_node = job_details["exit_node"]
                else:
                    exit_node = None

                # Retry fetching the same job up to the specified amount
                for _ in range(retry_budget):
                    # Connect to an exit node only if Tor is required
                    if "tor" in job_details["method"]:
                        try:
                            # Create the circuit and get the exact exit node used
                            job_details["exit_node"] = tor.new_circuit(
                                exit_node
                            )
                            logger.debug(
                                "Using %s as the exit node",
                                job_details["exit_node"],
                            )

                        except Exception as err:
                            fail_reason = (
                                "Cloud not connect to the specified exit node: %s",
                                err,
                            )
                            logger.debug(fail_reason)
                            break

                    try:
                        # Fetch the URL using the method specified
                        fetched_data = fetch_via_method(
                            job_details, fetchers_dir, timeout_value
                        )

                        # Stop retry loop if a meaningful result was returned
                        if fetched_data is not None:
                            success = True
                            break

                    except Exception as err:
                        fail_reason = "Cloud not fetch the URL: %s", err
                        logger.debug(fail_reason)

                # Process the results if the fetch was successful
                error_msg = "Invalid responses from another server/proxy"
                if success and (not error_msg in fetched_data["html_data"]):
                    # Detect any CAPTCHAs
                    fetched_data["is_captcha_found"] = captcha(
                        job_details["captcha_sign"],
                        fetched_data["html_data"],
                    )

                    fetched_data["is_data_modified"] = diff(
                        job_details["expected_hash"],
                        fetched_data["html_data"],
                    )

                    # Delete columns that we don't want in the results table
                    del job_details["id"]
                    del job_details["additional_headers"]
                    del job_details["claimed_by"]

                    job_details[
                        "captchamonitor_version"
                    ] = captchamonitor_version

                    # Combine the fetched data and job details
                    results = {**job_details, **fetched_data}

                    # Insert into the database
                    queue.insert_result(results)

                    # Remove completed job from queue
                    queue.remove_job(job_id)

                else:
                    logger.debug(
                        "Job %s failed %s time(s), giving up...",
                        job_id,
                        retry_budget,
                    )
                    queue.move_failed_job(job_id, str(fail_reason))

            if not loop:
                logger.info("No job found in the queue, exitting...")
                # Break out of the inner loop
                break

            # Wait a little before the next iteration
            time.sleep(0.1)

    except Exception as err:
        logging.error(err, exc_info=True)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping worker %s", worker_id)

    finally:
        # Get ready for stopping
        tor.stop()
