# Video editing

Motorcycle edit (vertical 9:16, Thunderstruck).

## How to render
Source clips and `song.mp3` are attached to release `v1`.
Download them into one folder, then run:

    python3 edit.py <clips_folder> <output_folder>

Produces `edit_music.mp4` (song + engine) and `edit_engine.mp4` (engine only).
The shot list (clip, start, beats, speed, effects) is at the top of `edit.py`.
