
import json
from typing import Dict, List

from constants.config import BASE_VERSION_STR
from constants.enums import EnvironmentEnum, S3BucketACLPermissions
from s3_service import S3Service


class GenerateAppJson:

    def generate_app_json(self, envs: List[EnvironmentEnum], message: str):
        all_envs_config_json = self.read_json('config_jsons/env_config.json')
        base_app_config_str = json.dumps(self.read_json('config_jsons/base.json'))

        envs = envs if envs else [each.value for each in EnvironmentEnum]
        env_apps_configs = self._get_env_apps_configs(envs=envs)
        for app_config in env_apps_configs:
            replace_patterns = app_config.get("replace_patterns", [])
            replace_patterns = self._add_default_replace_patterns(
                replace_patterns=replace_patterns,
                base_config=all_envs_config_json["base"],
                env_config=app_config
            )
            for pattern in replace_patterns:
                base_app_config_str = base_app_config_str.replace(pattern['from'], pattern['to'])
            updated_app_json = json.loads(base_app_config_str)
            formatted_resource_display_name = app_config["formatted_resource_display_name"]
            new_app_config_file_path = f"app_jsons/{formatted_resource_display_name}.json"
            self.write_json(new_app_config_file_path, updated_app_json)

            self._push_app_config_to_s3(
                app_json_prefix=formatted_resource_display_name,
                local_file_path=new_app_config_file_path
            )
            print(f"Generated {new_app_config_file_path}")

    @staticmethod
    def _add_default_replace_patterns(
        replace_patterns: List[Dict], base_config: Dict, env_config: Dict
    ) -> List[Dict]:
        replace_patterns.append({
            "from": base_config["resource_id"],
            "to": env_config["resource_id"],
        })
        replace_patterns.append({
            "from": base_config["resource_display_name"],
            "to": env_config["resource_display_name"],
        })
        return replace_patterns

    @staticmethod
    def read_json(file_path: str):
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        return data

    @staticmethod
    def write_json(file_path: str, updated_app_json: Dict):
        with open(file_path, 'w') as json_file:
            json.dump(updated_app_json, json_file, indent=4)

    def _push_app_config_to_s3(self, app_json_prefix: str, local_file_path: str):
        s3_service = S3Service()
        version_str = self._get_version_string(app_json_prefix=app_json_prefix, s3_service=s3_service)

        file_contents = open(local_file_path, "rb").read()
        # noinspection PyTypeChecker
        s3_service.put_object(
            body=file_contents,
            file_name=f"alpha/media/retool-app-jsons/{app_json_prefix}-{version_str}.json",
            acl=S3BucketACLPermissions.PUBLIC_READ.value
        )

    @staticmethod
    def _get_version_string(app_json_prefix: str, s3_service: S3Service) -> str:
        from utils import increment_version

        prev_file_names = s3_service.get_files_names(
            prefix=f"alpha/media/retool-app-jsons/{app_json_prefix}-"
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

    def _get_env_apps_configs(self, envs: List[EnvironmentEnum]) -> List[Dict]:
        apps_configs = []
        all_envs_config_json = self.read_json('config_jsons/env_config.json')
        for env in envs:
            env_config = all_envs_config_json.get(env)
            if not env_config:
                continue
            apps = env_config.get("apps")
            if not apps:
                continue
            for app in apps:
                app["formatted_resource_display_name"] = self._get_formatted_resource_display_name(
                    resource_display_name=app["resource_display_name"]
                )
            apps_configs.extend(apps)
        return apps_configs

    @staticmethod
    def _get_formatted_resource_display_name(resource_display_name: str) -> str:
        resource_display_name = resource_display_name.replace("-", " ")
        resource_display_name = resource_display_name.lower()
        words = resource_display_name.split()
        resource_display_name = " ".join(words)
        return resource_display_name.replace(" ", "-")


if __name__ == "__main__":
    GenerateAppJson().generate_app_json(
        envs=[],
        message=""
    )

# todo: command line args for envs and message
# todo: include app name in file path
