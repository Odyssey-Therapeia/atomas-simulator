# Real Atomas Reverse-Engineering Handoff

Date: 2026-04-25

Purpose: capture what was learned from the installed real Atomas app on Abe's Mac so the `atomas-simulator` / Nucleo work can move toward a faithful simulator before adding MCTS, expectimax, MuZero-style agents, or deep RL.

## Core Thesis

The project should not use an LLM as the gameplay brain. The right split is:

- **LLM / agent:** research assistant, rule investigator, code reviewer, planner explainer.
- **Simulator:** deterministic source of game physics.
- **Search:** expectimax / MCTS / beam search over the simulator.
- **Deep learning:** later value/policy approximation once the simulator is validated.

The immediate goal should be a **perfect recreation of the real Atomas rules**, including spawn distribution, chain resolution order, scoring, game-over logic, and special pieces. Only after that should we optimize or train.

## Installed Real App

The installed app is a Mac-runnable iOS app wrapper:

- App: `/Applications/Atomas.app`
- Bundle id: `com.sirnic.atomas`
- Display name: `Atomas`
- Inner executable: `/Applications/Atomas.app/Wrapper/Atomas-mobile.app/Atomas-mobile`
- Runtime process observed:
  - `/private/var/folders/.../Wrapper/Atomas-mobile.app/Atomas-mobile`
- App version from Info.plist: `3.15`
- `CFBundleShortVersionString`: `3.15`
- `CFBundleSupportedPlatforms`: `iPhoneOS`
- Local app container:
  - `/Users/abrahamabelboodala/Library/Containers/com.sirnic.atomas`

Binary strings show Cocos2d-style symbols (`cocos2d`, `GameField`, `AtomInfoOverlay`, etc.), not Unity. This means Timberborn-style Unity JSON assets should not be expected.

## App Bundle Data Worth Mining

Useful real-app files:

- `/Applications/Atomas.app/Wrapper/Atomas-mobile.app/asset/config/atoms_en.info`
  - CSV-like element metadata.
  - Contains symbol, name, and RGB color for elements through `Og`, plus custom `Bn` and `Gb`.
  - This is the best source for element identity/color mapping.

- `/Applications/Atomas.app/Wrapper/Atomas-mobile.app/asset/config/achievements.xml`
  - Contains achievement goals and hidden targets.
  - Examples observed:
    - `score_1000`, `score_10000`, `score_100000`
    - `highest_element` targets: Oxygen `8`, Silicon `14`, Chromium `24`, Germanium `32`, Gold `79`, Lead `82`, Bananium `119`, create all `124`
    - `chainreaction_14`
    - `clear_all`
    - `beat_dev` target `66543` points

- `/Applications/Atomas.app/Wrapper/Atomas-mobile.app/asset/config/config.ini`
  - Basic app metadata.

- `/Applications/Atomas.app/Wrapper/Atomas-mobile.app/asset/config/theme.ini`
  - Theme colors only.

- `/Applications/Atomas.app/Wrapper/Atomas-mobile.app/asset/config/ads.ini`
  - Ad config; not relevant for simulator.

- `/Applications/Atomas.app/Wrapper/Atomas-mobile.app/asset/config/iap.ini`
  - IAP metadata; not relevant for simulator except antimatter purchase context.

Do not copy proprietary sprites/sounds/assets into the simulator. Use extracted mechanics and public factual metadata only.

## Local User/App State Files

Useful local data files:

- `/Users/abrahamabelboodala/Library/Containers/com.sirnic.atomas/Data/Library/Preferences/com.sirnic.atomas.plist`
  - Observed values:
    - `hs_classic => 1129`
    - `le_classic => 9`
    - `selectedMainAtom => 9`
    - `hide_ads => true`
    - `soundOn => 1`
  - On the live app screen, the game-over state showed score `1129` and highest atom `Neon`, matching the preference/achievement data. Validate whether `le_classic` is zero-based while achievement `highest_element` uses atomic number.

- `/Users/abrahamabelboodala/Library/Containers/com.sirnic.atomas/Data/Documents/ac_save.xml`
  - Achievement progress.
  - Observed counters:
    - `<counter n="highest_element" v="10"/>`
    - `<counter n="classic_points" v="1129"/>`
  - Supports the Neon / 1129 observation.

- `/Users/abrahamabelboodala/Library/Containers/com.sirnic.atomas/Data/Documents/gss_tutorial.sg`
  - Plain XML game state. This is the most important evidence that the app has a simple internal state shape.
  - Observed structure:
    ```xml
    <gamestate>
      <mc>14</mc>
      <lv>0</lv>
      <hv>3</hv>
      <mwp>0</mwp>
      <las>0</las>
      <s>0</s>
      <le>7</le>
      <rau>0</rau>
      <lc>-1</lc>
      <uc>0</uc>
      <ucd>0</ucd>
      <bubbles>
        <bubble f="0" v="5" fr="0"></bubble>
        ...
      </bubbles>
      <centerbubble f="1" v="0"/>
      <nextAtom f="1" v="0"/>
    </gamestate>
    ```
  - Hypotheses to validate:
    - `bubbles` is the circular board.
    - `centerbubble` is current/held piece.
    - `nextAtom` is the visible next piece.
    - `f` is a piece family/type. `f=0` appears to mean regular atom. `f=1 v=0` likely means Plus in the tutorial save, but validate.
    - `v` is probably element value/index. Need determine zero-based vs one-based.
    - `fr` may be a frozen/free/recent flag.
    - `s` likely score.
    - `le` likely last/highest element or level-related field.
    - `mc`, `lv`, `hv`, `mwp`, `las`, `rau`, `lc`, `uc`, `ucd` need controlled experiments.

- `/Users/abrahamabelboodala/Library/Containers/com.sirnic.atomas/Data/Documents/classic.slb`
  - Binary-ish leaderboard/score data. Strings include `Albert E.` and `ints`.
  - Not enough for board state yet.

- `/Users/abrahamabelboodala/Library/Containers/com.sirnic.atomas/Data/Documents/sssai.na`
  - Encoded/obfuscated secure data. Unknown purpose.

## Observed Runtime Screen

Using Computer Use, the real Atomas app was visible and running. Earlier observed screen:

- Game over / name-entry state.
- Score: `1129`
- Highest atom: `NEON`
- Center shows `Ne 10`.
- Button: `NEW GAME`.

This matches:

- `hs_classic => 1129` in preferences.
- `highest_element v="10"` in `ac_save.xml`.

User-provided screenshots showed the upgrade screen. The user clarified the binary strings around "10% more Plus Atoms" etc. are **upgrade/booster effects**, not baseline mechanics. Model them as optional modifiers layered over classic rules.

## Upgrade / Booster Evidence

Binary strings expose these upgrade descriptions:

- `10% more Plus Atoms`
- `10% more Minus Atoms`
- `20% more Plus / 10% less Minus Atoms`
- `33% chance of higher spawing atoms` (typo in binary string)
- `20% more Points for chain reactions`
- `35% chance of higher fusion outcome`
- `Starts game at Mg (12)`
- `33% chance of plus if 18 Atoms`
- `+0.001% chance per round of Antimatter (1 per game)`
- `Destroys a random atom every 50 rounds`
- `Doubles points if 0 atoms on field`
- `Randomly rearrange atoms`

User screenshots imply the upgrade grid order maps these effects to visible atoms:

- O: likely `10% more Plus Atoms`
- Si: `10% more Minus Atoms` (confirmed by screenshot)
- K: likely `20% more Plus / 10% less Minus Atoms`
- Ti: likely `33% chance of higher spawning atoms`
- Co: likely `20% more Points for chain reactions`
- Ge: likely `35% chance of higher fusion outcome`
- Br: `Starts game at Mg (12)` (confirmed by screenshot)
- Kr: likely `33% chance of plus if 18 Atoms`
- Rb: likely `+0.001% chance per round of Antimatter`
- Ag: likely `Destroys a random atom every 50 rounds`
- Er: likely `Doubles points if 0 atoms on field`
- Rn: likely `Randomly rearrange atoms`

Treat this mapping as high-confidence for Si and Br, medium-confidence for the rest until verified in-app.

## Other Real-App Rule Strings

Binary strings include these tutorial/rule hints:

- `Tap between 2 Atoms to place the middle one`
- `A Plus fusions 2 similar Atoms into a higher one`
- `Look for symmetry in your atoms to start big chain reactions`
- `Various elements in chain reactions lead to higher fusions and more points`
- `Use minuses to absorb and replace an atom`
- `Alternatively tap the absorbed atom to sacrifice it for an plus`
- `The game ends when the circle is full, use Antimatter to remove half of the atoms`
- `Neutrino`
- `A Neutrino copies any Atom on the gamefield, tap on the atom you wish to copy.`
- `Dark Plus`
- `Dark pluses can start fusions between any two atoms`
- `Luxon`
- `In the Geneva mode there are no spawning pluses, but so called Luxons. Tap any atom on the gamefield and the Luxon will turn it into a plus for one round.`
- `Use antimatter to remove half of the atoms on the field`
- `You've already used antimatter in this game. To use it again you have to double the score since the last usage`

These strings support modeling:

- Plus
- Minus
- Dark Plus / Black Plus
- Neutrino
- Luxon / Geneva mode
- Antimatter
- Circle-full terminal condition

## Research Questions To Resolve Next

Priority order for a "perfect recreation":

1. **XML field semantics**
   - Create small real-app games, quit/save, inspect changed files.
   - Determine whether current classic state is persisted as `gss_classic.sg`, `classic.sg`, or only when paused/closed.
   - Map `f`, `v`, `fr`.
   - Map scalar fields: `mc`, `lv`, `hv`, `mwp`, `las`, `le`, `rau`, `lc`, `uc`, `ucd`.

2. **Indexing**
   - Determine whether element values are zero-based or one-based in internal saves.
   - Evidence conflict:
     - `highest_element v="10"` corresponds Neon atomic number 10.
     - Preference `le_classic => 9` may be zero-based Neon.

3. **Spawn distribution**
   - Existing README estimates plus/minus/black-plus/neutrino rates.
   - Need controlled real-app observation to validate:
     - Baseline plus probability and guarantee interval.
     - Minus probability.
     - Special unlock thresholds.
     - Regular atom range relative to highest/current max.
     - Pity/straggler logic.
   - Use screenshot/OCR or saved XML snapshots to log many turns.

4. **Fusion order**
   - Validate board-driven scan order and precedence against real app.
   - Existing repo states "counter-clockwise precedence"; verify with controlled boards if possible.
   - Need exact behavior when multiple Plus/Dark Plus tokens are simultaneously reactable.

5. **Scoring**
   - Existing repo says raw scores are exponential `2^X`, but real game may include chain multipliers, reaction depth, bonus points, and upgrade effects.
   - Need golden examples from the real app:
     - Single merge score.
     - Multi-chain score.
     - Dark Plus score.
     - Empty-board bonus.

6. **Terminal condition**
   - Binary string: "circle is full".
   - Existing repo says atom cap is `18`, while persistent Plus/Black Plus tokens can make total token count exceed atom cap.
   - Validate real terminal state around 18 atoms, Plus at 18, Minus at 18, Neutrino at 18, and persistent Plus tokens.

7. **Antimatter**
   - Optional rescue mechanic. Model after core classic rules.
   - Need exact random half-removal behavior and reuse score threshold.

## Suggested Engineering Plan

The repo already has Mojo engine, Python baseline, web UI, RL wrapper, and benchmarks. The next effort should be "truth alignment", not more optimization.

Recommended next branch/theme:

1. Add a `real_app/` or `tools/real_atomas/` parser for:
   - `atoms_en.info`
   - `achievements.xml`
   - `gss_*.sg`
   - `ac_save.xml`
   - preferences plist

2. Add fixtures copied from **user-generated state files only**:
   - Sanitize and store small XML snippets such as `gss_tutorial.sg`.
   - Do not vendor proprietary app assets.

3. Add a "real state" decoder:
   - `decode_gamestate_xml(path) -> GameStateLike`
   - Print ring values, center piece, next piece, score fields.
   - Keep unknown fields in an `extras` map.

4. Add golden tests:
   - Parse `gss_tutorial.sg` and assert 18 bubbles, center/next piece values, scalar fields.
   - Validate atom symbol/color lookup from `atoms_en.info`.
   - Validate achievement target extraction from `achievements.xml`.

5. Add controlled-experiment workflow:
   - Manual or Computer Use starts a new game.
   - Save/quit/pause after each move.
   - Snapshot `Data/Documents` files.
   - Diff XML/plist changes.
   - Build a move log of `(pre_state, action, post_state, score_delta, next_piece)`.

6. Only then adjust simulator rules:
   - Spawn RNG should accept an injected random stream / transcript.
   - This is essential for exact parity and MCTS experiments.
   - Existing README notes Mojo/Python cross-validation is blocked because the Mojo engine consumes RNG internally. Fix this before serious truth tests.

## Suggested Agent Prompt

Use this prompt for the next coding agent in this repo:

> We need to align Nucleo with the real installed Atomas app, prioritizing faithful rule recreation over optimization. Read `docs/research/real-atomas-handoff-2026-04-25.md`, then inspect the current Mojo/Python engine. Implement a read-only `tools/real_atomas` extraction layer for the installed app files and local user state files listed in the handoff. Start with parsers for `atoms_en.info`, `achievements.xml`, `gss_tutorial.sg`, `ac_save.xml`, and `com.sirnic.atomas.plist`. Add tests/fixtures using small sanitized XML snippets and keep unknown game-state fields preserved. Do not copy proprietary sprites/sounds/assets. The output should help us map real Atomas state to the simulator model and identify rule gaps.

## Useful Commands

Inspect app bundle:

```bash
find /Applications/Atomas.app/Wrapper/Atomas-mobile.app/asset/config -maxdepth 1 -type f -print | sort
plutil -p /Applications/Atomas.app/Wrapper/Atomas-mobile.app/Info.plist
strings /Applications/Atomas.app/Wrapper/Atomas-mobile.app/Atomas-mobile | rg -i 'plus|minus|atom|chain|score|reaction|spawn|neutrino|dark|antimatter|geneva|luxon'
```

Inspect local user state:

```bash
plutil -p "$HOME/Library/Containers/com.sirnic.atomas/Data/Library/Preferences/com.sirnic.atomas.plist"
find "$HOME/Library/Containers/com.sirnic.atomas/Data/Documents" -maxdepth 1 -type f -print -exec file {} \;
strings "$HOME/Library/Containers/com.sirnic.atomas/Data/Documents/gss_tutorial.sg"
strings "$HOME/Library/Containers/com.sirnic.atomas/Data/Documents/ac_save.xml"
```

Relevant repo path:

```bash
cd "/Users/abrahamabelboodala/Coding Projects/Odyssey Github/atomas-simulator"
```

