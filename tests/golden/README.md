# Golden renderings

`soft_drugs.txt` is what `render()` prints for `tests/fixtures/soft_drugs.py`. It is the
generated counterpart of the hand-written `docs/ARGUMENT_MAP_RENDERING.md`, which is the
design target for the view.

From `## Outline` to the end the two files are identical, except for two deliberate choices.
The header differs in the places where the document was written by hand and the renderer has
to generate the same information for any map.

## Deliberate differences

| Document | Renderer | Why |
|---|---|---|
| `#pro` / `#con` | `[pro]` / `[con]` | `#` opens a heading in Markdown, and `[mixed]` needs to fit the same shape. |
| `\| central claim \|` | `\| root claim \|` | A map may have several root claims, and none of them is then central. |
| `1 claim, 17 arguments, …` | `Map v23. 1 claim, …` | The version stamp lets a result say how far the map has moved since the last `show()`. |
| Title `Legalisation of soft drugs` | `Legalisation of Soft Drugs` | The title is the root claim's label, printed as it was entered. |
| A4's extra targets in the `"under X"` sentence | own `Items with more than one target:` block | One sentence cannot be generated for an arbitrary number of such items. |
| `Unchallenged arguments:` | `Unchallenged:` | Non-root claims can be unchallenged too. |
| "Each argument comes right after…" | "Each item comes right after…" | Same reason: the outline holds claims as well. |

## Regenerating

The file is not generated during a test run, so a change to the renderer shows up as a failing
diff. Once the change is intended:

```
uv run python -c "
import sys, pathlib; sys.path.insert(0, 'tests')
from fixtures.soft_drugs import soft_drugs_map
from cedrus.render import render
pathlib.Path('tests/golden/soft_drugs.txt').write_text(render(soft_drugs_map()), encoding='utf-8')
"
```
