# Biblioteca

A small, interactive library-management application written in Python. It models users, books, libraries, shelves, and shared access, with a keyboard-driven terminal interface.

> **Project status:** This repository is a work in progress. The current implementation is a Windows-oriented command-line prototype, not a production-ready library system.

## Features

- **User accounts** — register and sign in with a username and password.
- **Book management** — create books with a title and page-based content.
- **Library management** — create libraries and organize them into shelves.
- **Inventory tracking** — place copies of a book on selected shelves and remove copies later.
- **Shared libraries** — authorize other registered users to manage a library.
- **Library browsing** — visit libraries, list their books and shelves, and open a book for reading.
- **Local persistence** — serialize users, books, libraries, and their relationships to a JSON file.
- **Keyboard-driven menus** — navigate single-choice menus with the arrow keys; multi-choice menus also support Space to mark items and Enter to confirm.

## Requirements

- Windows (the current interface imports Python's `msvcrt` module and opens book files with `notepad.exe`).
- Python 3.12 or newer. The source uses modern Python syntax, including PEP 695 type parameter syntax.
- No third-party Python packages are currently declared; the application uses the Python standard library.

## Getting started

1. Clone the repository and switch to the `Better-UI` branch:

   ```bash
   git clone --branch Better-UI https://github.com/GUT-R/biblioteca.git
   cd biblioteca
   ```

2. Run the application:

   ```bash
   python main.py
   ```

3. Choose **Registrar-se** to create an account, or **Fazer login** to sign in.

The application creates or reads `dados.json` in its current working directory to persist data. Keep this file if you want to retain the local database between runs.

## Usage

The main menu provides the following operations:

| Operation | Description |
| --- | --- |
| Visit a library | Browse a library's books and shelves, or read one of its books. |
| Create a book | Enter a title and write the book's content in Notepad. Separate pages with three consecutive newline characters (two blank lines). |
| Create a library | Create a library and choose how many shelves it should contain. |
| Manage your libraries | Add or remove book copies, inspect shelves, and authorize other users. |
| Exit | Save the current data and close the application. |

### Keyboard controls

- **Arrow Up / Arrow Down** — move through menu options.
- **Enter** — select an option or confirm a multi-selection.
- **Space** — mark or unmark an option in a multi-selection menu.

## Project structure

| File | Purpose |
| --- | --- |
| `main.py` | Application entry point; creates the main UI instance. |
| `bibilioteca.py` | Core domain model, persistence layer, authentication flow, and library-management interface. The filename is intentionally shown as it exists in the repository. |
| `advanced_ui.py` | Reusable terminal menu components, including radio selections and confirmation prompts. |
| `msvcrt_linux.py` | A Linux-oriented keyboard-input module; it is not currently wired into the main interface. |
| `test.py` | Additional test or development code. |
| `pyrightconfig.json` | Pyright type-checker configuration. |

## Data and security notes

- Data is stored locally in `dados.json`; there is no database server or network synchronization.
- **Passwords are currently stored as plain text** in the JSON data file. Do not use real or reused passwords, and do not expose `dados.json` publicly.
- This project has no production-grade authorization, encryption, backup, or recovery guarantees. Treat it as an educational/development project.

## Current limitations

- The interactive input implementation depends on Windows' `msvcrt`; the presence of `msvcrt_linux.py` does not yet provide automatic cross-platform support.
- Book creation and reading launch `notepad.exe`, so those workflows are Windows-specific.
- The integrated text editor and the search-with-suggestions function are not implemented yet.
- The current branch contains a syntax issue in `carregar_banco()`: the exception clause should use a tuple, for example `except (FileNotFoundError, json.decoder.JSONDecodeError):`. Fix this before running `main.py`; otherwise Python cannot import the module.

## Contributing

Issues and pull requests are welcome. When contributing, please keep the domain model, persistence logic, and terminal interface clearly separated, and document platform-specific behavior.

## License

No license file was present in the inspected branch. Unless a license is added to the repository, all rights remain with the copyright holder; do not assume the code is available for reuse or redistribution.
