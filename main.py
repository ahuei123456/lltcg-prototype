import argparse
import asyncio
import json
import logging
import os

import httpx
from aiolimiter import AsyncLimiter
from InquirerPy import prompt_async
from InquirerPy.validator import EmptyInputValidator
from tqdm.asyncio import tqdm

from scrape.scrape import get_expansion_codes, scrape_expansion

logger = logging.getLogger(__name__)


class RateLimitedTransport(httpx.AsyncHTTPTransport):
    """
    A custom httpx transport that uses an aiolimiter to rate-limit requests.
    """

    def __init__(self, rate_limit_per_second: int, **kwargs):
        self.limiter = AsyncLimiter(rate_limit_per_second, 1)
        super().__init__(**kwargs)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        async with self.limiter:
            return await super().handle_async_request(request)


def get_expansion_select_question(expansions):
    """Builds a prompt for selecting expansions to scrape."""
    choices = [
        {"name": f"{exp['code']}: {exp['name']}", "value": exp["code"]}
        for exp in expansions
    ]
    question = {
        "type": "checkbox",
        "message": "Select expansions to scrape",
        "name": "selected_expansions",
        "choices": choices,
        "long_instruction": "Use arrow keys to navigate, <space> to select, and <enter> to confirm.",
        "validate": EmptyInputValidator("You must select at least one expansion."),
    }

    return question


def get_filename_question():
    """Builds a prompt for entering the output filename."""
    question = {
        "type": "input",
        "message": "Enter output filename",
        "name": "filename",
        "default": "card_data.json",
        "validate": EmptyInputValidator("Filename cannot be empty."),
    }
    return question


def get_confirmation_question():
    """Builds a confirmation prompt using radio buttons."""
    question = {
        "type": "list",
        "message": "Do you want to continue with scraping?",
        "name": "confirm",
        "choices": [
            {"name": "Yes", "value": True},
            {"name": "No", "value": False},
        ],
        "long_instruction": "Use arrow keys to navigate, and <enter> to confirm.",
        "default": True,
    }
    return question


def get_file_exists_question():
    """Builds a prompt for when the output file already exists."""
    question = {
        "type": "list",
        "message": "The file already exists. What would you like to do?",
        "name": "file_action",
        "choices": [
            {"name": "Overwrite the file", "value": "overwrite"},
            {"name": "Merge new data with existing data", "value": "merge"},
            {"name": "Quit", "value": "quit"},
        ],
        "default": "overwrite",
    }
    return question


async def main(rate_limit: int, timeout: float):
    """Main async function to orchestrate the scraping process."""
    transport = RateLimitedTransport(rate_limit_per_second=rate_limit)
    # httpx.AsyncClient is used for making async requests
    async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
        all_expansions = await get_expansion_codes(client)

        if not all_expansions:
            logger.warning("No expansion codes found. Exiting.")
            return

        # --- User Input Stage 1: Selection and Filename ---
        initial_questions = [
            get_expansion_select_question(all_expansions),
            get_filename_question(),
        ]
        prompt_result = await prompt_async(initial_questions)
        if not prompt_result:
            logger.info("Operation cancelled by user. Exiting.")
            return

        selected_codes = prompt_result.get("selected_expansions", [])
        output_file = prompt_result.get("filename", "card_data.json")

        # --- User Input Stage 2: File Exists Action ---
        file_action = "overwrite"  # Default if file doesn't exist
        if os.path.exists(output_file):
            action_result = await prompt_async([get_file_exists_question()])
            if not action_result:
                logger.info("Operation cancelled by user. Exiting.")
                return

            file_action = action_result.get("file_action")
            if file_action == "quit":
                logger.info("Operation cancelled by user. Exiting.")
                return

        # --- User Input Stage 3: Final Confirmation ---
        confirm_result = await prompt_async([get_confirmation_question()])
        if not confirm_result or not confirm_result.get("confirm"):
            logger.info("Operation cancelled by user. Exiting.")
            return

        # --- Scraping ---
        expansion_tasks = [scrape_expansion(client, code) for code in selected_codes]
        print()  # Add a newline for better formatting before the progress bar
        card_lists_results = await tqdm.gather(
            *expansion_tasks, desc="Scraping Expansions"
        )

        # Create a dictionary mapping expansion codes to their card lists.
        # asyncio.gather preserves the order, so we can safely zip the results.
        newly_scraped_data_map = dict(zip(selected_codes, card_lists_results))

        # --- Data Merging and Saving ---
        final_data_map = {}
        if file_action == "merge":
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

                if not isinstance(existing_data, dict):
                    logger.warning(
                        "Existing file %s does not contain a dictionary. Overwriting.",
                        output_file,
                    )
                    final_data_map = newly_scraped_data_map
                else:
                    # Start with the existing data, then update with newly scraped expansions
                    final_data_map = existing_data
                    final_data_map.update(newly_scraped_data_map)

            except FileNotFoundError:
                logger.info("File %s not found. Creating a new file.", output_file)
                final_data_map = newly_scraped_data_map
            except json.JSONDecodeError:
                logger.warning(
                    "Could not parse JSON from %s. Overwriting file.", output_file
                )
                final_data_map = newly_scraped_data_map
        else:  # Overwrite
            final_data_map = newly_scraped_data_map

        # Save the data
        try:
            # Calculate total number of cards for the log message
            total_cards = sum(len(cards) for cards in final_data_map.values())
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(final_data_map, f, ensure_ascii=False, indent=4)
            logger.info(
                "Scraping complete. Data for %s cards saved to %s",
                total_cards,
                output_file,
            )
        except IOError as e:
            logger.error("Failed to write to file %s: %s", output_file, e)


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape card data from the Love Live! TCG official website."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=argparse.SUPPRESS,  # Hide this from the standard help message
    )
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=10,
        help="Maximum requests per second to the server. Default: 10",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for network requests. Default: 30.0",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s:%(levelname)s:%(name)s: %(message)s",
        filename="scraper.log",
        filemode="w",
    )
    asyncio.run(main(rate_limit=args.rate_limit, timeout=args.timeout))
