import copy
import datetime
import os
import json
from typing import Dict, List, Any

from constants.config import BASE_VERSION_STR, VERSION_JSON_PATH, BASE_JSONS_PKG_PATH
from constants.enums import EnvironmentEnum, S3BucketACLPermissions
from exceptions import FileNotFound
from s3_service import S3Service


class GenerateAppJson:

    def generate_app_json(self, envs: List[EnvironmentEnum], version_message: str):
        all_envs_config_json = self.read_json('config_jsons/env_config.json')

        base_json_files = [
            f"{BASE_JSONS_PKG_PATH}/{file}"
            for file in os.listdir(BASE_JSONS_PKG_PATH)
            if file.endswith('.json')
        ]
        for base_json_path in base_json_files:
            self._generate_app_jsons_for_base_json(
                all_envs_config_json=all_envs_config_json,
                base_json_file_path=base_json_path,
                envs=envs,
                version_message=version_message
            )

    def _generate_app_jsons_for_base_json(
        self,
        all_envs_config_json: Dict,
        base_json_file_path: str,
        envs: List[EnvironmentEnum],
        version_message: str
    ):
        base_app_config_str = json.dumps(self.read_json(base_json_file_path))
        envs = envs if envs else [each.value for each in EnvironmentEnum]
        env_apps_configs = self._get_env_apps_configs(envs=envs)
        version_json_data = []
        for app_config in env_apps_configs:
            temp_base_app_config_str = copy.deepcopy(base_app_config_str)
            replace_patterns = app_config.get("replace_patterns", [])
            replace_patterns = self._add_default_replace_patterns(
                replace_patterns=replace_patterns,
                base_config=all_envs_config_json["base"],
                env_config=app_config
            )
            for pattern in replace_patterns:
                temp_base_app_config_str = temp_base_app_config_str.replace(pattern['from'], pattern['to'])
            updated_app_json = json.loads(temp_base_app_config_str)
            formatted_resource_display_name = app_config["formatted_resource_display_name"]
            new_app_config_file_path = f"app_jsons/{formatted_resource_display_name}.json"
            self.write_json(new_app_config_file_path, updated_app_json)

            s3_url = self._push_app_config_to_s3(
                app_json_prefix=formatted_resource_display_name,
                local_file_path=new_app_config_file_path
            )
            version_json_data.append({
                "version_s3_url": s3_url,
                "published_datetime": datetime.datetime.now(),
                "version_message": version_message
            })
        self._update_version_message(version_json_data=version_json_data)

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
    def write_json(file_path: str, file_content: Any):
        with open(file_path, 'w') as json_file:
            json.dump(file_content, json_file, indent=4)

    def _push_app_config_to_s3(self, app_json_prefix: str, local_file_path: str) -> str:
        s3_service = S3Service()
        version_str = self._get_version_string(app_json_prefix=app_json_prefix, s3_service=s3_service)

        file_contents = open(local_file_path, "rb").read()
        # noinspection PyTypeChecker
        return s3_service.put_object(
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

    def _update_version_message(self, version_json_data: List[Dict]):
        s3_service = S3Service()
        try:
            versions = s3_service.get_object(key=VERSION_JSON_PATH)
            versions = json.loads(versions)
        except FileNotFound:
            versions = []
        for version in versions:
            version["published_datetime"] = datetime.datetime.strptime(
                version["published_datetime"], "%Y-%m-%d %H:%M:%S.%f"
            )
        versions.extend(version_json_data)
        versions.sort(key=lambda v: v["published_datetime"], reverse=True)
        for version in versions:
            version["published_datetime"] = version["published_datetime"].strftime("%Y-%m-%d %H:%M:%S.%f")

        local_version_json_path = "app_jsons/version.json"
        self.write_json(
            file_path=local_version_json_path,
            file_content=versions
        )
        file_contents = open(local_version_json_path, "rb").read()
        # noinspection PyTypeChecker
        return s3_service.put_object(
            body=file_contents,
            file_name=VERSION_JSON_PATH,
            acl=S3BucketACLPermissions.PUBLIC_READ.value
        )


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python gen_app_json.py all 'Major changes'")
        sys.exit(1)

    # Retrieve command-line arguments
    env_str = sys.argv[1]
    envs_list = [] if "all" in env_str else env_str.split(",")
    envs_list = [each.strip() for each in envs_list]

    invalid_envs = [each for each in envs_list if each not in EnvironmentEnum.get_list_of_values()]
    if invalid_envs:
        print(f"Invalid envs: {invalid_envs}")
        sys.exit(1)

    version_msg = sys.argv[2]
    if not version_msg.strip():
        print("Please provide a version message")
        sys.exit(1)

    # noinspection PyTypeChecker
    GenerateAppJson().generate_app_json(
        envs=envs_list,
        version_message=version_msg
    )
