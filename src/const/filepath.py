import dataclasses
import pathlib
import uuid

import src.util.time_util


@dataclasses.dataclass(frozen=True)
class FileUploadTo:
    base_path: pathlib.Path

    @staticmethod
    def assure_dir(target_path: pathlib.Path) -> pathlib.Path:
        target_path.mkdir(parents=True, exist_ok=True)
        return target_path

    @property
    def current_timestamp(self) -> int:
        return int(src.util.time_util.get_utcnow().timestamp())

    def user_file(self, user_uuid: uuid.UUID, file_name: str) -> pathlib.Path:
        return self.assure_dir(self.base_path / "user" / str(user_uuid)) / file_name
