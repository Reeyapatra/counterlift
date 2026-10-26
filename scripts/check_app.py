"""Headless UI checks, including aggregate integrity failures and interactions."""
import os
import tempfile
import shutil
from pathlib import Path
from streamlit.testing.v1 import AppTest

root = Path(__file__).resolve().parents[1]
app_path = str(root / 'app.py')
app = AppTest.from_file(app_path).run(timeout=30)
assert not app.exception, str(app.exception)
assert len(app.tabs) == 4
assert any('SYNTHETIC' in item.value for item in app.info), 'This check expects a labeled synthetic run'
for budget in (0., .5, 1.):
    app.select_slider[0].set_value(budget).run()
    assert not app.exception, str(app.exception)
for index, value in ((0,1000),(1,.01),(2,20.)):
    app.number_input[index].set_value(value).run()
    assert not app.exception, str(app.exception)
assert len(app.json) >= 2
old = os.environ.get('COUNTERLIFT_RUN')
try:
    with tempfile.TemporaryDirectory() as d:
        os.environ['COUNTERLIFT_RUN'] = str(Path(d)/'missing')
        missing = AppTest.from_file(app_path).run(timeout=30)
        assert not missing.exception and missing.info
        shutil.copytree(Path(old) if old else root/'runs/demo', Path(d)/'bad')
        (Path(d)/'bad/experiment.json').write_text('{}')
        os.environ['COUNTERLIFT_RUN'] = str(Path(d)/'bad')
        corrupt = AppTest.from_file(app_path).run(timeout=30)
        assert not corrupt.exception and corrupt.error
finally:
    if old is None: os.environ.pop('COUNTERLIFT_RUN',None)
    else: os.environ['COUNTERLIFT_RUN'] = old
print('Four UI tabs, synthetic labels, all budget endpoints, financial inputs, missing/corrupt artifact states passed')
