# Chatbot_RH

## Requirements

- Python `>=3.12,<3.14`
- `uv` installed

Install uv (Powershell):

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup (first time)

Create a virtual environment and install dependencies:

```bash
uv venv
uv sync --all-groups OR uv sync -dev
```

If you only want production dependencies:

```bash
uv sync
```

## Add / Update dependencies

Add a runtime dependency:

```bash
uv add <package>
```

Add a dev dependency:

```bash
uv add --dev <package>
```
## Run Application

```bash
streamlit run src\ui\streamlit_app.py```


