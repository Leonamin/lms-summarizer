"""Desktop adapter for the framework independent item processor."""
from src.core.runtime.item_processor import ItemProcessor as CoreItemProcessor, CancelledException

class ItemProcessor(CoreItemProcessor):
    def __init__(self, modules, settings, on_log, cancel_check=None):
        from src.desktop.legacy_storage import add_history_entry
        from src.desktop.actions import open_chatbot
        super().__init__(modules, settings, on_log, cancel_check,
                         history_writer=add_history_entry, manual_action=open_chatbot)
