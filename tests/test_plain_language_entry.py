"""Entry-page clarity and existing-data playback integration, not physics validation. MIT."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_default_entry_does_not_lead_with_hypothetical_output():
 text=(ROOT/'tools/pages/overview.html').read_text(encoding='utf-8')
 assert 'We have not produced fusion or generated electricity.' in text
 assert text.index('beginner-intro')<text.index('power-summary')
 assert text.index('<details class="beginner-advanced">')<text.index('power-summary')
 assert 'What-if power estimates' in text and 'what-if estimates' in text
 assert 'id="beginner-viewport"' in text and 'href="#watch"' in text
 assert 'not demonstrated' in text and 'Other laboratories' in text

def test_design_uses_actual_existing_asset_not_invented_simulation():
 text=(ROOT/'tools/pages/beginner.js').read_text(encoding='utf-8')
 assert "viewer.load('r838')" in text and 'DeviceViewer' in text
 assert 'autoRotate' in text and 'prefers-reduced-motion' in text
 assert 'Plasma glow' not in text or 'only' in text
 assert 'physics' in text and '/api/' not in text

def test_watch_link_loads_recorded_reference_case_and_explains_source():
 js=(ROOT/'app/web/transport-lab.js').read_text(encoding='utf-8');html=(ROOT/'app/web/index.html').read_text(encoding='utf-8')
 assert "workbench:watch-particles" in js and 'pendingGuidedPlayback' in js
 assert 'select(4)' in js and "current.paths" in js
 assert 'assumed source of fusion neutrons' in html and 'fusion starting' in html
 assert 'not the later higher-power alternative' in html
 assert 'Technical values and calculation details' in html
 assert html.index('id="transport-play"')<html.index('id="transport-viewport"')

def test_direct_links_and_static_rebuild_are_supported():
 route=(ROOT/'tools/pages/pages.js').read_text(encoding='utf-8');builder=(ROOT/'tools/build_pages.py').read_text(encoding='utf-8')
 assert "['#watch','#design']" in route and "openView('transport')" in route
 assert "'beginner.js'" in builder
 assert './beginner.js' in (ROOT/'docs/index.html').read_text(encoding='utf-8')
 assert (ROOT/'tools/pages/beginner.js').read_bytes()==(ROOT/'docs/beginner.js').read_bytes()

def test_existing_physical_output_remains_absent():
 d=json.loads((ROOT/'docs/power-progress/data.json').read_text(encoding='utf-8'))
 assert d['summary']['physical_net_electric_MW'] is None
 assert d['summary']['best_average_net_MW']>0
 assert d['summary']['best_model_physical_status'].startswith('Unqualified')
