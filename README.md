# Divinity agent models

The loose model and material files the Divinity model changer needs (skins tab → terrorist /
counter-terrorist model). The 2018 game files have no Agents, so without these the dropdowns
print `[model] … could not be loaded` and keep the normal model.

## Install

1. Download this repo (green **Code** button → **Download ZIP**) and extract it.
2. Find your game folder, the one that contains `csgo.exe`. Inside it is a folder also named
   `csgo` (it has `pak01_dir.vpk`, `cfg`, `maps`, and so on in it). For example:

   ```
   ...\csgo 2018\csgo.exe
   ...\csgo 2018\csgo\pak01_dir.vpk     <- this csgo folder
   ```

3. Copy the `csgo` folder from this repo into your game folder, next to `csgo.exe`, so it merges
   with the existing `csgo` folder. When Windows asks, choose to merge folders and replace files.
4. Check it worked: these should now exist in your game folder.

   ```
   csgo\models\player\custom_player\legacy\ctm_fbi_variantb.mdl
   csgo\materials\models\player\custom_player\econ\
   ```

5. Restart the game, then pick an agent in Divinity under skins tab → terrorist model /
   counter-terrorist model.

If an agent still shows your normal model, the console prints `[model] <path> could not be loaded`.
That path is relative to the `csgo` folder, so check that file exists there. Purple-and-black
checkerboard textures mean the `materials` folder didn't get copied.

Nothing is overwritten that the game ships with: every file here is one the 2018 game files don't
include.

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
