import argparse
import asyncio
import logging
import os
import sys

logger = logging.getLogger(__name__)

class ContextLogRecord(logging.LogRecord):
    no_context_found = "NoContext"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        task = asyncio.Task.current_task()
        if task is not None:
            self.log_context = getattr(task, "log_context", self.no_context_found)
        else:
            self.log_context = self.no_context_found

#
# Subcommands
#

def run_subcommand(args):
    from . import server

    # Logging
    configure_logging(logging.INFO, args.log, args.verbose, args.quiet, args.silent)

    # Go
    server.start_server(
        bind=(args.address, args.port),
        mount_root=args.mount_root,
    )

#
# General
#

def create_argparser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Run the server"
    )
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity one level, repeatable.")
    parser.add_argument("-q", "--quiet", action="count", default=0, help="Decrease logging verbosity one level, repeatable.")
    parser.add_argument("-s", "--silent", action="store_true", help="Do not log to stdio.")
    parser.add_argument("-l", "--log", default=None, help="Log to the given file path.")

    parser.add_argument("-a", "--address", default=None, help="Change the bind IP address")
    parser.add_argument("-p", "--port", default=8080, help="Change the bind port number")

    return parser

def configure_logging(default_level, log_path=None, verbose_count=0, quiet_count=0, silent=False):
    logging.setLogRecordFactory(ContextLogRecord)

    formatter = logging.Formatter(
        fmt="{asctime} [{log_context}] {levelname} {name}:{lineno} {message}",
        style="{",
    )

    root_logger = logging.getLogger()

    if log_path is not None:
        file_log = logging.FileHandler(log_path)
        file_log.setFormatter(formatter)
        root_logger.addHandler(file_log)

    if not silent:
        console_log = logging.StreamHandler()
        console_log.setFormatter(formatter)
        root_logger.addHandler(console_log)

    log_level = default_level + (10 * quiet_count) - (10 * verbose_count)
    root_logger.setLevel(log_level)

def main():
    # Args
    parser = create_argparser()
    args = parser.parse_args()

    if "func" in args:
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1)
