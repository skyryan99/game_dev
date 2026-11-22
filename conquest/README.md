# Conquest

My attempt at recreating **Conquest**, the two-player turn-based tactics minigame from RuneScape
(see the [wiki page](https://runescape.wiki/w/Conquest)). Full disclaimer: I have never played it before.

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

## How the code is organized

| File | What it does |
| --- | --- |
| `data.py` | Troop and command definitions (stored as dicts). Add a buff command by adding an entry. |
| `engine.py` | **All the rules**: `Loadout`, `Game`, movement, combat, commands, turns, win check. |
| `main.py` | The window and event loop (`App`): START -> LOADOUT -> GAME. |
| `menus.py` | Start screen and the troop / command pickers. |
| `hud.py`, `render.py`, `gameboard.py` | Drawing: side panels, units + highlights, board and zoom maths. |
| `actions.py` | `Controller`: converts clicks into engine actions. |
| `assets.py` | Loads and caches images and fonts (paths are relative to the file, not the working directory). |
| `protocol.py`, `server.py`, `network.py` | Online play: JSON messages, server, and non-blocking client. |

The UI doesn't edit game state directly, sends an action to `Game.apply_action(player, {...})` to validate it

## Controls

* Left click a troop to select it, a blue tile to move, a red-highlighted enemy to attack.
* Side panel: End Phase, End Turn, Resign, and your commands (click a command, then click its target).
* Right click / Esc cancels a pending command. Mouse wheel zooms, middle-drag pans.
* For the time being, both players share one screen (hot seat) and the squad is replicated for both players.

## Some assumptions on game rules

* Movement is 4-directional and cannot pass through other troops; range is Manhattan distance.
* A defender hits back only if the attacker is inside the defender's own range.
* Buff health (Battle Cry, Stoicism) is taken away when the buff expires (this is currently bugged, so the temp health counts as a regen).
* Bombard is not "damage", so Shield Wall does not reduce it - not that it would matter anyway

## Server (work in progress)

```
python server.py                      # terminal 1 (listens on port 5555)
set CONQUEST_HOST=192.168.1.100       # on the other machine, point the client at the server
```

`network.Network` and `server.GameServer` work and are tested, but `main.py` is not wired to them yet.

## TODO / Future Improvements

* Formation editor (currently troops are auto-placed in your first three rows).
* Wire `main.py` to the server for real two-player games; add a lobby / waiting screen.
* Turn timer (30 s to 3 min per turn).
* Obstacle improvements: never side by side, symmetric layouts.
* Add real assets for the units and obstacles. Add animations for attacks (melee/ranged/castings)
* Fix fullscreen issue, and resize all clipping assets
* Add ESC opening menu capability (build out the menu later)
* AI opponent
* Clean up / beautify the end phase / end turn buttons, and make it occur automatically if there are no mroe valid choices for the user
