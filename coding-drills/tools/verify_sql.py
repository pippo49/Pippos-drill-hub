#!/usr/bin/env python3
"""Run every sqlDrill predict and rows query against a real PostgreSQL server.

Hand-computed SQL results are exactly the kind of thing that looks right and is
not: a LEFT JOIN row count, what NOT IN does with a NULL, whether RANK skips.
Those are the cards worth having and the cards easiest to get wrong, so the
answers are checked by the database rather than by whoever wrote them.

It also enforces the deck's own lesson back on itself: a predict query that
returns more than one row must carry an ORDER BY, or its expected output is
only the order the planner happened to choose today.

Needs a server. Start a throwaway one with:

    initdb -D /tmp/pgdata -A trust -U pg
    pg_ctl -D /tmp/pgdata -o '-p 5433 -k /tmp' start

    python3 tools/verify_sql.py                    # uses PGPORT or 5433

Cards that cannot be checked this way carry "verify": False with a reason --
EXPLAIN output, anything involving now(), and statements whose point is that
they raise. Every skip is printed, so the list stays honest.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sql_deck

HOST = os.environ.get("PGHOST", "/tmp")
PORT = os.environ.get("PGPORT", "5433")
USER = os.environ.get("PGUSER", "pg")


def psql(sql, db="postgres"):
    r = subprocess.run(
        ["psql", "-h", HOST, "-p", PORT, "-U", USER, "-d", db,
         "-q", "-v", "ON_ERROR_STOP=1", "-tAF|", "-P", "null=NULL", "-c", sql],
        capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def fresh_db(name, setup):
    psql(f'DROP DATABASE IF EXISTS "{name}"')
    rc, _, err = psql(f'CREATE DATABASE "{name}"')
    if rc != 0:
        raise SystemExit(f"cannot create database: {err}")
    if setup.strip():
        rc, _, err = psql(setup, db=name)
        if rc != 0:
            raise SystemExit(f"fixture setup failed: {err}")


def clone_db(template, name):
    """A throwaway copy per query. Several cards mutate their fixture — an
    UPDATE ... RETURNING, a DELETE ... RETURNING, a CREATE TEMP TABLE — and
    running them against a shared database made each one depend on whichever
    ran first. Cloning is cheap enough at this deck size and removes the
    ordering dependency entirely."""
    psql(f'DROP DATABASE IF EXISTS "{name}"')
    rc, _, err = psql(f'CREATE DATABASE "{name}" TEMPLATE "{template}"')
    if rc != 0:
        raise SystemExit(f"cannot clone {template}: {err}")


# Physically reshuffle every table. A predict card whose ORDER BY is not a TOTAL
# order looks deterministic against one physical layout and silently depends on
# it: two rows tying on the sort key can come back either way round. Running
# each query against several shuffles is what turns that from "I did not notice"
# into a build failure.
SHUFFLE = """
DO $$DECLARE r record; BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('CREATE TABLE %I_shuf AS SELECT * FROM %I ORDER BY random()',
                   r.tablename, r.tablename);
    EXECUTE format('TRUNCATE %I', r.tablename);
    EXECUTE format('INSERT INTO %I SELECT * FROM %I_shuf', r.tablename, r.tablename);
    EXECUTE format('DROP TABLE %I_shuf', r.tablename);
  END LOOP;
END$$;
"""


def strip_parens(sql):
    """Drop every parenthesised group, so only top-level clauses remain."""
    out, depth = [], 0
    for ch in sql:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def normalise(out):
    """psql -tAF| prints row-per-line, pipe-separated; -P null=NULL spells out
    nulls so an all-null row is a real line rather than a blank one. Booleans
    come back as psql prints them, t and f."""
    return out.rstrip("\n")


def main():
    rc, out, err = psql("select 1")
    if rc != 0:
        raise SystemExit(f"no PostgreSQL server on {HOST}:{PORT} — {err.strip()}")

    # one database per fixture, built once
    dbs = {}
    for i, (art, setup) in enumerate(sql_deck.SETUP.items()):
        name = f"drillfix{i}"
        fresh_db(name, setup)
        dbs[art] = name

    checked = skipped = 0
    fails, skips, unordered, unstable = [], [], [], []

    for card in sql_deck.CARDS:
        art = card.get("fixture")
        for mode in ("predict", "rows"):
            for i, it in enumerate(card.get(mode, [])):
                qid = f"{card['id']}/{mode}[{i}]"
                fixture = it.get("fixture", art)
                if it.get("verify") is False:
                    skipped += 1
                    skips.append(f"{qid}: {it.get('verify_note', 'no reason given')}")
                    continue
                if fixture not in dbs:
                    fails.append(f"{qid}: fixture has no SETUP entry")
                    continue

                # A CTE, not a subquery: DELETE/UPDATE ... RETURNING is legal
                # inside WITH and illegal in a FROM clause.
                query = it["code"]
                if mode == "rows":
                    query = f"WITH _q AS (\n{query.rstrip().rstrip(';')}\n) SELECT count(*) FROM _q;"
                clone_db(dbs[fixture], "drillrun")
                rc, out, err = psql(query, db="drillrun")
                checked += 1
                if rc != 0:
                    fails.append(f"{qid}: query failed — {err.strip().splitlines()[-1]}")
                    continue
                got = normalise(out)

                # same query, different physical row order, three times over
                if mode == "predict" and len(got.splitlines()) > 1:
                    for _ in range(3):
                        clone_db(dbs[fixture], "drillrun")
                        psql(SHUFFLE, db="drillrun")
                        rc2, out2, _ = psql(query, db="drillrun")
                        if rc2 == 0 and normalise(out2) != got:
                            unstable.append(f"{qid}: order changed when rows were "
                                            f"reshuffled — {got!r} vs {normalise(out2)!r}")
                            break

                want = str(it["output"] if mode == "predict" else it["answer"]).strip()
                if got != want:
                    fails.append(f"{qid}: postgres says {got!r}, deck says {want!r}")

                # The deck teaches that no ORDER BY means no order, so hold it to
                # that. Parenthesised groups are stripped first: the ORDER BY
                # inside OVER (...) or a subquery orders that construct, not the
                # result, and a naive substring search reads it as ordering.
                if mode == "predict" and len(got.split("\n")) > 1 \
                        and "order by" not in strip_parens(query).lower():
                    unordered.append(f"{qid}: {len(got.splitlines())} rows, no top-level ORDER BY")

    psql('DROP DATABASE IF EXISTS "drillrun"')
    for name in dbs.values():
        psql(f'DROP DATABASE IF EXISTS "{name}"')

    print(f"verified {checked} queries against PostgreSQL, {skipped} skipped")
    for s in skips:
        print(f"  skip  {s}")
    for u in unordered:
        print(f"  ORDER {u}")
    for u in unstable:
        print(f"  TIE   {u}")
    for f in fails:
        print(f"  FAIL  {f}")
    if fails or unordered or unstable:
        sys.exit(1)


if __name__ == "__main__":
    main()
