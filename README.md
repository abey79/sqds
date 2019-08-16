# sqds

## Intro

_To be completed._

## Installation Instructions

_WIP!_

 - Install PostgreSQL
 - Checkout repository
 - `python -m venv .venv`
 - `pip install -r requirements.txt`
 - create .env file
 
Example .env file:
 
```sh
# Make up a long, random secret key
export DJANGO_SECRET_KEY='..............'

# .local is pre-configured for a local PostgreSQL database. You just need to set
# the password. You can further customize the database setting by setting other
# variables. See sqdssite/settings/local.py for details.
export DJANGO_DB_PASSWORD='<my password>'

# Note: export keyword are not necessary (ignored by python_dotenv), they are
# just there in case one want to source the file in bash
 ```
