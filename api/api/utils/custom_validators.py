import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordComplexityValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Your password must be at least %(min_length)d characters long."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )
        if not re.findall(r'[A-Z]', password):
            raise ValidationError(
                _("Your password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        if not re.findall(r'[a-z]', password):
            raise ValidationError(
                _("Your password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        if not re.findall(r'\d', password):
            raise ValidationError(
                _("Your password must contain at least one digit."),
                code='password_no_digit',
            )
        if not re.findall(r'[^A-Za-z0-9]', password):
            raise ValidationError(
                _("Your password must contain at least one special character."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            "Your password must be at least %(min_length)d characters long, "
            "and contain at least one uppercase letter, one lowercase letter, "
            "one number, and one special character."
        ) % {'min_length': self.min_length}
