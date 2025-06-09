# Created by: Faliseven 
import sys
import os
import importlib.util
import random
def is_frozen():
    return getattr(sys, 'frozen', False)

def supports_ansi():
    if sys.platform != 'win32':
        return True
    return 'ANSICON' in os.environ or 'WT_SESSION' in os.environ or os.environ.get('TERM_PROGRAM') == 'vscode'

USE_COLOR = supports_ansi()
def c(text, code):
    return f'\033[{code}m{text}\033[0m' if USE_COLOR else text

def ensure_pyfiglet():
    try:
        import pyfiglet
    except ImportError:
        import subprocess
        print('Installing pyfiglet for beautiful banners...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyfiglet'])
        import pyfiglet

if is_frozen():
    print('[!] This installer .exe cannot install modules because it is not running under Python.')
    print('Please use the .py version or run this .exe from a Python environment.')
    input('Press Enter to exit...')
    sys.exit(0)

ensure_pyfiglet()
from pyfiglet import figlet_format
def print_banner():
    banner = figlet_format('BOOTSTRAP', font='slant')
    print(c(banner, '96'))
print_banner()
print(c('Created by: Faliseven ', '94'))
# Thanks and contacts (EN only)
print(c('Author: Fal1sev4n | Discord: https://discord.gg/CZtqqx5phE', '94'))
# Easter egg: random quote (EN only)
quotes = [
    'Code with soul and everything will work out!',
    'Python is easy And you are awesome!',
    'May bugs stay away from your code!',
    'Fal1sev4n wishes you luck in coding!',
    'The best bootstrap is the one that works on the first try!',
    'Keep calm and pip install!',
    'Every bug is a lesson',
    'Automate the boring stuff',
    'Good code is its own best documentation',
    'Do not repeat yourself unless it is fun',
    'If it works do not touch it If it does not debug it',
    'Real coders use virtual environments',
    'One more module one more superpower',
    'Your script your rules!',
]
print(c(random.choice(quotes), '93'))
# ASCII-art with nickname
print(c(figlet_format('Fal1sev4n', font='mini'), '95'))
import platform
print(c(f'Python: {platform.python_version()} | OS: {platform.system()} {platform.release()}', '93'))
print(c('Starting... ⏳', '96'))
import time
time.sleep(1)

def is_module_installed(module_name):
    return importlib.util.find_spec(module_name) is not None

modules = ['customtkinter', 'pillow']

print(c('\n🚀 Installing modules:\n', '96'))
for m in modules:
    if is_module_installed(m):
        print(c(f'✅ Module {m} already installed.', '92'))
    else:
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', m])
            print(c(f"✅ Module '{m}' installed successfully.", '96'))
        except Exception as e:
            print(c(f"❌ Error installing '{m}': {e}", '91'))

print(c('\n🎉 All done! Thank you for using Bootstrap Universal!', '95'))
input('\nPress Enter to exit...')
