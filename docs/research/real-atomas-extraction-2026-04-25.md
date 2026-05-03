# Real Atomas Extraction Layer

Date: 2026-04-25

## What Changed

The repo now has a read-only `tools.real_atomas` package that parses installed
Atomas evidence without copying app assets into the simulator.

Implemented parsers:

- `atoms_en.info`: ordered `symbol-name-r,g,b` rows.
- `achievements.xml`: static achievement definitions and nested targets.
- `ac_save.xml`: user achievement progress and root counters.
- `gss_*.sg`: XML game-state saves with raw scalar and bubble fields preserved.
- `com.sirnic.atomas.plist`: preference plist with known score/index keys grouped.
- `*.strings`: simple localized string key/value files for mechanics corroboration.
- The inspect command also fingerprints every discovered source with SHA-256 so
  before/after gameplay experiments can identify changed files exactly.

The tests use synthetic schema fixtures under `tests/fixtures/real_atomas/`.
They intentionally do not vendor proprietary sprites, sounds, binaries, full
config files, or real localized copy.

## Local Evidence Snapshot

Command:

```bash
.pixi/envs/default/bin/python -m tools.real_atomas.inspect
```

Observed on Abe's installed app:

- Atomas app config sources are present under
  `/Applications/Atomas.app/Wrapper/Atomas-mobile.app`.
- User-state sources are present under
  `/Users/abrahamabelboodala/Library/Containers/com.sirnic.atomas`.
- `atoms_en.info` parses as 125 ordered records. The achievement target
  `create_all = 124` therefore probably excludes the final unknown sentinel row.
- `achievements.xml` contains 18 achievement definitions.
- `ac_save.xml` currently reports `highest_element = 10` and
  `classic_points = 1129`.
- Preferences currently report `hs_classic = 1129`, `le_classic = 9`, and
  `selectedMainAtom = 9`, reinforcing the zero-based vs one-based indexing
  question.
- `gss_tutorial.sg` is XML with 18 `bubble` rows plus `centerbubble` and
  `nextAtom`. The parser keeps `f`, `v`, `fr`, and all scalar tags raw.
- `en_main.strings` has 88 key/value entries, with 22 entries mentioning rule
  keywords such as plus, minus, neutrino, dark plus, or antimatter.

## Why This Matters

This gives Nucleo a durable evidence ingestion layer before changing simulator
physics. The next parity work can now consume real app state in typed form,
compare it with Mojo/Python state, and log controlled experiments instead of
embedding reverse-engineering guesses directly into the engine.

## Next Experiments

1. Add a snapshot command that records hashes plus parsed summaries before and
   after one real-app move. The hashing half now exists in
   `tools.real_atomas.inspect`.
2. Use controlled gameplay to map `f`, `v`, `fr`, and scalar fields like `mc`,
   `mwp`, `rau`, `uc`, and `ucd`.
3. Add an injected RNG transcript path to the Mojo engine so real spawn logs can
   be replayed deterministically.
4. Once the save fields are mapped, add golden simulator tests for real single
   merges, chain merges, scoring deltas, and terminal transitions.

## Verification

```bash
pixi run test-real-atomas
pixi run test
```
