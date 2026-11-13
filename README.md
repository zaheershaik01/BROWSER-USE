# Scripted Browser Agent

This folder contains a Python browser agent built with the
[browser-use](https://github.com/browser-use/browser-use) framework. The agent
uses Google Gemini to search an Indian e-commerce site for laptops matching
the criteria in `bu_agent.py`, inspect up to four product pages, and report up
to three matches.

The script does not log in, add products to a cart, or make purchases. It saves
the final response to `laptop_result.md`, replacing that file each time it
runs.

## Requirements

- Python
- A Google Gemini API key
- Internet access

## Setup

Open PowerShell in this folder and create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the Python dependencies and a browser for Playwright:

```powershell
python -m pip install browser-use google-genai
playwright install
```

Create a `.env` file in this folder and add your API key:

```text
GOOGLE_API_KEY=your_api_key_here
```

The script also accepts `GEMINI_API_KEY` from the `.env` file. Do not commit or
share your API key.

## Run

```powershell
python bu_agent.py
```

The script first checks a list of Gemini models and selects the fastest one
that responds; if a second model responds, it is configured as a fallback.
These checks make API requests. Then a visible browser window opens and the
agent begins the shopping search. The final result is printed in the terminal
and written to `laptop_result.md`.

## Customize the task

Edit the `TASK` text in `bu_agent.py` to change the search instructions,
websites, or product criteria. The agent is configured for at most 30 steps;
the model-check candidate list and agent options are also defined in that
file.
