"""Second brain hooks for Claude Code: a diary that writes itself, lessons loaded at the right time,
corrections detected automatically, a summary kept when the chat is compacted, and a daily backup.

One file, standard library only (Python 3.9+). Wire it in .claude/settings.local.json (see README):
  SessionStart      -> brain.py start    (load Lessons + Direction, back up memory, write Alerts.md)
  UserPromptSubmit  -> brain.py recall   (the 3 lessons most related to this request)
  Stop              -> brain.py diary    (one diary line per answer; detect corrections/confirmations)
  PostCompact       -> brain.py compact  (keep the compaction summary as a session note)

Configuration (environment variables, all optional):
  BRAIN_VAULT   folder of the Obsidian vault (default: ./brain next to the project's .claude folder)
  BRAIN_ALERT_DAYS  days in a row at zero before a stagnation alert (default 5)
A hook must never break your session: on any error this script exits quietly.
"""
import datetime
import json
import os
import re
import shutil
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))          # <project>/.claude/hooks/brain.py
VAULT = os.environ.get('BRAIN_VAULT') or os.path.join(PROJECT, 'brain')
DIARY = os.path.join(VAULT, 'Diary')
BACKUP = os.path.join(VAULT, '.backup')
ALERT_DAYS = int(os.environ.get('BRAIN_ALERT_DAYS', '5'))

# A front is "stagnant" when every diary day in the window matches its pattern. Edit to your fronts.
STAGNATION = {
    'No replies from clients': r'0 (replies|invitations|respuestas|invitaciones)',
    'No real buyers': r'0 real buyers|0 compradores reales',
    'Zero income': r'no income|USD 0 de afuera|0 income',
}
# Kept narrow on purpose: a loose «no»/«not» flags ordinary questions and instructions as corrections.
CORRECTION = (r"(\bthat'?s (not|wrong)\b|\bwrong\b|\bwhy did you\b|\bi told you\b|\byou should have\b|\bare you sure\b|"
              r"\bdidn'?t (work|do)\b|\bnot what i\b|\bno (es|era|sirve|anda|funciona)\b|est[aá] mal\b|\bno hiciste\b|"
              r"\bte dije\b|\bya te dije\b|\bpor qu[eé] (no|hiciste)\b|\byo no voy a\b|\bdeber[ií]as\b|\bseguro\?|"
              r"te parece bien|esto es manual)")
CONFIRMATION = r'\b(perfect|great|exactly|that\'s it|love it|yes,? do|perfecto|genial|excelente|eso es|dale|joya)'


def read(p, limit=None):
    try:
        s = open(p, encoding='utf-8').read()
        return s[:limit] if limit else s
    except OSError:
        return ''


def short(t, n):
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t or '')).strip()
    return t if len(t) <= n else t[:n - 1] + '…'


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ' '.join(c.get('text', '') for c in content if isinstance(c, dict) and c.get('type') == 'text')
    return ''


def memory_dir(data):
    tp = data.get('transcript_path') or ''
    d = os.path.join(os.path.dirname(tp), 'memory') if tp else ''
    return d if os.path.isdir(d) else ''


def now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------- start ----------
def backup(data, today):
    dest = os.path.join(BACKUP, today)
    if os.path.isdir(dest):
        return
    os.makedirs(dest)
    mem = memory_dir(data)
    if mem:
        shutil.copytree(mem, os.path.join(dest, 'memory'))
    for n in os.listdir(VAULT):
        src = os.path.join(VAULT, n)
        if n.endswith('.md') and os.path.isfile(src):
            shutil.copy2(src, dest)
        elif n in ('Diary', 'Sessions') and os.path.isdir(src):
            shutil.copytree(src, os.path.join(dest, n))
    old = sorted(d for d in os.listdir(BACKUP) if re.match(r'\d{4}-\d{2}-\d{2}$', d))
    for d in old[:-14]:
        shutil.rmtree(os.path.join(BACKUP, d), ignore_errors=True)


def alerts(today):
    days = sorted(f[:-3] for f in os.listdir(DIARY) if re.match(r'\d{4}-\d{2}-\d{2}\.md$', f))[-ALERT_DAYS:] \
        if os.path.isdir(DIARY) else []
    lines = []
    if len(days) >= ALERT_DAYS:
        for front, pat in STAGNATION.items():
            if all(re.search(pat, read(os.path.join(DIARY, d + '.md')), re.I) for d in days):
                lines.append('- **' + front + f'**: zero for {ALERT_DAYS} days in a row ({days[0]} to {days[-1]}). '
                             'Change course today (market, product, channel or customer); do not polish.')
    body = ('# Alerts\n\nWritten by the brain hook at session start from the last '
            f'{ALERT_DAYS} days of [[Home|diary]].\n\n' + ('\n'.join(lines) if lines else 'No alerts.') + '\n')
    p = os.path.join(VAULT, 'Alerts.md')
    if read(p) != body:
        open(p, 'w', encoding='utf-8', newline='\n').write(body)
    return '\n'.join(lines)


def start(data):
    today = now().strftime('%Y-%m-%d')
    for step in (lambda: backup(data, today),):
        try:
            step()
        except Exception:
            pass
    try:
        al = alerts(today)
    except Exception:
        al = ''
    last = [l for l in read(os.path.join(DIARY, today + '.md')).splitlines() if l.startswith('- ')][-8:]
    ctx = ('SECOND BRAIN (' + VAULT + '; the human edits it in Obsidian and their edits win). ACE method: after each '
           'task REFLECT (what went differently, which lesson applied) and CURATE one item at a time (bump a '
           'lesson\'s helped/failed counter or append a new lesson with date and evidence; never rewrite the file).\n\n'
           + ('STAGNATION ALERTS (act today):\n' + al + '\n\n' if al else '')
           + read(os.path.join(VAULT, 'Lessons.md'), 9000) + '\n\n' + read(os.path.join(VAULT, 'Direction.md'), 4000)
           + ('\n\nLatest diary lines:\n' + '\n'.join(last) if last else ''))
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': ctx}}))


# ---------- recall ----------
STOP = {'about', 'after', 'before', 'there', 'their', 'which', 'would', 'could', 'should', 'please', 'claude',
        'from', 'this', 'that', 'what', 'when', 'have', 'your', 'with', 'make', 'more', 'just', 'like', 'some',
        'sobre', 'antes', 'despues', 'cuando', 'porque', 'desde', 'hasta', 'entre', 'tiene', 'hacer', 'puede',
        'como', 'para', 'esta', 'este', 'esto', 'pero', 'todo', 'cada', 'solo', 'bien', 'hace', 'algo', 'nada'}


def roots(t):
    t = ''.join(c for c in unicodedata.normalize('NFKD', t.lower()) if not unicodedata.combining(c))
    return {w[:5] for w in re.findall(r'[a-z0-9]{4,}', t) if w not in STOP}


def recall(data):
    words = roots((data.get('prompt') or '')[:4000])
    if len(words) < 2:
        return
    cands = []
    for note in ('Lessons.md', 'Technical lessons.md', 'Working with me.md'):
        for l in read(os.path.join(VAULT, note)).splitlines():
            if re.match(r'^(- |\d+\. )\S', l):
                cands.append((note[:-3], l))
    mem = memory_dir(data)
    for f in (os.listdir(mem) if mem else []):
        m = re.search(r'^description:\s*(.+)$', read(os.path.join(mem, f), 1500), re.M)
        if m:
            cands.append(('memory ' + f[:-3], m.group(1)))
    ranked = sorted(((len(words & roots(t)), src, t) for src, t in cands), reverse=True)
    minimum = 2 if len(words) < 25 else 4     # long prompts share many words with everything
    picked = [(s, t) for n, s, t in ranked[:3] if n >= minimum]
    if picked:
        ctx = 'RECALL (lessons related to this request; apply them and count «helped» when you close):\n' + \
              '\n'.join('- [' + s + '] ' + short(t, 300) for s, t in picked)
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': ctx}}))


# ---------- diary ----------
def signals(msg, ts):
    t = msg.splitlines()[0][:200].lower() if msg.strip() else ''
    kind = 'Correction' if re.search(CORRECTION, t) else ('Confirmation' if re.search(CONFIRMATION, t) else '')
    if not kind:
        return
    p = os.path.join(VAULT, 'Corrections.md')
    new = not os.path.exists(p)
    with open(p, 'a', encoding='utf-8', newline='\n') as f:
        if new:
            f.write('# Corrections and confirmations\n\nDetected automatically in what the human writes. The daily '
                    'review moves the ones that teach something into [[Working with me]] and marks them «done». '
                    'Keeping confirmations too avoids drifting away from what works.\n\n')
        f.write('- ' + ts.strftime('%d/%m %H:%MZ') + ' **' + kind + ':** «' + short(msg, 220) + '»\n')


def diary(data):
    tp = data.get('transcript_path') or ''
    if not os.path.isfile(tp):
        return
    request, answer, human, scheduled = '', '', [], False
    with open(tp, encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            m = e.get('message') or {}
            if e.get('type') == 'system' and e.get('subtype') == 'scheduled_task_fire' and e.get('prompt'):
                request, answer, human, scheduled = str(e['prompt']), '', [], True   # scheduled tasks (crons)
            elif e.get('type') == 'queue-operation' and e.get('reason') == 'absorbed_mid_turn' \
                    and isinstance(e.get('content'), str) and e['content'].strip():
                request = (request + ' / ' + e['content']) if request else e['content']   # sent while working
                human.append(e['content'])
            elif e.get('type') == 'user' and m.get('role') == 'user' and not e.get('isMeta'):
                t = m.get('content')
                if isinstance(t, str) and t.strip() and not t.lstrip().startswith('<'):
                    if request and not answer:
                        request, human = request + ' / ' + t, human + [t]
                    else:
                        request, human, scheduled = t, [t], False
                    answer = ''
            elif e.get('type') == 'assistant':
                t = text_of(m.get('content'))
                if t.strip():
                    answer = t
    if not request or not answer:
        return
    who = 'scheduled' if scheduled else 'human'
    ts = now()
    os.makedirs(DIARY, exist_ok=True)
    p = os.path.join(DIARY, ts.strftime('%Y-%m-%d') + '.md')
    new = not os.path.exists(p)
    with open(p, 'a', encoding='utf-8', newline='\n') as f:
        if new:
            f.write('# Diary ' + ts.strftime('%Y-%m-%d') + '\n\nWritten by the brain hook after every answer. '
                    'Distilled daily into [[Lessons]].\n\n')
        f.write('- ' + ts.strftime('%H:%MZ') + ' **' + who + ':** ' + short(request, 160) + ' → ' + short(answer, 260) + '\n')
    for msg in human:
        signals(msg, ts)


# ---------- compact ----------
def compact(data):
    texts = []

    def walk(x):
        if isinstance(x, str) and len(x) > 300:
            texts.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(data)
    if texts:
        ts = now()
        d = os.path.join(VAULT, 'Sessions')
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, ts.strftime('%Y-%m-%d %H%M') + 'Z.md'), 'w', encoding='utf-8', newline='\n').write(
            '# Session summary ' + ts.strftime('%Y-%m-%d %H:%M') + ' UTC\n\nSaved by the PostCompact hook. What was '
            'learned goes to [[Lessons]].\n\n' + max(texts, key=len) + '\n')


if __name__ == '__main__':
    try:
        data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except Exception:
        data = {}
    try:
        {'start': start, 'recall': recall, 'diary': diary, 'compact': compact}[sys.argv[1]](data)
    except Exception:
        pass
