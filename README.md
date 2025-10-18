# shaberookie - 喋rookie
AI-powered assistant that adapts its Japanese conversation level to match the learner, helping beginners build fluency and confidence through natural dialogue.

## Prerequisites
- Python 3.10 or newer installed on your system.
- Access credentials for any protected services (configure via environment variables).
- (Optional) [Poetry](https://python-poetry.org/docs/#installation) if you prefer Poetry-managed environments.

## 1. Set up your Python environment

### Create a virtual environment
**PowerShell**
```powershell
python -m venv .venv
```

**Bash**
```bash
python3 -m venv .venv
```

### Activate the virtual environment
**PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**Bash**
```bash
source .venv/bin/activate
```

> Deactivate at any time with `deactivate`.

### Install project dependencies
Run the commands below inside the activated environment.

**PowerShell**
```powershell
python -m pip install --upgrade pip
pip install -e .
```

**Bash**
```bash
python -m pip install --upgrade pip
pip install -e .
```

If you need optional Redis cache support, append `.[cache]` to the install command.

#### Optional: manage dependencies with Poetry
Poetry can create and maintain the virtual environment for you.

**PowerShell**
```powershell
pip install --user poetry
poetry install
```

**Bash**
```bash
python -m pip install --user poetry
poetry install
```

Afterwards, spawn a shell in the Poetry-managed environment with `poetry shell`.

## 2. Configure environment variables
Copy the provided environment template to `.env` and fill in the required values before running the application.

**PowerShell**
```powershell
Copy-Item .env.example .env
```

**Bash**
```bash
cp .env.example .env
```

## 3. Running the application

### Command-line chat client
Launch the interactive console chat (replace `<RENSHUU_USER_ID>` with an actual identifier).

**PowerShell**
```powershell
python -m shaberookie.main console --help
python -m shaberookie.main console chat <RENSHUU_USER_ID>
```

**Bash**
```bash
python -m shaberookie.main console --help
python -m shaberookie.main console chat <RENSHUU_USER_ID>
```

Use `--help` to discover additional options exposed by the Typer CLI.

### Gradio web interface
Start the Gradio UI on the configured host and port. Omit `--host`/`--port` to fall back to settings defined in your configuration.

**PowerShell**
```powershell
python -m shaberookie.main gradio --host 127.0.0.1 --port 7860
```

**Bash**
```bash
python -m shaberookie.main gradio --host 127.0.0.1 --port 7860
```

Add `--share` if you want to generate a temporary public Gradio link.

## 4. Running tests
Execute the automated test suite from the project root.

**PowerShell**
```powershell
pytest
```

**Bash**
```bash
pytest
```

For coverage details:

**PowerShell**
```powershell
coverage run -m pytest
coverage report
```

**Bash**
```bash
coverage run -m pytest
coverage report
```

## 5. Troubleshooting
- Ensure your virtual environment is active before installing dependencies or running commands.
- Regenerate dependencies with `pip install --force-reinstall -e .` if imports are missing.
- Review `--help` output on any CLI command for additional flags and usage tips.

Happy studying and 頑張ってください!
