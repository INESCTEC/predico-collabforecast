# ruff: noqa: E501

EMAIL_SIGNATURE = '\n\nThe Collabforecast project team'
EMAIL_SUBJECT_FORMAT = '[Collabforecast] - '

# Insert here the different components for your email subject and body message

EMAIL_OPTS = {
    'registration': {
        'subject': EMAIL_SUBJECT_FORMAT + 'Register to Collabforecast!',
        'message': '<p>Click the following button to register to Collabforecast.'
    },

    'generic-error-email': {
        'subject': EMAIL_SUBJECT_FORMAT + 'An error occurred. Please contact the developers.',
        'message': "{message}"
    },

    'email-challenge-confirmation': {
        'subject': EMAIL_SUBJECT_FORMAT + 'Challenge confirmation',
        'message': "<p>A new challenge of was successfully registered.<br>"
                   "Some related information about the offer: <br>"
                   "<strong>Challenge ID:</strong> {challenge_id}<br>"
                   "<strong>Resource:</strong> {resource}<br>"
    },

    'email-challenge-submission-confirmation': {
        'subject': EMAIL_SUBJECT_FORMAT + 'Challenge submission confirmation',
        'message': "<p>A submission was successfully registered.<br>"
                   "Some related information about the offer: <br>"
                   "<strong>Challenge ID:</strong> {challenge_id}<br>"
                   "<strong>Resource:</strong> {resource}<br>"
    },

    'email-verification': {
        'subject': EMAIL_SUBJECT_FORMAT + 'Email verification',
        'message': '<p>Before using the platform through the API or Website, '
                   'please verify first your email address using '
                   'the button bellow: <br><br></p>'},

    'email-verification-success': {
        'subject': EMAIL_SUBJECT_FORMAT + 'Email verification Success',
        'message': '<p>Your user has been successfully verified! '
                   'Welcome to Predico!</p>'},

    'password-reset-verification': {
        'subject': EMAIL_SUBJECT_FORMAT + 'Password reset verification',
        'message': '<p>Please use the following bellow button to '
                   'reset your password.<br></p>'
                   '<p>If you didn\'t request a password reset you may ignore this email and alert us.</p><br>'},

    'password-reset-success': {
        'subject': EMAIL_SUBJECT_FORMAT + 'Password reset successful',
        'message': '<p>Your password was correctly reset.<br>'
                   'If you didn\'t requested a reset password reply as soon as possible to'
                   ' this email.</p>'},

    'password-change-success': {
        'subject': EMAIL_SUBJECT_FORMAT + 'Password change successful',
        'message': '<p>Your password was correctly changed from the '
                   'Dashboard settings page.<br>'
                   'If you didn\'t requested a password change reply as soon as possible to'
                   ' this email.</p>'},
}
