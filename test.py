#!/usr/bin/env python3

import lib.log
import os
import argparse
import subprocess
import ruamel.yaml
import random
import string
logger = lib.log.setup_logging(__name__)


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--os",
                        type=str,
                        action='append',
                        required=True,
                        help="OS to test")
    return vars(parser.parse_args())


def main():
    try:
        try:
            args = parse()
            args['basepath'] = os.getcwd()
            work(args)
        except:
            logger.critical(
                'Program failed unexpectedy. Check debuglog for details.')
            raise
        finally:
            logger.info('#####################')
    except KeyboardInterrupt:
        print("KeyboardInterrupt has been caught.")


def work(args):
    oses = []
    for distrib in os.listdir('oses'):
        if distrib not in args['os']:
            if 'all' not in args['os']:
                logger.info('Skipping distribution {}'.format(distrib))
                continue
        for version in os.listdir(os.path.join('oses', distrib)):
            oses.append(OS(args, distrib, version))
    for element in oses:
        print('FLAG XXXXXXXXXXXXXXx')
        element.run()


class OS:
    def __init__(self, args, distrib, version):
        self.args = args
        self.distrib = distrib
        self.version = version
        self.root = os.path.join(args['basepath'], 'oses', distrib, version)
        logger.info('Loaded OS from {}'.format(self.root))

    def load_cases(self):
        self.cases = []
        try:
            specs = read_yaml(os.path.join(self.root, 'specs.yaml'))
            for _id in specs['cases'].keys():
                self.cases.append(Case(self.root, _id, specs['cases'][_id]))
        except:
            logger.error('Unable to load cases for {}/{}'.format(
                self.distrib, self.version))

    def run(self):
        self.load_cases()
        for case in self.cases:
            case.run()


class Case:
    def __init__(self, root, _id, case):
        self.root = root
        self._id = _id
        self.case = case
        self.name = gen_random_string(prefix='ci-%d-' % self._id, length=10)
        logger.info('Loaded case {}'.format(_id))

    def run(self):
        try:
            logger.info('Running case with name {}'.format(self.name))
            self.deploy_infra(
                self.name,
                self.case['infra']['script'],
                self.case['infra']['master'],
                self.case['infra']['worker'])
            self.deploy_k8s(self.case['infra']['script'])
            self.deploy_rook()
        finally:
            self.undeploy_infra(
                self.name,
                self.case['infra']['script'],
            )


    def deploy_infra(self, name, script, master, worker):
        logger.info("Deploying infra")
        root = os.path.join(self.root, 'deploy')
        try:
            subprocess.run(['./{}'.format(script),
                            '--action', 'deploy',
                            '--name', name,
                            '--master', str(master),
                            '--worker', str(worker)],
                           cwd=root)
        except:
            raise

    def undeploy_infra(self, name, script):
        logger.info("Undeploying infra")
        root = os.path.join(self.root, 'deploy')
        subprocess.run(['./{}'.format(script),
                        '--action', 'undeploy',
                        '--name', name],
                       cwd=root)

    def deploy_k8s(self, script):
        logger.info("Deploying Kubernetes")
        root = os.path.join(self.root, 'deploy')
        try:
            subprocess.run(['./{}'.format(script), cwd=root)
        except:
            raise

    def deploy_rook(self):
        pass


def write_yaml(data, outfile):
    with open(outfile, 'w') as fp:
        fp.write(ruamel.yaml.dump(
            data,
            default_flow_style=False,
            explicit_start=True))


def read_yaml(template):
    with open(template, 'r') as fp:
        model = ruamel.yaml.load(fp, Loader=ruamel.yaml.Loader)
    return model


def gen_random_string(prefix='', length=10):
    return '{}-{}'.format(
        prefix,
        ''.join(random.choice(string.ascii_letters) for x in range(length)))


main()
