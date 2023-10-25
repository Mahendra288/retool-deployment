
import json
from typing import Dict, List

from constants.config import BASE_VERSION_STR
from constants.enums import EnvironmentEnum, S3BucketACLPermissions
from s3_service import S3Service


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
            new_app_config_file_path = f"app_jsons/{env}-app.json"
            self.write_json(new_app_config_file_path, app_config)
            self._push_app_config_to_s3(
                env=env,
                local_file_path=new_app_config_file_path
            )
            print(f"Generated {new_app_config_file_path}")

    @staticmethod
    def read_json(file_path: str):
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        return data

    @staticmethod
    def write_json(file_path: str, app_config: Dict):
        with open(file_path, 'w') as json_file:
            json.dump(app_config, json_file, indent=4)

    def _push_app_config_to_s3(self, env: EnvironmentEnum, local_file_path: str):
        s3_service = S3Service()
        version_str = self._get_version_string(env=env, s3_service=s3_service)

        file_contents = open(local_file_path, "rb").read()
        # noinspection PyTypeChecker
        s3_service.put_object(
            body=file_contents,
            file_name=f"alpha/media/retool-app-jsons/{env}-app-{version_str}.json",
            acl=S3BucketACLPermissions.PUBLIC_READ.value
        )

    @staticmethod
    def _get_version_string(env: EnvironmentEnum, s3_service: S3Service) -> str:
        from utils import increment_version

        prev_file_names = s3_service.get_files_names(
            prefix=f"alpha/media/retool-app-jsons/{env}-app"
        )
        if not prev_file_names:
            return BASE_VERSION_STR
        all_versions, version_str_map = [], {}
        for file in prev_file_names:
            version_str = file.split('-')[-1].replace(".json", "")
            version_number = int(version_str.replace(".", ""))
            all_versions.append(version_number)
            version_str_map[version_number] = version_str
        max_version_number = max(all_versions)
        version_str = version_str_map[max_version_number]
        return increment_version(version_str=version_str)


if __name__ == "__main__":
    GenerateAppJson().generate_app_json([EnvironmentEnum.ALPHA.value])
