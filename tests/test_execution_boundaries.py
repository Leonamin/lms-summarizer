import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from src.core.runtime.item_processor import ItemProcessor
from src.core.validation import initial_stage, validate_stage_range
from src.core.models.stages import PipelineStage

class ExecutionTests(unittest.TestCase):
    def test_local_input_and_injected_history(self):
        class Audio:
            def __init__(self, **kwargs):
                self.downloads_dir = None
            def transcribe(self, source, remove_wav):
                if remove_wav:
                    Path(source).unlink()
                out = Path(source).with_suffix('.txt')
                out.write_text('transcript')
                return str(out)
        class Summary:
            def __init__(self, *args, **kwargs):
                pass
            def process(self, source):
                out = Path(source).with_name('summary.txt')
                out.write_text('summary')
                return str(out)
        settings = {'user_inputs': {}, 'model_name':'model', 'engine':'custom',
                    'summary_prompt':'prompt', 'stt_engine':'openai-whisper',
                    'stt_model':'model', 'stt_params': {'api_key':'supplied'}}
        history = []
        with tempfile.TemporaryDirectory() as root:
            source = Path(root)/'source.wav'
            source.write_bytes(b'original')
            processor = ItemProcessor({'AudioToTextPipeline': Audio, 'SummarizePipeline': Summary}, settings, lambda _: None, history_writer=history.append)
            result = processor.process_full(str(source), lambda _: None, start_stage='STT')
            processor.finalize(str(source), '', result, 1, delete_source=False)
            self.assertEqual(source.read_bytes(), b'original')
            self.assertEqual(len(history), 1)
            self.assertEqual(processor.stt_params['api_key'], 'supplied')

    def test_file_and_stage_validation(self):
        self.assertEqual(initial_stage('lecture.MP3'), PipelineStage.STT)
        self.assertEqual(initial_stage('lecture.txt'), PipelineStage.SUMMARIZE)
        with self.assertRaises(ValueError):
            initial_stage('unsupported.pdf')
        with self.assertRaises(ValueError):
            validate_stage_range(PipelineStage.STT, PipelineStage.DOWNLOAD)

if __name__ == '__main__':
    unittest.main()
