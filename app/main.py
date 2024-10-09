import os
import logging
from dotenv import load_dotenv
import yaml
from baserowapi import Baserow, Filter

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Set the log level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
)
logger = logging.getLogger(__name__)  # Create a logger object

# Load configuration for record linkers
def load_record_linkers():
    config_file = "config.yml"
    try:
        with open(config_file, "r") as file:
            logger.info(f"Loading configuration from {config_file}")
            yaml_content = yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Configuration file {config_file} not found.")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise

    # Extract the list of record linkers
    record_linkers = yaml_content.get("record_linker_configs", [])
    logger.info(f"Loaded {len(record_linkers)} record linkers from configuration.")

    return record_linkers

# Load environment variables from .env file
def load_env_variables():
    load_dotenv()
    baserow_url = os.getenv("BASEROW_URL")
    baserow_api_token = os.getenv("BASEROW_API_TOKEN")

    # Check if the environment variables were successfully loaded
    if not baserow_url or not baserow_api_token:
        logger.error("BASEROW_URL or BASEROW_API_TOKEN not set in .env file.")
        raise ValueError("BASEROW_URL or BASEROW_API_TOKEN not set in .env file.")
    else:
        logger.info("Environment variables loaded successfully.")

    return baserow_url, baserow_api_token

# Create an index from a Baserow table based on a specified field
def create_index_from_table(baserow_client, table_id, field_name):
    """
    Creates an index from a table based on a specified field, with logging and error handling.

    :param baserow_client: The Baserow client object.
    :param table_id: The ID of the Baserow table.
    :param field_name: The name of the field to be used for indexing.
    :return: A dictionary representing the index where the key is the cleaned field value.
    """

    logger = logging.getLogger(__name__)

    try:
        # Retrieve the table instance
        table = baserow_client.get_table(table_id)
    except Exception as e:
        logger.error(f"Failed to retrieve table with ID {table_id}. Error: {e}")
        raise

    try:
        # Fetch all rows from the table
        rows = table.get_rows()
    except Exception as e:
        logger.error(f"Failed to retrieve rows for table ID {table_id}. Error: {e}")
        raise

    index = {}

    for row in rows:
        try:
            # Get the field value for the specified field name
            field_value = row[field_name]

            if field_value:
                # Clean the field value: trim and convert to lower case
                clean_value = field_value.strip().lower()

                # Log the processed field value
                logger.debug(
                    f"Processed field '{field_name}' value: '{clean_value}' from row: {row.id}"
                )

                # Add the cleaned value to the index (using the row ID or the full row as value)
                if clean_value in index:
                    logger.warning(
                        f"Duplicate index key found for value '{clean_value}' in row {row.id}"
                    )
                index[clean_value] = row
            else:
                logger.warning(f"Missing field '{field_name}' in row {row.id}")

        except KeyError:
            logger.error(f"Field '{field_name}' not found in row {row.id}")
            continue  # Skip this row and move to the next one
        except Exception as e:
            logger.error(f"Unexpected error processing row {row.id}. Error: {e}")
            raise

    logger.info(f"Index creation completed for table ID: {table_id}")
    return index

# Filter rows from a Baserow table based on a provided filter object
def filter_baserow_table(baserow_client: Baserow, table_id: int, baserow_filters: list):
    """
    Filters rows from a Baserow table based on a provided filter object.

    :param baserow_client: An instance of the Baserow client to interact with the API.
    :type baserow_client: Baserow
    :param table_id: The ID of the table to filter.
    :type table_id: int
    :param baserow_filter: The filter object used to filter rows.
                          It should follow the Baserow API filter structure.
    :type baserow_filter: dict
    :return: A list of filtered rows if successful, None otherwise.
    :rtype: list | None

    :raises ValueError: If the table_id is not valid or filter format is incorrect.
    :raises Exception: For other generic errors.

    Example:

    >>> baserow_client = Baserow(api_token="your_api_token")
    >>> table_id = 123
    >>> filter = {"field_name": "value"}
    >>> rows = filter_baserow_table(baserow_client, table_id, filter)
    """
    try:
        # Retrieve table object
        table = baserow_client.get_table(table_id)

        if table is None:
            raise ValueError(f"Table with ID {table_id} not found.")

        # Apply the filter and fetch rows
        filtered_rows = table.get_rows(
            filters=baserow_filters
        )

        if filtered_rows:
            logging.info("Successfully retrieved %d filtered rows.", len(filtered_rows))
            return filtered_rows
        else:
            logging.warning("No rows matched the filter criteria.")
            return []

    except ValueError as ve:
        logging.error("Value error occurred: %s", ve)
        raise
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        raise

# Link related records between source and target tables
def link_related_records(baserow_client: Baserow, record_linker_configs: list):
    """
    Links related records between source and target tables based on provided configurations.

    This function matches rows between a source and a target table using a matching field
    and updates the reference field in the source table with the primary key of the target row.

    :param baserow_client: An instance of the Baserow client to interact with the API.
    :type baserow_client: Baserow
    :param record_linker_configs: A list of dictionaries containing configuration for linking records.
                                  Each dictionary should have the following keys:
                                  - "source_table_id" (int): ID of the source table.
                                  - "target_table_id" (int): ID of the target table.
                                  - "source_table_match_field" (str): The field name in the source table used to match.
                                  - "target_table_match_field" (str): The field name in the target table used to match.
                                  - "target_table_primary_key_field" (str): The primary key field name in the target table.
                                  - "source_table_reference_field" (str): The reference field in the source table to be updated.
    :type record_linker_configs: list
    :raises ValueError: If any required config fields are missing or invalid.
    :raises Exception: For any other unexpected errors during the linking process.
    :return: None
    :rtype: None
    """
    try:
        for record_linker_config in record_linker_configs:
            # Validate configuration fields
            required_fields = [
                "source_table_id",
                "target_table_id",
                "source_table_match_field",
                "target_table_match_field",
                "target_table_primary_key_field",
                "source_table_reference_field",
            ]

            for field in required_fields:
                if field not in record_linker_config:
                    raise ValueError(f"Missing required config field: {field}")

            # Extract configuration details
            source_table_id = record_linker_config["source_table_id"]
            target_table_id = record_linker_config["target_table_id"]
            source_table_match_field = record_linker_config["source_table_match_field"]
            target_table_match_field = record_linker_config["target_table_match_field"]
            target_table_primary_key_field = record_linker_config[
                "target_table_primary_key_field"
            ]
            source_table_reference_field = record_linker_config[
                "source_table_reference_field"
            ]

            logging.info(
                "Linking records between source table %s and target table %s",
                source_table_id,
                target_table_id,
            )

            # Get rows from the source table with empty reference fields
            empty_reference_filter = Filter(source_table_reference_field, "", "empty")
            source_table_rows = filter_baserow_table(
                baserow_client, source_table_id, [empty_reference_filter]
            )

            if not source_table_rows:
                logging.warning(
                    "No rows with empty reference fields found in source table %s",
                    source_table_id,
                )
                continue

            # Create an index for the target table using the match field
            target_table_index = create_index_from_table(
                baserow_client, target_table_id, target_table_match_field
            )

            # Link related records
            for source_row in source_table_rows:
                match_field_value = source_row[source_table_match_field].strip().lower()

                if match_field_value in target_table_index:
                    target_row = target_table_index[match_field_value]

                    # Update the reference field in the source row
                    source_row.update(
                        {
                            source_table_reference_field: target_row[
                                target_table_primary_key_field
                            ]
                        }
                    )
                    logging.info(
                        "Linked source row %s to target row %s",
                        source_row.id,
                        target_row.id,
                    )
                else:
                    logging.warning(
                        "No match found for source row %s (Match field: %s)",
                        source_row.id,
                        match_field_value,
                    )

    except ValueError as ve:
        logging.error("Value error occurred: %s", ve)
        raise
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        raise


if __name__ == "__main__":
    try:
        # Load record linkers configuration
        record_linkers = load_record_linkers()

        # Load environment variables
        baserow_url, baserow_api_token = load_env_variables()

        # Create a Baserow client
        baserow = Baserow(baserow_url, baserow_api_token)

        # Link related records
        link_related_records(baserow, record_linkers)

    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
