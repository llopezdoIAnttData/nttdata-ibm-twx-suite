# Contributing to NTTDATA IBM TWX Suite

Thank you for your interest in improving this suite! This guide covers the
process for reporting issues, proposing features, and submitting code.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Reporting Bugs](#reporting-bugs)
3. [Suggesting Enhancements](#suggesting-enhancements)
4. [Development Setup](#development-setup)
5. [Pull Request Process](#pull-request-process)
6. [Coding Standards](#coding-standards)

---

## Code of Conduct

Please be respectful and professional. Harassment of any kind will not be
tolerated.

---

## Reporting Bugs

1. Search existing [Issues](../../issues) to avoid duplicates.
2. Open a new issue using the **Bug Report** template.
3. Provide a TWX file excerpt (anonymized) if possible.

---

## Suggesting Enhancements

1. Open an issue using the **Feature Request** template.
2. Describe the use case in terms of IBM BPM / TWX artefacts.
3. If proposing a new analysis cycle (Ciclo N), describe the XML prefix and
   expected output format.

---

## Development Setup

```bash
# 1. Clone the repo
git clone https://github.com/llopezdoIAnttData/nttdata-ibm-twx-suite.git
cd nttdata-ibm-twx-suite

# 2. Install in editable mode
cd 01_herramientas_python
pip install -e .

# 3. Verify
python -m ibm_twx_tools --help
```

### Running tests (when available)

```bash
cd 01_herramientas_python
pytest tests/ -v
```

---

## Pull Request Process

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes following the coding standards below.
4. Run a test analysis: `python run_analysis.py <sample.twx>`
5. Commit with a descriptive message.
6. Open a PR against the `main` branch.
7. Fill in the PR template completely.

---

## Coding Standards

- **Python**: Follow PEP 8. Use f-strings. Type hints welcome.
- **ANSI colors**: Use the constants in `banner.py` — no raw escape codes.
- **New cycle commands**: Add to `cli.py`, create a corresponding skill in
  `.copilot/skills/twx-<name>/SKILL.md`.
- **Documentation**: Update `CHANGELOG.md` under `[Unreleased]` for every
  non-trivial change.
- **Sensitive data**: Never commit `.twx` files or `output/` directories.

---

*NTT DATA EMEAL · IBM TWX Suite Team*
