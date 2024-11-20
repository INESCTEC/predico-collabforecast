# Predico-Collabforecast Frontend

This is the frontend for the Predico Collabforecast service.
It is a **React application** that allows users to interact with the service documentation and 
for administrators to invite and manage user access to the platform.

---

## Prerequisites

### System Requirements
- **Node.js**: You will need Node.js installed on your machine. Download it from the [official website](https://nodejs.org/).

- **Docker (Optional)**: Docker is required for building and running the production version of the application. Visit the [Docker website](https://www.docker.com/) for installation instructions.

---

## Development Setup

1. **Clone the repository**:
```bash
   git clone git@github.com:INESCTEC/predico-collabforecast.git
   cd predico-collabforecast/frontend
```

2. **Install dependencies**:

```bash
   npm install
```

3. **Start the development server**:

```bash
   npm start
```
The application will be available at `http://localhost:3000`.

## Production Setup

1. **Build the dependencies**:

```bash
   npm run build
```

2. **Serve the application**:

```bash
   npm install -g serve
   serve -s build
```

# Docker Deployment

## Build the Docker Image

1. **Clear the docker cache**:
If you’ve made any changes to the frontend module, clear Docker caches thoroughly before rebuilding images. 
Docker might still be using cached layers or containers.

```bash
   docker volume rm predico_frontend_build
```

2. **Build the Docker image**:

```bash
   docker-compose -f docker-compose.prod.yml build frontend
```

3. **Run the Docker container**:

```bash
   docker-compose -f docker-compose.prod.yml up frontend
```

## Environment Variables

The frontend application requires the following environment variables to be set:

- REACT_APP_API_URL=https://predico.inesctec.pt/api/v1
- REACT_APP_BASE_URL=https://predico.inesctec.pt
- REACT_APP_EMAIL=predico@example.com

## Features

### User interaction

- To be defined

### Admin interaction

- Invite users and manage user roles.
- Monitor platform access logs and activity.

# Clearing Caches and Resetting

Clearing Caches and Resetting

1. Clearing Caches and Resetting

```bash
rm -rf node_modules
npm install
```

2. Remove Docker containers and volumes:

```bash
docker-compose -f docker-compose.prod.yml down
docker volume rm predico_frontend_build
```

3. Rebuild and restart the services:

```bash
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d
```
