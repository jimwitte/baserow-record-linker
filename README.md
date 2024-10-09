# Record Linking App

This project automates the linking of related records between source and target tables in Baserow using a custom configuration. The app loads the configuration from a YAML file (`config.yml`) and uses the Baserow API to link records based on specified match fields.


## Features

- Links related records between source and target tables in Baserow.
- Supports multiple record linker configurations via `config.yml`.
- Configurable using environment variables and YAML.
- Error handling and logging for tracking the linking process.

## Run via docker-compose

1. clone this repo
2. copy env-sample to .env, edit with your values
3. modify config.yml to configure linking of related records
4. docker compose up

