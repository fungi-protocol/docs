import json
from pathlib import Path
import subprocess
import sys

import pdf_preprocess


DATAFRAME = '''<div class="dataframe-wrapper">
<table border="1" class="dataframe">
  <thead><tr><th></th><th>amount</th><th>label</th></tr></thead>
  <tbody>
    <tr><th>0</th><td>123</td><td>Alice &amp; Bob</td></tr>
    <tr><th>1</th><td>456</td><td>change</td></tr>
  </tbody>
</table>
</div>'''


def test_saved_dataframe_becomes_a_markdown_table_inside_its_wrapper():
    content = 'Before output.\n\n' + DATAFRAME + '\n\nAfter output.'
    converted = pdf_preprocess.convert_tables(content)
    assert converted.startswith('Before output.\n\n<div class="dataframe-wrapper">')
    assert converted.endswith('</div>\n\nAfter output.')
    assert '<table' not in converted
    parsed = json.loads(subprocess.run(
        ['pandoc', '-f', 'gfm', '-t', 'json'], input=converted,
        text=True, capture_output=True, check=True).stdout)
    table, = [block['c'] for block in parsed['blocks'] if block['t'] == 'Table']
    assert len(table[2]) == 3
    headers = table[3][1][0][1]
    assert [cell[4] for cell in headers] == [
        [],
        [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'amount'}]}],
        [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'label'}]}],
    ]
    values = []
    for row in table[4][0][3]:
        values.append([
            ''.join(item.get('c', ' ') if item['t'] == 'Str' else ' '
                    for block in cell[4] for item in block['c'])
            for cell in row[1]
        ])
    assert values == [['0', '123', 'Alice & Bob'], ['1', '456', 'change']]


def test_walk_converts_only_notebook_chapters_including_children():
    nested = {'Chapter': {'source_path': 'analysis.IPYNB', 'content': DATAFRAME,
                          'sub_items': []}}
    markdown = {'Chapter': {'source_path': 'guide.md', 'content': DATAFRAME,
                            'sub_items': [nested]}}
    pdf_preprocess.walk(['Separator', {'PartTitle': 'Part'}, markdown])
    assert markdown['Chapter']['content'] == DATAFRAME
    assert '<table' not in nested['Chapter']['content']


def test_json_protocol_and_renderer_support():
    script = Path(pdf_preprocess.__file__)
    for renderer, code in [('pandoc', 0), ('html', 1)]:
        result = subprocess.run([sys.executable, script, 'supports', renderer])
        assert result.returncode == code
    book = {'sections': [{'Chapter': {
        'source_path': 'analysis.ipynb', 'content': DATAFRAME, 'sub_items': []}}]}
    for renderer in ['html', 'pandoc']:
        result = subprocess.run([sys.executable, script],
                                input=json.dumps([{'renderer': renderer}, book]),
                                text=True, capture_output=True, check=True)
        content = json.loads(result.stdout)['sections'][0]['Chapter']['content']
        assert ('<table' not in content) == (renderer == 'pandoc')
