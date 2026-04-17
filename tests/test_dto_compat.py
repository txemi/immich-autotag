import datetime
import unittest
from typing import Any, cast
from types import SimpleNamespace
from uuid import UUID, uuid4

from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.album_user_response_dto import AlbumUserResponseDto
from immich_client.models.album_user_role import AlbumUserRole
from immich_client.models.user_avatar_color import UserAvatarColor
from immich_client.models.user_response_dto import UserResponseDto

from immich_autotag.albums.album.album_dto_state import AlbumDtoState, AlbumLoadSource
from immich_autotag.albums.album.album_user_wrapper import AlbumUserWrapper
from immich_autotag.users.user_response_wrapper import UserResponseWrapper


def _build_user_dto(*, user_id: str | UUID) -> UserResponseDto:
    return UserResponseDto(
        avatar_color=UserAvatarColor.PRIMARY,
        email="user@example.com",
        id=str(user_id),
        name="User Name",
        profile_changed_at=datetime.datetime.now(),
        profile_image_path="",
    )


def _build_album_dto(*, album_id: str, assets: list[object]) -> AlbumResponseDto:
    owner = _build_user_dto(user_id=str(uuid4()))
    return AlbumResponseDto(
        album_name="Album",
        album_thumbnail_asset_id=None,
        album_users=[],
        asset_count=len(assets),
        assets=cast(Any, assets),
        created_at=datetime.datetime.now(),
        description="",
        has_shared_link=False,
        id=album_id,
        is_activity_enabled=False,
        owner=owner,
        owner_id=str(uuid4()),
        shared=False,
        updated_at=datetime.datetime.now(),
    )


class _AlbumWithoutAssets(AlbumResponseDto):
    def __getattribute__(self, name: str):
        if name == "assets":
            raise AttributeError("assets not available in this DTO version")
        return super().__getattribute__(name)


class TestDtoCompatibility(unittest.TestCase):
    def test_user_response_wrapper_accepts_uuid_id(self) -> None:
        uid = uuid4()
        wrapper = UserResponseWrapper.from_user(_build_user_dto(user_id=uid))
        self.assertEqual(wrapper.get_uuid().to_uuid(), uid)

    def test_album_user_wrapper_accepts_uuid_id(self) -> None:
        uid = uuid4()
        album_user_dto = AlbumUserResponseDto(
            role=AlbumUserRole.EDITOR,
            user=_build_user_dto(user_id=uid),
        )
        wrapper = AlbumUserWrapper(album_user_dto)
        self.assertEqual(wrapper.get_uuid().to_uuid(), uid)

    def test_album_dto_state_handles_missing_assets_attribute(self) -> None:
        owner = _build_user_dto(user_id=str(uuid4()))
        album = _AlbumWithoutAssets(
            album_name="Album",
            album_thumbnail_asset_id=None,
            album_users=[],
            asset_count=0,
            assets=[],
            created_at=datetime.datetime.now(),
            description="",
            has_shared_link=False,
            id=str(uuid4()),
            is_activity_enabled=False,
            owner=owner,
            owner_id=str(uuid4()),
            shared=False,
            updated_at=datetime.datetime.now(),
        )
        state = AlbumDtoState.create(dto=album, load_source=AlbumLoadSource.DETAIL)
        self.assertEqual(state.get_asset_uuids(), set())

    def test_album_dto_state_reads_asset_ids_from_dict_and_object_assets(self) -> None:
        asset_id_1 = str(uuid4())
        asset_id_2 = str(uuid4())
        assets = [{"id": asset_id_1}, SimpleNamespace(id=asset_id_2)]
        album = _build_album_dto(album_id=str(uuid4()), assets=assets)
        state = AlbumDtoState.create(dto=album, load_source=AlbumLoadSource.DETAIL)
        self.assertEqual(
            {str(v) for v in state.get_asset_uuids()},
            {asset_id_1, asset_id_2},
        )


if __name__ == "__main__":
    unittest.main()
