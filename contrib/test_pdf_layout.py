import copy
import json
from pathlib import Path
import subprocess


FILTER = Path(__file__).with_name('pdf-layout.lua')


def parse_markdown(markdown):
    return json.loads(subprocess.run(
        ['pandoc', '-f', 'gfm', '-t', 'json'], input=markdown,
        text=True, capture_output=True, check=True).stdout)


def apply_layout(document):
    return json.loads(subprocess.run(
        ['pandoc', '-f', 'json', '-t', 'json', '--lua-filter', str(FILTER)],
        input=json.dumps(document), text=True, capture_output=True,
        check=True).stdout)


def only_table(document):
    table, = [block['c'] for block in document['blocks'] if block['t'] == 'Table']
    return table


def cell_text(cell):
    return ''.join(inline['c'] if inline['t'] == 'Str' else ' '
                   for block in cell[4] for inline in block['c'])


def test_consecutive_notebook_images_each_get_their_own_block():
    document = parse_markdown('![First plot](first.svg) ![Second plot](second.svg)')
    block, = document['blocks']
    block['t'] = 'Plain'  # mdbook-pandoc emits notebook outputs as Plain.
    original = [inline for inline in block['c'] if inline['t'] == 'Image']
    result = apply_layout(document)
    assert len(result['blocks']) == 2
    assert all(block['t'] in ['Plain', 'Para'] for block in result['blocks'])
    assert [block['c'] for block in result['blocks']] == [[image] for image in original]


def test_notebook_index_header_is_restored_without_shifting_column_names():
    document = parse_markdown('''
| | set | value | binary (little endian) | popcount | weight (base 3) | weight (base 10) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | ternary | 0.00000486 | 011001111 | 6 | 1 | 3 |
| 1 | decimal | 0.00000500 | 001011111 | 6 | 4 | 1 |
''')
    table = only_table(document)
    del table[3][1][0][1][0]  # mdbook-pandoc omits the empty index header.
    result = only_table(apply_layout(document))
    headers = result[3][1][0][1]
    assert len(result[2]) == len(headers) == 7
    assert [cell_text(cell) for cell in headers] == [
        '', 'set', 'value', 'binary (little endian)', 'popcount',
        'weight (base 3)', 'weight (base 10)',
    ]
    rows = result[4][0][3]
    assert [len(row[1]) for row in rows] == [7, 7]
    assert [[cell_text(cell) for cell in row[1][:3]] for row in rows] == [
        ['0', 'ternary', '0.00000486'], ['1', 'decimal', '0.00000500'],
    ]


def test_bip_mixed_code_and_text_headers_keep_six_columns():
    document = parse_markdown('''
| Name | `keytype` | `keydata` | `keydata` Description | `valuedata` | `valuedata` Description |
| --- | --- | --- | --- | --- | --- |
| Input Sort Key | `PSBT_IN_SORT_KEY = TBD` | None | No key data | `<bytes sort key>` | Orders inputs. |
''')
    table = only_table(document)
    headers = table[3][1][0][1]

    def split_header(cell):
        code, description = copy.deepcopy(cell), copy.deepcopy(cell)
        code[4][0]['c'] = code[4][0]['c'][:1]
        description[4][0]['c'] = description[4][0]['c'][1:]
        return [code, description]

    table[3][1][0][1] = (headers[:3] + split_header(headers[3])
                          + [headers[4]] + split_header(headers[5]))
    result = only_table(apply_layout(document))
    assert len(result[2]) == len(result[3][1][0][1]) == 6
    assert len(result[4][0][3][0][1]) == 6
    restored = result[3][1][0][1]
    for index in [3, 5]:
        inlines = restored[index][4][0]['c']
        assert len(inlines) > 1
        assert inlines[-1] == {'t': 'Str', 'c': 'Description'}
