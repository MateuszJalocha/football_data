# Getting Started

This project is designed to take match information and process it into a suitable form to be saved

## Setting up for Development

### Prerequisites

The following tools must be installed in your system:
- python 3.10.4
- poetry
- pyenv


### Dev-dependencies

- pytest
- pre-commit
- bump2version

### Setup

Use pyenv to install and set **python 3.10.4** in project directory:

    pyenv install 3.10.4
    pyenv local 3.10.4

Then install the dependencies with poetry:

    poetry install

If you installed poetry with a different python version than **3.10.4** it is
possible that you will have to change the interpeter used by poetry:

    poetry env use /path/to/interpreter

or create environment with venv (after you set local python as **3.10.4**):

    python -m venv .venv
    poetry install

### Git hooks
We use pre-commit to automate a few steps in our workflow.
(See https://pre-commit.com/ ; Configuration file: .pre-commit-config.yaml)

Before every commit, some syntax checks will be run.  
And before every push, unit tests are executed.
