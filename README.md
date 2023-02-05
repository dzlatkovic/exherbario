# Herbarium Research and Botanical Archive Resource (HERBAR)

A herbarium is a collection of dried, documented plant specimens. After collecting specimens in the field, the material is dried and then arranged in herbarium sheets. Each sheet is labeled with relevant information about the specimen, such as its scientific name and collection location. The sheets are then stored in boxes, and the entire collection provides information on the diversity, evolution, and distribution of the plant species in a specific region.

Herbariums are important resources for fields such as botany, ecology, and conservation. Having an online catalog offers significant advantages over non-digital herbariums, including faster and easier access to the data, automated statistical analysis, increased public accessibility to the collection, and the ability for researchers to access the Herbarium from the field through their mobile devices.

## Usage

This application is built using [FastAPI](https://fastapi.tiangolo.com/), a modern and fast Python web framework. It also uses a [MySQL](https://www.mysql.com/) database and follows the [controller-service-model](https://en.wikipedia.org/wiki/Multitier_architecture#Three-tier_architecture) architecture pattern.

### Prerequisites

Before you start, make sure you have the following installed:

- Python 3.10 or later
- Pip (for installing Python packages)
- MySQL (for the database)

### Setup

1. Clone the repository and navigate to the project directory
2. Create a virtual environment with `python -m venv venv` and activate it with `source venv/bin/activate` on Linux/macOS or `.\venv\Scripts\activate` on Windows.
3. Install the required packages with `pip install -r requirements.txt`
4. Set the environment variables in a `.env`file . The required environment variables are:
   - `DB_USER`: the MySQL database username
   - `DB_PASSWORD`: the MySQL database password
   - `DB_HOST`: the hostname or IP address of the MySQL server
   - `DB_NAME`: the name of the MySQL database
5. Run the database migrations with `alembic upgrade head`.
6. Run the application with `uvicorn app.main:app --reload`.
7. The API will be available at http://localhost:8000/

### User Guide

TODO

## Meta

Dragan Zlatković – [dragan.zlatkovic@gmail.com](mailto:dragan.zlatkovic@gmail.com)