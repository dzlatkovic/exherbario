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

4. Set the environment variables in a `.env`file . The required environment variables are:
   - `DB_HOST`: the database host URL.
   - `DB_HOSTNAME`: the hostname of the database server.
   - `DB_PORT`: the port number of the database server.
   - `DB_USER`: the username to access the database. 
   - `DB_PASSWORD`: the password to access the database. 
   - `DB_NAME`: the name of the database. 
   - `USER_SECRET`: the secret key used for JSON Web Token (JWT) encoding. 
   - `ALGORITHM`: the algorithm used for JWT encoding. 
   
5. Start MySQL server and execute all commands in `init_db/init_db.sql`

6. Run the application with 

   ```
   python -m uvicorn app.main:app --reload --reload-delay 5 --host localhost --port 8000
   ```

7. The API will be available at http://localhost:8000/

### User Guide

TODO

## Meta

Dragan Zlatković – [dragan.zlatkovic@gmail.com](mailto:dragan.zlatkovic@gmail.com)