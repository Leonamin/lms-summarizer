import tempfile
from pathlib import Path
import unittest
from src.core.runtime.executor import PipelineExecutor
from src.core.models.jobs import StageCommand, WorkToken
import json
import threading
from src.core.validation import initial_stage, validate_stage_range
from src.core.models.stages import PipelineStage

class ExecutionTests(unittest.TestCase):
    def test_clipboard_executor_keeps_original_and_returns_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.txt'
            source.write_text('original', encoding='utf-8')
            token = WorkToken('job', 'attempt', 'run', 'generation', PipelineStage.SUMMARIZE)
            command = StageCommand(token, str(source), str(root / 'output'),
                                   json.dumps({'ai_engine': 'clipboard', 'ai_model': 'chatgpt'}), 'prompt')
            executor = PipelineExecutor()
            try:
                result = executor.execute(command, threading.Event())
                self.assertEqual(result.kind, 'prompt')
                self.assertIn('original', Path(result.output).read_text(encoding='utf-8'))
                self.assertEqual(source.read_text(encoding='utf-8'), 'original')
            finally:
                executor.close()

    def test_file_and_stage_validation(self):
        self.assertEqual(initial_stage('lecture.MP3'), PipelineStage.STT)
        self.assertEqual(initial_stage('lecture.txt'), PipelineStage.SUMMARIZE)
        with self.assertRaises(ValueError):
            initial_stage('unsupported.pdf')
        with self.assertRaises(ValueError):
            validate_stage_range(PipelineStage.STT, PipelineStage.DOWNLOAD)

if __name__ == '__main__':
    unittest.main()
