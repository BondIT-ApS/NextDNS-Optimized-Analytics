# 🧱 NextDNS Optimized Analytics

[![Build Status](https://img.shields.io/github/actions/workflow/status/BondIT-ApS/NextDNS-Optimized-Analytics/docker-publish.yml?branch=main&style=for-the-badge)](https://github.com/BondIT-ApS/NextDNS-Optimized-Analytics/actions)
[![License](https://img.shields.io/github/license/BondIT-ApS/NextDNS-Optimized-Analytics?style=for-the-badge)](LICENSE)
[![Repo Size](https://img.shields.io/github/repo-size/BondIT-ApS/NextDNS-Optimized-Analytics?style=for-the-badge)](https://github.com/BondIT-ApS/NextDNS-Optimized-Analytics)
[![Made in Denmark](https://img.shields.io/badge/made%20in-Denmark%20🇩🇰-red?style=for-the-badge)](https://bondit.dk)
[![Powered by Coffee](https://img.shields.io/badge/powered%20by-coffee%20☕-brown?style=for-the-badge)](https://bondit.dk)

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-nextdns--optimized--analytics--frontend-blue?logo=docker&style=for-the-badge)](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-frontend)
[![Docker Pulls](https://img.shields.io/docker/pulls/maboni82/nextdns-optimized-analytics-frontend?style=for-the-badge)](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-frontend)

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-nextdns--optimized--analytics--backend-blue?logo=docker&style=for-the-badge)](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-backend)
[![Docker Pulls](https://img.shields.io/docker/pulls/maboni82/nextdns-optimized-analytics-backend?style=for-the-badge)](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-backend)

## 🔍 Building Better Insights, One DNS Brick at a Time

Welcome to NextDNS Optimized Analytics - where we do for NextDNS logs what LEGO did for children's toys: make them more structured, easier to work with, and way more fun to explore! 

Just like building a LEGO masterpiece, we've crafted a solution that assembles NextDNS data into something greater than the sum of its parts. This Dockerized solution fetches, stores, and visualizes logs from the NextDNS API with precision and elegance. It includes a Python-based API for querying logs with sophisticated filtering options (e.g., excluding domains), stores data in a local database foundation, and connects all the pieces with Grafana for beautiful DNS activity visualization.

## 🚀 Features - The Building Blocks

- **🔄 Local NextDNS Log Synchronization** – Securely fetch logs and store them locally, like collecting all the right LEGO pieces before starting your build
- **📊 Interactive Visualization** – Stunning Grafana dashboards that transform raw data into visual insights, like seeing your LEGO creation from every angle
- **🔍 Advanced Data Filtering** – Powerful filtering capabilities that go beyond NextDNS's standard UI, like sorting LEGO bricks by color, shape and size
- **🐳 Dockerized Deployment** – Quick, containerized setup for both backend and frontend, as easy as following a LEGO instruction manual
- **🔐 Basic Authentication** – Secure access to your data, because even the best LEGO collections need protection

## 🧱 Getting Started - The Foundation Pieces

### Prerequisites - Tools You'll Need

- [Docker](https://www.docker.com/get-started) - Your primary building tool
- [Docker Compose](https://docs.docker.com/compose/install/) - For connecting the pieces
- [NextDNS Account](https://nextdns.io/?from=dzgsz9sg) - The raw materials

### Installation - Assembly Instructions

1. **📦 Clone the repository**:
    ```bash
    git clone https://github.com/BondIT-ApS/NextDNS-Optimized-Analytics.git
    cd NextDNS-Optimized-Analytics
    ```

2. **⚙️ Configure Your Build**:
    Update the `./config/.env` file with your personal building materials:
    ```
    API_KEY=<your_nextdns_api_key>
    PROFILE_ID=<your_nextdns_profile_id>
    LOCAL_API_KEY=<your_local_api_key>
    ```

3. **🚀 Assemble the Solution**:
    ```bash
    docker-compose up -d
    ```
    Just like that final satisfying "click" when LEGO pieces connect, your containers are now running!

### 🐳 Docker Hub Building Sets

Our pre-built Docker images are ready for your collection:

- **Backend Set**: [nextdns-optimized-analytics-backend](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-backend)
- **Frontend Set**: [nextdns-optimized-analytics-frontend](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-frontend)

## 🔐 Using the API - Playing with Your Creation

The API requires Basic Authentication with the credentials you've configured in your .env file - because every good LEGO creation deserves protection!

Use the API to query your data, filter domains, and generate insights that the standard NextDNS interface simply can't provide. It's like having a master LEGO builder's toolkit at your fingertips!

## 📊 Analytics - Admiring Your Build

Once everything is running, access the Grafana dashboard to visualize your DNS activity. The data is transformed into intuitive charts and graphs, giving you insights into your network traffic patterns, blocked domains, query types, and more.

It's like stepping back to admire your completed LEGO masterpiece, seeing how all the individual bricks come together to form something spectacular!

## 🧰 Project Architecture - The Building Design

Just like a well-designed LEGO set, this solution consists of several key components:

1. **Backend API** - The foundation pieces that connect to NextDNS and store data
2. **Database** - The stable baseplate that holds all your logs
3. **Grafana** - The decorative and functional elements that make your data beautiful
4. **Docker Containers** - The instruction manual that makes assembly a breeze

## 👷‍♂️ Contributing - Join Our Building Team

Contributions are welcome! Feel free to open an issue or submit a pull request. Like any good LEGO enthusiast, we believe more builders create better creations.

1. Fork the repository (like borrowing a few bricks)
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request (show us your creation!)

## 📄 License - The Building Rules

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
Like LEGO, you're free to rebuild and reimagine as you see fit!

## 📈 Repobeats Analytics

![Repobeats analytics image](https://repobeats.axiom.co/api/embed/abcc9fac036c51dc10cd34ef580cca8475df93ad.svg "Repobeats analytics image")

---

## 🏢 About BondIT ApS

This project is maintained by [BondIT ApS](https://bondit.dk), a Danish IT consultancy that builds digital solutions one brick at a time. Just like our fellow Danish company LEGO, we believe in building things methodically, with precision and a touch of playfulness. Because the best solutions, like the best LEGO creations, are both functional AND fun!

**Made with ❤️, ☕, and 🧱 by BondIT ApS**
