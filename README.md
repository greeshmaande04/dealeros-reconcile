# DealerOS reconciliation

Django + Django REST Framework + SQLite backend with a plain HTML table page.

## How to run (from a clean clone)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py import_data
python manage.py runserver

Open http://127.0.0.1:8000/ for the table.
Tests (in backend): pytest

## What I built
A CSV importer that keeps dirty rows, a pure comparison function, one API endpoint (org is required), a plain table page, and tests.

## What I deliberately did not build
Auth, pagination, Docker, React, styling.

## How I worked with the agent
I used Claude as my AI agent. I first wrote the importer and services myself with help,
then asked Claude to review my code against the assignment. It found that my code treated
a blank B value as 0, did not use the required reason names, and had no required org check.
I asked it to fix these one file at a time. I ran the importer and checked that it printed
A: 120 read, 120 saved and B: 121 read, 121 saved, ran it twice to check there were no
duplicates, ran pytest (20 passed), and opened the API for ORG-A and ORG-B in my browser
to check that no other org's locations appeared.

## Three answers
a. Claude first told me to paste the table page code into views.py, then changed to a separate page.py file, but my config/urls.py still imported table_page from reconcile.views. The server crashed with "ImportError: cannot import name 'table_page'". I noticed it from the error in the terminal, and I fixed it by changing the import in config/urls.py to reconcile.page.
b. I am least confident about the cross-org row (REC-1077) and about how I treat VOIDED records. For the cross-org row I only show an org its own location and hide the other org's location, so only the org that owns System A's record sees the row. ORG-B does not see it at all. I am not sure that is the best choice. For VOIDED I decided a voided record should not exist in B, so a B entry for it is flagged. I would check the VOIDED rows in system_a.csv and system_b.csv by hand to confirm that is right.
c. I would add a test for the importer itself, checking the row counts and that running it twice does not create duplicates. Right now I only checked this by hand in the terminal. I would do it first because losing or duplicating rows would break every comparison, and a test would catch that if someone changed the importer later.