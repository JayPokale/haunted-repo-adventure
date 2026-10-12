import subprocess
import sys

import adventure


def test_every_choice_points_to_an_existing_scene():
    for scene in adventure.STORY.values():
        for _label, destination in scene.get("choices", []):
            assert destination in adventure.STORY


def test_every_non_ending_scene_has_a_choice():
    for scene in adventure.STORY.values():
        if "ending" not in scene:
            assert scene.get("choices")


def test_every_scene_is_reachable_from_start():
    reached = set()
    pending = [adventure.START_SCENE]
    while pending:
        scene_id = pending.pop()
        if scene_id in reached:
            continue
        reached.add(scene_id)
        pending.extend(
            destination
            for _label, destination in adventure.STORY[scene_id].get("choices", [])
        )
    assert reached == set(adventure.STORY)


def test_good_and_bad_endings_exist():
    endings = [
        scene["ending"] for scene in adventure.STORY.values() if "ending" in scene
    ]
    assert "good" in endings
    assert "bad" in endings


def test_path_mode_reaches_an_ending():
    result = subprocess.run(
        [sys.executable, "adventure.py", "--path", "1,2"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "ending reached:" in result.stdout.lower()
