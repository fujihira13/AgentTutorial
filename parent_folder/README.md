# Multi-tool Agent

This project is a multi-tool agent built using the Google ADK, following the [Quickstart guide](https://google.github.io/adk-docs/get-started/quickstart/).

## Setup

1.  Create a virtual environment:
    ```bash
    python -m venv .venv
    ```

2.  Activate the virtual environment:
    - Windows: `.venv\Scripts\activate`
    - Mac/Linux: `source .venv/bin/activate`

3.  Install dependencies:
    ```bash
    pip install google-adk
    ```

4.  Configure Environment Variables:
    - Copy `.env.example` to `.env`:
        - Windows: `copy .env.example .env`
        - Mac/Linux: `cp .env.example .env`
    - Open `.env` and add your Gemni API key to `GOOGLE_API_KEY`.

## Running the Agent

You can run the agent using the ADK CLI.

To start the web UI:
```bash
adk web
# OR specifying the path
adk web multi_tool_agent
```

To run in terminal:
```bash
adk run multi_tool_agent
```

## Example Prompts

- What is the weather in New York?
- What is the time in New York?
- What is the weather in Paris? (Note: This agent only knows New York in the mock implementation)
