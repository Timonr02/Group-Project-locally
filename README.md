<h1 align="center">
  Industrial IoT Ingestion & REST API
</h1>
<br>

<p align="center">
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat&logo=fastapi" alt="FastAPI"></a>
  <a href="https://www.timescale.com"><img src="https://img.shields.io/badge/TimescaleDB-PostgreSQL-002F6C.svg?style=flat&logo=postgresql" alt="TimescaleDB"></a>
  <a href="https://www.docker.com"><img src="https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat&logo=docker" alt="Docker"></a>
  <a href="https://mosquitto.org"><img src="https://img.shields.io/badge/MQTT-Mosquitto-3C5280.svg?style=flat&logo=eclipse-mosquitto" alt="MQTT"></a>
</p>

This repository contains the complete modular microservice stack for our Digital Factory Group Project. It features an asynchronous **OPC UA Ingest Worker** that subscribes to live machine variables on the shop floor, and a secure **FastAPI REST API** to query historical telemetry and text logs.

- **Local Swagger UI Docs:** http://localhost:8000/docs
- **Ingestion Mapping:** `ingest/mapping.json`
- **Database Schema:** `init.sql`

## Key Capabilities

- **Asynchronous Ingestion:** Subscribes to multiple live OPC UA nodes concurrently using `asyncua`.
- **Dynamic Data Routing:** Automatically separates float telemetry from text logs (events) at the database layer.
- **RESTful API:** Powered by FastAPI with an asynchronous pool manager (`asyncpg`) for fast query execution.
- **MQTT Publishing (Hot Path):** Instant alerts and real-time state changes published directly to Mosquitto.
- **Historical Storage (Cold Path):** Time-series optimizations using TimescaleDB hypertables, compression, and retention.

---

## Quick Start (Deployment)

This deployment guide is optimized for a clean Debian-based virtual machine.

### 1. Install Docker & Docker Compose
Execute the following commands to configure the official Docker repository and install the engine (Detailed installation guide: https://docs.docker.com/engine/install/debian/#install-using-the-repository):

```bash
# Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

# Install Docker Engine and Plugins:
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. Start the Stack
Navigate to the repository root directory and start all services in the background:

```bash
docker compose up -d
```

---

## Project Roles & Grading Info

This section details the division of work and individual contributions of each team member.

### Timon — Backend & API Orchestration
* **Contributions:**
  * Programmed the asynchronous **OPC UA Ingest Worker** (`ingest/` directory) for subscription handling, data cleaning, and mapping.
  * Designed the **FastAPI REST API Service** (`RESTfulAPI/` directory) and asynchronous database pooling.
  * Implemented the **MQTT Manager** (`mqtt.py`) including debug connection callbacks.
  * Orchestrated the multi-service deployment via **Docker Compose**.
* **Prior Knowledge & Background:**
  * Had basic prior experience with TimescaleDB/PostgreSQL databases and beginner-level familiarity with building REST APIs.

### Sara — Database Administration & SQL
* **Contributions:**
  * Example: Authored the database initialization and setup script (`init.sql`).
  * ...

* **Prior Knowledge & Background:**
  * ...
---

## Extensibility Guide

The project's metadata-driven design allows scaling the shop floor configuration without modifying any Python code.

### A) Adding Variables/Nodes
To track new variables on an existing machine, open `ingest/mapping.json`, add the node ID under the respective machine, and configure its path:
* **`"hot_path": true`**: Saves the value to TimescaleDB **and** publishes it instantly to the MQTT broker (ideal for live alerts).
* **`"hot_path": false`**: Only saves the value to the database (ideal for slow diagnostics/telemetry).

### B) Adding a New Machine (Module)
1. **Update `mapping.json`**: Add the new module block containing its OPC UA URL, target table name, and mapped nodes.
2. **Update `init.sql`**: Create a matching table schema using our standardized `(time, sensor_name, value)` structure and register it as a hypertable.
3. **Rebuild the stack**: Run `docker compose up --build -d`.

---

## REST API Endpoints

The API is fully asynchronous and focuses on two key endpoints:

* **`GET /api/v1/{machine}/metrics`**  
  Used by Grafana to retrieve historical numeric sensor telemetry values (temperatures, positions, etc.) from the `{machine}_data` tables.
  * *Query Parameters:* `sensors` (comma-separated list), `start_time` (optional), `end_time` (optional), `limit` (default `10000`).

* **`GET /api/v1/{machine}/events`**  
  Used by Grafana to retrieve text-based event log entries (error descriptions, job names, statuses) from the `machine_events` table.
  * *Query Parameters:* `event_names` (comma-separated list, optional), `limit` (default `1000`).