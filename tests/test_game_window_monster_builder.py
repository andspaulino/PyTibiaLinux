import cv2
import numpy as np

from builders.repositories.gameWindow.buildMonsters import (
    MONSTERS_DIR,
    buildMonsterImage,
)


def test_build_single_game_window_template_matches_existing_asset(tmp_path):
    generated_path = buildMonsterImage("Bug", outputDirectory=tmp_path)
    generated = cv2.imread(str(generated_path), cv2.IMREAD_GRAYSCALE)
    existing = cv2.imread(str(MONSTERS_DIR / "Bug.png"), cv2.IMREAD_GRAYSCALE)

    assert generated.shape[0] == 11
    assert set(np.unique(generated)) == {0, 255}
    assert np.array_equal(generated, existing)


def test_build_single_game_window_template_uses_white_background(tmp_path):
    generated_path = buildMonsterImage(
        "Muglex Clan Footman",
        outputDirectory=tmp_path,
    )
    generated = cv2.imread(str(generated_path), cv2.IMREAD_GRAYSCALE)

    assert np.count_nonzero(generated == 255) > 0
    assert np.count_nonzero(generated == 0) > 0
