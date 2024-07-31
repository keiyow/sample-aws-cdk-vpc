import os
import yaml


class Helper:
    @staticmethod
    def load_config(config_dir, config_file_name):
        with open(os.path.join(config_dir, config_file_name), "r") as f:
            return yaml.safe_load(f)
