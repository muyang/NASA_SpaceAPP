"""Reproduce only the final field diagnostic and the observed trial reanalysis."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
for name in ['audit_management','audit_hydraulics','analyze_economics','run_field_replay','evaluate_replay','verify_admission','build_deliverables']:
 subprocess.run([sys.executable,str(root/'case-study/field-admission-v2/src'/f'{name}.py')],cwd=root,check=True)
for name in ['audit_workbooks','analyze_trials']:
 subprocess.run([sys.executable,str(root/'case-study/public-field-validation/src'/f'{name}.py')],cwd=root,check=True)
