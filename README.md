# NextDNS Local API and Dashboard


This project fetches, stores, and visualizes logs from the NextDNS API. It includes a Python-based API for querying logs with filtering options (e.g., excluding domains), stores data in a local database, and integrates with Grafana for DNS activity visualization. Docker is used for containerization.



## Prerequisites

- Docker
- Docker Compose
- Grafana with the JSON Datasource Plugin


## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/NextDNS-Local-API.git
   cd NextDNS-Local-API

2. Set up the .env file in the /config directory with the following variables:

   ```bash
   API_KEY=<your_nextdns_api_key>
   PROFILE_ID=<your_nextdns_profile_id>
   LOCAL_API_KEY=<your_local_api_key>

3. Ensure Grafana is installed, and the JSON Datasource Plugin is configured.


##  Using the API
The API requires Basic Authentication with the following:

Username: admin
Password: The value of LOCAL_API_KEY from the .env file.

## Example API Endpoints
Get All Logs: GET /logs
Exclude Domains: GET /logs?exclude=example.com&exclude=test.com

## Visualizing in Grafana
1. Add the local API as a JSON datasource in Grafana.
2. Create panels to visualize DNS activity (queries over time, top domains, etc.).


## Running the Project
This will:

Fetch logs from NextDNS and store them in a local database.
Expose the local API at http://<host>:5000/logs.
Allow Grafana to visualize the stored data.

To start the solution:

```bash
docker-compose up --build