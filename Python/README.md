# Python Scripts for AppMagician Pipeline

This folder contains Python scripts that were extracted from the Jenkins pipeline to improve maintainability and code organization.

## Scripts

### `generate_prompts.py`
- **Purpose**: Generates app specifications and prompts using ChatGPT or DeepSeek APIs
- **Usage**: Called by Jenkins pipeline to create app specifications based on user input
- **Environment Variables**:
  - `LLM_PROVIDER`: 'chatgpt' or 'deepseek'
  - `OPENAI_MODEL`: OpenAI model name (when using ChatGPT)
  - `DEEPSEEK_MODEL`: DeepSeek model name (when using DeepSeek)
  - `OPENAI_API_KEY`: API key for OpenAI (when using ChatGPT)
  - `DEEPSEEK_API_KEY`: API key for DeepSeek (when using DeepSeek)
  - `APP_IDEA`: App idea/prompt hint
  - `BUNDLE_ID`: iOS bundle identifier
  - `LOCALES`: Comma-separated locale codes
  - `DEFAULT_LOCALE`: Default locale
  - `TEST_MODE`: Set to '1' for testing without API keys (generates mock response)
  - `DEBUG_MODE`: Set to '1' to enable debug output

### `cursor_fix.py`
- **Purpose**: Automatically fixes Flutter analyze and test issues using cursor-agent
- **Usage**: Called when previous pipeline steps introduce issues
- **Environment Variables**:
  - `STEP`: Current step number for context
  - `CURSOR_API_KEY`: API key for cursor-agent
  - `CURSOR_CI`: Set to '1' for CI mode
  - `CURSOR_NO_INTERACTIVE`: Set to '1' for non-interactive mode

### `cursor_run.py`
- **Purpose**: Executes cursor-agent with prompts and handles output with sentinel detection
- **Usage**: Runs cursor-agent for each step in the pipeline
- **Environment Variables**:
  - `CURSOR_API_KEY`: API key for cursor-agent
  - `CURSOR_CI`: Set to '1' for CI mode
  - `CURSOR_NO_INTERACTIVE`: Set to '1' for non-interactive mode

### `build_fix.py`
- **Purpose**: Automatically fixes Flutter build issues using cursor-agent
- **Usage**: Called when iOS build fails to apply fixes
- **Environment Variables**:
  - `CURSOR_API_KEY`: API key for cursor-agent

## Requirements

- Python 3.6+
- cursor-agent CLI tool
- Required environment variables (see individual script documentation)

## Usage in Jenkins

The scripts are called from the Jenkins pipeline using:
```bash
python3 "${WORKSPACE}/Python/script_name.py"
```

Where `${WORKSPACE}` is the Jenkins workspace directory containing both the Jenkinsfile and Python folder.
