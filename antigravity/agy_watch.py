"""Watch and talk to an `agy` session that streams NDJSON.

One-shot dispatch (agy -p "<spec>" --output-format stream-json > LOG):
    python -I agy_watch.py LOG                      snapshot, then exit
    python -I agy_watch.py LOG --follow             print steps as they land

Live chat session (agy reads its turns from INBOX, see the skill):
    python -I agy_watch.py LOG --send INBOX "text"  send one turn, follow its reply
    python -I agy_watch.py LOG --send INBOX @file   same, message read from a file

--follow and --send stop at the first of: the turn's result, a stall (no event
for --stall s), or --budget s (default 540, under the 600 s tool cap).

Exit codes:
  0  turn finished                 2  agy is asking: last reply line starts ASK:
  1  turn finished with an error   3  stalled
  4  budget spent, still running   5  log never appeared
"""
import argparse
import json
import os
import sys
import time

NOISE = ("TLS handshake error",)  # agy's internal server chatter, not about the task


def read_events(path, since=0):
    """Parsed events from line `since` on, plus raw non-JSON lines."""
    events, raw = [], []
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f):
            if n < since:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except ValueError:
                if not any(k in line for k in NOISE):
                    raw.append(line)
    return events, raw


def line_count(path):
    if not os.path.exists(path):
        return 0
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def detail(s):
    params = (s.get("tool_info") or {}).get("parameters") or {}
    for key in ("CommandLine", "TargetFile", "AbsolutePath", "DirectoryPath", "Query", "Url"):
        if key in params:
            return str(params[key])
    return next((str(v) for v in params.values() if isinstance(v, str)), "")


class Turn:
    """Folds a stream of events into printable step lines."""

    def __init__(self):
        self.init, self.steps, self.order, self.text, self.result = None, {}, [], {}, None

    def feed(self, ev):
        kind = ev.get("event")
        if kind == "init":
            self.init = dict(ev.get("init", {}), conversation_id=ev.get("conversation_id"))
        elif kind == "step_update":
            s = ev["step_update"]
            i = s.get("step_index")
            if i not in self.steps:
                self.order.append(i)
            self.steps[i] = s
            if s.get("text_delta"):
                self.text[i] = self.text.get(i, "") + s["text_delta"]
        elif kind == "result":
            self.result = ev["result"]

    def line(self, i):
        s = self.steps[i]
        kind, state = s.get("step_type", "?"), s.get("state", "?")
        if kind == "user_input":
            return None
        if kind == "agent_response":
            # prose streams in deltas; show it once the step settles
            said = self.text.get(i, "").strip()
            if state != "DONE" or not said:
                return None
            first = said.splitlines()[0]
            more = "  ..." if len(said.splitlines()) > 1 else ""
            return f"#{i:<3} gemini: {first[:120]}{more}"
        out = f"#{i:<3} {state:<6} {s.get('tool_name') or kind}"
        d = detail(s).replace("\n", " ")
        if d:
            out += f"  {d[:110]}"
        if s.get("duration_seconds"):
            out += f"  ({s['duration_seconds']:.0f}s)"
        err = (s.get("tool_info") or {}).get("error")
        if err:
            out += f"\n      ! {err.get('message', '').splitlines()[0][:140]}"
        return out


def result_lines(r):
    u = r.get("usage", {})
    yield (f"RESULT {r.get('status')}  {r.get('duration_seconds', 0):.0f}s  "
           f"in {u.get('input_tokens')} out {u.get('output_tokens')}  "
           f"turn {r.get('num_turns')}  conv {r.get('conversation_id')}")
    for d in r.get("denied_actions") or []:
        yield f"  denied: {d.get('display_name') or d.get('action')}"
    if r.get("error"):
        yield f"  error: {r['error'][:200]}"
    reply = (r.get("response") or "").strip()
    if reply:
        lines = reply.splitlines()
        for ln in lines[:15]:
            yield f"  | {ln[:160]}"
        if len(lines) > 15:
            yield f"  | ... ({len(lines) - 15} more lines)"


def verdict(r):
    if r.get("status") != "SUCCESS":
        return 1
    tail = [ln.strip() for ln in (r.get("response") or "").splitlines() if ln.strip()]
    if tail and tail[-1].upper().startswith("ASK:"):
        return 2
    return 0


def snapshot(path):
    events, raw = read_events(path)
    t = Turn()
    for ev in events:
        t.feed(ev)
        if ev.get("event") == "init":
            print(f"model {t.init.get('model')}  conv {t.init.get('conversation_id')}")
        if ev.get("event") == "result":
            for i in t.order:
                ln = t.line(i)
                if ln:
                    print(ln)
            for ln in result_lines(t.result):
                print(ln)
            conv = t.init
            t = Turn()
            t.init = conv
    for i in t.order:
        ln = t.line(i)
        if ln:
            print(ln)
    for r in raw:
        print(f"  ~ {r[:160]}")
    if t.order:
        age = time.time() - os.path.getmtime(path)
        print(f"RUNNING  last event {age:.0f}s ago")
        return 4
    print(f"next --since {line_count(path)}")
    return 0


def follow(path, since, budget, stall):
    start = time.time()
    while not os.path.exists(path):
        if time.time() - start > 60:
            print("log never appeared - did agy start?")
            return 5
        time.sleep(1)

    shown, shown_raw = {}, 0
    said_init = since > 0  # a later turn in a live session: init was already reported
    last_change = time.time()
    while True:
        events, raw = read_events(path, since)
        t = Turn()
        for ev in events:
            t.feed(ev)
        changed = False
        if t.init and not said_init:
            print(f"model {t.init.get('model')}  conv {t.init.get('conversation_id')}", flush=True)
            said_init = changed = True
        for i in t.order:
            ln = t.line(i)
            if ln and shown.get(i) != ln:
                print(ln, flush=True)
                shown[i] = ln
                changed = True
        for r in raw[shown_raw:]:
            print(f"  ~ {r[:160]}", flush=True)
            changed = True
        shown_raw = len(raw)
        if changed:
            last_change = time.time()

        if t.result:
            for ln in result_lines(t.result):
                print(ln, flush=True)
            code = verdict(t.result)
            if code == 2:
                print("ASKING  answer with --send", flush=True)
            print(f"next --since {line_count(path)}", flush=True)
            return code

        quiet = time.time() - last_change
        if quiet > stall:
            live = [t.steps[i] for i in t.order if t.steps[i].get("state") == "ACTIVE"]
            what = t.line(live[-1]["step_index"]) if live else None
            what = what.split("\n")[0] if what else "no active step"
            print(f"STALL  {quiet:.0f}s without an event; last active: {what}", flush=True)
            return 3
        if time.time() - start > budget:
            print(f"STILL RUNNING after {budget}s - follow again with --since {since}", flush=True)
            return 4
        time.sleep(2)


def send(inbox, text):
    if text.startswith("@"):
        with open(text[1:], encoding="utf-8") as f:
            text = f.read()
    msg = {"event": "user", "message": {"content": text}}
    with open(inbox, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--follow", action="store_true")
    ap.add_argument("--since", type=int, default=0, help="ignore log lines before this one")
    ap.add_argument("--send", nargs=2, metavar=("INBOX", "TEXT"))
    ap.add_argument("--budget", type=int, default=540)
    ap.add_argument("--stall", type=int, default=240)
    a = ap.parse_args()

    if a.send:
        mark = line_count(a.log)  # the reply to this message starts after here
        send(*a.send)
        return follow(a.log, mark, a.budget, a.stall)
    if a.follow:
        return follow(a.log, a.since, a.budget, a.stall)
    if not os.path.exists(a.log):
        print("log not found")
        return 5
    return snapshot(a.log)


if __name__ == "__main__":
    sys.exit(main())
