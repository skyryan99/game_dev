# Conquest

My attempt at recreating **Conquest**, the two-player turn-based tactics minigame from RuneScape
(see the [wiki page](https://runescape.wiki/w/Conquest)). Full disclaimer: I had never played it.

## Setup (Windows)

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

## Tests

```
python -m unittest discover -s tests -v
```

No pygame is needed for the tests: the rules engine does not import it.

## How the code is organised

| File | What it does |
| --- | --- |
| `data.py` | Troop and command definitions (plain dicts, no pygame). Add a buff command by adding an entry. |
| `engine.py` | **All the rules**: `Loadout`, `Game`, movement, combat, commands, turns, win check. No pygame. |
| `main.py` | The window and event loop (`App`): START -> LOADOUT -> GAME. |
| `gamemenu.py`, `screenconfig.py` | The Esc menu, and the window/resolution settings + canvas-to-window maths (no pygame, tested). |
| `menus.py` | Start screen and the troop / command pickers. |
| `hud.py`, `render.py`, `gameboard.py` | Drawing: side panels, units + highlights, board and zoom maths. |
| `textures.py` | Procedural wood-grain floor tiles and rock obstacles (no image files needed). |
| `actions.py` | `Controller`: turns clicks into engine actions. |
| `assets.py` | Loads and caches images and fonts (paths are relative to the file, not the working directory). |
| `protocol.py`, `server.py`, `network.py` | Online play: JSON messages, an authoritative server, a non-blocking client. |

Everything is drawn on a fixed 1920x1080 canvas that is scaled to fit the window (black bars if it is not 16:9),
so the board, menus and HUD follow any resolution without extra layout code.

The UI never edits game state directly. It sends an action to `Game.apply_action(player, {...})`,
the same call the server makes for each client message, so illegal moves are rejected in one place.

## Controls

* Left click a troop to select it, a blue tile to move, a red-highlighted enemy to attack.
* The side panel has a **Phases** section (one button per phase, End Turn, Resign) and a **Commands** section.
  The current phase's button circles with a golden glow; click it to end that phase. Phases also end by
  themselves when nothing is left to do.
* Each turn has a time limit, picked in the loadout menu (10s / 30s / 60s / 180s / unlimited). The countdown is at
  the top right of the side panel and the turn ends by itself when it reaches zero. It pauses while Esc's menu is open.
* The panel's bottom box is a fixed-size log of the last three turns.
* Side panel: End Phase, End Turn, Resign, and your commands (click a command, then click its target).
* Right click cancels a pending command. Mouse wheel zooms, middle-drag pans.
* **Esc** cancels a pending command in a game; with nothing to cancel (and on every other screen) it opens the menu:
  a Fullscreen checkbox and a window resolution picker. Esc again closes it.
  Settings are remembered in `settings.json` (git-ignored). Fullscreen uses your desktop resolution.
* Right now both players share one screen and Player 2 gets a copy of Player 1's squad.

## Rules I had to decide myself

The wiki does not say, so these are assumptions (all in one place at the top of `engine.py`):

* Movement is 4-directional and cannot pass through troops or obstacles; range is Manhattan distance.
* A defender hits back only if the attacker is inside the defender's own range.
* Battle Cry and Stoicism grant *temporary* health: a separate pool that damage (including Bombard) drains
  first, stripped at the start of your next turn. It never heals real health, so a buff can't leave a troop
  healthier than it was. Regenerate restores real health only.
* Bombard is not "damage", so Shield Wall does not reduce it.
* Commands cost no squad gold in the loadout (only troops do); they cost command points in the game.
  The menus label these "Gold cost" and "Command point cost".
* Obstacles live in rows 5-14 (0-indexed) so each army has five clear rows.
* A phase ends automatically when it has nothing left in it: no steps left (or nowhere to step), no enemy in
  range, or no troop able to act. The movement phase waits while a Charge could still give a troop more room to
  move. When you reach the rally phase with no command you could use (none ready, too few command points, no sensible
  target), the rally phase and your turn end automatically. Commands work in every phase, so skipping ahead never
  costs you one.

## Server (work in progress)

```
python server.py                      # terminal 1 (listens on port 5555)
python server.py --turn-limit 30      # optional: 10, 30, 60, 180 or inf seconds per turn (default 60)
set CONQUEST_HOST=192.168.1.100       # on the other machine, point the client at the server
```

`network.Network` and `server.GameServer` work and are tested, but `main.py` is not wired to them yet.

## TODO

* Formation editor (currently troops are auto-placed in your first three rows).
* Wire `main.py` to the server for real two-machine play; add a lobby / waiting screen.
* Turn timer (30 s to 3 min per turn).
* Obstacle ideas: never side by side, symmetric layouts.
* Distinct icons per command; ranking / commendations; AI opponent.
