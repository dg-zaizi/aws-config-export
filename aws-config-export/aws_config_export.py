import logging
import os
import boto3
import json
from pathlib import Path
import argparse
import re

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Instantiate logger
logger = logging.getLogger(__name__)

class AWSConfigExporter():
    ENV_AWS_PROFILE = 'AWS_PROFILE'

    """
    Load config file and initialise AWS API session.
    """
    def __init__(self, aws_profile: str=None, config_file: str=None):
        logger.info(f'AWSConfigExporter __init__ : aws_profile={aws_profile}')

        if config_file is None:
            self.config = []
        else:
            with open(config_file) as f:
                self.config = json.load(f)

        # Fallback to AWS_PROFILE env var if no AWS profile(s) specified
        if (aws_profile is None) or (len(aws_profile) == 0):
            if (
              (self.ENV_AWS_PROFILE in os.environ)
              and 
              (len(os.environ[self.ENV_AWS_PROFILE]) > 0)
            ):
                aws_profile = os.environ[self.ENV_AWS_PROFILE]
            else:
                raise ValueError('No AWS environment specified or set in '
                    f'{self.ENV_AWS_PROFILE}')

        self.aws_session = boto3.Session(profile_name=aws_profile)
        self.aws_client_sf = self.aws_session.client('stepfunctions')

    def get_state_machine_arn(self, name: str) -> str:
        logger.info(f'get_state_machine_arn: start name={name}')
        sm_list = self.aws_client_sf.list_state_machines()
        filtered_list = [
            i for i in sm_list['stateMachines']
            if i['name'] == name
        ]
        return filtered_list[0]['stateMachineArn']

    def get_state_machine_json(self, name: str) -> str:
        logger.info(f'get_state_machine_json: start name={name}')
        arn = self.get_state_machine_arn(name=name)
        logger.info(f'arn={arn}')
        return self.aws_client_sf.describe_state_machine(stateMachineArn=arn)

    def get_state_machine_definition_json(self, name: str) -> dict:
        logger.info(f'get_state_machine_definition_json: start name={name}')
        sm_json = self.get_state_machine_json(name=name)
        return json.loads(sm_json['definition'])

    def get_replace_value(self, value):
        logger.info(f'get_replace_value: start value={value}')

        for mr in self.config:
            # if mr['match'] == value:
            if re.match(pattern=mr['match'], string=value):
                return mr['replace']
        return value

    def key_value_iterator(self, branch: dict):
        logger.info(f'key_value_iterator: start: type(branch)={type(branch)}')
        if type(branch) is dict:
            for key in branch:
                logger.info(f'key={key} type(branch[key])={type(branch[key])}')
                if type(branch[key]) is str:
                    branch[key] = self.get_replace_value(branch[key])
                elif (type(branch[key]) is dict) or (type(branch[key]) is list):
                    self.key_value_iterator(branch=branch[key])                    
        elif type(branch) is list:
            for list_item in branch:
                self.key_value_iterator(branch=list_item)

    def get_state_machine_definition_json_terraform(self, name: str) -> dict:
        sf = self.get_state_machine_definition_json(name=name)
        self.key_value_iterator(branch=sf)
        return sf


def main(
        state_machine_name: str,
        config_file: str=None,
        aws_profile: str=None,
        output_file: str=None
):
    e = AWSConfigExporter(
            config_file=config_file,
            aws_profile=aws_profile)
            
    j = e.get_state_machine_definition_json_terraform(name=state_machine_name)
    if output_file is None:
        output_file = f'{state_machine_name}.json'
    p = Path(output_file)

    if p.exists():
        raise ValueError(f'File "{output_file}" already exists')

    f = open(output_file, 'wt', encoding='utf-8')
    f.write(json.dumps(j, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            'Export AWS State Machine config JSON. Use the optional '
            '--config_file argument to specify a set of regular expressions '
            'to replace values such as ARNs wth Terraform variable names.'
        ))

    parser.add_argument('state_machine_name', type=str,
            help='Name of State Machine to export')
    parser.add_argument('--config_file', type=str,
            help='Optional regular expression replacement configuration file')
    parser.add_argument('--aws_profile', type=str,
            help='Optional AWS_PROFILE override')
    parser.add_argument('--output_file', type=str,
            help='Optional output filename override')

    args = parser.parse_args()

    main(
        state_machine_name=args.state_machine_name,
        config_file=args.config_file,
        aws_profile=args.aws_profile,
        output_file=args.output_file
    )
