# DevDox Ai Git 

devdox-ai-git is a reusable Python package that provides functionalities specific to Git operations.
It is built using the modern `src/` layout, with strong emphasis on type safety, linting, and testing discipline.

---

## 🚀 Quick Default Setup when Developing

1. Install with dev dependencies (testing + tooling)
    ```bash
    pip install -e .[dev]
    ```

2. Install pre-commit hooks (runs on every commit)
    ```bash
    pre-commit install
    ```

3. Run tests (coverage is enabled by default)
    ```bash
    pytest
    ```

4. When Committing changes (hooks auto-format, lint, and check types) auto kicks in

---

## 📦 Installation

Clone the repo and install it locally:
```bash
git clone https://github.com/montymobile1/devdox-ai-git.git
cd devdox-ai-git
```

### Runtime only:
```bash
pip install -e .
```

### With development dependencies (Recommended for local dev)
For development, testing, and code quality tools:
```bash
pip install -e .[dev]
```

---

## 🏗️ Project Layout

This project uses the `src/` layout.

Reference: [src-layout vs flat-layout (PyPA docs)](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) 

```terminaloutput
devdox-ai-git/
├── src/
│   └── devdox_ai_git/   <- actual package code
│       └── __init__.py
├── tests/               <- test suite
├── LICENSE
├── README.md
├── pyproject.toml       <- build system + tool configs
└── .pre-commit-config.yaml
```
### Why `src/` Layout?
- Prevents accidental imports from local working directory.
- Forces you to install the package (editable or normal) before importing.
- Matches industry best practices for modern Python packaging.

---

## ⚡ Development Workflow

### Tiered Enforcement Philosophy

This project uses pre-commit locally for fast feedback and CI/CD remotely for strict checks.

> ⚠️ CI/CD not implemented yet

- **Local (pre-commit hooks)**
  - Black → auto-formats code before commit.
  - Ruff → auto-fixes common lint issues.
  - Mypy → runs only on staged files (quick checks).
  - ✅ Keeps development smooth, prevents friction.

- **CI/CD (remote)** 
  - Black → runs in --check mode (ensures formatting is consistent). 
  - Ruff → runs in strict mode. 
  - Mypy → runs on the entire codebase. 
  - Pytest → runs the full test suite with coverage. 
  - ✅ Ensures code quality across the whole repository.

### Setup Pre-Commit
```bash
pre-commit install
```
Now, every commit will:
- Auto-format your code.
- Auto-fix trivial issues.
- Block only if serious type errors remain.

Not recommended, but you can bypass hooks with `--no-verify`:
```bash
git commit -m "WIP" --no-verify
```

--- 

## 🧪 Testing

Run the test suite:
```bash
pytest
```

### Coverage
Coverage reporting is already preconfigured in `pyproject.toml`, so running `pytest` automatically collects coverage data.
This means running plain `pytest` will:
- Collect coverage information on the `devdox_ai_git` package.  
- Include branch coverage (not just lines).  
- Report missing lines directly in the terminal.  
- Skip reporting files that already have 100% coverage.  

👉 In short: **you don’t need extra flags**, just run `pytest`. 

If you want to manually override or customize reports (e.g. HTML output), you can still run for example:
```bash
pytest --cov=devdox_ai_git --cov-report=term-missing
```

---

## 🛡️ Type Checking, Formatting & Linting

**These are handled automatically by `pre-commit` on every commit and are pre-configured in the `pyproject.toml`.**

beware, that the very first time you commit after installing pre-commit it takes long but Subsequent runs should be much faster, its slow at the start because:
- It downloads hook environments.
- Builds them in isolated virtualenvs. This can take several minutes.

### Configuration

#### Ruff Configuration

Ruff is our main **linter** (it checks code style, catches mistakes, and enforces consistency).  
We configured it to cover a wide range of rules:

- **Select**: `["E", "F", "W", "B", "I", "UP"]`  
  - **E, F, W** → the basic Python style and bug rules (like missing imports, unused variables).  
  - **B** → Bugbear: catches tricky mistakes (e.g., using a mutable default argument).  
  - **I** → Import sorting: makes sure imports are grouped and ordered consistently (so we don’t need isort).  
  - **UP** → PyUpgrade: reminds us to use modern Python syntax where possible.

- **Ignore**: `["E501"]`  
  - Normally, Ruff would complain about lines longer than 88 characters.  
  - But since Black automatically formats our code, we let Black handle line length instead of Ruff.

- **Per-file Ignores**:
  - **`tests/* = ["D", "S101"]`**  
    - We don’t require docstrings in test files — tests should be quick and readable, not over-documented.  
    - We also allow the use of raw `assert` statements in tests (which Ruff normally warns against) because they are simple and perfectly fine in a testing context.  
  - **`__init__.py = ["F401"]`**  
    - Ruff normally flags unused imports as a problem.  
    - But in `__init__.py` files, those imports are intentional: we *re-export* them so users can access our package API from a single place.  
    - Example: instead of `from devdox_ai_git.git_managers import GitManager`, users can just do `from devdox_ai_git import GitManager`.  
    - Ruff sees them as “unused”, but they are part of our design.

👉 In short: Ruff enforces strict rules everywhere, but we made **practical exceptions** for test readability and for our clean public API design.

#### Types-Requests Configuration

This project uses the `requests` library for HTTP calls.  
The problem is: `requests` itself does **not** include proper type hints.  
That means tools like **Mypy** or your IDE don’t know what types its functions return.  

Example without `types-requests`:  
```python
import requests

r = requests.get("https://httpbin.org/get")
print(r.status_code)  # is this an int? a string? Mypy has no idea.
```
Mypy will just treat everything as `Any`, which defeats the purpose of type checking.

That’s where `types-requests` comes in:
- It’s a type stub package, which is a set of `.pyi` files that describe the API of `requests`.
- It tells Mypy (and your IDE):
  - Response.status_code → is an int.
  - Response.json() → returns Any.
  - Response.text → is a str.

With it installed:

```python
import requests

r = requests.get("https://httpbin.org/get")
reveal_type(r.status_code)  # Mypy: Revealed type is "builtins.int"
```
👉 Important notes:
- `types-requests` is never imported in your code.
- It exists only to help development tools understand types.
- At runtime, only the real requests library is used. That’s why we keep it in dev dependencies only, production code doesn’t need it.

In short: types-requests makes our codebase type-safe when working with requests, without affecting runtime.

### PyCharm Integration

PyCharm comes with its own formatter, linter, and type checker, but those are **not** the same as Black, Ruff, and Mypy.  

To ensure consistency with our `pyproject.toml` configuration, you must set up PyCharm to use the tools we defined.

#### 1. Black (Code Formatter)
PyCharm has built-in support for Black.

1. Go to **Settings → Tools → Black**.  
2. Set *Execution mode* = **Package**.  
3. Choose your project’s Python interpreter (with Black installed via `[dev]`).  
4. Check:
   - *On code reformat (Ctrl+Alt+L)*  
   - *On save*  

👉 Black will now run automatically inside PyCharm and respect the `[tool.black]` configuration in `pyproject.toml`.

---

#### 2. Ruff (Linter)

1. Install the **Ruff plugin for PyCharm** (available in Marketplace), adn then Go to **Settings → Tools → Ruff** to configure it

##### Key Settings for Ruff in PyCharm

- **Run Ruff when the Python file is saved**
  - Optionally Check this → Ruff lints your file every time you save. 
  - Similar to how pre-commit works, but instant feedback inside IDE.


- **Run Ruff when Reformat Code** 
  - Optional — if enabled, pressing Ctrl+Alt+L (Reformat) will also run Ruff fixes. 
  - 👉 I suggest enabling this so Ruff + Black run together when you reformat.


- **Import Optimizer in Ruff**
  - ❌ Leave unchecked. 
  - Ruff already has rules for import sorting (I) built-in, which we enabled in the `pyproject.toml`. 
  - If you check “Use Import Optimizer”, PyCharm will try to optimize/sort imports on its own, separate from Ruff. 
  - That risks conflicts: PyCharm might reorder imports differently than Ruff (or Black), and you’ll end up with “fight loops” where Ruff fixes them back.


- **Always use Global executable**
  - ❌ Leave unchecked.
  - We want Ruff to come from your project’s virtual environment (so it matches pre-commit & CI), not some global install.


- **Ruff executable:**
  - Under Project Specific, if not detected automatically, point it to the Ruff binary in your .venv.
  - 👉 Once that’s set, the plugin will run the same Ruff as your CLI and pre-commit hooks.


- **Ruff config file** 
  - Leave blank. 
  - Ruff automatically picks up your `[tool.ruff]` config from `pyproject.toml`.
  - You only need to specify this if you kept Ruff config in a separate file like ruff.toml, which we didn’t.


- **Enable Ruff LSP feature (optional, advanced)**
  -  This uses Ruff’s new Language Server Protocol mode (more IDE-like, with hover diagnostics, quick fixes, etc.).
    - Check Enable Ruff LSP feature.
    - Set LSP Server = ruff server command.
  - 👉 If this feels too much, you can skip it — Ruff will still lint on save with the normal mode.

---

#### 3. Mypy (Type Checker)
PyCharm has native support for Mypy, but you need to point it to the correct executable in your virtual environment.

1. Go to Settings → Other Settings → Mypy.
2. Ensure Path to Mypy executable points to your project’s venv. PyCharm usually auto-detects this if you installed mypy via `pip install .[dev]` extras.
3. Leave Path to config file blank.
   - Mypy will automatically read the `[tool.mypy]` configuration from `pyproject.toml`.
   - You only need this if you use mypy.ini or setup.cfg (not the case here).
4. (Optional) Add extra arguments:
   - `--show-error-codes` → shows rule codes along with error messages.
   - `src/` → restricts checks to just the source directory.
5. Click Test to verify PyCharm runs Mypy correctly.

👉 Once enabled, PyCharm will run Mypy in the background using the strict rules we defined in `pyproject.toml` (e.g. `disallow_untyped_defs`, `no_implicit_optional`, etc.).

---

### ⚡ Why This Matters
- Without these steps, PyCharm uses its **built-in tools**, which are less strict and don’t match our shared configuration.  
- With this setup, **PyCharm = pre-commit = CI** → everyone sees the same errors, the same formatting, and the same type rules.

### Manual runs (useful for quick checks without committing):

#### Type Checking
```bash
mypy src/
```

#### Formatting
```bash
black src/ tests/
```

#### Linting
```bash
ruff check src/ tests/
ruff check --fix src/ tests/
```