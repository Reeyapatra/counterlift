"""Exercise aggregate run selection and restoration without training."""
import os
import tempfile
from pathlib import Path
from streamlit.testing.v1 import AppTest
from counterlift.artifacts import export_public, verify_run

root = Path(__file__).resolve().parents[1]
import argparse
p=argparse.ArgumentParser()
p.add_argument("--previous", default="runs/demo")
p.add_argument("--candidate", default="runs/demo-verification")
args=p.parse_args()
old = os.environ.get('COUNTERLIFT_RUN')
source = root / args.previous
candidate = root / args.candidate
previous_id = verify_run(source)['run_id']
candidate_id = verify_run(candidate)['run_id']
assert previous_id != candidate_id, 'Use two distinct evaluated runs'
try:
    with tempfile.TemporaryDirectory() as d:
        a,b=Path(d)/'a',Path(d)/'b'
        export_public(source,a); export_public(candidate,b)
        for target, expected in ((a,previous_id),(b,candidate_id),(a,previous_id)):
            os.environ['COUNTERLIFT_RUN']=str(target)
            app=AppTest.from_file(str(root/'app.py')).run(timeout=30)
            assert not app.exception, str(app.exception)
            assert any(expected in item.value for item in app.json), 'Wrong displayed run ID'
finally:
    if old is None: os.environ.pop('COUNTERLIFT_RUN',None)
    else: os.environ['COUNTERLIFT_RUN']=old
print('A → B → A aggregate path rollback and displayed run ID verified')
