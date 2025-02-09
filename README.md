![Build Status](https://img.shields.io/github/actions/workflow/status/MaBoNi/NextDNS-Optimized-Analytics/docker-publish.yml?branch=main&style=for-the-badge)
![License](https://img.shields.io/github/license/MaBoNi/NextDNS-Optimized-Analytics?style=for-the-badge)
![Repo Size](https://img.shields.io/github/repo-size/MaBoNi/NextDNS-Optimized-Analytics?style=for-the-badge)

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-nextdns--optimized--analytics--frontend-blue?logo=docker&style=for-the-badge)](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-frontend)
[![Docker Pulls](https://img.shields.io/docker/pulls/maboni82/nextdns-optimized-analytics-frontend?style=for-the-badge)](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-frontend)

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-nextdns--optimized--analytics--backend-blue?logo=docker&style=for-the-badge)](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-backend)
[![Docker Pulls](https://img.shields.io/docker/pulls/maboni82/nextdns-optimized-analytics-backend?style=for-the-badge)](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-backend)



A Dockerized solution which fetches, stores, and visualizes logs from the NextDNS API. It includes a Python-based API for querying logs with filtering options (e.g., excluding domains), stores data in a local database, and integrates with Grafana for DNS activity visualization. Docker is used for containerization.

## Features
- **Local sync of NextDNS logs** – Fetch logs and ensure they are kept locally for better analytics
- **Visualization** – Enable Grafana dashboard for better visualisation.
- **Data Filtering** – Enable better data filtering than Next DNS standard UI provides
- **Dockerized** – Quick deployment of backend and frontend via Docker.

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [NextDNS Account](https://my.nextdns.io/signup/)


### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/maboni/ha-gps-tracker.git
    cd ha-gps-tracker

2. **Set up Docker environment**:
    Update the `./config/.env` file and configure the details:
    ```
    API_KEY=<your_nextdns_api_key>
    PROFILE_ID=<your_nextdns_profile_id>
    LOCAL_API_KEY=<your_local_api_key>
    ```

3. **Run the containers**:
    ```bash
    docker-compose up -d
    ```

### Docker Hub Repositories

- **Backend**: <a href="https://hub.docker.com/r/maboni82/homeassistant-tracker-backend" target="_blank">homeassistant-tracker-backend</a>
- **Frontend**: <a href="https://hub.docker.com/r/maboni82/homeassistant-tracker-frontend" target="_blank">homeassistant-tracker-frontend</a>

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Built for better filtering posibilities and visualization of NextDNS date using open-source tools.

## Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.


##  Using the API
The API requires Basic Authentication with the following:


## Repobeats Analytics
---

![Alt](https://repobeats.axiom.co/api/embed/bdefb2b5821082ae5d7ef63926053e0edc2ec335.svg "Repobeats analytics image")

---