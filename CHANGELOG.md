# Changelog

All notable changes to this project will be documented in this file.

<!--next-version-placeholder-->

## 2026.10.0

### 🔧 Improvements

- **Config flow**: migrated schema validation from `voluptuous` to `probatio`, in line with Home Assistant core.
- Minimum Home Assistant version raised to `2026.9.0`.
- `VERSION` constant (device `sw_version`) aligned with the manifest.

### 🔧 Bug fixes

- **Main sensor**: the last measurement time sensor and the morphology were read from the entry data instead of the options, so a missing or invalid last weigh-in time was never reported. The main sensor now reports `problem` with `last_time_unavailable` in that case.
- **Options**: changing the options now reloads the integration so new values (morphology, environment, sensors) are applied immediately, without restarting Home Assistant.

#### Developer tooling

- Migration from `setup.cfg` + `mypy.ini` + `requirements.txt` + `bandit.yaml` → unified `pyproject.toml`
- Replaced pyupgrade/black/flake8/isort with **Ruff** (lint + format)
- Modernized `.devcontainer.json` — `astral-sh.ruff` extension, removed black/flake8/autopep8
- Added `.codespell-ignore`
- `pre-commit`: added `codespell`, `check-json`, `end-of-file-fixer`, `trailing-whitespace` hooks
- CI installs with `pip install -e ".[dev]"` and runs `ruff check`, `ruff format --check`, `mypy`, `pylint` and `pytest`
- Added a test suite (`tests/`, 78 tests, ~93% coverage) based on `pytest-homeassistant-custom-component`: config/options flow, setup/unload, sensors, coordinator and calculation helpers

### 🗑️ Removals

- `setup.cfg`, `mypy.ini`, `requirements.txt`, `bandit.yaml` removed — consolidated into `pyproject.toml`

## 2026.7.0

- Fixed config/options flow crash on `weight_sensor` and `last_time_sensor` fields (`Entity None is neither a valid entity ID nor a valid UUID`) by using suggested values instead of forced defaults ([The empty field isn't working](https://github.com/dckiller51/bodypetscale/issues/77)).
- Previously saved values for living environment, morphology, weight sensor and last weigh-in sensor now remain pre-filled but editable when reopening options, instead of being reset.

## 2026.1.0

- Fixed invalid URL in translations by using description placeholders for morphology help link

## 2025.12.0

- Fix quality code error

## 2025.6.0

- added Russian language support (thank you @Kvasenok)

## 2025.5.1

- Added new attributes to the main sensor.
- Internal improvement to age calculation logic (more accurate monthly age detection).

## 2025.5.0

- Initial public release on HACS.
- Weight tracking and ideal weight estimation for dogs and cats.
- Support for both `sensor` and `input_number` entities as weight inputs.
- Customizable configuration including:
  - Animal type, birthday, breed
  - Activity level, reproductive status, temperament, appetite
  - Living environment and body condition (morphology)
- Optional last weigh-in sensor support.
- All calculations are performed locally within Home Assistant.
- Full multi-pet support with dedicated sensors per animal.
