# Divinity agent models

The loose model and material files the Divinity model changer needs (skins tab → terrorist /
counter-terrorist model). The 2018 game files have no Agents, so without these the dropdowns
print `[model] … could not be loaded` and keep the normal model.

## Install

Copy the `csgo` folder from this repo over your game's `csgo` folder, merging folders when asked.
Restart the game afterwards.

Only the 63 agents in the model changer are included, and only files not already inside the stock
`pak01` VPKs (about 945 files, 530 MB).

## Rebuilding

`pack_agents.py` regenerates `csgo/` from a game folder that has the agents installed:

```
python pack_agents.py "path\to\csgo"
python pack_agents.py "path\to\csgo" --zip
```

It reads each agent `.mdl` for its materials and search paths, follows every `.vmt` to the
textures and includes it references, and skips anything already packed in `pak01_dir.vpk`. Keep
its `AGENTS` list in sync with `PlayerModels` in Divinity's `features/visuals/skins.cpp`.
