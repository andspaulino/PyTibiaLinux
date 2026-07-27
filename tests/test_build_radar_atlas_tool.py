from pathlib import Path

import numpy as np
from PIL import Image

from tools import build_radar_atlas


def save_indexed_chunk(path: Path, value: int, color: tuple[int, int, int]):
    image = Image.fromarray(
        np.full((256, 256), value, dtype=np.uint8),
        mode="P",
    )
    palette = [0] * (256 * 3)
    palette[value * 3:value * 3 + 3] = list(color)
    image.putpalette(palette)
    image.save(path)


def test_parse_chunk_path_reads_kind_coordinates_and_floor(tmp_path):
    path = tmp_path / "Minimap_Color_32256_32000_7.png"

    chunk = build_radar_atlas.parseChunkPath(path)

    assert chunk["kind"] == "Color"
    assert chunk["x"] == 32256
    assert chunk["y"] == 32000
    assert chunk["z"] == 7


def test_build_atlas_preserves_color_and_waypoint_index(
    tmp_path,
    monkeypatch,
):
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"
    input_directory.mkdir()
    save_indexed_chunk(
        input_directory / "Minimap_Color_1000_2000_0.png",
        12,
        (0, 102, 0),
    )
    save_indexed_chunk(
        input_directory / "Minimap_WaypointCost_1000_2000_0.png",
        95,
        (95, 95, 95),
    )
    monkeypatch.setattr(build_radar_atlas, "ATLAS_ORIGIN_X", 1000)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_ORIGIN_Y", 2000)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_WIDTH", 256)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_HEIGHT", 256)
    monkeypatch.setattr(build_radar_atlas, "FLOORS", (0,))

    chunks, ignored = build_radar_atlas.discoverChunks(input_directory)
    report = build_radar_atlas.buildAtlases(chunks, output_directory)

    color = np.asarray(
        Image.open(output_directory / "images" / "floor-0.png").convert("RGBA")
    )
    waypoint = np.load(output_directory / "npys" / "floorsPathsSqms.npy")
    assert ignored == []
    assert tuple(color[0, 0]) == (0, 102, 0, 255)
    assert waypoint.shape == (1, 256, 256)
    assert int(waypoint[0, 0, 0]) == 95
    assert report["accepted_chunks"] == 2
    assert report["floors"][0]["missing_color"] == []
    assert report["floors"][0]["missing_waypoint"] == []


def test_waypoint_npy_uses_red_palette_channel_like_original_builder(
    tmp_path,
    monkeypatch,
):
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"
    input_directory.mkdir()
    save_indexed_chunk(
        input_directory / "Minimap_WaypointCost_1000_2000_0.png",
        254,
        (255, 0, 255),
    )
    monkeypatch.setattr(build_radar_atlas, "ATLAS_ORIGIN_X", 1000)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_ORIGIN_Y", 2000)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_WIDTH", 256)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_HEIGHT", 256)
    monkeypatch.setattr(build_radar_atlas, "FLOORS", (0,))

    chunks, _ = build_radar_atlas.discoverChunks(input_directory)
    report = build_radar_atlas.buildAtlases(chunks, output_directory)
    waypoint = np.load(output_directory / "npys" / "floorsPathsSqms.npy")

    assert int(waypoint[0, 0, 0]) == 255
    assert report["floors"][0]["waypoint_palette_indices"] == [254]
    assert report["floors"][0]["friction_values"] == [255]


def test_outside_chunk_is_reported_without_overwriting_atlas(
    tmp_path,
    monkeypatch,
):
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"
    input_directory.mkdir()
    path = input_directory / "Minimap_Color_2000_2000_0.png"
    save_indexed_chunk(path, 12, (0, 102, 0))
    monkeypatch.setattr(build_radar_atlas, "ATLAS_ORIGIN_X", 1000)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_ORIGIN_Y", 2000)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_WIDTH", 256)
    monkeypatch.setattr(build_radar_atlas, "ATLAS_HEIGHT", 256)
    monkeypatch.setattr(build_radar_atlas, "FLOORS", (0,))

    chunks, _ = build_radar_atlas.discoverChunks(input_directory)
    report = build_radar_atlas.buildAtlases(chunks, output_directory)

    waypoint_image = Image.open(
        output_directory / "images" / "paths" / "floor-0.png"
    ).convert("RGBA")
    waypoint = np.load(output_directory / "npys" / "floorsPathsSqms.npy")

    assert report["accepted_chunks"] == 0
    assert report["outside_atlas"][0]["file"] == path.name
    assert waypoint_image.getpixel((0, 0)) == (255, 0, 255, 255)
    assert int(waypoint[0, 0, 0]) == 255
