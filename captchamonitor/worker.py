import time
import port_for
import os
import logging
import captchamonitor.utils
from captchamonitor.utils.detect import captcha
from captchamonitor.utils.detect import diff
from captchamonitor.utils.fetch import fetch_via_method
from captchamonitor.utils.queue import Queue
import captchamonitor.utils.tor_launcher as tor_launcher


def worker(loop, env_var, retry_budget, timeout_value=30):

    # Set environment variables specific to indidual worker
    os.environ['CM_TOR_HOST'] = str(env_var['CM_TOR_HOST'])
    os.environ['CM_TOR_DIR_PATH'] = str(env_var['CM_TOR_DIR_PATH'])
    os.environ['CM_WORKER_ID'] = str(env_var['CM_WORKER_ID'])
    os.environ['CM_DOWNLOAD_FOLDER'] = str(env_var['CM_TOR_DIR_PATH'])

    worker_id = os.environ['CM_WORKER_ID']

    captchamonitor_version = captchamonitor.__version__

    logger = logging.getLogger(__name__)

    logger.info('Worker #%s has started' % worker_id)
    first_run = True

    # The loop for running the worker unless closed explicitly
    while True:

        if not first_run:
            logger.info('Worker #%s has restarted' % worker_id)
        first_run = False

        try:
            # Do setup
            queue = Queue()

            # Determine the unused ports right before lauching Tor
            #   to decrease the chance of any collisions
            os.environ['CM_TOR_SOCKS_PORT'] = str(port_for.select_random())
            os.environ['CM_TOR_CONTROL_PORT'] = str(port_for.select_random())

            tor = tor_launcher.TorLauncher()
            tor.start()

            # The main loop for getting a new job and processing it
            while True:

                # Get the details of the first available job
                job_details = queue.get_job(worker_id)

                # Process the job if there is one in the queue
                if job_details is not None:
                    job_details = job_details[0]

                    job_id = job_details['id']
                    success = False

                    if job_details['exit_node']:
                        exit_node = job_details['exit_node']
                    else:
                        exit_node = None

                    # Retry fetching the same job up to the specified amount
                    for number_of_retries in range(retry_budget):
                        # Connect to an exit node only if Tor is required
                        if 'tor' in job_details['method']:
                            try:
                                # Create the circuit and get the exact exit node used
                                job_details['exit_node'] = tor.new_circuit(exit_node)
                                logger.debug('Using %s as the exit node' % job_details['exit_node'])

                            except Exception as err:
                                logger.info(
                                    'Cloud not connect to the specified exit node: %s' % err)
                                break

                        try:
                            # Fetch the URL using the method specified
                            fetched_data = fetch_via_method(job_details, timeout_value)

                            # Stop retry loop if a meaningful result was returned
                            if fetched_data is not None:
                                success = True
                                break

                        except Exception as err:
                            logger.info('Cloud not fetch the URL: %s' % err)

                    # Process the results if the fetch was successful
                    error_msg = 'Invalid responses from another server/proxy'
                    if success and (not error_msg in fetched_data['html_data']):
                        # Detect any CAPTCHAs
                        fetched_data['is_captcha_found'] = captcha(job_details['captcha_sign'],
                                                                   fetched_data['html_data'])

                        fetched_data['is_data_modified'] = diff(job_details['expected_hash'],
                                                                fetched_data['html_data'])

                        # Delete columns that we don't want in the results table
                        del job_details['id']
                        del job_details['additional_headers']
                        del job_details['claimed_by']

                        job_details['captchamonitor_version'] = captchamonitor_version

                        # Combine the fetched data and job details
                        results = {**job_details, **fetched_data}

                        # Insert into the database
                        queue.insert_result(results)

                        # Remove completed job from queue
                        queue.remove_job(job_id)

                    else:
                        logger.info('Job %s failed %s time(s), giving up...',
                                    job_id, retry_budget)
                        queue.move_failed_job(job_id)

                if not loop:
                    logger.info('No job found in the queue, exitting...')
                    # Break out of the inner loop
                    break

                # Wait a little before the next iteration
                time.sleep(0.1)

            if not loop:
                # Break out of the outer loop
                break

        except Exception as err:
            logging.error(err, exc_info=True)

        except (KeyboardInterrupt, SystemExit):
            logger.info('Stopping worker %s' % worker_id)

        finally:
            # Get ready for stopping
            tor.stop()
            # Break out of the outer loop
            break
