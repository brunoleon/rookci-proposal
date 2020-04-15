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
    parser.add_argument("-a", "--action",
                        choices=['deploy', 'undeploy'],
                        required=True,
                        help="Mode of action")
    parser.add_argument("-n", "--name",
						type=str,
                        required=True,
                        help="Name of the stack")
    parser.add_argument("-m", "--master",
						type=int,
                        help="Number of masters")
    parser.add_argument("-w", "--worker",
						type=int,
                        help="Number of workers")
    return vars(parser.parse_args())


def main():
    try:
        try:
            args = parse()
            args['basepath'] = os.getcwd()
            deployment = Deployment(
                args['name'],
                args['master'],
                args['worker']
            )
            if args['action'] == 'deploy':
                deployment.deploy()
            else:
                deployment.undeploy()

        except:
            logger.critical(
                'Program failed unexpectedy. Check debuglog for details.')
            raise
        finally:
            logger.info('#####################')
    except KeyboardInterrupt:
        print("KeyboardInterrupt has been caught.")


class Deployment:
    def __init__(self, name, master, worker):
        self.name = name
        self.master = master
        self.worker = worker

    def gen_ssh_key(self):
        logger.info('Generate SSH key')
        subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '2048', '-N', '',
                        '-f', '{}'.format(self.name)],
                       stdout=subprocess.DEVNULL)
        logger.info('Add SSH key to ssh-agent')
        subprocess.run(['ssh-add', '{}'.format(self.name)],
                       stdout=subprocess.DEVNULL)
        with open('%s.pub' % self.name) as f:
            pubkey = f.read().strip()
        self.data['authorized_keys'] = [pubkey]

    def setup(self):
        try:
            if os.path.isdir(self.name):
                shutil.rmtree(self.name)
            shutil.copytree('openstack', self.name)
            os.chdir(self.name)
            self.data = read_json('terraform.tfvars.json.ci.example')
            self.data['stack_name'] = self.name
            self.data['internal_net'] = self.name
            self.data['internal_subnet'] = '%s-subnet' % self.name
            self.data['internal_router'] = '%s-router' % self.name
            self.data['masters'] = self.master
            self.data['workers'] = self.worker
            # needed on internal only
            self.data['packages'].append('ca-certificates-suse')
            self.gen_ssh_key()
            write_json('terraform.auto.tfvars.json', self.data)
        except:
            raise

    def deploy(self):
        try:
            logger.info('Deploy using terraform')
            self.setup()
            res = subprocess.run(
                ['terraform', 'init'], stdout=subprocess.DEVNULL)
            if res.returncode != 0:
                raise
            res = subprocess.run(
                ['terraform', 'validate'], stdout=subprocess.DEVNULL)
            if res.returncode != 0:
                raise
            res = subprocess.run(
                ['terraform', 'apply', '-auto-approve'],
                stdout=subprocess.DEVNULL)
            if res.returncode != 0:
                raise
            res = subprocess.run(
                ['terraform', 'output', '-json'],
                stdout=subprocess.PIPE)
            if res.returncode != 0:
                raise
            with open('infra_deploy.json', 'w') as f:
                json.dump(simplejson.loads(res.stdout), f)
        except:
            raise
        finally:
            pass

    def undeploy(self):
        try:
            logger.info('Undeploying...')
            os.chdir(self.name)
            subprocess.run(['terraform', 'destroy', '-auto-approve'])
            logger.info('Removing ssh key from agent')
            subprocess.run(['ssh-add', '-d', '{}'.format(self.name)])
            os.chdir('..')
            #shutil.rmtree(self.name)
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
