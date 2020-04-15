#!/usr/bin/env python3

import logging
import os
import systemd.journal

def setup_logging(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.addHandler(systemd.journal.JournalHandler())
    return logger
