"""Distribution checks for the fresh integration."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / 'custom_components/shinybow_sb8804lcm'


class MetadataTests(unittest.TestCase):
    def test_manifest_and_hacs(self):
        manifest = json.loads((COMPONENT / 'manifest.json').read_text())
        self.assertEqual(manifest['domain'], COMPONENT.name)
        self.assertEqual(manifest['version'], '0.2.0')
        self.assertEqual(manifest['iot_class'], 'assumed_state')
        self.assertEqual(manifest['requirements'], ['pyserial==3.5'])
        self.assertEqual(json.loads((ROOT / 'hacs.json').read_text())['name'], manifest['name'])
    def test_translations_and_actions(self):
        strings = json.loads((COMPONENT / 'strings.json').read_text())
        self.assertEqual(strings, json.loads((COMPONENT / 'translations/en.json').read_text()))
        self.assertIn('reconfigure', strings['config']['step'])
        services = json.loads((COMPONENT / 'services.yaml').read_text())
        self.assertEqual(set(services), {'set_route', 'set_all_outputs', 'all_off', 'send_command'})
        for service in services.values():
            self.assertTrue(service['fields']['entry_id']['required'])
    def test_sources_parse(self):
        for path in COMPONENT.glob('*.py'):
            with self.subTest(path=path.name):
                ast.parse(path.read_text())
    def test_old_domain_removed(self):
        self.assertFalse((ROOT / 'custom_components/pyxo_shinybow_sb8804lcm').exists())
