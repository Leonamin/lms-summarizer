import unittest

from src.core.naming import artifact_filename, build_stem, lecture_label, sanitize_component


class NamingTests(unittest.TestCase):
    def job(self, **overrides):
        base = {'display_name': '선대4_2', 'course_name': '선형대수', 'week_title': '4주차'}
        base.update(overrides)
        return base

    def artifact(self, kind, display_name):
        return {'kind': kind, 'display_name': display_name}

    def test_scope_controls_prefix_depth(self):
        summary = self.artifact('summary', 'summary.txt')
        self.assertEqual(artifact_filename(summary, self.job(), 'lecture'), '선대4_2_요약.txt')
        self.assertEqual(artifact_filename(summary, self.job(), 'week'), '4주차_선대4_2_요약.txt')
        self.assertEqual(artifact_filename(summary, self.job(), 'course'), '선형대수_4주차_선대4_2_요약.txt')

    def test_role_suffix_and_original_extension(self):
        job = self.job()
        self.assertEqual(artifact_filename(self.artifact('video', 'x.mp4'), job), '선대4_2_영상.mp4')
        self.assertEqual(artifact_filename(self.artifact('audio', 'audio.wav'), job), '선대4_2_음성.wav')
        self.assertEqual(artifact_filename(self.artifact('transcript', 'transcript.txt'), job), '선대4_2_대본.txt')
        self.assertEqual(artifact_filename(self.artifact('prompt', 'prompt.txt'), job), '선대4_2_프롬프트.txt')

    def test_missing_hierarchy_levels_are_skipped(self):
        job = self.job(week_title=None, course_name=None)
        self.assertEqual(artifact_filename(self.artifact('summary', 'summary.txt'), job, 'course'), '선대4_2_요약.txt')
        self.assertEqual(artifact_filename(self.artifact('summary', 'summary.txt'), None, 'course'), '요약.txt')

    def test_input_artifact_keeps_original_name(self):
        self.assertEqual(artifact_filename(self.artifact('input', 'lecture note.txt'), self.job()), 'lecture_note.txt')

    def test_file_display_name_extension_is_stripped_for_prefix(self):
        self.assertEqual(lecture_label('선대4_2.txt'), '선대4_2')
        self.assertEqual(lecture_label('선대 4.2강'), '선대_4.2강')

    def test_unsafe_characters_are_removed(self):
        self.assertEqual(sanitize_component('a/b:c*d?"<>|'), 'abcd')
        self.assertEqual(sanitize_component('  spaced   name  '), 'spaced_name')
        self.assertEqual(build_stem('summary', lecture='a/b', scope='lecture'), 'ab_요약')


if __name__ == '__main__':
    unittest.main()
