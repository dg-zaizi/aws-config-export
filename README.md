# Help

```
% python3 aws-config-export/aws_config_export.py -h                                                 
usage: aws_config_export.py [-h] [--config_file CONFIG_FILE] [--aws_profile AWS_PROFILE] [--output_file OUTPUT_FILE] state_machine_name

Export AWS State Machine config JSON. Use the optional --config_file argument to specify a set of regular expressions to replace values such as ARNs wth Terraform variable names.

positional arguments:
  state_machine_name    Name of State Machine to export

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
                        Optional regular expression replacement configuration file
  --aws_profile AWS_PROFILE
                        Optional AWS_PROFILE override
  --output_file OUTPUT_FILE
                        Optional output filename override
% 
```

# Example Use

```
python3 -m venv .venv
```

```
pip3 install boto3
```

```
python3 aws-config-export/aws_config_export.py \
    a-state-machine-name \
    --config_file=example-config.json
```

```
cat a-state-machine-name.json
```
