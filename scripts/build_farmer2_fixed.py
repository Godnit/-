from pathlib import Path

script_path = Path(__file__).with_name('build_farmer2.py')
source = script_path.read_text(encoding='utf-8')

replacements = {
    "cart('PumpkinCart_A',(3.0,14.0),yaw=.10,pumpkins=True,scale=.95)": "cart('PumpkinCart_A',3.0,14.0,yaw=.10,pumpkins=True,scale=.95)",
    "cart('PumpkinCart_B',(5.6,14.9),yaw=-.22,pumpkins=True,scale=.80)": "cart('PumpkinCart_B',5.6,14.9,yaw=-.22,pumpkins=True,scale=.80)",
    "cart('PastureCart',(0.5,-24.0),yaw=.18,pumpkins=False,scale=.88)": "cart('PastureCart',0.5,-24.0,yaw=.18,pumpkins=False,scale=.88)",
}

for old, new in replacements.items():
    if old not in source:
        raise RuntimeError(f'Expected Farmer 2 source line not found: {old}')
    source = source.replace(old, new)

namespace = {
    '__file__': str(script_path),
    '__name__': '__main__',
}
exec(compile(source, str(script_path), 'exec'), namespace, namespace)
