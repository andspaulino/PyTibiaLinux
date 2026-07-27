from tools import capture_unknown_monsters


def test_upsert_creature_wiki_adds_exp_and_hp(tmp_path, monkeypatch):
    creatures_file = tmp_path / "creatures.py"
    creatures_file.write_text("creatures = {\n}\n", encoding="utf-8")
    monkeypatch.setattr(
        capture_unknown_monsters,
        "CREATURES_FILE",
        creatures_file,
    )
    monkeypatch.setattr(capture_unknown_monsters, "wikiCreatures", {})

    assert capture_unknown_monsters.upsertCreatureWiki(
        "Test Creature",
        exp=120,
        hp=450,
    )

    content = creatures_file.read_text(encoding="utf-8")
    assert "'Test Creature': {'exp': 120, 'hp': 450" in content
    assert "'gameWindowMisalignment': {'x': 0, 'y': 0}" in content


def test_upsert_creature_wiki_updates_none_without_changing_misalignment(
    tmp_path,
    monkeypatch,
):
    creatures_file = tmp_path / "creatures.py"
    creatures_file.write_text(
        "creatures = {\n"
        "    'Existing': {'exp': None, 'hp': None, "
        "'gameWindowMisalignment': {'x': 16, 'y': 1}},\n"
        "}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        capture_unknown_monsters,
        "CREATURES_FILE",
        creatures_file,
    )
    monkeypatch.setattr(
        capture_unknown_monsters,
        "wikiCreatures",
        {
            "Existing": {
                "exp": None,
                "hp": None,
                "gameWindowMisalignment": {"x": 16, "y": 1},
            }
        },
    )

    assert capture_unknown_monsters.upsertCreatureWiki(
        "Existing",
        exp=900,
        hp=2500,
    )

    content = creatures_file.read_text(encoding="utf-8")
    assert "'Existing': {'exp': 900, 'hp': 2500" in content
    assert "'gameWindowMisalignment': {'x': 16, 'y': 1}" in content


def test_upsert_preserves_existing_value_when_optional_input_is_empty(
    tmp_path,
    monkeypatch,
):
    creatures_file = tmp_path / "creatures.py"
    creatures_file.write_text(
        "creatures = {\n"
        "    'Existing': {'exp': 50, 'hp': 100, "
        "'gameWindowMisalignment': {'x': 0, 'y': 0}},\n"
        "}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        capture_unknown_monsters,
        "CREATURES_FILE",
        creatures_file,
    )
    monkeypatch.setattr(
        capture_unknown_monsters,
        "wikiCreatures",
        {
            "Existing": {
                "exp": 50,
                "hp": 100,
                "gameWindowMisalignment": {"x": 0, "y": 0},
            }
        },
    )

    assert capture_unknown_monsters.upsertCreatureWiki("Existing")

    content = creatures_file.read_text(encoding="utf-8")
    assert "'Existing': {'exp': 50, 'hp': 100" in content
