# Steps to Ensure the Frontend Updates 
Clear Docker Caches Thoroughly: Sometimes, even when you run --no-cache, 
Docker might still be using cached layers or containers. To ensure everything is completely rebuilt, you should:

- Remove the Docker volume for the frontend service:

```bash
    docker volume rm collabforecast_frontend_build
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