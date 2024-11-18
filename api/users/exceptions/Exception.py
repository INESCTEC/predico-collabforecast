from rest_framework.exceptions import APIException


class EmailAlreadyExists(APIException):

    def __init__(self, value):
        super().__init__(self.default_detail.format(value))
    status_code = 409
    default_detail = "The email '{}' already exists!"
    default_code = 'email_already_exists'


class ResourceAlreadyExists(APIException):

    def __init__(self, user, resource_name):
        super().__init__(self.default_detail.format(resource_name, user))
    status_code = 409
    default_detail = "Resource '{}' already registered for user {}"
    default_code = 'resource_already_exists'


class ResourceNotFound(APIException):
    def __init__(self):
        super().__init__(self.default_detail)
    status_code = 409
    default_detail = "Resource ID not found."
    default_code = 'resource_not_found'


class RegistrationError(APIException):
    def __init__(self, user_email):
        super().__init__(self.default_detail.format(user_email))
    status_code = 409
    default_detail = "Unable to register user '{}'."
    default_code = 'registration_error'
