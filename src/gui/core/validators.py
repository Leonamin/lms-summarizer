"""Desktop validation adapter with Chrome discovery."""
from src.core.validation import InputValidator as CoreInputValidator
from src.gui.core.file_manager import get_chrome_path

class InputValidator(CoreInputValidator):
    @staticmethod
    def validate_chrome():
        return CoreInputValidator.validate_chrome(get_chrome_path())

    @staticmethod
    def validate_all_inputs(inputs, **kwargs):
        return CoreInputValidator.validate_all_inputs(inputs, chrome_path=get_chrome_path(), **kwargs)
