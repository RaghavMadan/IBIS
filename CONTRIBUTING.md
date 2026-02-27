# Contributing to IBIS (Integrated Brain Information System)

Contributions are welcome. Please follow these guidelines.

## Development setup

1. Fork and clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```
3. Run tests: `python test_pipeline.py`

## Code style

- Follow PEP 8.
- Add docstrings to public functions and classes.
- Use type hints where helpful.

## Pull requests

- Create a feature branch from `main`.
- Ensure `python test_pipeline.py` passes.
- Update README or config docs if you change behavior or add options.
- Keep the PR focused; use a clear title and description.

## Reporting issues

- Use GitHub Issues for bugs or feature requests.
- Include Python version, OS, and steps to reproduce where relevant.

By contributing, you agree that your contributions will be licensed under the project’s MIT License.
