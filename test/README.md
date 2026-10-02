# Lunara tests

Two reports, matching the shape of the Perpex harness.

## Unit report

`./run_tests.sh unit --skip-device` runs the Python layout, language, moon, and battery tests and writes `test_output/unit_report.html`.

`./run_tests.sh unit` then compiles the Monkey C tests and runs them in the Connect IQ simulator for every round device. `./run_tests.sh unit fenix7` limits the device pass to one watch.

Monkey C covers:

- `DialPhaseTest.mc` — moon phase bins and the January 2000 new moon
- `BatteryTest.mc` — 0%, 100%, and out-of-range battery text
- `LanguageTest.mc` — explicit language ids, and Same as watch for French, Spanish, both Chinese scripts, Japanese kanji, Italian, and German

## Visual report

`./run_tests.sh ui` renders the face for each round resolution, checks ink and clearance, and writes `test_output/visual_report.html`.

Columns match the Perpex report:

1. Pass and assertions
2. Watch face screenshot
3. Layout zones (green text boxes, orange date ring, blue 15% hand mask)
4. Baseline, current, and diff. The center 15% is excluded so clock hands do not count as a change. Variance above 5% fails.

```bash
./run_tests.sh ui --update-baselines
./run_tests.sh ui --device fenix7
./run_tests.sh ui --full
./run_tests.sh ui --with-hands
```

A focused run gives every device English and a 5% battery, and spreads the other languages across the matrix. `--full` renders every language plus 0% and 100% battery on every device.

Baselines live in `test_output/baselines/`. Updating them first copies the previous set to `test_output/baselines_backup_<timestamp>/`.

## Simulator

```bash
./run_tests.sh sim fenix7
./run_tests.sh sim venu3
```

## Memory

```bash
./profile_memory.sh
```

Writes `test_output/memory_report.html` with foreground data and code against the watch-face limit.

## Everything

```bash
./run_tests.sh all
```

Python units, visual compare, memory profile, then simulator unit tests.
