# Love Live! TCG Scraper

A command-line tool to scrape card data from the official Love Live! Official Card Game website. It provides an interactive interface to select expansions, scrape data concurrently, and save it to a JSON file.

## Features

- **Interactive Interface**: User-friendly prompts for selecting expansions and configuring output.
- **Concurrent Scraping**: Fetches data for multiple expansions and cards simultaneously for high speed.
- **Configurable Rate Limiting**: Respects the server by allowing you to set a global request rate limit.
- **Dual Progress Bars**: Visual feedback on the scraping progress for both overall expansions and cards within each expansion.
- **Smart File Handling**: Choose to overwrite your data file or intelligently merge new data with existing records.
- **Advanced Configuration**: Use command-line flags for advanced settings like timeouts and logging levels.
- **File-based Logging**: All diagnostic information is saved to `scraper.log`, keeping the console clean for the user interface.

## Setup and Installation (Manual)

These instructions are for users who prefer to run the script directly with Python instead of using a pre-built executable. This guide uses `uv`, a fast Python package installer from Astral.

### 1. Install `uv`

If you don't have `uv` installed, open your terminal and run the appropriate command for your operating system:

**macOS / Linux:**
```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. Clone the Repository

Clone this project to your local machine.

```shell
git clone git@github.com:ahuei123456/lltcg-prototype.git
cd lltcg-prototype
```

### 3. Create Virtual Environment & Install Dependencies

`uv` can create a virtual environment and install your project's dependencies directly from `pyproject.toml`.

```shell
uv venv
```

Next, activate the environment:

**macOS / Linux:**
```shell
source .venv/bin/activate
```

**Windows (Command Prompt):**
```shell
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

Finally, install the dependencies into the active environment:
```shell
uv pip install -r requirements.txt
```

## Usage

With your virtual environment activated, you can run the scraper:

```shell
python main.py
```

The program will guide you through the scraping process with interactive prompts.

### Command-Line Arguments

You can also use command-line arguments to customize the scraper's behavior:

-   `--rate-limit`: Set the maximum number of requests per second (e.g., `--rate-limit 5`). Default is 10.
-   `--timeout`: Set the timeout for network requests in seconds (e.g., `--timeout 60`). Default is 30.

**Example:**
```shell
python main.py --rate-limit 3 --timeout 45
```
