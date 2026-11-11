# Blood Donor Finder
# Blood Donor Finder

A web application to find blood donors quickly in an emergency.

## Problem Statement
In emergencies, families waste time searching for blood donors through calls and
WhatsApp forwards. There is no single place to find donors by blood group and city.

## Features
- Donor registration with phone number validation
- View all donors
- Search by blood group and city
- Eligibility check (donor is eligible 90 days after the last donation)
- Admin panel to edit and delete donors, protected by login

## Technologies
Python, Flask, SQLite, HTML, Git and GitHub

## How to Run
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate`
4. Install Flask: `pip install -r requirements.txt`
5. Run: `python app.py`
6. Open http://127.0.0.1:5000

## Admin Login
Open `/admin` and enter the admin password set in `app.py`.

## Git Workflow
Every feature was built on its own branch (database, register, search,
eligibility, admin, readme), merged into `main`, and then deleted.

## Future Scope
SMS alerts, map view, hashed passwords, online deployment

## Author
Aditya Singh (ID 2581195)
Vishal Singh (ID 2581360)
