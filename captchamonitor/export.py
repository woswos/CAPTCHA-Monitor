import logging
import sys
from captchamonitor.utils.db_export import export as export_db


def export(args):
    logger = logging.getLogger(__name__)

    export_location = args.path

    if args.verbose:
        logging.getLogger('captchamonitor').setLevel(logging.DEBUG)

    try:
        logger.info('Exporting to %s', export_location)
        export_db(export_location)
        logger.info('Done!')

    except KeyboardInterrupt:
        logger.info('Stopping, bye!')

    except Exception as err:
        logging.error(err, exc_info=True)

    finally:
        sys.exit()
