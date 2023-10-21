
import json
from typing import Dict, List

from constants import EnvironmentEnum


class GenerateAppJson:

    def generate_app_json(self, envs: List[EnvironmentEnum]):
        env_config = self.read_json('config_jsons/env_config.json')
        app_config = self.read_json('config_jsons/app.json')

        envs = envs if envs else [each.value for each in EnvironmentEnum]
        for env in envs:
            replace_patterns = env_config[env].get("replace_patterns", [])
            app_state_str = app_config['page']['data']['appState']
            for pattern in replace_patterns:
                app_state_str = app_state_str.replace(pattern['from'], pattern['to'])
            app_config['page']['data']['appState'] = app_state_str
            new_app_config_file_name = f"app_jsons/{env}-app.json"
            self.write_json(new_app_config_file_name, app_config)
            print(f"Generated {new_app_config_file_name}")

    @staticmethod
    def read_json(file_path: str):
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        return data

    @staticmethod
    def write_json(file_path: str, app_config: Dict):
        with open(file_path, 'w') as json_file:
            json.dump(app_config, json_file, indent=4)


if __name__ == "__main__":
    GenerateAppJson().generate_app_json([])
