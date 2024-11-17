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

# Frontend printscreens

### Home Page

![img.png](public/homepage.png)

- The home page is the first page that the user sees when they visit the website. 
- It contains links to documentation and the login page (for admins only).
### Login Page
![img.png](public/signing.png)

- The login page is where admins can sign in.
- All users can also click on the "Forgot Password" link to reset their password.
- 
### Register Page

![img_1.png](public/register_page.png)

- The register page is where new users can sign up for an account. A link invitation only.

### Dashboard
![img.png](public/dashboard.png)

- The dashboard is where admins can view the progress and activity of the users. 
- Admins can also invite new users to the platform.