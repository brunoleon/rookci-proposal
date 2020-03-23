#!/usr/bin/env python3

import lib.log
import os
import argparse
from ruamel import yaml
logger = lib.log.setup_logging(__name__)

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--os",
                        type=str,
                        required=True,
                        help="OS to test")
    return vars(parser.parse_args())


def main():
    try:
        try:
            args = parse()
            args['basepath'] = os.getcwd()
            work(args)
        except Exception as e:
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
        for version in os.listdir(os.path.join('oses', distrib)):
            oses.append(OS(args, distrib, version))
    for element in oses:
        element.deploy_infra()


class OS:
    def __init__(self, args, distrib, version):
        self.args = args
        self.distrib = distrib
        self.version = version

    def deploy_infra(self):
        root = os.path.join(self.args['basepath'], 'oses', self.distrib,
                            self.version, 'deploy')
        for element in os.listdir(root):
            fp = os.path.join(root, element)
            if not os.path.isfile(fp) or \
                    not os.path.splitext(fp)[-1] in ['.sh', '.py']:
                continue
            os.chdir(root)
            os.system(fp)

    def deploy_k8s():
        pass

    def deploy_rook():
        pass

main()
