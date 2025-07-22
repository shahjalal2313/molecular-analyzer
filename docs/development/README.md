# Development Guide

This guide provides instructions for setting up the development environment and contributing to the `molecular-analyzer` project.

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/shahjalal2313/molecular-analyzer.git
    cd molecular-analyzer
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

## Running Tests

To run the test suite, use `pytest`:
```bash
pytest
```

## Coding Style

We use `black` for code formatting and `flake8` for linting.
```bash
black .
flake8 .
```

## Contributing

Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to contribute to the project.