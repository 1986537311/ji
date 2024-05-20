# Copyright 2022-2024 XProbe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from logging import getLogger
from typing import Dict, List, Optional

import xoscar as xo

logger = getLogger(__name__)


class CacheTrackerActor(xo.Actor):
    def __init__(self):
        super().__init__()
        self._model_name_to_version_info: Dict[str, List[Dict]] = {}  # type: ignore

    @classmethod
    def uid(cls) -> str:
        return "cache_tracker"

    @staticmethod
    def _map_address_to_file_location(
        model_version: Dict[str, List[Dict]], address: str
    ):
        for model_name, model_versions in model_version.items():
            for info_dict in model_versions:
                info_dict["model_file_location"] = (
                    {address: info_dict["model_file_location"]}
                    if info_dict["cache_status"]
                    else None
                )

    @staticmethod
    def _update_file_location(data: Dict, origin_version_info: Dict):
        if origin_version_info["model_file_location"] is None:
            origin_version_info["model_file_location"] = data
        else:
            assert isinstance(origin_version_info["model_file_location"], dict)
            origin_version_info["model_file_location"].update(data)

    def record_model_version(self, version_info: Dict[str, List[Dict]], address: str):
        self._map_address_to_file_location(version_info, address)
        for model_name, model_versions in version_info.items():
            if model_name not in self._model_name_to_version_info:
                self._model_name_to_version_info[model_name] = model_versions
            else:
                assert len(model_versions) == len(
                    self._model_name_to_version_info[model_name]
                ), "Model version info inconsistency between supervisor and worker"
                for version, origin_version in zip(
                    model_versions, self._model_name_to_version_info[model_name]
                ):
                    if (
                        version["cache_status"]
                        and version["model_file_location"] is not None
                    ):
                        origin_version["cache_status"] = True
                        self._update_file_location(
                            version["model_file_location"], origin_version
                        )

    def update_cache_status(
        self,
        address: str,
        model_name: str,
        model_version: Optional[str],
        model_path: str,
    ):
        if model_name not in self._model_name_to_version_info:
            logger.warning(f"Not record version info for {model_name} for now.")
        else:
            for version_info in self._model_name_to_version_info[model_name]:
                if model_version is None:  # image model
                    self._update_file_location({address: model_path}, version_info)
                    version_info["cache_status"] = True
                else:
                    if version_info["model_version"] == model_version:
                        self._update_file_location({address: model_path}, version_info)
                        version_info["cache_status"] = True

    def unregister_model_version(self, model_name: str):
        self._model_name_to_version_info.pop(model_name, None)

    def get_model_versions(self, model_name: str) -> List[Dict]:
        if model_name not in self._model_name_to_version_info:
            logger.warning(f"Not record version info for model_name: {model_name}")
            return []
        else:
            return self._model_name_to_version_info[model_name]

    def get_model_version_count(self, model_name: str) -> int:
        return len(self.get_model_versions(model_name))

    def list_cached_models(self):
        cached_models = {}
        ret = []
        for model_name, model_versions in self._model_name_to_version_info.items():
            for version_info in model_versions:
                if version_info["cache_status"]:
                    ret.append(version_info)
            cached_models[model_name] = ret
            ret = []
        return cached_models
