# Record Linking App

This project automates the linking of related records between source and target tables in Baserow, based on a customizable configuration table. Configurations are loaded from a designated Baserow table specified in the `.env` file.

## Use Case Example

Imagine managing multiple datasets where certain records, like customer details, are shared across tables. This app allows you to link related customer records between a "Source" and "Target" table in Baserow by defining match criteria, such as email address or phone number. It saves time and ensures consistency by automatically identifying and linking related records across tables.
Can be triggered manually or set up as a cron job.

## Features

- Links related records between source and target tables in Baserow.
- Configurable via environment variables.
- Error handling and logging for tracking the linking process.
- Simplified configuration management using a dedicated Baserow table.

## Run via Docker Compose

1. Clone this repository.
2. Copy `env-sample` to `.env` and edit it with your values, ensuring you specify the table ID of the configuration table.
3. Run `docker-compose up`.

## Configuration Table Schema

The configurations for linking records are stored in a Baserow table. Each row in this table defines a specific linking configuration.

| Field Name                   | Field Type | Description                                      |
|------------------------------|------------|--------------------------------------------------|
| Link Config Name             | string     | Stores the name of the link configuration.       |
| Source Table ID              | string     | Contains the ID of the source table.             |
| Active                       | boolean    | Indicates if the configuration is active.        |
| Target Table ID              | string     | Holds the ID of the target table.                |
| Source Table Match Field     | string     | Specifies the matching field in the source table.|
| Target Table Match Field     | string     | Specifies the matching field in the target table.|
| Source Table Reference Field | string     | Identifies the reference field in the source table.|

### Environment Variables
- **CONFIG_TABLE_ID**: The ID of the Baserow table storing configuration data. This is defined in the `.env` file.
  