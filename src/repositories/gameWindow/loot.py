"""Detecção temporal de Loot Highlighting na grade da Game Window.

O módulo não captura screenshots nem envia input. Ele recebe uma sequência
estável de frames grayscale e classifica movimento por SQM da grade 15x11.
Os limites atuais são conservadores e permanecem provisórios até ampliar a
regressão com oclusões, bordas, outros pisos e versões do cliente.
"""

import cv2
import numpy as np


LOOT_GRID_COLUMNS = 15
LOOT_GRID_ROWS = 11
LOOT_HIGHLIGHT_MOTION_RANGE_MIN = 12
LOOT_HIGHLIGHT_CANDIDATE_PIXELS_MIN = 800
LOOT_HIGHLIGHT_GEOMETRY_PIXELS_MIN = 600
LOOT_HIGHLIGHT_GEOMETRY_SIZE_MIN = 48
LOOT_HIGHLIGHT_GEOMETRY_COMPONENT_MIN = 600
LOOT_HIGHLIGHT_AMBIENT_PIXELS_MIN = 200
LOOT_HIGHLIGHT_MAX_GLOBAL_MOTION_RATIO = 0.10
LOOT_HIGHLIGHT_TEMPORAL_FRAMES_MIN = 6
LOOT_HIGHLIGHT_MEAN_MOTION_RANGE_MIN = 75
LOOT_HIGHLIGHT_ADJACENT_MOTION_MEDIAN_MAX = 96


def getLootHighlightMotionMask(
    frames,
    motionRangeMin=LOOT_HIGHLIGHT_MOTION_RANGE_MIN,
):
    frameStack = np.asarray(frames)
    if frameStack.ndim != 3:
        raise ValueError("frames deve possuir shape (quantidade, altura, largura)")
    if frameStack.shape[0] < 2:
        raise ValueError("ao menos dois frames são necessários")
    if frameStack.shape[1] == 0 or frameStack.shape[2] == 0:
        raise ValueError("frames não podem possuir dimensões espaciais vazias")

    signedFrames = frameStack.astype(np.int16, copy=False)
    motionMagnitude = np.max(signedFrames, axis=0) - np.min(signedFrames, axis=0)
    motionMask = motionMagnitude >= motionRangeMin
    return motionMask, motionMagnitude.astype(np.uint8)


def getLootHighlightMotionGeometry(motionMask):
    motionPixels = int(np.count_nonzero(motionMask))
    if motionPixels == 0:
        return {
            "motionBounds": None,
            "motionWidth": 0,
            "motionHeight": 0,
            "largestComponent": 0,
        }

    rows, columns = np.where(motionMask)
    x0 = int(np.min(columns))
    y0 = int(np.min(rows))
    x1 = int(np.max(columns)) + 1
    y1 = int(np.max(rows)) + 1
    componentCount, _, componentStats, _ = cv2.connectedComponentsWithStats(
        motionMask.astype(np.uint8),
        connectivity=8,
    )
    largestComponent = (
        int(np.max(componentStats[1:, cv2.CC_STAT_AREA]))
        if componentCount > 1
        else 0
    )
    return {
        "motionBounds": (x0, y0, x1, y1),
        "motionWidth": x1 - x0,
        "motionHeight": y1 - y0,
        "largestComponent": largestComponent,
    }


def classifyLootHighlightSlots(
    frames,
    motionRangeMin=LOOT_HIGHLIGHT_MOTION_RANGE_MIN,
    candidatePixelsMin=LOOT_HIGHLIGHT_CANDIDATE_PIXELS_MIN,
    ambientPixelsMin=LOOT_HIGHLIGHT_AMBIENT_PIXELS_MIN,
    maxGlobalMotionRatio=LOOT_HIGHLIGHT_MAX_GLOBAL_MOTION_RATIO,
    eligibleSlots=None,
):
    motionMask, motionMagnitude = getLootHighlightMotionMask(
        frames,
        motionRangeMin,
    )
    frameStack = np.asarray(frames)
    signedFrames = frameStack.astype(np.int16, copy=False)
    adjacentMotionMasks = (
        np.abs(np.diff(signedFrames, axis=0)) >= motionRangeMin
    )
    hasEnoughTemporalFrames = (
        frameStack.shape[0] >= LOOT_HIGHLIGHT_TEMPORAL_FRAMES_MIN
    )
    globalMotionRatio = float(np.count_nonzero(motionMask)) / motionMask.size
    result = {
        "accepted": globalMotionRatio <= maxGlobalMotionRatio,
        "failureReason": None,
        "globalMotionRatio": globalMotionRatio,
        "motionMask": motionMask,
        "motionMagnitude": motionMagnitude,
        "candidates": [],
        "ambient": [],
    }
    if not result["accepted"]:
        result["failureReason"] = "global-motion"
        return result

    height, width = motionMask.shape
    xEdges = np.rint(np.linspace(0, width, LOOT_GRID_COLUMNS + 1)).astype(int)
    yEdges = np.rint(np.linspace(0, height, LOOT_GRID_ROWS + 1)).astype(int)
    eligibleSlotsSet = (
        None
        if eligibleSlots is None
        else {tuple(slot) for slot in eligibleSlots}
    )
    for row in range(LOOT_GRID_ROWS):
        for column in range(LOOT_GRID_COLUMNS):
            if eligibleSlotsSet is not None and (column, row) not in eligibleSlotsSet:
                continue
            x0, x1 = xEdges[column], xEdges[column + 1]
            y0, y1 = yEdges[row], yEdges[row + 1]
            motionPixels = int(np.count_nonzero(motionMask[y0:y1, x0:x1]))
            slotMotionMask = motionMask[y0:y1, x0:x1]
            slotMotionMagnitude = motionMagnitude[y0:y1, x0:x1]
            meanMotionRange = (
                float(np.mean(slotMotionMagnitude[slotMotionMask]))
                if motionPixels > 0
                else 0.0
            )
            adjacentMotionPixels = np.count_nonzero(
                adjacentMotionMasks[:, y0:y1, x0:x1],
                axis=(1, 2),
            )
            adjacentMotionMedian = (
                float(np.median(adjacentMotionPixels))
                if adjacentMotionPixels.size > 0
                else 0.0
            )
            temporalSignatureAccepted = (
                not hasEnoughTemporalFrames
                or (
                    meanMotionRange
                    >= LOOT_HIGHLIGHT_MEAN_MOTION_RANGE_MIN
                    and adjacentMotionMedian
                    <= LOOT_HIGHLIGHT_ADJACENT_MOTION_MEDIAN_MAX
                )
            )
            geometry = getLootHighlightMotionGeometry(slotMotionMask)
            slotResult = {
                "slot": (column, row),
                "motionPixels": motionPixels,
                "bounds": (int(x0), int(y0), int(x1), int(y1)),
                "meanMotionRange": meanMotionRange,
                "adjacentMotionMedian": adjacentMotionMedian,
                "temporalSignatureAvailable": hasEnoughTemporalFrames,
                "temporalSignatureAccepted": temporalSignatureAccepted,
                **geometry,
            }
            isMagnitudeCandidate = motionPixels >= candidatePixelsMin
            isGeometryCandidate = (
                motionPixels >= LOOT_HIGHLIGHT_GEOMETRY_PIXELS_MIN
                and geometry["motionWidth"] >= LOOT_HIGHLIGHT_GEOMETRY_SIZE_MIN
                and geometry["motionHeight"] >= LOOT_HIGHLIGHT_GEOMETRY_SIZE_MIN
                and geometry["largestComponent"]
                >= LOOT_HIGHLIGHT_GEOMETRY_COMPONENT_MIN
            )
            # Código anterior da adaptação Linux:
            # if isMagnitudeCandidate or isGeometryCandidate:
            #     slotResult["method"] = (
            #         "magnitude" if isMagnitudeCandidate else "geometry"
            #     )
            #     result["candidates"].append(slotResult)
            # elif motionPixels >= ambientPixelsMin:
            #     slotResult["method"] = "ambient"
            #     result["ambient"].append(slotResult)
            if (
                temporalSignatureAccepted
                and (isMagnitudeCandidate or isGeometryCandidate)
            ):
                slotResult["method"] = (
                    "magnitude" if isMagnitudeCandidate else "geometry"
                )
                result["candidates"].append(slotResult)
            elif motionPixels >= ambientPixelsMin:
                slotResult["method"] = "ambient"
                slotResult["rejectionReason"] = (
                    "temporal-signature"
                    if not temporalSignatureAccepted
                    else None
                )
                result["ambient"].append(slotResult)

    result["candidates"].sort(
        key=lambda item: item["motionPixels"],
        reverse=True,
    )
    result["ambient"].sort(
        key=lambda item: item["motionPixels"],
        reverse=True,
    )
    return result
