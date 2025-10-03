# CLOCK (Cloud Lifecycle Orchestrator for Cryptographic Keys)

CLOCK (Cloud Lifecycle Orchestrator for Cryptographic Keys) is a full-stack application that provides a unified, vendor-agnostic platform for managing the entire lifecycle of cryptographic keys across AWS, Azure, and GCP.

## Project Structure

This repository is a monorepo containing the full-stack application.

-   **/frontend**: Contains the Angular single-page application, containerized with Nginx.
-   **/backend**: Contains the Python backend services and its Docker configuration.

---
## Prerequisites

Before you begin, ensure you have the following installed:

-   [Docker](https://www.docker.com/products/docker-desktop/) & Docker Compose

---
## How to Run

First, clone the GitHub Repo:

```sh
git clone https://github.com/ChiefDennis/CLOCK.git
```

Then, navigate to the CLOCK directory:

```sh
cd CLOCK
```

### Backend

The backend can be run by itself, either in standard mode or with a mock profile for testing.

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Build and run the containers:
    ```bash
    # For the standard environment
    docker-compose up --build

    # To run with the testing mocks enabled
    docker-compose --profile mocks up --build
    ```

### Frontend

The frontend can also be run independently. It is served by a lightweight Nginx web server.

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Build and run the container:
    ```bash
    docker-compose up --build
    ```
    The application will be available at **http://localhost:8080**.

### Running the Full Stack

To run the entire application, you will need to open **two separate terminal windows**:

1.  In the first terminal, start the **backend** services.
2.  In the second terminal, start the **frontend** service.

### Log-in credentials

The default credentials are the following:

-    Admin user: Username: admin, Password: admin.
-    Non-Admin user: Username: user, Password: user.

### Documentation

The Swagger documentation is available at **http://localhost:8181/docs/swagger-ui**
