from io import BytesIO

import numpy as np
import pytest
import trimesh

from roadside_drive.world.exports import glb, reframe_legacy_glb
from roadside_drive.world.orientation import (
    GEOGRAPHIC_EXCHANGE,
    camera_right_m,
    local_to_ue_cm,
    start_yaw_deg,
    ue_bounds_cm,
)


def test_legacy_mirror_reproduces_and_geographic_exchange_places_north_left():
    assert camera_right_m((1, 0), (0, 8)) == 8
    assert local_to_ue_cm((100, 8, 0)) == (10_000, -800, 0)
    assert camera_right_m((1, 0), (0, -8)) == -8
    assert start_yaw_deg([(0, 0), (0, -1), (-30, -40)]) == pytest.approx(126.86989765)
    assert ue_bounds_cm(((0, 5, 0), (3, 9, 1)), GEOGRAPHIC_EXCHANGE) == (
        (0, -900, 0),
        (300, -500, 100),
    )


def test_new_and_reframed_meshes_have_signed_positions_and_keep_winding():
    triangle = [((0.0, 5.0, 0.0), (10.0, 5.0, 0.0), (1.0, 8.0, 0.0))]
    old = glb(triangle, "road")
    for data in (glb(triangle, "road", GEOGRAPHIC_EXCHANGE), reframe_legacy_glb(old)):
        mesh = trimesh.load(BytesIO(data), file_type="glb", force="mesh", process=False)
        assert np.allclose(mesh.bounds, ((0, 0, -8), (10, 0, -5)))
        assert np.allclose(mesh.face_normals, [(0, 1, 0)])
