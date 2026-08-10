#!/usr/bin/env python3
"""Check gitDrill's answers against real git, the way verify_sql.py uses a real
PostgreSQL server.

Until this existed, gitDrill's answers were checked by reading them, which is
exactly the weakness noted in CLAUDE.md. git is installed, so most of the deck
has an oracle available:

  history   Build the commit graph for real, run the command, read back
            git log --oneline, and map the hashes to labels. A commit whose
            subject is B but whose hash is not B's original hash is B' -- so
            the primes in the expected answer are DERIVED, not asserted. This
            is the check that matters most: whether rebase rewrites and merge
            does not is the whole point of the mode, and it is now measured.

  command   Run the answer, and every accepted alternative, in a prepared
            scratch repo (with a real bare remote, a modified file, a staged
            file and an untracked file) and require it to succeed. Commands
            that need a state this harness does not build carry
            "verify": "exists" and are only checked for being real git
            subcommands -- which still catches a typo like "git brunch".

  fill      The blank is filled in and the whole line run the same way.

  danger    Scenario probes: build the described state, run the command, then
            actually try to recover. The three-way rating is a factual claim
            about git and can be tested rather than asserted.

    python3 tools/verify_git.py
"""
import os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import git_deck

ENV = dict(os.environ,
           GIT_AUTHOR_NAME="D", GIT_AUTHOR_EMAIL="d@e",
           GIT_COMMITTER_NAME="D", GIT_COMMITTER_EMAIL="d@e",
           GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null",
           GIT_TERMINAL_PROMPT="0",
           # nothing may open an editor or the harness hangs
           GIT_EDITOR="true", GIT_SEQUENCE_EDITOR="true")


def sh(cmd, cwd, check=True):
    r = subprocess.run(cmd, cwd=cwd, shell=True, env=ENV,
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{cmd}\n{r.stderr.strip()}")
    return r


COMMIT_CLOCK = [0]


def commit(repo, label):
    """One commit whose subject IS its label, so the log maps back to letters.

    Each commit gets a distinct, increasing timestamp. Without that every commit
    in a freshly built graph shares a second, and `git log` — which walks in
    commit-date order — returns them in an arbitrary sequence, so the check
    would be measuring the harness rather than git.
    """
    with open(os.path.join(repo, f"{label}.txt"), "w") as f:
        f.write(label)
    COMMIT_CLOCK[0] += 60
    when = f"2026-01-01T00:00:{COMMIT_CLOCK[0] % 60:02d}+00:00"
    when = f"@{1767225600 + COMMIT_CLOCK[0]} +0000"
    env = dict(ENV, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    r = subprocess.run(f"git add -A && git commit -q -m {label}", cwd=repo,
                       shell=True, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)


# --- the graphs the deck draws, built for real -----------------------------
# Keyed by the ASCII art itself, exactly like sql_deck.SETUP.
FORK = git_deck.FORK
FF = "before:\nA---B          main (HEAD)\n     \\\n      C---D    feature"


def build_fork(repo):
    """A---B---C main, with feature branching at B and carrying D---E."""
    sh("git init -q -b main .", repo)
    commit(repo, "A")
    commit(repo, "B")
    sh("git branch feature", repo)
    commit(repo, "C")
    sh("git switch -q feature", repo)
    commit(repo, "D")
    commit(repo, "E")
    sh("git switch -q main", repo)


def build_ff(repo):
    """A---B main, feature ahead with C---D: main has nothing of its own."""
    sh("git init -q -b main .", repo)
    commit(repo, "A")
    commit(repo, "B")
    sh("git switch -q -c feature", repo)
    commit(repo, "C")
    commit(repo, "D")
    sh("git switch -q main", repo)


LINEAR = git_deck.LINEAR
ONTO = git_deck.ONTO


def build_linear(repo):
    """A---B---C on main and nothing else."""
    sh("git init -q -b main .", repo)
    for label in ("A", "B", "C"):
        commit(repo, label)


def build_onto(repo):
    """main A---B---C, old-base X---Y off B, feature D---E off Y."""
    sh("git init -q -b main .", repo)
    commit(repo, "A")
    commit(repo, "B")
    sh("git switch -q -c old-base", repo)
    commit(repo, "X")
    commit(repo, "Y")
    sh("git switch -q -c feature", repo)
    commit(repo, "D")
    commit(repo, "E")
    sh("git switch -q main", repo)
    commit(repo, "C")


GRAPHS = {FORK: build_fork, FF: build_ff, LINEAR: build_linear, ONTO: build_onto}

# An interactive rebase's real "command" includes what you type in the editor.
# The card says so in prose; the harness needs it as a non-interactive script,
# and that belongs here rather than in the deck.
HIST_ENV = {
    # No $ in the sed: git runs the editor through sh -c without quoting, so a
    # $ in the value is expanded away before sed ever sees it.
    "g13-002/history[0]": "GIT_SEQUENCE_EDITOR='sed -i 2s/pick/squash/' ",
}


def label_map(repo):
    """subject -> hash, before anything rewrites them."""
    out = sh("git log --all --format=%H%x09%s", repo).stdout
    m = {}
    for line in out.strip().split("\n"):
        h, subject = line.split("\t", 1)
        m.setdefault(subject, h)
    return m


def read_labels(repo, cmd, originals):
    """git log as the deck writes it: newest first, a prime where rewritten."""
    out = sh(cmd, repo).stdout.strip()
    labels = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        # --graph decorations are not used here; the format is "<hash> <subject>"
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue
        short, subject = parts
        full = sh(f"git rev-parse {short}", repo).stdout.strip()
        original = originals.get(subject)
        # A subject that did not exist before is a NEW commit (a merge commit,
        # a revert), not a rewritten one, so it takes no prime. Only a label
        # that existed and now has a different hash has been rewritten.
        rewritten = original is not None and original != full
        labels.append(subject + "'" if rewritten else subject)
    return " ".join(labels)


def check_history(fails):
    n = 0
    for card in git_deck.CARDS:
        for i, it in enumerate(card.get("history", [])):
            qid = f"{card['id']}/history[{i}]"
            art = it.get("fixture", card.get("fixture"))
            if art not in GRAPHS:
                fails.append(f"{qid}: no builder for its graph")
                continue
            repo = tempfile.mkdtemp()
            try:
                GRAPHS[art](repo)
                # Which branch the card says you are standing on. rebase and
                # merge mean opposite things depending on it, so it is declared
                # per item rather than inferred from the prompt.
                sh(f"git switch -q {it.get('on', 'main')}", repo)
                originals = label_map(repo)
                # the card's cmd may carry a trailing "# then: <log command>"
                cmd, _, tail = it["cmd"].partition("#")
                log_cmd = "git log --oneline"
                if tail.strip().startswith("then:"):
                    log_cmd = tail.split("then:", 1)[1].strip()
                # letters in the command name commits; resolve them to hashes
                run = re.sub(r"\b([A-E])\b", lambda m: originals[m.group(1)], cmd.strip())
                # A real merge would open an editor; -m names the merge commit
                # M so it reads back as the deck writes it.
                if run.startswith("git merge"):
                    run += " -m M"
                r = sh(HIST_ENV.get(qid, "") + run, repo, check=False)
                if r.returncode != 0:
                    fails.append(f"{qid}: {run} failed — {r.stderr.strip().splitlines()[-1]}")
                    continue
                merges = sh("git rev-list --merges HEAD", repo).stdout.strip()
                if merges and "--first-parent" not in log_cmd:
                    fails.append(f"{qid}: the result contains a merge but the log has no "
                                 f"--first-parent, so the order depends on commit "
                                 f"timestamps the learner cannot see")
                got = read_labels(repo, log_cmd, originals)
                if got != it["answer"]:
                    fails.append(f"{qid}: git says {got!r}, deck says {it['answer']!r}")
                n += 1
            finally:
                shutil.rmtree(repo, ignore_errors=True)
    return n


# --- command / fill: does it actually run? ---------------------------------
def build_scratch(root):
    """A repo with what the deck's commands tend to need: history, a second
    branch, a real bare remote with an upstream, and a modified, a staged and an
    untracked file.

    Deliberately NO branch called `feature` and no `upstream` remote -- several
    cards create exactly those, and a pre-existing one made the command fail for
    a reason that had nothing to do with the card.
    """
    remote = os.path.join(root, "remote.git")
    repo = os.path.join(root, "work")
    os.makedirs(repo)
    sh(f"git init -q --bare {remote}", root)
    sh("git init -q -b main .", repo)
    commit(repo, "A")
    commit(repo, "B")
    sh("git branch other", repo)
    commit(repo, "C")
    sh(f"git remote add origin {remote} && git push -q -u origin main", repo)
    sh("git tag base", repo)
    with open(os.path.join(repo, "f"), "w") as fh:
        fh.write("tracked\n")
    sh("git add f && git commit -q -m f", repo)
    with open(os.path.join(repo, "secrets.env"), "w") as fh:
        fh.write("k=v\n")
    sh("git add secrets.env && git commit -q -m secrets", repo)
    with open(os.path.join(repo, "parser.py"), "w") as fh:
        fh.write("\n".join(f"line {i}" for i in range(1, 80)) + "\n")
    sh("git add parser.py && git commit -q -m parser", repo)
    # a commit that is NOT an ancestor of main, so cherry-pick has something to
    # pick that is not already applied
    sh("git switch -q -c pickable other", repo)
    commit(repo, "P")
    sh("git switch -q main", repo)
    # the dirty state comes LAST, or a later commit swallows the staged file
    with open(os.path.join(repo, "f"), "a") as fh:
        fh.write("edited\n")           # modified, unstaged
    with open(os.path.join(repo, "staged.txt"), "w") as fh:
        fh.write("s\n")
    sh("git add staged.txt", repo)      # staged, uncommitted
    with open(os.path.join(repo, "new.py"), "w") as fh:
        fh.write("n\n")                 # untracked
    return repo


# Per-item state the scratch repo does not have by default. Keyed by card id and
# mode, run in the repo before the command. Writing these out is what turns
# "the subcommand exists" into "this actually works", which is the difference
# between checking spelling and checking the answer.
SETUPS = {
    "g3-003/fill":     "git stash -q -u && git switch -q other && git switch -q main",
    "g4-003/command":  ("git stash -q -u && git switch -q -c conflicting other && "
                        "echo x > c.txt && git add -A && git commit -qm ca && "
                        "git switch -q main && echo y > c.txt && git add -A && "
                        "git commit -qm cb && (git merge conflicting || true)"),
    "g4-004/command":  "git stash -q -u",
    "g5-004/command":  "git stash -q -u && git branch old-base other && git branch feature pickable",
    "g5-004/fill":     "git stash -q -u && git branch old-base other && git branch feature pickable",
    "g5-005/command":  ("git stash -q -u && git switch -q -c conflicting other && "
                        "echo x > c.txt && git add -A && git commit -qm ca && "
                        "git switch -q main && echo y > c.txt && git add -A && "
                        "git commit -qm cb && (git rebase conflicting || true) && "
                        "echo r > c.txt && git add c.txt"),
    "g6-003/command":  "git stash -q -u",
    "g7-003/command":  "git stash -q -u",
    "g9-003/command":  "git branch feature other",
    "g9-003/fill":     "git branch feature other",
    "g7-002/command":  "git stash -q -u && git reset -q --hard HEAD~1",
    "g8-003/command":  "git stash -q",
    "g10-004/command": "git branch feature other && git push -q origin feature",
    "g12-001/command": "git stash -q -u",
    "g12-002/command": ("git stash -q -u && git merge --no-ff -q -m M other"),
    "g13-001/command": "git stash -q -u",
    "g13-002/fill":    "git stash -q -u",
    "g15-001/command": "git stash -q -u && git switch -q other",
}

# Genuinely unrunnable here, with the reason. Kept short and explicit so the
# list cannot quietly grow.
EXISTS_ONLY = {
    "g14-002/fill": "runs pytest, which is not installed",
    "g14-001/command": "bisect start leaves the repo bisecting; harmless but stateful",
}

SUBCOMMANDS = None


SUBCOMMANDS = None


def git_subcommands():
    global SUBCOMMANDS
    if SUBCOMMANDS is None:
        out = subprocess.run("git --list-cmds=main,others,alias,nohelpers",
                             shell=True, capture_output=True, text=True, env=ENV).stdout
        SUBCOMMANDS = set(out.split())
    return SUBCOMMANDS


PLACEHOLDER = re.compile(r"<[a-z]+>|\bd4e5f6\b|\ba1b2c3\b|\bDEBUG_MODE\b|\bM\b(?!\w)")


def runnable(cmd, repo):
    """Substitute the deck's stand-in tokens for things this repo really has."""
    head = sh("git rev-parse HEAD", repo).stdout.strip()
    pick = sh("git rev-parse pickable", repo).stdout.strip()
    merge = sh("git rev-parse HEAD", repo).stdout.strip()
    cmd = cmd.replace("<commit>", head).replace("<merge>", merge).replace("<tag>", "base")
    # d4e5f6 stands for "some other commit" in the deck; a cherry-pick or a
    # branch-recreate needs one that is not already in this branch's history.
    cmd = cmd.replace("d4e5f6", pick).replace("a1b2c3", head)
    cmd = re.sub(r"\bM\b(?!\w)", merge, cmd) if cmd.startswith("git revert -m") \
        or cmd.startswith("git revert --mainline") else cmd
    return cmd


def check_commands(fails, notes, skipped):
    known = git_subcommands()
    ran = existed = 0
    for card in git_deck.CARDS:
        for mode in ("command", "fill"):
            for i, it in enumerate(card.get(mode, [])):
                qid = f"{card['id']}/{mode}[{i}]"
                if mode == "fill":
                    # every accepted spelling of the blank, not just the answer
                    line = [l for l in it["code"].split("\n") if "_" in l][0]
                    cands = [line.replace("__", str(a))
                             for a in [it["answer"]] + list(it.get("accept", []))]
                else:
                    cands = [it["answer"]] + list(it.get("accept", []))

                for cand in cands:
                    words = cand.split()
                    if not words or words[0] != "git":
                        fails.append(f"{qid}: {cand!r} is not a git command")
                        continue
                    sub = words[1] if len(words) > 1 else ""
                    if sub and not sub.startswith("-") and sub not in known:
                        fails.append(f"{qid}: git has no subcommand {sub!r} ({cand!r})")
                        continue
                    existed += 1

                    key = f"{card['id']}/{mode}"
                    if key in EXISTS_ONLY:
                        skipped.append(f"{key}: {EXISTS_ONLY[key]}")
                        continue
                    root = tempfile.mkdtemp()
                    try:
                        repo = build_scratch(root)
                        if key in SETUPS:
                            sh(SETUPS[key], repo)
                        r = sh(runnable(cand, repo), repo, check=False)
                        if r.returncode != 0:
                            msg = ((r.stderr or r.stdout).strip().splitlines() or ["(no output)"])[-1]
                            notes.append(f"{qid}: {cand!r} exited {r.returncode} — {msg[:90]}")
                        else:
                            ran += 1
                    finally:
                        shutil.rmtree(root, ignore_errors=True)
    return existed, ran


# --- danger: is the rating true? -------------------------------------------
# The three-way scale is a factual claim about git, so it is measured rather
# than asserted. Two probe kinds cover the deck:
#
#   content  a canary string is put somewhere, the dangerous command runs, and
#            we ask where the canary ended up. In the working tree (possibly
#            after the card's own documented recovery) is SAFE; only inside a
#            git object is RECOVERABLE, because the reflog or fsck can reach it;
#            nowhere at all is GONE. `git cat-file --batch-all-objects` makes
#            "is it anywhere in the object store" a single honest question.
#
#   commit   the thing at risk is a COMMIT, not content -- a rebase keeps every
#            byte while replacing every hash. Reachable from a branch is SAFE,
#            existing but unreferenced is RECOVERABLE, absent is GONE.
CANARY = "CANARY-8f3a"

PROBES = {
    "g2-002": dict(kind="content",
                   setup=f"echo {CANARY} > brand-new.py",
                   cmd="git commit -a -q -m 'add feature'"),
    "g2-003": dict(kind="commit",
                   setup=f"echo {CANARY} >> f && git add -A && git commit -qm x && "
                         "echo other > f && git add -A",
                   cmd="git commit --amend --no-edit -q"),
    "g2-004": dict(kind="content",
                   setup=f"echo {CANARY} >> f",
                   cmd="git restore f"),
    "g3-004": dict(kind="commit", ref="doomed",
                   setup=f"git stash -q -u && git switch -q -c doomed && "
                         f"echo {CANARY} > d.txt && git add -A && git commit -qm d && "
                         "git switch -q main",
                   cmd="git branch -D doomed"),
    "g4-003": dict(kind="content",
                   setup=("git stash -q -u && git switch -q -c conflicting other && "
                          "echo x > c.txt && git add -A && git commit -qm ca && "
                          "git switch -q main && echo y > c.txt && git add -A && "
                          "git commit -qm cb && "
                          f"echo {CANARY} >> f && (git merge conflicting || true)"),
                   cmd="git merge --abort"),
    "g5-001": dict(kind="commit",
                   setup="git stash -q -u && git switch -q -c work other && "
                         "echo w > w.txt && git add -A && git commit -qm D",
                   cmd="git rebase -q main"),
    "g6-002": dict(kind="content",
                   setup=f"echo {CANARY} >> f",
                   cmd="git reset -q --hard HEAD~1"),
    "g6-004": dict(kind="content",
                   setup=f"echo {CANARY} > junk.local",
                   cmd="git clean -fdxq"),
    "g7-002": dict(kind="content",
                   setup=f"echo {CANARY} >> f && git add -A && git commit -qm x",
                   cmd="git reset -q --hard HEAD~1"),
    "g8-001": dict(kind="content",
                   setup=f"echo {CANARY} >> f",
                   cmd="git stash -q",
                   restore="git stash pop -q"),
    "g13-002": dict(kind="commit",
                    setup="git stash -q -u && echo a > s1 && git add -A && git commit -qm s1 && "
                          "echo b > s2 && git add -A && git commit -qm s2",
                    cmd="GIT_SEQUENCE_EDITOR='sed -i 2,\\$s/^pick/squash/' git rebase -i -q HEAD~2"),
}

# Claims this harness deliberately does not test, with the reason. Both are
# about what a DIFFERENT clone still holds, which needs a two-repo scenario and
# a judgement about coordinating with a colleague rather than a git fact.
UNPROBED = {
    "g5-003": "the claim is about a colleague's clone, not this repository",
    "g10-002": "same — recovery depends on someone else still having the commits",
    "g5-005": "a skipped commit mid-rebase; reachable only through a conflicted rebase state",
}


def observed_level(repo, probe, before_hash):
    if probe["kind"] == "content":
        if probe.get("restore"):
            sh(probe["restore"], repo, check=False)
        tree = subprocess.run(f"grep -rqs {CANARY} . --exclude-dir=.git",
                              cwd=repo, shell=True, env=ENV)
        if tree.returncode == 0:
            return 0                                   # SAFE
        objs = subprocess.run(
            f"git cat-file --batch-all-objects --batch 2>/dev/null | grep -qs {CANARY}",
            cwd=repo, shell=True, env=ENV)
        return 1 if objs.returncode == 0 else 2        # RECOVERABLE / GONE
    reachable = sh(f"git merge-base --is-ancestor {before_hash} HEAD", repo, check=False)
    if reachable.returncode == 0:
        return 0
    exists = sh(f"git cat-file -e {before_hash}", repo, check=False)
    return 1 if exists.returncode == 0 else 2


LEVEL_NAME = ["safe", "recoverable", "gone"]


def check_danger(fails, skipped):
    n = 0
    for card in git_deck.CARDS:
        for i, it in enumerate(card.get("danger", [])):
            cid = card["id"]
            if cid in UNPROBED:
                skipped.append(f"{cid}/danger: {UNPROBED[cid]}")
                continue
            if cid not in PROBES:
                fails.append(f"{cid}/danger: no probe and no documented reason")
                continue
            probe = PROBES[cid]
            root = tempfile.mkdtemp()
            try:
                repo = build_scratch(root)
                sh(probe["setup"], repo)
                before = sh(f"git rev-parse {probe.get('ref', 'HEAD')}", repo).stdout.strip()
                r = sh(probe["cmd"], repo, check=False)
                if r.returncode != 0 and probe["kind"] == "commit":
                    fails.append(f"{cid}/danger: probe command failed — "
                                 f"{(r.stderr or '').strip().splitlines()[-1:]}")
                    continue
                got = observed_level(repo, probe, before)
                if got != it["answer"]:
                    fails.append(f"{cid}/danger: git behaves as {LEVEL_NAME[got]!r}, "
                                 f"deck rates it {LEVEL_NAME[it['answer']]!r}")
                n += 1
            finally:
                shutil.rmtree(root, ignore_errors=True)
    return n


def main():
    fails, notes = [], []
    n_hist = check_history(fails)
    skipped = []
    n_exist, n_ran = check_commands(fails, notes, skipped)
    n_danger = check_danger(fails, skipped)

    print(f"history: {n_hist} graphs built and replayed in real git")
    print(f"commands: {n_exist} checked as real subcommands, {n_ran} ran cleanly")
    print(f"danger: {n_danger} ratings tested empirically")
    for sk in sorted(set(skipped)):
        print(f"  skip  {sk}")
    for n in notes:
        print(f"  note  {n}")
    for f in fails:
        print(f"  FAIL  {f}")
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
