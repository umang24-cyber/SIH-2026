import re

def undo_patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Match the noise block
    pattern = r'\s*# --- V4 NOISE INJECTION ---.*?# --------------------------\n'
    content = re.sub(pattern, '\n', content, flags=re.DOTALL)

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    undo_patch('data_pipeline/generate_v4.py')
