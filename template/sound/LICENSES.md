# Sound bed sources and licences

Licence for all library files: Mixkit Sound Effects Free License (https://mixkit.co/license/), free for commercial use, no attribution required, **not to be redistributed as files**. So the plugin does not ship them: `scripts/install.py --install --only sfx` downloads them into `~/.skit-studio/sfx/` from the URLs in `sfx_sources.json`, and `scripts/new_skit.py` copies them into the skit's `sound/src/`.

| File in `src/` | Used for | Source URL |
|---|---|---|
| `sfx-keyboard-click.mp3` | key hits (`typing[].keys`), first 0.15 s | https://assets.mixkit.co/active_storage/sfx/2533/2533-preview.mp3 |
| `typewriter-hit-soft.mp3` | enter (`enter[]`) | https://assets.mixkit.co/active_storage/sfx/1366/1366-preview.mp3 |
| `glitch-virtual-quick.mp3` | limit (first 0.35 s, under the synthesised tones) | https://assets.mixkit.co/active_storage/sfx/2946/2946-preview.mp3 |
| `sparkle-wand.mp3` | sparkle | https://assets.mixkit.co/active_storage/sfx/3062/3062-preview.mp3 |
| `swoosh-quick.mp3` | popcorn slide | https://assets.mixkit.co/active_storage/sfx/166/166-preview.mp3 |
| `paper-crumple-quick.mp3` | popcorn land | https://assets.mixkit.co/active_storage/sfx/2996/2996-preview.mp3 |
| `clock-tick-single.mp3` | clock ticks | https://assets.mixkit.co/active_storage/sfx/1061/1061-preview.mp3 |

Synthesised, no source file: room tone (brown + pink noise, seeded), limit two-tone (triangle waves 523 Hz and 392 Hz), «дзынь» (two-tone bell), marker tick, pop.

`sfx_bed.wav` in the template is the mixed demo bed (the sounds used inside a finished soundtrack, as the licence allows).

Music is not shipped either: at step 10 the lead finds a track on Mixkit (Mixkit Stock Music Free License, https://mixkit.co/license/#musicFree) and downloads it on the person's machine after their «да».
