
def validation_error_response(data):
    return {"code": 400,
            "data": data,
            "status": "error",
            'message': "Validation error. Please re-check your request "
                       "parameters or body fields and fix the errors "
                       "mentioned in this response 'data' field."}


def conflict_error_response(message):
    return {"code": 409,
            "data": None,
            "status": "error",
            'message': message}


def missing_field_response(field_name):
    return validation_error_response({field_name: ["This field is required."]})
