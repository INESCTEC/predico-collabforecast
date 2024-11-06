# Authentication

Before interacting with the Predico API, you need to authenticate using your registered email and password.
**Ensure that you have completed the registration process and that your email address has been validated**. 
If you haven't registered yet, please refer to the [Forecaster Application](introduction.md) section for instructions.

## Retrieving an Access Token

To authenticate with the Predico API, you need to obtain an access token using your credentials. This token will be used in the headers of your subsequent API requests to authorize your actions.

Here is how you can retrieve an access token using Python:

```python title="authentication.py"
--8<-- "docs/examples/authentication.py"
```

<a href="../examples/authentication.py" download="authentication.py"><b>Download Full Example</b></a>

### JSON Example Response 
??? example "Click to view Example Response"

    ```json
    {
      "access": "jwt_access_token",
      "refresh": "jwt_refresh_token"
    }
    ```

