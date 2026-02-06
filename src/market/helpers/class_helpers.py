class ValidatorClass:
    def validate_attr_types(self):
        for field_name, field_info in self.__dataclass_fields__.items():
            field_data = getattr(self, field_name)
            if field_data is not None and not isinstance(field_data, field_info.type):
                raise TypeError(
                    f"Error! Attribute {field_name} type is "
                    f"'{type(field_data)}' but should "
                    f"be '{field_info.type}'"
                )
        return True
