"""Run interactively on the server; prompts never echo credentials."""
from pathlib import Path
from getpass import getpass
import os
from dotenv import set_key
p=Path(__file__).resolve().parents[1]/'.env'
p.touch(mode=0o600,exist_ok=True)
os.chmod(p,0o600)
for key in ('MAIL_USERNAME','MAIL_PASSWORD','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID'):
    value=getpass(key+' (hidden; blank keeps current setting): ').strip()
    if value:
        set_key(str(p),key,value)
print('Configuration saved privately. Restart revive-thrive and its notification worker.')
