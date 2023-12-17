# gcode2png

python3 script for 3D rendering gcode files with [Mayavi](https://docs.enthought.com/mayavi/mayavi/)

Good:

![tests/1.512.png](tests/1.512.png)
![tests/2.512.png](tests/2.512.png)
![tests/hana_swimsuit_fv_solid_v1.512.png](tests/hana_swimsuit_fv_solid_v1.512.png)
![tests/skullbowl_0.4n_0.2mm_PETG_MINI_17h6m.512.png](tests/skullbowl_0.4n_0.2mm_PETG_MINI_17h6m.512.png)

Not so great:

![tests/crystal.512.png](tests/crystal.512.png)
![tests/tension-meter_petg_mini.512.png](tests/tension-meter_petg_mini.512.png)
![tests/test_nano.512.png](tests/test_nano.512.png)

## Features

- `--help` is showing usage
- option to define output image resolution
- option to show image preview (no more weird unrendered windows)
- set env var `LOGLEVEL=DEBUG` to see log flood on stderr

## Known limitations

- python 3.10+
- tested under Ubuntu 22.04, and nothing else
- no longer compatible with forked projects
- some gcode files are rendered weird, see `test_nano.gcode`

## Requirements

```shell
pip3 install -r requirements.txt
```

## Usage

```shell
python ./gcode2png.py --help
```

## Develop

```shell
make clean
make -j12 all
make -j12 previews previews_md
```

## Thanks

- initial gcode2png idea forked from [Zst](https://github.com/Zst/gcode2png),
  which was forked from [shodushi](https://github.com/shodushi/gcode2png)
- [gcodeParser.py](https://github.com/jonathanwin/yagv)

## Todo

- add thumbail generations
- add install to makefile
