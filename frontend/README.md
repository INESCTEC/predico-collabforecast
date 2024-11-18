# Predico-Collabforecast Frontend

This is the frontend for the Predico Collabforecast service. It is a React application that allows users to interact with the service documentation and administrators to invite and manage user accesses to the platform.

For the frontend, as it is a React application, you will need to have Node.js installed. You can download it from the [official website](https://nodejs.org/).
 
#### Important! Steps to Ensure correct Frontend Updates 

If you make any changes on the Frontend module, please clear Docker caches thoroughly before rebuilding images.
Docker might still be using cached layers or containers. To ensure everything is completely rebuilt, you should:

- Remove the Docker volume for the frontend service:

```bash
    docker volume rm predico_frontend_build
```
