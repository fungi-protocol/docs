local escapes = {
  [' ']='\\ ',
  ['\\']='\\textbackslash{}', ['{']='\\{', ['}']='\\}',
  ['$']='\\$', ['&']='\\&', ['#']='\\#', ['%']='\\%',
  ['_']='\\_', ['^']='\\textasciicircum{}', ['~']='\\textasciitilde{}'
}
local function breakable_code(code)
  local chars = {}
  for _, point in utf8.codes(code.text) do
    local char = utf8.char(point)
    chars[#chars + 1] = escapes[char] or char
  end
  return pandoc.RawInline('latex', '\\texttt{' .. table.concat(chars, '\\allowbreak ') .. '}')
end
function Table(tbl)
  local headers = {}
  if #tbl.head.rows > 0 then
    for _, cell in ipairs(tbl.head.rows[1].cells) do
      headers[#headers + 1] = pandoc.utils.stringify(cell.contents)
    end
  end
  local key = table.concat(headers, '|')
  if key == 'set|value|binary (little endian)|popcount|weight (base 3)|weight (base 10)'
      and #tbl.colspecs == 7 then
    tbl.head.rows[1].cells:insert(1, pandoc.Cell {})
    key = '|' .. key
  end
  -- mdbook-pandoc splits these mixed code/text headers into extra cells.
  if key == 'Name|keytype|keydata|keydata| Description|valuedata|valuedata| Description' then
    local cells = tbl.head.rows[1].cells
    for _, i in ipairs {4, 7} do
      local label = cells[i].contents[1].content
      label:extend(cells[i + 1].contents[1].content)
      cells[i].contents = {pandoc.Plain(label)}
    end
    tbl.head.rows[1].cells = {cells[1], cells[2], cells[3], cells[4], cells[6], cells[7]}
    key = 'Name|keytype|keydata|keydata Description|valuedata|valuedata Description'
  end
  local widths
  if key == 'Name|keytype|keydata|keydata Description|valuedata|valuedata Description' then
    widths = { .175, .195, .11, .14, .14, .24 }
  elseif key == '<keytype>|PSBT version|BIP' then
    widths = { .7, .15, .15 }
  elseif key == '|set|value|binary (little endian)|popcount|weight (base 3)|weight (base 10)' then
    widths = { .04, .13, .15, .25, .13, .15, .15 }
    for _, body in ipairs(tbl.bodies) do
      for _, row in ipairs(body.body) do
        local cell = row.cells[4]
        cell.contents = {pandoc.Plain {pandoc.Code(pandoc.utils.stringify(cell.contents))}}
      end
    end
  end
  if widths then
    for i, width in ipairs(widths) do tbl.colspecs[i][2] = width end
  end
  tbl = tbl:walk { Code = breakable_code }
  if widths and (#tbl.colspecs == 6 or #tbl.colspecs == 7) then
    return {pandoc.RawBlock('latex', '\\begingroup\\small\\setlength{\\tabcolsep}{3pt}'), tbl, pandoc.RawBlock('latex', '\\endgroup')}
  end
  return tbl
end

function Para(para)
  local images = pandoc.List()
  for _, inline in ipairs(para.content) do
    if inline.t == 'Image' then
      images:insert(pandoc.Para {inline})
    elseif inline.t ~= 'Space' and inline.t ~= 'SoftBreak' then
      return nil
    end
  end
  if #images > 1 then return images end
end

Plain = Para
