# Herbarium Research and Botanical Archive Resource (HERBAR)

A [herbarium](https://en.wikipedia.org/wiki/Herbarium) is a collection of dried, documented plant specimens that provides information on the diversity, evolution, and distribution of plant species in a specific region. Herbariums are important resources for fields such as botany, ecology, and conservation. HERBAR is an online platform that offers significant advantages over non-digital herbariums, including faster and easier access to the data, automated statistical analysis, increased [public accessibility](https://en.wikipedia.org/wiki/Virtual_herbarium) to the collection, and the ability for researchers to access the Herbarium from the field through their mobile devices

## Usage

This application is built using [FastAPI](https://fastapi.tiangolo.com/), a modern and fast Python web framework. It also uses a [MySQL](https://www.mysql.com/) database and follows the [controller-service-model](https://en.wikipedia.org/wiki/Multitier_architecture#Three-tier_architecture) architecture pattern.

### Prerequisites

Before you start, make sure you have the following installed:

- Python 3.6 or later
- Pip (for installing Python packages)
- MySQL (for the database)

### Setup

1. Clone the repository and navigate to the project directory

2. Create a virtual environment with `python -m venv venv` and activate it with `source venv/bin/activate` on Linux/macOS or `.\venv\Scripts\activate` on Windows.

3. Install the required packages with `pip install -r requirements.txt`

4. Environment Variables

   The following environment variables are required to run the application:

   - `DB_HOST`: the host URL of the database server.
   - `DB_HOSTNAME`: the hostname of the database server.
   - `DB_PORT`: the port number of the database server.
   - `DB_USER`: the username used to access the database.
   - `DB_PASSWORD`: the password used to access the database.
   - `DB_NAME`: the name of the main database.
   - `USER_SECRET`: the secret key used for JSON Web Token (JWT) encoding.
   - `ALGORITHM`: the algorithm used for JWT encoding.
   - `TOKEN_DURATION`: the expiration time of the JWT token.
   - `LATITUDE` and `LONGITUDE`: GPS coordinates used in distance calculations (e.g. University building).

   The following environment variables have been added to support running tests on a separate test database:

   - `DB_NAME_TEST`: the name of the test database.
   - `USE_TEST_DB`: set to `True` to use the test database, `False` otherwise.

   You can set these environment variables in a `.env` file in the root directory of the project. An example `.env` file is provided in the repository as `.env-template`.

5. Start MySQL server and execute all commands in `init_db/init_db.sql`

6. Run the application with 

   ```
   python -m uvicorn app.main:app --reload --reload-delay 5 --host localhost --port 8000
   ```

7. The API will be available at http://localhost:8000/

8. To test the app, set the `USE_TEST_DB` parameter in the `.env` file to `True`, run `pytest` in the terminal to execute any test files in the `tests/` directories, then set `USE_TEST_DB` back to `False` to use the main database again. This ensures that tests don't modify the main database.

### Documentation

The `docs/` folder contains a project proposal, an EER scheme image, and a sample MySQL database that can be used to test the app. Simply import the database into your local MySQL server and update the `.env` file to use the correct database name, username, and password. Note that the sample database contains a superuser with email "user@example.com" and password "string". You can use this superuser to access the protected routes in the app.

## Meta

Dragan Zlatković – [dragan.zlatkovic@gmail.com](mailto:dragan.zlatkovic@gmail.com)