.PHONY: clean all test segments gcode2png gcode2png_all gcode2png_moves gcode2png_supports

all: test segments previews
test: test_tension test_1 test_2 test_hana test_skull

clean:
	rm -rf tests/*.log
	rm -rf tests/*.png

gcode2png:
	python3 ./gcode2png.py "tests/$(FILENAME).gcode" "tests/$(FILENAME).png" >"tests/$(FILENAME).stout.log" 2>"tests/$(FILENAME).stderr.log"

gcode2png512:
	python3 ./gcode2png.py "tests/$(FILENAME).gcode" --imgx 512 --imgy 512 "tests/$(FILENAME).512.png" >"tests/$(FILENAME).512.stout.log" 2>"tests/$(FILENAME).512.stderr.log"

gcode2png_all:
	python3 ./gcode2png.py "tests/$(FILENAME).gcode" --moves true --supports true "tests/$(FILENAME).all.png" >"tests/$(FILENAME).all.stout.log" 2>"tests/$(FILENAME).all.stderr.log"

gcode2png_moves:
	python3 ./gcode2png.py "tests/$(FILENAME).gcode" --moves true "tests/$(FILENAME).moves.png" >"tests/$(FILENAME).moves.stout.log" 2>"tests/$(FILENAME).moves.stderr.log"

gcode2png_supports:
	python3 ./gcode2png.py "tests/$(FILENAME).gcode" --supports true "tests/$(FILENAME).supports.png" >"tests/$(FILENAME).supports.stout.log" 2>"tests/$(FILENAME).supports.stderr.log"


test_1:
	$(MAKE) FILENAME=1 gcode2png gcode2png_moves gcode2png_supports gcode2png_all

test_512:
	$(MAKE) FILENAME=1 gcode2png512

test_2:
	$(MAKE) FILENAME=2 gcode2png gcode2png_moves gcode2png_supports gcode2png_all

test_hana:
	$(MAKE) FILENAME=hana_swimsuit_fv_solid_v1 gcode2png gcode2png_moves gcode2png_supports gcode2png_all

test_nano:
	$(MAKE) FILENAME=test_nano gcode2png gcode2png_moves gcode2png_supports gcode2png_all

test_skull:
	$(MAKE) FILENAME=skullbowl_0.4n_0.2mm_PETG_MINI_17h6m gcode2png gcode2png_moves gcode2png_supports gcode2png_all

test_tension:
	$(MAKE) FILENAME=tension-meter_petg_mini gcode2png gcode2png_moves gcode2png_supports gcode2png_all

test_crystal:
	$(MAKE) FILENAME="crystal" gcode2png gcode2png_moves gcode2png_supports gcode2png_all

segments: test_1 test_2 test_crystal test_hana test_skull test_tension test_nano
	grep "segment" tests/*.stderr.log|awk '{print $$6}'|sort|uniq

previews:
	$(MAKE) FILENAME=1 gcode2png512
	$(MAKE) FILENAME=2 gcode2png512
	$(MAKE) FILENAME=hana_swimsuit_fv_solid_v1 gcode2png512
	$(MAKE) FILENAME=test_nano gcode2png512
	$(MAKE) FILENAME=skullbowl_0.4n_0.2mm_PETG_MINI_17h6m gcode2png512
	$(MAKE) FILENAME=tension-meter_petg_mini gcode2png512
	$(MAKE) FILENAME=crystal gcode2png512

previews_md:
	@ls -1 tests/*.512.png | xargs -I{} echo "![$$(basename {})]({})"
