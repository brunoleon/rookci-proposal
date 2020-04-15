#!/usr/bin/env python3

import os
import shutil
import json
import string
import random
import simplejson
import subprocess
import logging
import os
import systemd.journal
import argparse


def setup_logging(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.addHandler(systemd.journal.JournalHandler())
    return logger

logger = setup_logging(__name__)

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name",
						type=str,
                        required=True,
                        help="Name of the stack")
    return vars(parser.parse_args())


def main():
    try:
        try:
            args = parse()
            args['basepath'] = os.getcwd()
            deployment = Deployment(
                args['name']
            )
            deployment.deploy()
        except:
            logger.critical(
                'Program failed unexpectedy. Check debuglog for details.')
            raise
        finally:
            logger.info('#####################')
    except KeyboardInterrupt:
        print("KeyboardInterrupt has been caught.")


class Deployment:
    def __init__(self, name):
        self.name = name

    def setup(self):
        try:
            if not os.path.isdir(self.name):
                logger.error('Specified infra deployment path {} does not \
exist'.format(self.name))
                raise
            os.chdir(self.name)
            self.data = read_json('infra_deploy.json')
            print(self.data)
        except:
            raise

    def deploy(self):
        try:
            logger.info('Deploy using skuba...')
            self.setup()
            #, stdout=subprocess.DEVNULL
            for k, v in self.data['ip_load_balancer']['value'].items():
                res = subprocess.run(
                    ['skuba', 'cluster', 'init', '--control-plane',
                    v, 'cluster'])
                logger.debug(res.args)
                if res.returncode != 0:
                    raise
                break  # there should be only one LB but just in case
            os.chdir('cluster')
            for k, v in self.data['ip_masters']['value'].items():
                res = subprocess.run(
                    ['skuba', 'node', 'bootstrap',
                     '--user', 'sles', '--sudo',
                     '--target', v, k])
                logger.debug(res.args)
                if res.returncode != 0:
                    raise
                break  # we only need to bootstrap one master
            for k, v in self.data['ip_workers']['value'].items():
                res = subprocess.run(
                    ['skuba', 'node', 'join', '--role', 'worker',
                     '--user', 'sles', '--sudo',
                     '--target', v, k], stdout=subprocess.DEVNULL)
                logger.debug(res.args)
                if res.returncode != 0:
                    raise
        except:
            raise
        finally:
            pass


def read_json(path):
    with open(path) as json_file:
        data = json.load(json_file)
        return data


def write_json(path, data):
    with open(path, 'w') as outfile:
        json.dump(data, outfile)


main()
