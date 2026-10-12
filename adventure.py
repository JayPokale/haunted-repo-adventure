"""The Haunted Repo: a small data-driven command-line adventure."""

from __future__ import annotations

import argparse
import random
from typing import Callable


START_SCENE = "gate"

# Story content is deliberately kept separate from the game engine below.
# Each choice is (display text, destination scene id).
STORY = {
    "gate": {
        "text": (
            "Hacktoberfest night has settled over the old open-source repository. "
            "You push open the gate and see three paths in the moonlight."
        ),
        "choices": [
            ("Follow the green contribution guide", "guide"),
            ("Investigate the flickering CI sign", "ci"),
            ("Knock on the maintainer's office door", "office"),
        ],
    },
    "guide": {
        "text": (
            "The contribution guide glows green. A ghostly merge conflict whispers "
            "from the README: 'Choose carefully, newcomer.'"
        ),
        "choices": [
            ("Resolve the conflict line by line", "workbench"),
            ("Delete the conflicting branch", "conflict"),
        ],
    },
    "ci": {
        "text": (
            "The CI pipeline is a crooked conveyor belt of red lights. A cursed "
            "build artifact rattles inside its last job."
        ),
        "choices": [
            ("Read the failing test logs", "logs"),
            ("Rerun everything and hope", "pipeline_bad"),
        ],
    },
    "office": {
        "text": (
            "A friendly maintainer ghost rises from a desk piled with issue labels. "
            "They offer you a spectral cup of cocoa."
        ),
        "choices": [
            ("Ask for a review of your first patch", "review"),
            ("Thank them and explore the release room", "release"),
        ],
    },
    "workbench": {
        "text": (
            "You compare both sides of the conflict instead of guessing. The "
            "ghostly brackets settle into place, revealing a hidden test."
        ),
        "choices": [
            ("Run the hidden test", "review"),
            ("Commit without running it", "conflict"),
        ],
    },
    "conflict": {
        "text": (
            "The deleted branch screams back into existence. Its conflict markers "
            "wrap around your terminal like cobwebs."
        ),
        "ending": "bad",
    },
    "logs": {
        "text": (
            "The logs reveal a missing fixture, not a haunted dependency. You add "
            "the fixture and the red lights turn amber."
        ),
        "choices": [
            ("Fix the fixture and run CI again", "review"),
            ("Ignore the logs and force-push", "pipeline_bad"),
        ],
    },
    "pipeline_bad": {
        "text": (
            "The cursed pipeline accepts the force-push. Every test becomes a "
            "ghostly ❌, and the repository locks its doors until dawn."
        ),
        "ending": "bad",
    },
    "review": {
        "text": (
            "The maintainer ghost reviews your patch. One small suggestion later, "
            "your checks pass and the merge button shines."
        ),
        "choices": [
            ("Apply the suggestion and merge", "celebration"),
            ("Ignore the suggestion and merge anyway", "stubborn"),
        ],
    },
    "release": {
        "text": (
            "The release room is filled with floating version tags. One tag is "
            "marked 'needs tests' and another is marked 'ready to learn.'"
        ),
        "choices": [
            ("Pick the ready-to-learn tag and add tests", "celebration"),
            ("Publish the untested tag", "stubborn"),
        ],
    },
    "stubborn": {
        "text": (
            "Your patch merges, but the repository's tests catch the shortcut. "
            "The ghosts politely ask you to return with a fix."
        ),
        "ending": "bad",
    },
    "celebration": {
        "text": (
            "The merge lands! The friendly maintainer ghost rings a bell, and the "
            "repository welcomes you as a real contributor. Happy Hacktoberfest!"
        ),
        "ending": "good",
    },
}


def show_scene(scene_id: str, output: Callable[[str], None] = print) -> None:
    """Print one scene and its numbered choices."""
    scene = STORY[scene_id]
    output(f"\n{scene['text']}")
    for number, (choice, _destination) in enumerate(scene.get("choices", []), 1):
        output(f"  {number}. {choice}")


def choose_next(scene_id: str, choice_number: int) -> str:
    """Return the destination selected by a one-based choice number."""
    choices = STORY[scene_id].get("choices", [])
    if not 1 <= choice_number <= len(choices):
        raise ValueError("choice number is out of range")
    return choices[choice_number - 1][1]


def play_path(
    path: list[int],
    *,
    output: Callable[[str], None] = print,
) -> str:
    """Play choices from *path* and return the ending scene id.

    Raises ValueError when the path ends before an ending or contains an invalid
    choice. This makes scripted play failures clear to callers and tests.
    """
    scene_id = START_SCENE
    for choice_number in path:
        show_scene(scene_id, output)
        if "ending" in STORY[scene_id]:
            return scene_id
        scene_id = choose_next(scene_id, choice_number)
    show_scene(scene_id, output)
    if "ending" not in STORY[scene_id]:
        raise ValueError("path ended before reaching an ending")
    return scene_id


def play_interactive(
    *,
    input_fn: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    rng: random.Random | None = None,
) -> str | None:
    """Run one interactive game, or return None when the player quits."""
    scene_id = START_SCENE
    while True:
        show_scene(scene_id, output)
        scene = STORY[scene_id]
        if "ending" in scene:
            return scene_id
        answer = input_fn("\nChoose a number (or q to quit): ").strip().lower()
        if answer == "q":
            output("You leave the haunted repository before midnight.")
            return None
        try:
            choice_number = int(answer)
            scene_id = choose_next(scene_id, choice_number)
        except (TypeError, ValueError):
            output("Please enter one of the numbered choices, or q to quit.")
            continue


def play_seeded(seed: int, output: Callable[[str], None] = print) -> str:
    """Play a deterministic random route selected by *seed*."""
    rng = random.Random(seed)
    scene_id = START_SCENE
    while "ending" not in STORY[scene_id]:
        show_scene(scene_id, output)
        choices = STORY[scene_id]["choices"]
        scene_id = choices[rng.randrange(len(choices))][1]
    show_scene(scene_id, output)
    return scene_id


def parse_path(value: str) -> list[int]:
    """Parse a comma-separated sequence of positive choice numbers."""
    if not value.strip():
        raise argparse.ArgumentTypeError("path must contain at least one choice")
    try:
        path = [int(part.strip()) for part in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("path must contain only numbers") from exc
    if any(number < 1 for number in path):
        raise argparse.ArgumentTypeError("path choices must be positive numbers")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Play The Haunted Repo.")
    parser.add_argument("--seed", type=int, help="play a deterministic random route")
    parser.add_argument(
        "--path",
        type=parse_path,
        help="play a comma-separated route non-interactively, e.g. 1,1,1",
    )
    args = parser.parse_args()
    if args.seed is not None and args.path is not None:
        parser.error("--seed and --path cannot be used together")

    if args.path is not None:
        try:
            ending = play_path(args.path)
        except ValueError as exc:
            parser.error(str(exc))
        print(f"\nEnding reached: {STORY[ending]['ending']}.")
        return 0
    if args.seed is not None:
        ending = play_seeded(args.seed)
        print(f"\nEnding reached: {STORY[ending]['ending']}.")
        return 0

    while True:
        ending = play_interactive()
        if ending is None:
            return 0
        answer = input("\nPlay again? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
