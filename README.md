# Lunara

A cream calendar watch face. The dial carries Roman hours, a month and date pair, and a moon-phase sub-dial with days 1–31.

Perpex is a separate face. This project does not share its name or its tactical ring layout.

## Dial

`tools/dial_layout.py` is the geometry. `tools/dial_render.py` paints the ivory bitmap and the eight moon sprites. `source/Dial.mc` draws that bitmap plus the live month, weekday, date, side legends, and battery percentage.

The language setting defaults to the watch language. Japanese can be kanji, hiragana, or katakana. Chinese is simplified or traditional. Hindi is in the setting list; Garmin has no Hindi device language, so it is chosen explicitly.

```bash
cd tools
python3 -m unittest discover -s . -p 'test_*.py'
python3 generate_dial.py
python3 generate_font.py
```

Screen sizes: 240, 260, 280, 360, 390, 416, 454, and 466.

## Build

Requires the Connect IQ SDK.

```bash
./build.sh fenix7
```

The first build creates a local `developer_key.der`. That key stays on this machine.

## Tests and reports

```bash
./run_tests.sh unit --skip-device   # Python suite → test_output/unit_report.html
./run_tests.sh ui --update-baselines
./run_tests.sh ui                   # visual gallery → test_output/visual_report.html
./profile_memory.sh                 # test_output/memory_report.html
./run_tests.sh sim fenix7
```

Details are in `test/README.md`.
