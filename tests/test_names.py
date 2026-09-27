"""Check channel naming, ambiguity prevention, and hardware address mapping."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('names', Path(__file__).parents[1] / 'custom_components/shinybow_sb8804lcm/names.py')
names = importlib.util.module_from_spec(spec)
spec.loader.exec_module(names)


class NamingTests(unittest.TestCase):
    def test_existing_entries_keep_defaults(self):
        self.assertEqual(names.input_options({}), ['Off', *[f'Input {i}' for i in range(1, 9)]])
        self.assertEqual(names.channel_name({}, 'output', 8), 'Output 8')

    def test_labels_keep_input_addresses(self):
        options = names.normalize_names({'input_3': ' TV ', 'output_1': ' Living room '})
        self.assertEqual(names.input_options(options).index('TV'), 3)
        self.assertEqual(names.channel_name(options, 'output', 1), 'Living room')
        self.assertEqual(names.input_options(options).index('Off'), 0)

    def test_blank_names_restore_defaults(self):
        options = names.normalize_names({'input_1': '  ', 'output_2': ''})
        self.assertEqual(options['input_1'], 'Input 1')
        self.assertEqual(options['output_2'], 'Output 2')

    def test_reject_ambiguous_inputs(self):
        for values in ({'input_1': 'TV', 'input_2': 'tv'}, {'input_8': ' off '}, {'input_1': 'Input 2'}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                names.normalize_names(values)

    def test_matrices_have_independent_labels(self):
        a = names.normalize_names({'input_1': 'TV'})
        b = names.normalize_names({'input_1': 'Radio'})
        self.assertEqual(names.input_options(a)[1], 'TV')
        self.assertEqual(names.input_options(b)[1], 'Radio')
