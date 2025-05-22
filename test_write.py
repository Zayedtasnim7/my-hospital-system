import os

path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'test_write.txt')

try:
    with open(path, 'w') as f:
        f.write('test')
    print('Write successful')
    os.remove(path)
except Exception as e:
    print('Write failed:', e)