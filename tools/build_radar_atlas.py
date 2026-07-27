#!/usr/bin/env python3
"""Monta atlas do Radar a partir dos chunks PNG do minimapa do Tibia.

A pasta de entrada é tratada como somente leitura. A saída é sempre gravada em
staging e nunca substitui os assets oficiais automaticamente.

Execução a partir da raiz do repositório:
  poetry -C PyTibia-Linux run python tools/build_radar_atlas.py \
    --input "/home/anders/.local/share/CipSoft GmbH/Tibia/packages/Tibia/minimap"
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


CHUNK_SIZE = 256
ATLAS_ORIGIN_X = 31744
ATLAS_ORIGIN_Y = 30976
ATLAS_WIDTH = 2560
ATLAS_HEIGHT = 2048
FLOORS = tuple(range(16))
DEFAULT_INPUT = Path(
    "/home/anders/.local/share/CipSoft GmbH/Tibia/packages/Tibia/minimap"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "radar"
CHUNK_PATTERN = re.compile(
    r"^Minimap_(Color|WaypointCost)_(\d+)_(\d+)_(\d+)\.png$"
)


def parseChunkPath(path: Path):
    match = CHUNK_PATTERN.match(path.name)
    if match is None:
        return None
    kind, x, y, z = match.groups()
    return {
        "kind": kind,
        "x": int(x),
        "y": int(y),
        "z": int(z),
        "path": path,
    }


def getChunkAtlasPosition(chunk):
    return chunk["x"] - ATLAS_ORIGIN_X, chunk["y"] - ATLAS_ORIGIN_Y


def chunkIsInsideAtlas(chunk):
    x, y = getChunkAtlasPosition(chunk)
    return (
        chunk["z"] in FLOORS
        and x >= 0
        and y >= 0
        and x + CHUNK_SIZE <= ATLAS_WIDTH
        and y + CHUNK_SIZE <= ATLAS_HEIGHT
        and x % CHUNK_SIZE == 0
        and y % CHUNK_SIZE == 0
    )


def discoverChunks(inputDirectory: Path):
    chunks = []
    ignored = []
    for path in sorted(inputDirectory.glob("*.png")):
        parsed = parseChunkPath(path)
        if parsed is None:
            ignored.append(path.name)
        else:
            chunks.append(parsed)
    return chunks, ignored


def validateChunkImage(chunk):
    with Image.open(chunk["path"]) as image:
        if image.size != (CHUNK_SIZE, CHUNK_SIZE):
            raise ValueError(
                f"Chunk com dimensão inválida: {chunk['path']} ({image.size})"
            )
        if image.mode != "P":
            raise ValueError(
                f"Chunk deve ser PNG indexado (modo P): {chunk['path']} ({image.mode})"
            )


def buildAtlases(chunks, outputDirectory: Path):
    imagesDirectory = outputDirectory / "images"
    pathsDirectory = imagesDirectory / "paths"
    npysDirectory = outputDirectory / "npys"
    imagesDirectory.mkdir(parents=True, exist_ok=True)
    pathsDirectory.mkdir(parents=True, exist_ok=True)
    npysDirectory.mkdir(parents=True, exist_ok=True)

    byKey = {}
    duplicates = []
    outside = []
    for chunk in chunks:
        validateChunkImage(chunk)
        key = (chunk["kind"], chunk["x"], chunk["y"], chunk["z"])
        if key in byKey:
            duplicates.append({
                "key": list(key),
                "first": str(byKey[key]["path"]),
                "second": str(chunk["path"]),
            })
            continue
        if not chunkIsInsideAtlas(chunk):
            outside.append({
                "file": chunk["path"].name,
                "kind": chunk["kind"],
                "x": chunk["x"],
                "y": chunk["y"],
                "z": chunk["z"],
            })
            continue
        byKey[key] = chunk

    grouped = defaultdict(list)
    for chunk in byKey.values():
        grouped[(chunk["kind"], chunk["z"])].append(chunk)

    waypointSqms = np.full(
        (len(FLOORS), ATLAS_HEIGHT, ATLAS_WIDTH),
        255,
        dtype=np.uint8,
    )
    floorReports = []
    expectedPerFloor = (ATLAS_WIDTH // CHUNK_SIZE) * (ATLAS_HEIGHT // CHUNK_SIZE)

    for floor in FLOORS:
        colorAtlas = Image.new(
            "RGBA",
            (ATLAS_WIDTH, ATLAS_HEIGHT),
            (0, 0, 0, 255),  # type: ignore[arg-type] Pillow stub omits RGBA tuples
        )
        # Fundo amarelo usado inicialmente na adaptação Linux:
        # waypointAtlas = Image.new(
        #     "RGBA",
        #     (ATLAS_WIDTH, ATLAS_HEIGHT),
        #     (255, 255, 0, 255),
        # )
        # Magenta preserva o padrão visual original para chunks sem cobertura.
        waypointAtlas = Image.new(
            "RGBA",
            (ATLAS_WIDTH, ATLAS_HEIGHT),
            (255, 0, 255, 255),  # type: ignore[arg-type] Pillow stub omits RGBA tuples
        )
        covered = {"Color": set(), "WaypointCost": set()}
        waypointValues = set()
        frictionValues = set()

        for kind in ("Color", "WaypointCost"):
            for chunk in grouped[(kind, floor)]:
                atlasX, atlasY = getChunkAtlasPosition(chunk)
                gridPosition = (atlasX // CHUNK_SIZE, atlasY // CHUNK_SIZE)
                covered[kind].add(gridPosition)
                with Image.open(chunk["path"]) as image:
                    if kind == "Color":
                        colorAtlas.paste(image.convert("RGBA"), (atlasX, atlasY))
                    else:
                        indexed = np.asarray(image, dtype=np.uint8)
                        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
                        friction = rgba[:, :, 0]
                        waypointSqms[
                            floor,
                            atlasY:atlasY + CHUNK_SIZE,
                            atlasX:atlasX + CHUNK_SIZE,
                        ] = friction
                        waypointValues.update(int(value) for value in np.unique(indexed))
                        frictionValues.update(int(value) for value in np.unique(friction))
                        waypointAtlas.paste(Image.fromarray(rgba, mode="RGBA"), (atlasX, atlasY))

        colorAtlas.save(imagesDirectory / f"floor-{floor}.png")
        waypointAtlas.save(pathsDirectory / f"floor-{floor}.png")

        expectedPositions = {
            (x, y)
            for y in range(ATLAS_HEIGHT // CHUNK_SIZE)
            for x in range(ATLAS_WIDTH // CHUNK_SIZE)
        }
        floorReports.append({
            "floor": floor,
            "expected_chunks": expectedPerFloor,
            "color_chunks": len(covered["Color"]),
            "waypoint_chunks": len(covered["WaypointCost"]),
            "missing_color": sorted(
                [list(position) for position in expectedPositions - covered["Color"]]
            ),
            "missing_waypoint": sorted(
                [list(position) for position in expectedPositions - covered["WaypointCost"]]
            ),
            "waypoint_palette_indices": sorted(waypointValues),
            "friction_values": sorted(frictionValues),
        })

    np.save(npysDirectory / "floorsPathsSqms.npy", waypointSqms)
    return {
        "format_version": 1,
        "input_chunk_size": CHUNK_SIZE,
        "atlas": {
            "origin_x": ATLAS_ORIGIN_X,
            "origin_y": ATLAS_ORIGIN_Y,
            "width": ATLAS_WIDTH,
            "height": ATLAS_HEIGHT,
            "floors": list(FLOORS),
        },
        "accepted_chunks": len(byKey),
        "duplicates": duplicates,
        "outside_atlas": outside,
        "floors": floorReports,
        "npy": {
            "path": "npys/floorsPathsSqms.npy",
            "shape": list(waypointSqms.shape),
            "dtype": str(waypointSqms.dtype),
            "values": sorted(int(value) for value in np.unique(waypointSqms)),
        },
    }


def parseArguments():
    parser = argparse.ArgumentParser(
        description="Monta atlas do Radar a partir dos chunks PNG do minimapa."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Pasta somente leitura contendo Minimap_Color_* e Minimap_WaypointCost_*.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Pasta de staging; nunca substitui assets oficiais automaticamente.",
    )
    return parser.parse_args()


def main():
    arguments = parseArguments()
    inputDirectory = arguments.input.expanduser().resolve()
    outputDirectory = arguments.output.expanduser().resolve()
    if not inputDirectory.is_dir():
        raise SystemExit(f"Pasta de entrada não encontrada: {inputDirectory}")

    chunks, ignored = discoverChunks(inputDirectory)
    if not chunks:
        raise SystemExit(f"Nenhum chunk compatível encontrado em: {inputDirectory}")

    report = buildAtlases(chunks, outputDirectory)
    report["input"] = str(inputDirectory)
    report["output"] = str(outputDirectory)
    report["ignored_pngs"] = ignored
    reportPath = outputDirectory / "report.json"
    reportPath.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Chunks aceitos: {report['accepted_chunks']}")
    print(f"Fora do atlas: {len(report['outside_atlas'])}")
    print(f"Duplicados: {len(report['duplicates'])}")
    for floor in report["floors"]:
        print(
            f"Floor {floor['floor']:2d}: "
            f"color={floor['color_chunks']:2d}/80 "
            f"waypoint={floor['waypoint_chunks']:2d}/80"
        )
    print(f"Staging: {outputDirectory}")
    print(f"Relatório: {reportPath}")
    print("Nenhum asset oficial foi substituído.")


if __name__ == "__main__":
    main()
