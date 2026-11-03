
from abc import ABC, abstractmethod


class BaseValidator(ABC):

    @abstractmethod
    def validate(self, record: dict) -> list:
        """
        Return a list of validation errors.
        Empty list means the record is valid.
        """
        pass
