#!/usr/bin/env python3
"""sqlDrill deck — curated. Built by tools/build_deck.py, never hand-edited JSON.

Dialect: PostgreSQL. Where MySQL or SQLite genuinely behave differently the card
says so, because the difference is the lesson — a deck that silently teaches one
vendor's habit as "SQL" is worse than no deck.

Answer format for predict cards: the result rows in order, one per line, columns
separated by | and a null written as NULL. Most cards deliberately select a
single column so there is no separator to get wrong; the few that need two carry
a spaced variant in the accept-list, since a space either side of the pipe is a
formatting choice, not a wrong answer.
"""

TOPICS = [
    ("s1",  "SELECT, WHERE, ORDER BY"),
    ("s2",  "NULL & three-valued logic"),
    ("s3",  "Joins"),
    ("s4",  "Aggregation & GROUP BY"),
    ("s5",  "Subqueries & EXISTS"),
    ("s6",  "Set operations"),
    ("s7",  "CTEs"),
    ("s8",  "Window functions"),
    ("s9",  "Recursive CTEs"),
    ("s10", "CASE, COALESCE & casting"),
    ("s11", "INSERT, UPDATE, DELETE"),
    ("s12", "Constraints & keys"),
    ("s13", "Transactions & isolation"),
    ("s14", "Indexes & EXPLAIN"),
]

# The house fixture. Barbara has no department and Legal has no employees, so
# every join type gives a different row count -- which is the whole point.
EMP = """employees                 departments
 id | name    | dept | sal    id | name
----+---------+------+----   ----+-------
  1 | Ada     |   10 | 100     10 | Eng
  2 | Grace   |   10 |  90     20 | Sales
  3 | Linus   |   20 |  80     30 | Legal
  4 | Barbara | NULL |  70"""

# Ties on purpose: the three ranking functions all disagree here.
NO_TABLES = "-- PostgreSQL, no tables needed"

# One order with three items, one with a single item, one with none: enough to
# show fan-out, an anti-join, and why summing across a join inflates a total.
ORD = """orders                items
 id | cust  | total    ord | sku | qty
----+-------+------   -----+-----+----
  1 | Ada   |  100       1 | A   |  2
  2 | Grace |   50       1 | B   |  1
  3 | Linus |   30       1 | C   |  3
                         2 | A   |  1"""

# A three-level tree with one branch two deep, for recursive CTEs.
TREE = """node
 id | parent | name
----+--------+------
  1 |  NULL  | root
  2 |     1  | a
  3 |     1  | b
  4 |     2  | a1
  5 |     4  | a1x"""

# An ordered series, for running totals and LAG/LEAD.
SALES = """sales
 mon | amt
-----+-----
   1 | 100
   2 | 150
   3 |  90
   4 | 200"""

SCORES = """scores
 name  | pts
-------+-----
 Ada   | 100
 Grace | 100
 Linus |  90
 Bela  |  80"""

# Machine-readable counterpart of the ASCII fixtures above, keyed by the art
# itself. tools/verify_sql.py builds these in a real PostgreSQL server and runs
# every predict and rows query against them, so an authored answer that is
# merely plausible fails the build. Hand-computed SQL results are exactly the
# kind of thing that looks right and is not.
SETUP = {
    EMP: """
        CREATE TABLE employees (id int, name text, dept int, sal int);
        INSERT INTO employees VALUES
          (1,'Ada',10,100), (2,'Grace',10,90), (3,'Linus',20,80), (4,'Barbara',NULL,70);
        CREATE TABLE departments (id int, name text);
        INSERT INTO departments VALUES (10,'Eng'), (20,'Sales'), (30,'Legal');
    """,
    SCORES: """
        CREATE TABLE scores (name text, pts int);
        INSERT INTO scores VALUES ('Ada',100), ('Grace',100), ('Linus',90), ('Bela',80);
    """,
    ORD: """
        CREATE TABLE orders (id int, cust text, total int);
        INSERT INTO orders VALUES (1,'Ada',100), (2,'Grace',50), (3,'Linus',30);
        CREATE TABLE items (ord int, sku text, qty int);
        INSERT INTO items VALUES (1,'A',2), (1,'B',1), (1,'C',3), (2,'A',1);
    """,
    TREE: """
        CREATE TABLE node (id int, parent int, name text);
        INSERT INTO node VALUES
          (1,NULL,'root'), (2,1,'a'), (3,1,'b'), (4,2,'a1'), (5,4,'a1x');
    """,
    SALES: """
        CREATE TABLE sales (mon int, amt int);
        INSERT INTO sales VALUES (1,100), (2,150), (3,90), (4,200);
    """,
    NO_TABLES: "",
}

CARDS = [

# ==================== s1 · SELECT, WHERE, ORDER BY ====================
{
 "id": "s1-001", "topic": "s1", "name": "Logical order of a query",
 "summary": (
  "SQL is written in one order and evaluated in another, and almost every "
  "beginner error comes from that mismatch.\n\n"
  "    written:    SELECT ... FROM ... WHERE ... GROUP BY ...\n"
  "                HAVING ... ORDER BY ... LIMIT\n\n"
  "    evaluated:  FROM -> WHERE -> GROUP BY -> HAVING ->\n"
  "                SELECT -> ORDER BY -> LIMIT\n\n"
  "SELECT runs almost last. That is why WHERE cannot see a column alias you "
  "defined in SELECT, and why HAVING can filter on an aggregate but WHERE "
  "cannot: when WHERE runs, no grouping has happened yet.\n\n"
  "ORDER BY is the exception that trips people the other way — it runs after "
  "SELECT, so it CAN use an alias. Postgres allows it; some engines do not."
 ),
 "recall": [{"prompt": "Which clause is evaluated first in a SELECT statement?",
             "answer": "FROM", "accept": ["from", "the FROM clause"],
             "why": "FROM builds the row source; everything else filters, groups or shapes it."}],
 "confusable": [{
   "prompt": "Why can't WHERE filter on a column alias defined in SELECT?",
   "options": ["WHERE runs before SELECT", "Aliases are only for display",
               "Aliases must be quoted in WHERE", "It works in standard SQL"],
   "answer": 0,
   "explain": "Evaluation order is FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY. The alias does not exist yet when WHERE runs."}],
},
{
 "id": "s1-002", "topic": "s1", "name": "No ORDER BY means no order",
 "summary": (
  "A query without ORDER BY returns rows in whatever order the engine finds "
  "convenient. Not insertion order, not primary-key order — no order at all.\n\n"
  "It usually looks sorted on a small table, because a sequential scan happens "
  "to read rows in physical order. Then the table grows, the planner switches to "
  "an index scan or a parallel scan, and the same query starts returning rows in "
  "a different order with no code change.\n\n"
  "    SELECT name FROM employees ORDER BY id;\n\n"
  "If order matters, say so. And make the ordering total: ORDER BY sal alone "
  "leaves ties in an arbitrary order, so pagination can show the same row twice. "
  "Add a unique tiebreaker, usually the primary key."
 ),
 "confusable": [{
   "prompt": "A query with no ORDER BY has always returned rows in id order. Can you rely on it?",
   "options": ["No — the order is undefined", "Yes, insertion order is guaranteed",
               "Yes, primary-key order is guaranteed", "Only inside a transaction"],
   "answer": 0,
   "explain": "It is an accident of the current plan. A new index, more rows or a parallel scan can change it at any time."}],
 "fill": [{"code": "-- highest salary first, stable for paging\nSELECT name FROM employees\nORDER BY sal DESC, __;",
           "answer": "id", "hint": "a unique column to break ties"}],
},
{
 "id": "s1-003", "topic": "s1", "name": "LIMIT without ORDER BY",
 "summary": (
  "LIMIT takes rows from the front of the result, and without ORDER BY the front "
  "is meaningless. LIMIT 10 gives you ten arbitrary rows, not the first ten of "
  "anything.\n\n"
  "    SELECT * FROM employees ORDER BY sal DESC LIMIT 3;   -- top 3 earners\n"
  "    SELECT * FROM employees LIMIT 3;                     -- 3 random rows\n\n"
  "The pairing matters even more for paging. OFFSET 20 LIMIT 10 skips twenty "
  "rows of an undefined ordering, so pages can overlap or miss rows entirely.\n\n"
  "Postgres and SQLite spell it LIMIT n OFFSET m; the standard spelling, also "
  "accepted by Postgres, is OFFSET m FETCH FIRST n ROWS ONLY. SQL Server uses "
  "TOP n instead."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT name FROM employees\nORDER BY sal DESC\nLIMIT 2;",
              "output": "Ada\nGrace",
              "why": "Sorted by salary descending: 100, 90, 80, 70. The first two names are Ada and Grace."}],
 "confusable": [{
   "prompt": "What does SELECT * FROM t LIMIT 10 return?",
   "options": ["Ten arbitrary rows", "The ten oldest rows", "The ten newest rows",
               "The first ten by primary key"],
   "answer": 0,
   "explain": "Without ORDER BY there is no first. LIMIT just stops after ten of whatever order the plan produced."}],
},

# ==================== s2 · NULL & three-valued logic ====================
{
 "id": "s2-001", "topic": "s2", "name": "NULL is not equal to anything",
 "summary": (
  "NULL means unknown, so comparing it produces unknown rather than true or "
  "false. That includes comparing it with itself.\n\n"
  "    NULL = NULL      -> NULL   (not true)\n"
  "    NULL <> 5        -> NULL   (not true)\n"
  "    NULL IS NULL     -> true\n\n"
  "WHERE keeps a row only when the condition is true, so a row whose value is "
  "NULL is dropped by both x = 5 and x <> 5. People read those as opposites and "
  "expect every row to appear in one or the other; NULLs appear in neither.\n\n"
  "The only reliable tests are IS NULL and IS NOT NULL. Postgres also has IS "
  "DISTINCT FROM, which compares treating NULLs as ordinary values, so "
  "a IS DISTINCT FROM b is true when one side is NULL and the other is not."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM employees WHERE dept <> 10;",
           "answer": "1",
           "why": "Only Linus (dept 20). Barbara's dept is NULL, so NULL <> 10 is NULL, not true, and the row is dropped."}],
 "confusable": [{
   "prompt": "What does NULL = NULL evaluate to?",
   "options": ["NULL", "true", "false", "An error"],
   "answer": 0,
   "explain": "Unknown compared with unknown is unknown. Use IS NULL, or IS NOT DISTINCT FROM for null-aware equality."}],
},
{
 "id": "s2-002", "topic": "s2", "name": "NOT IN with a NULL returns nothing",
 "summary": (
  "This is the single most expensive NULL trap, because the query returns zero "
  "rows and looks like it simply found no matches.\n\n"
  "    WHERE id NOT IN (1, 2, NULL)\n\n"
  "expands to id <> 1 AND id <> 2 AND id <> NULL. That last comparison is NULL "
  "for every row, and true AND NULL is NULL, so no row is ever true. The result "
  "is empty whatever the data.\n\n"
  "IN behaves sanely — a match still returns true — so the asymmetry catches "
  "people out. The usual source is NOT IN (SELECT col FROM ...) where col is "
  "nullable.\n\n"
  "The fixes: use NOT EXISTS, which is null-safe and usually faster, or add "
  "WHERE col IS NOT NULL to the subquery."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM employees\nWHERE dept NOT IN\n  (SELECT dept FROM employees);",
           "answer": "0",
           "why": "The subquery yields 10, 10, 20 and NULL. NOT IN against a list containing NULL can never be true, so nothing is returned."}],
 "confusable": [{
   "prompt": "Which rewrite of NOT IN (subquery) is safe when the subquery can return NULL?",
   "options": ["NOT EXISTS", "NOT ANY", "<> ALL", "NOT IN with DISTINCT"],
   "answer": 0,
   "explain": "NOT EXISTS asks whether a matching row exists, which is a two-valued question — NULLs cannot poison it."}],
},
{
 "id": "s2-003", "topic": "s2", "name": "Aggregates skip NULLs",
 "summary": (
  "Every aggregate except count(*) ignores NULL inputs entirely.\n\n"
  "    count(*)      counts rows\n"
  "    count(col)    counts rows where col IS NOT NULL\n"
  "    avg(col)      sum of non-null values / COUNT OF NON-NULL VALUES\n\n"
  "So avg is not sum(col)/count(*). If a fifth of your rows have a NULL amount, "
  "avg silently reports the average of the rest — often the right answer, "
  "sometimes badly wrong, and never visible in the output.\n\n"
  "Decide deliberately. avg(coalesce(col, 0)) treats missing as zero and gives a "
  "different, equally defensible number. The bug is not choosing either one; it "
  "is not noticing there was a choice.\n\n"
  "One more: sum over zero rows returns NULL, not 0. Wrap it in coalesce."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT count(*), count(dept) FROM employees;",
              "output": "4|3",
              "accept": ["4 | 3"],
              "why": "count(*) counts rows; count(dept) skips Barbara's NULL department."}],
 "confusable": [{
   "prompt": "sum(amount) over a set of rows where every amount is NULL returns what?",
   "options": ["NULL", "0", "An error", "The row count"],
   "answer": 0,
   "explain": "sum ignores NULLs, and summing nothing is NULL rather than zero. Use coalesce(sum(amount), 0)."}],
},

# ============================== s3 · Joins ==============================
{
 "id": "s3-001", "topic": "s3", "name": "INNER JOIN drops non-matching rows",
 "summary": (
  "An inner join returns only rows that match on both sides. Anything unmatched "
  "on either side disappears, silently.\n\n"
  "    SELECT e.name, d.name\n"
  "    FROM employees e\n"
  "    JOIN departments d ON e.dept = d.id;\n\n"
  "JOIN with no qualifier means INNER JOIN.\n\n"
  "In the house tables that returns three rows: Barbara has no department, so "
  "she is dropped, and Legal has no employees, so it is dropped too. A count "
  "that comes out lower than expected after adding a join is nearly always this.\n\n"
  "The habit worth having: when a join changes your row count, ask which side "
  "lost rows and whether that is what you meant. LEFT JOIN keeps the left side "
  "whole and is often what you actually wanted."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM employees e\nJOIN departments d ON e.dept = d.id;",
           "answer": "3",
           "why": "Ada, Grace and Linus match. Barbara's NULL dept matches nothing, and Legal has no employees."}],
 "fill": [{"code": "-- keep every employee, dept or not\nSELECT e.name, d.name\nFROM employees e\n__ JOIN departments d ON e.dept = d.id;",
           "answer": "LEFT", "accept": ["left", "LEFT OUTER"], "hint": "which side to keep whole"}],
},
{
 "id": "s3-002", "topic": "s3", "name": "LEFT, RIGHT and FULL",
 "summary": (
  "An outer join keeps unmatched rows from one or both sides, filling the other "
  "side with NULLs.\n\n"
  "    LEFT JOIN    every row from the left, matched or not\n"
  "    RIGHT JOIN   every row from the right\n"
  "    FULL JOIN    every row from both\n\n"
  "On the house tables: inner gives 3, left gives 4 (Barbara joins with NULLs), "
  "right gives 4 (Legal joins with NULLs), full gives 5.\n\n"
  "RIGHT JOIN is rare in practice — most people swap the table order and use "
  "LEFT, which reads more naturally because the table you care about comes "
  "first. FULL JOIN is genuinely useful for reconciling two sources and finding "
  "what exists in one but not the other."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM employees e\nFULL JOIN departments d ON e.dept = d.id;",
           "answer": "5",
           "why": "Three matches, plus Barbara with no department, plus Legal with no employees."}],
 "confusable": [{
   "prompt": "Which join keeps rows that exist in only one of the two tables, from either side?",
   "options": ["FULL OUTER JOIN", "LEFT JOIN", "INNER JOIN", "CROSS JOIN"],
   "answer": 0,
   "explain": "LEFT keeps unmatched rows from the left only; FULL keeps unmatched rows from both."}],
},
{
 "id": "s3-003", "topic": "s3", "name": "A WHERE clause undoes a LEFT JOIN",
 "summary": (
  "This one looks harmless and quietly turns an outer join back into an inner "
  "one.\n\n"
  "    FROM employees e\n"
  "    LEFT JOIN departments d ON e.dept = d.id\n"
  "    WHERE d.name = 'Eng'\n\n"
  "The LEFT JOIN dutifully keeps Barbara with a NULL department name. Then WHERE "
  "runs, NULL = 'Eng' is NULL, and Barbara is filtered out. The outer join "
  "achieved nothing.\n\n"
  "The rule: a condition on the RIGHT table belongs in ON, not WHERE.\n\n"
  "    LEFT JOIN departments d\n"
  "      ON e.dept = d.id AND d.name = 'Eng'\n\n"
  "ON decides what counts as a match; WHERE filters the finished result. The "
  "same condition in the two places gives different answers, and only for outer "
  "joins — which is why the distinction is invisible until it bites."
 ),
 "confusable": [{
   "prompt": "Where does a condition on the right-hand table of a LEFT JOIN belong?",
   "options": ["In the ON clause", "In the WHERE clause", "In a HAVING clause",
               "Either — they are equivalent"],
   "answer": 0,
   "explain": "In WHERE it discards the NULL-filled unmatched rows, turning the outer join into an inner one."}],
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM employees e\nLEFT JOIN departments d ON e.dept = d.id\nWHERE d.name = 'Eng';",
           "answer": "2",
           "why": "Only Ada and Grace. The WHERE drops every NULL-filled row, so the LEFT behaves as an INNER join."}],
},
{
 "id": "s3-004", "topic": "s3", "name": "Join fan-out multiplies rows",
 "summary": (
  "A join is not a lookup. If the right-hand side has three rows matching one "
  "left row, that left row comes back three times.\n\n"
  "    orders (1 row)  JOIN  items (3 rows for that order)  ->  3 rows\n\n"
  "That is correct behaviour, and it is also how sums get silently inflated: "
  "join orders to items and then sum the order total, and each order's total is "
  "counted once per item.\n\n"
  "    sum(o.total)             wrong, multiplied by the item count\n"
  "    sum(DISTINCT o.total)    still wrong, drops equal totals\n\n"
  "The fix is to aggregate before joining, in a subquery or CTE, so each side "
  "has one row per key. When a report's numbers are too big by a suspiciously "
  "round factor, look for a fan-out."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM departments d\nJOIN employees e ON e.dept = d.id\nWHERE d.id = 10;",
           "answer": "2",
           "why": "Eng has two employees, so the single Eng row is duplicated once per matching employee."}],
 "confusable": [{
   "prompt": "You join orders to items and sum the order total. The result is far too large. Why?",
   "options": ["Each order repeats once per item", "The join dropped rows",
               "sum ignores NULLs", "ORDER BY was missing"],
   "answer": 0,
   "explain": "Fan-out: one order matching three items yields three rows, so its total is added three times. Aggregate before joining."}],
},
{
 "id": "s3-005", "topic": "s3", "name": "CROSS JOIN and the accidental one",
 "summary": (
  "A cross join pairs every row on the left with every row on the right. Four "
  "employees and three departments give twelve rows.\n\n"
  "    SELECT * FROM employees\nCROSS JOIN departments;   -- 12 rows\n\n"
  "It is genuinely useful for generating combinations — every product against "
  "every month, say — but it is far more often an accident. Writing a join in "
  "the old comma style and forgetting the WHERE produces exactly this:\n\n"
  "    SELECT * FROM employees, departments;   -- also 12 rows\n\n"
  "On real tables that is a cartesian product of millions by millions, which is "
  "how a query brings down a database. Explicit JOIN ... ON syntax makes the "
  "mistake much harder, because a missing ON is a syntax error rather than a "
  "silent disaster."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM employees\nCROSS JOIN departments;",
           "answer": "12",
           "why": "Every left row paired with every right row: 4 x 3."}],
 "recall": [{"prompt": "What is the row count of a CROSS JOIN between a 4-row and a 3-row table?",
             "answer": "12", "why": "A cartesian product multiplies the row counts."}],
},

# ==================== s4 · Aggregation & GROUP BY ====================
{
 "id": "s4-001", "topic": "s4", "name": "GROUP BY and the SELECT rule",
 "summary": (
  "Once you GROUP BY, every column in SELECT must either be one of the grouping "
  "columns or be wrapped in an aggregate. Anything else has no single value for "
  "the group.\n\n"
  "    SELECT dept, count(*) FROM employees\nGROUP BY dept;        -- fine\n"
  "    SELECT dept, name, count(*) FROM employees GROUP BY dept;  -- error\n\n"
  "Postgres rejects the second outright. MySQL historically allowed it and "
  "returned an arbitrary name from each group, which is why queries ported from "
  "MySQL suddenly fail — and why they were quietly wrong before.\n\n"
  "Postgres does allow a helpful exception: group by a primary key and you may "
  "select any column of that table, because the key functionally determines "
  "them all.\n\n"
  "NULLs form their own group, so the house table gives three groups: 10, 20 and "
  "NULL."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT dept, count(*) FROM employees\nGROUP BY dept;",
           "answer": "3",
           "why": "Groups are 10 (two rows), 20 (one) and NULL (one). GROUP BY puts all NULLs in a single group."}],
 "confusable": [{
   "prompt": "In Postgres, why is SELECT dept, name FROM employees GROUP BY dept an error?",
   "options": ["name has no single value per group", "name must be indexed",
               "GROUP BY allows only one column", "name is a reserved word"],
   "answer": 0,
   "explain": "Each dept group holds several names. Aggregate it (min(name), string_agg) or add it to GROUP BY."}],
},
{
 "id": "s4-002", "topic": "s4", "name": "WHERE versus HAVING",
 "summary": (
  "    WHERE     filters rows, before grouping\n"
  "    HAVING    filters groups, after grouping\n\n"
  "So an aggregate can only appear in HAVING — when WHERE runs, no group exists "
  "yet to aggregate.\n\n"
  "    SELECT dept, count(*)\n"
  "    FROM employees\n"
  "    WHERE sal > 75          -- drop rows first\n"
  "    GROUP BY dept\n"
  "    HAVING count(*) > 1;    -- then drop small groups\n\n"
  "Both clauses in one query is normal and the order matters: WHERE changes "
  "which rows are counted, HAVING only discards finished groups.\n\n"
  "Where you have a choice, prefer WHERE. It removes rows before the grouping "
  "work happens, so it is usually cheaper as well as clearer."
 ),
 "fill": [{"code": "-- departments with more than one employee\nSELECT dept, count(*)\nFROM employees\nGROUP BY dept\n__ count(*) > 1;",
           "answer": "HAVING", "accept": ["having"], "hint": "the clause that filters groups"}],
 "confusable": [{
   "prompt": "Which clause can contain an aggregate like count(*)?",
   "options": ["HAVING", "WHERE", "Both equally", "Neither — only SELECT"],
   "answer": 0,
   "explain": "WHERE runs before grouping, so no aggregate exists yet. HAVING runs after and filters the groups."}],
},
{
 "id": "s4-003", "topic": "s4", "name": "Aggregate with no GROUP BY",
 "summary": (
  "An aggregate with no GROUP BY treats the whole result as one group and always "
  "returns exactly one row — even when no rows matched.\n\n"
  "    SELECT count(*) FROM employees WHERE sal > 1000;\n"
  "    -- one row, containing 0\n\n"
  "That is the difference between count and the others. count over zero rows is "
  "0; sum, avg, max and min over zero rows are NULL.\n\n"
  "    SELECT max(sal) FROM employees\nWHERE sal > 1000;\n"
  "    -- one row, containing NULL\n\n"
  "It matters when the value feeds something else. coalesce(max(sal), 0) makes "
  "the empty case explicit. And code that expects zero rows back when nothing "
  "matched will be surprised: there is always exactly one row."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT max(sal) FROM employees\nWHERE sal > 1000;",
           "answer": "1",
           "why": "An ungrouped aggregate always returns exactly one row. Here it contains NULL, but the row exists."}],
 "confusable": [{
   "prompt": "SELECT count(*) FROM t WHERE false returns what?",
   "options": ["One row containing 0", "Zero rows", "One row containing NULL", "An error"],
   "answer": 0,
   "explain": "Ungrouped aggregates always produce one row. count gives 0 there; sum, avg, max and min would give NULL."}],
},

# ==================== s5 · Subqueries & EXISTS ====================
{
 "id": "s5-001", "topic": "s5", "name": "EXISTS versus IN",
 "summary": (
  "Both ask whether a related row exists. They differ in how they handle NULLs "
  "and, on many engines, in how they perform.\n\n"
  "    WHERE dept IN (SELECT id FROM departments)\n"
  "    WHERE EXISTS (SELECT 1 FROM departments d WHERE d.id = e.dept)\n\n"
  "IN materialises a list of values and compares against it. EXISTS stops at the "
  "first matching row and only ever answers true or false, so a NULL inside "
  "cannot poison the result the way it does with NOT IN.\n\n"
  "The SELECT 1 is conventional: EXISTS never looks at the selected columns, so "
  "there is no point naming any.\n\n"
  "For the positive case they usually plan identically in Postgres. For the "
  "negative case NOT EXISTS is both safer and generally faster than NOT IN."
 ),
 "fill": [{"code": "-- employees whose department row exists\nSELECT * FROM employees e\nWHERE __ (SELECT 1 FROM departments d\n          WHERE d.id = e.dept);",
           "answer": "EXISTS", "accept": ["exists"], "hint": "the null-safe existence test"}],
 "confusable": [{
   "prompt": "Why is NOT EXISTS preferred over NOT IN for a nullable subquery column?",
   "options": ["NOT IN returns nothing if the subquery yields a NULL",
               "NOT IN cannot be indexed", "NOT EXISTS allows more columns",
               "NOT IN is not standard SQL"],
   "answer": 0,
   "explain": "NOT IN expands to a chain of <> comparisons; one NULL makes every row unknown, so the result is empty."}],
},
{
 "id": "s5-002", "topic": "s5", "name": "Correlated subqueries",
 "summary": (
  "A correlated subquery references a column from the outer query, so "
  "conceptually it runs once per outer row.\n\n"
  "    SELECT name,\n"
  "           (SELECT count(*) FROM orders o\n"
  "            WHERE o.emp = e.id) AS n\n"
  "    FROM employees e;\n\n"
  "It reads well and is often the clearest way to express one value per row. "
  "Modern planners frequently rewrite it into a join, so it is not automatically "
  "slow — but it can be, on a large outer set with no supporting index.\n\n"
  "The scalar form must return at most one row and one column, or the query "
  "fails at runtime with more than one row returned. That failure often appears "
  "only once the data grows, which makes it a nasty one to meet in production.\n\n"
  "A LEFT JOIN with GROUP BY, or a lateral join, is the usual rewrite."
 ),
 "confusable": [{
   "prompt": "A scalar subquery in SELECT returns two rows for one outer row. What happens?",
   "options": ["A runtime error", "The first row is used", "NULL is returned",
               "The outer row is duplicated"],
   "answer": 0,
   "explain": "A scalar subquery must yield at most one row. Postgres raises \"more than one row returned by a subquery\"."}],
 "recall": [{"prompt": "What makes a subquery correlated?",
             "answer": "it references a column from the outer query",
             "accept": ["it refers to the outer query", "it uses an outer column",
                        "it depends on the outer row"],
             "why": "That dependency is why it conceptually runs once per outer row."}],
},

# ========================= s6 · Set operations =========================
{
 "id": "s6-001", "topic": "s6", "name": "UNION removes duplicates, UNION ALL does not",
 "summary": (
  "    UNION        combine and remove duplicate rows\n"
  "    UNION ALL    combine, keep everything\n\n"
  "De-duplicating is not free: the engine has to sort or hash the whole result "
  "to find duplicates. On large sets UNION ALL is dramatically faster.\n\n"
  "So the rule is to use UNION ALL by default and reach for UNION only when you "
  "genuinely need duplicates gone. Most of the time the branches are disjoint "
  "anyway — different date ranges, different statuses — and the de-duplication "
  "pass finds nothing while costing a full sort.\n\n"
  "Both require the branches to have the same number of columns with compatible "
  "types, and the column names come from the first branch. INTERSECT and EXCEPT "
  "follow the same rules, and also de-duplicate unless you add ALL."
 ),
 "confusable": [{
   "prompt": "Two branches return 100 rows each with no overlap. What is faster, and why?",
   "options": ["UNION ALL — UNION still sorts to look for duplicates",
               "UNION — fewer rows to return", "They are identical",
               "UNION — it can use an index"],
   "answer": 0,
   "explain": "UNION always pays for de-duplication even when there is nothing to remove."}],
 "fill": [{"code": "-- stack both result sets, keeping every row\nSELECT id FROM a\nUNION __\nSELECT id FROM b;",
           "answer": "ALL", "accept": ["all"], "hint": "do not de-duplicate"}],
},
{
 "id": "s6-002", "topic": "s6", "name": "EXCEPT and INTERSECT",
 "summary": (
  "    EXCEPT       rows in the first query that are not in the second\n"
  "    INTERSECT    rows in both\n\n"
  "Both compare whole rows, not a key, and both remove duplicates unless you add "
  "ALL. Unlike NOT IN they are null-safe: two NULLs in the same position count "
  "as the same row.\n\n"
  "    SELECT id FROM expected\n"
  "    EXCEPT\n"
  "    SELECT id FROM actual;\n\n"
  "That is the quickest way to diff two tables, and running it both ways round "
  "tells you what is missing and what is extra. It is a genuinely useful "
  "migration check.\n\n"
  "MySQL only gained EXCEPT and INTERSECT in 8.0.31; older versions need a LEFT "
  "JOIN ... WHERE IS NULL, which is the same idea written longhand."
 ),
 "recall": [{"prompt": "Which set operator returns rows from the first query that are absent from the second?",
             "answer": "EXCEPT", "accept": ["except", "EXCEPT (MINUS in Oracle)", "minus"],
             "why": "Oracle spells it MINUS; the standard and Postgres spelling is EXCEPT."}],
 "confusable": [{
   "prompt": "How do EXCEPT and INTERSECT treat NULLs when comparing rows?",
   "options": ["Two NULLs in the same column count as equal", "Any NULL makes the row unmatched",
               "They raise an error", "NULL rows are skipped entirely"],
   "answer": 0,
   "explain": "Set operators compare rows by value distinctness, not by =, so they are null-safe unlike IN and NOT IN."}],
},

# ============================== s7 · CTEs ==============================
{
 "id": "s7-001", "topic": "s7", "name": "WITH names a subquery",
 "summary": (
  "A common table expression gives a subquery a name and puts it at the top, so "
  "the query reads in the order it is computed.\n\n"
  "    WITH recent AS (\n"
  "      SELECT * FROM orders WHERE created > now() - interval '7 days'\n"
  "    )\n"
  "    SELECT emp, count(*) FROM recent GROUP BY emp;\n\n"
  "You can chain them, each one referring to the previous, which is how a "
  "twelve-line nested query becomes four readable steps.\n\n"
  "A CTE may be referenced more than once in the same query, unlike a derived "
  "table in FROM, which has to be repeated. In Postgres 12 and later a "
  "referenced-once CTE is normally inlined and optimised as if written inline; "
  "before that it was always materialised, and MATERIALIZED or NOT MATERIALIZED "
  "still lets you force either behaviour."
 ),
 "fill": [{"code": "-- name a subquery for readability\n__ recent AS (\n  SELECT * FROM orders WHERE created > now()\n)\nSELECT count(*) FROM recent;",
           "answer": "WITH", "accept": ["with"], "hint": "the keyword that opens a CTE"}],
 "confusable": [{
   "prompt": "In Postgres 12+, is a CTE referenced once materialised by default?",
   "options": ["No — it is inlined and optimised with the outer query",
               "Yes, always", "Only if it contains an aggregate",
               "Only inside a transaction"],
   "answer": 0,
   "explain": "Before 12 a CTE was an optimisation fence. Now inlining is the default; MATERIALIZED forces the old behaviour."}],
},
{
 "id": "s7-002", "topic": "s7", "name": "Data-modifying CTEs",
 "summary": (
  "In Postgres a CTE can contain INSERT, UPDATE or DELETE with a RETURNING "
  "clause, so one statement can move rows between tables atomically.\n\n"
  "    WITH moved AS (\n"
  "      DELETE FROM queue WHERE id = 1 RETURNING *\n"
  "    )\n"
  "    INSERT INTO archive SELECT * FROM moved;\n\n"
  "All the sub-statements see the same snapshot of the database, taken at the "
  "start. So a data-modifying CTE cannot see its own changes, and two branches "
  "modifying the same row have an undefined outcome.\n\n"
  "This is a Postgres extension. SQLite and MySQL do not support it, so the "
  "portable version is two statements inside a transaction.\n\n"
  "RETURNING itself is worth knowing on its own: it hands back the inserted or "
  "deleted rows, including generated ids, without a second round trip."
 ),
 "recall": [{"prompt": "Which Postgres clause makes INSERT hand back the rows it created, including generated ids?",
             "answer": "RETURNING", "accept": ["returning", "RETURNING *"],
             "why": "It works on INSERT, UPDATE and DELETE, and is what makes data-modifying CTEs possible."}],
 "confusable": [{
   "prompt": "Can a data-modifying CTE see the rows another branch of the same statement just changed?",
   "options": ["No — every branch sees the same starting snapshot",
               "Yes, in declaration order", "Yes, if it is MATERIALIZED",
               "Only for INSERT"],
   "answer": 0,
   "explain": "All sub-statements run against one snapshot, so the effects are not visible to each other."}],
},

# ========================= s8 · Window functions =========================
{
 "id": "s8-001", "topic": "s8", "name": "ROW_NUMBER, RANK, DENSE_RANK",
 "summary": (
  "All three number rows in an order. They differ only in how they treat ties.\n\n"
  "    pts   ROW_NUMBER  RANK  DENSE_RANK\n"
  "    100        1        1        1\n"
  "    100        2        1        1\n"
  "     90        3        3        2\n"
  "     80        4        4        3\n\n"
  "ROW_NUMBER never ties — it just counts, and which tied row gets 1 is "
  "arbitrary unless you add a tiebreaker to ORDER BY.\n\n"
  "RANK ties, then skips: two firsts means no second. DENSE_RANK ties without "
  "skipping.\n\n"
  "Pick by intent. Deduplicating rows wants ROW_NUMBER, since you need exactly "
  "one per group. A leaderboard usually wants RANK, because two people really "
  "did come first. Top-N-distinct-values wants DENSE_RANK."
 ),
 "fixture": SCORES,
 "predict": [{"code": "SELECT rank() OVER (ORDER BY pts DESC)\nFROM scores\nORDER BY 1;",
              "output": "1\n1\n3\n4",
              "why": "Ada and Grace tie at 100 and both rank 1; rank then SKIPS 2. DENSE_RANK would give 1, 1, 2, 3."}],
 "confusable": [{
   "prompt": "Two rows tie for first. Which function gives the next row the number 2?",
   "options": ["DENSE_RANK", "RANK", "ROW_NUMBER", "NTILE"],
   "answer": 0,
   "explain": "RANK skips to 3 after two firsts. ROW_NUMBER would have already used 2 on the second tied row."}],
},
{
 "id": "s8-002", "topic": "s8", "name": "PARTITION BY restarts the window",
 "summary": (
  "PARTITION BY splits the rows into groups and applies the window function "
  "separately within each one. It is GROUP BY's shape without GROUP BY's "
  "collapsing.\n\n"
  "    SELECT name, dept,\n"
  "           rank() OVER (PARTITION BY dept ORDER BY sal DESC)\n"
  "    FROM employees;\n\n"
  "Every input row still comes back — you get the ranking alongside the detail, "
  "which is exactly what GROUP BY cannot do.\n\n"
  "That is the whole reason window functions exist. Before them, showing each "
  "employee next to their department average meant a self-join to an aggregated "
  "subquery. Now it is avg(sal) OVER (PARTITION BY dept).\n\n"
  "Windows run after WHERE and GROUP BY and before ORDER BY, so you cannot "
  "filter on a window result in WHERE — wrap the query in a CTE and filter "
  "outside."
 ),
 "confusable": [{
   "prompt": "How many rows does a query with PARTITION BY return?",
   "options": ["The same as the input", "One per partition", "One in total",
               "One per distinct ordering value"],
   "answer": 0,
   "explain": "Window functions add a column; they never collapse rows. That is the difference from GROUP BY."}],
 "fill": [{"code": "-- rank within each department\nSELECT name,\n  rank() OVER (__ BY dept ORDER BY sal DESC)\nFROM employees;",
           "answer": "PARTITION", "accept": ["partition"], "hint": "the window's grouping keyword"}],
},
{
 "id": "s8-003", "topic": "s8", "name": "Filtering on a window result",
 "summary": (
  "You cannot put a window function in WHERE. Windows are evaluated after WHERE "
  "and after GROUP BY, so the value does not exist yet when WHERE runs.\n\n"
  "    -- error\n"
  "    SELECT * FROM employees\n"
  "    WHERE row_number() OVER (ORDER BY sal) <= 3;\n\n"
  "    -- correct\n"
  "    WITH ranked AS (\n"
  "      SELECT *, row_number() OVER (ORDER BY sal DESC) AS rn\n"
  "      FROM employees\n"
  "    )\n"
  "    SELECT * FROM ranked WHERE rn <= 3;\n\n"
  "Wrapping in a CTE, or a subquery in FROM, gives the window a chance to run "
  "before the filter.\n\n"
  "This is the standard pattern for top-N-per-group: partition by the group, "
  "order by the ranking column, then filter the row number outside."
 ),
 "confusable": [{
   "prompt": "Why is WHERE row_number() OVER (...) <= 3 invalid?",
   "options": ["Window functions are evaluated after WHERE",
               "row_number needs PARTITION BY", "WHERE cannot contain any function",
               "It must be in HAVING instead"],
   "answer": 0,
   "explain": "The window value does not exist yet. Compute it in a CTE or subquery, then filter outside."}],
 "recall": [{"prompt": "What is the standard way to get the top 3 rows per group?",
             "answer": "row_number in a CTE, filtered outside",
             "accept": ["a CTE with row_number then WHERE rn <= 3",
                        "row_number over partition by, filtered in an outer query",
                        "window function in a subquery then filter"],
             "why": "PARTITION BY the group, ORDER BY the ranking column, then filter the number outside."}],
},

# ======================== s9 · Recursive CTEs ========================
{
 "id": "s9-001", "topic": "s9", "name": "The shape of a recursive CTE",
 "summary": (
  "A recursive CTE has two halves joined by UNION ALL: a base case, and a step "
  "that refers back to the CTE itself.\n\n"
  "    WITH RECURSIVE nums AS (\n"
  "      SELECT 1 AS n                      -- base\n"
  "      UNION ALL\n"
  "      SELECT n + 1 FROM nums WHERE n < 5 -- step\n"
  "    )\n"
  "    SELECT n FROM nums;                  -- 1 2 3 4 5\n\n"
  "The step runs repeatedly on the rows produced last time round, and stops when "
  "it produces none. That termination condition is yours to get right — without "
  "the WHERE, the query runs until it exhausts memory.\n\n"
  "The keyword is RECURSIVE in Postgres even when it is not needed; SQL Server "
  "omits it. It is the standard tool for walking a tree: org charts, category "
  "hierarchies, dependency graphs."
 ),
 "fill": [{"code": "-- walk a hierarchy from the root downwards\nWITH __ tree AS (\n  SELECT id, parent FROM node\n  WHERE parent IS NULL\n  UNION ALL\n  SELECT n.id, n.parent FROM node n\n  JOIN tree t ON n.parent = t.id\n)\nSELECT * FROM tree;",
           "answer": "RECURSIVE", "accept": ["recursive"], "hint": "the keyword after WITH"}],
 "confusable": [{
   "prompt": "What stops a recursive CTE?",
   "options": ["The step producing no new rows", "A fixed depth limit",
               "The RECURSIVE keyword", "The first NULL encountered"],
   "answer": 0,
   "explain": "It iterates until the recursive branch returns nothing. A missing or wrong condition runs forever."}],
},
{
 "id": "s9-002", "topic": "s9", "name": "Cycles in a recursive query",
 "summary": (
  "A recursive CTE over a graph with a cycle never terminates — each pass "
  "produces rows, so there is no stopping point.\n\n"
  "Two defences. Carry the path and refuse to revisit:\n\n"
  "    SELECT n.id, p.path || n.id\n"
  "    FROM node n JOIN paths p ON n.parent = p.id\n"
  "    WHERE NOT n.id = ANY(p.path)\n\n"
  "Or use the built-in cycle detection Postgres 14 added:\n\n"
  "    WITH RECURSIVE t AS (...)\n"
  "    CYCLE id SET is_cycle USING path\n\n"
  "which maintains the path array for you and marks the row that closes a loop.\n\n"
  "Even with a correct tree, a depth guard is cheap insurance: one bad row with "
  "a parent pointing at itself turns a report into an outage."
 ),
 "confusable": [{
   "prompt": "Your recursive CTE over an org chart never finishes. What is the most likely cause?",
   "options": ["A cycle in the data", "Too many rows", "A missing index",
               "UNION ALL instead of UNION"],
   "answer": 0,
   "explain": "An employee whose manager chain loops back means the step always produces rows. Track the path, or use the CYCLE clause."}],
 "recall": [{"prompt": "Which Postgres 14 clause detects loops in a recursive CTE for you?",
             "answer": "CYCLE", "accept": ["the CYCLE clause", "cycle"],
             "why": "CYCLE col SET flag USING path maintains the visited-path array and flags the repeat."}],
},

# ==================== s10 · CASE, COALESCE & casting ====================
{
 "id": "s10-001", "topic": "s10", "name": "COALESCE and NULLIF",
 "summary": (
  "    coalesce(a, b, c)   the first argument that is not NULL\n"
  "    nullif(a, b)        NULL if a = b, otherwise a\n\n"
  "coalesce is the standard way to supply a default: coalesce(nickname, name) "
  "shows the nickname when there is one. It short-circuits, so later arguments "
  "are not evaluated once one is non-null.\n\n"
  "nullif is the mirror image, and its classic use is avoiding division by "
  "zero:\n\n"
  "    total / nullif(count, 0)\n\n"
  "When count is zero the denominator becomes NULL and the whole expression is "
  "NULL, instead of raising a division-by-zero error. Combine the two — "
  "coalesce(total / nullif(count, 0), 0) — and you get a clean zero.\n\n"
  "Postgres also has ifnull-style greatest and least, which ignore NULLs "
  "entirely, unlike max and min over rows."
 ),
 "fill": [{"code": "-- return NULL, not an error, when n is 0\nSELECT total / __(n, 0) FROM stats;",
           "answer": "nullif", "accept": ["NULLIF"], "hint": "turns one specific value into NULL"}],
 "confusable": [{
   "prompt": "What does coalesce(NULL, NULL, 3, 5) return?",
   "options": ["3", "NULL", "5", "8"],
   "answer": 0,
   "explain": "It returns the first non-null argument and stops there — 5 is never evaluated."}],
},
{
 "id": "s10-002", "topic": "s10", "name": "CASE returns a value, not a branch",
 "summary": (
  "CASE is an expression. It evaluates to a single value and can go anywhere a "
  "value can — inside SELECT, inside an aggregate, inside ORDER BY.\n\n"
  "    SELECT count(*) FILTER (WHERE sal > 90) AS high,\n"
  "           sum(CASE WHEN sal > 90 THEN 1 ELSE 0 END) AS also_high\n"
  "    FROM employees;\n\n"
  "Both count the same thing. The CASE form is portable; the FILTER clause is "
  "standard SQL, supported by Postgres and SQLite, and much easier to read.\n\n"
  "Two traps. Without an ELSE, an unmatched CASE returns NULL rather than "
  "erroring — which is fine inside sum, and a silent hole anywhere else. And the "
  "branches must have compatible types; mixing a number and a string makes "
  "Postgres pick a type and then fail at runtime on the first bad row."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT count(*) FILTER (WHERE sal > 90)\nFROM employees;",
              "output": "1",
              "why": "Only Ada earns more than 90. FILTER applies the condition to that aggregate alone."}],
 "confusable": [{
   "prompt": "A CASE with no ELSE and no matching WHEN returns what?",
   "options": ["NULL", "0", "An empty string", "An error"],
   "answer": 0,
   "explain": "The implicit ELSE is NULL. That is harmless inside sum and a silent hole almost everywhere else."}],
},
{
 "id": "s10-003", "topic": "s10", "name": "Integer division and casting",
 "summary": (
  "In Postgres, dividing two integers gives an integer. The fractional part is "
  "truncated, not rounded, and there is no warning.\n\n"
  "    SELECT 7 / 2;            -- 3\n"
  "    SELECT 7.0 / 2;          -- 3.5000000000000000\n"
  "    SELECT 7::numeric / 2;   -- 3.5000000000000000\n\n"
  "So a percentage computed as correct / total * 100 comes out as 0 or 100 and "
  "nothing in between. Cast one side, or multiply by 100.0 first.\n\n"
  "The :: syntax is Postgres shorthand for CAST(x AS type), which is the "
  "portable spelling.\n\n"
  "Prefer numeric to float for money and percentages: numeric is exact decimal, "
  "while float is binary and cannot represent 0.1 exactly, so sums of currency "
  "drift."
 ),
 "predict": [{"code": "SELECT 7 / 2;",
              "fixture": NO_TABLES,
              "output": "3",
              "why": "Both operands are integers, so the result is an integer and the remainder is truncated."}],
 "confusable": [{
   "prompt": "Which type should hold money in Postgres?",
   "options": ["numeric", "float8", "real", "double precision"],
   "answer": 0,
   "explain": "numeric is exact decimal. Binary floats cannot represent 0.1, so repeated addition drifts."}],
},

# ==================== s11 · INSERT, UPDATE, DELETE ====================
{
 "id": "s11-001", "topic": "s11", "name": "UPDATE without WHERE",
 "summary": (
  "An UPDATE or DELETE with no WHERE applies to every row in the table. The "
  "syntax is perfectly valid, so nothing warns you.\n\n"
  "    UPDATE employees SET sal = 100;    -- every employee\n"
  "    DELETE FROM employees;             -- every row\n\n"
  "Two habits make it survivable. First, wrap it in a transaction and check the "
  "row count before committing:\n\n"
  "    BEGIN;\n"
  "    UPDATE employees SET sal = 100 WHERE id = 3;\n"
  "    -- UPDATE 1   <- read this number\n"
  "    COMMIT;\n\n"
  "Second, write the SELECT first with the same WHERE, look at the rows, then "
  "change SELECT to UPDATE.\n\n"
  "psql has no autocommit-off by default, so without BEGIN the statement is "
  "committed the instant it runs."
 ),
 "fill": [{"code": "-- make it reversible until you check\n__;\nUPDATE employees SET sal = 100 WHERE id = 3;",
           "answer": "BEGIN", "accept": ["begin", "START TRANSACTION", "BEGIN TRANSACTION"],
           "hint": "open a transaction"}],
 "confusable": [{
   "prompt": "You ran DELETE FROM t; with no WHERE and have not committed. What saves you?",
   "options": ["ROLLBACK, if you are inside a transaction",
               "DELETE is always reversible", "The undo log, automatically",
               "Nothing — DELETE cannot be undone"],
   "answer": 0,
   "explain": "Inside a transaction, ROLLBACK discards it. Outside one, the statement committed the moment it ran."}],
},
{
 "id": "s11-002", "topic": "s11", "name": "UPSERT: ON CONFLICT",
 "summary": (
  "Inserting a row that may already exist is a race in two statements and atomic "
  "in one.\n\n"
  "    INSERT INTO stock (sku, qty)\nVALUES ('abc', 5)\n"
  "    ON CONFLICT (sku) DO UPDATE\n"
  "      SET qty = stock.qty + EXCLUDED.qty;\n\n"
  "EXCLUDED is the row you tried to insert; the table name refers to the row "
  "already there. That pairing is what lets you merge rather than overwrite.\n\n"
  "    ON CONFLICT DO NOTHING     insert if absent, else skip silently\n\n"
  "The conflict target must match a unique constraint or index — without one "
  "there is nothing for Postgres to detect a conflict against.\n\n"
  "MySQL spells it INSERT ... ON DUPLICATE KEY UPDATE, SQLite supports the "
  "Postgres syntax, and the standard MERGE arrived in Postgres 15."
 ),
 "fill": [{"code": "-- insert, or add to the existing quantity\nINSERT INTO stock (sku, qty)\nVALUES ('abc', 5)\nON CONFLICT (sku) DO UPDATE\n  SET qty = stock.qty + __.qty;",
           "answer": "EXCLUDED", "accept": ["excluded"], "hint": "the row that was rejected"}],
 "confusable": [{
   "prompt": "In ON CONFLICT DO UPDATE, what does EXCLUDED refer to?",
   "options": ["The row you tried to insert", "The row already in the table",
               "Rows excluded by the WHERE clause", "The previous statement's result"],
   "answer": 0,
   "explain": "EXCLUDED is the proposed row; the table name refers to the existing one. Both are available in the SET."}],
},
{
 "id": "s11-003", "topic": "s11", "name": "DELETE, TRUNCATE and DROP",
 "summary": (
  "    DELETE FROM t         removes rows, one at a time, WHERE-able,\n"
  "                          transactional, fires triggers\n"
  "    TRUNCATE t            removes all rows at once, no WHERE,\n"
  "                          much faster, resets nothing by default\n"
  "    DROP TABLE t          removes the table itself\n\n"
  "In Postgres TRUNCATE is transactional — you can roll it back — which is not "
  "true in MySQL, where it is an implicit commit. That difference matters if you "
  "are used to one and move to the other.\n\n"
  "TRUNCATE does not fire row triggers and does not scan, so it is the right "
  "tool for emptying a large table. Add RESTART IDENTITY to reset sequences, and "
  "CASCADE if other tables reference it — without CASCADE, a foreign key makes "
  "it fail rather than silently orphan rows."
 ),
 "confusable": [{
   "prompt": "In PostgreSQL, can TRUNCATE be rolled back?",
   "options": ["Yes — it is transactional", "No — it commits immediately",
               "Only with RESTART IDENTITY", "Only inside a savepoint"],
   "answer": 0,
   "explain": "Postgres treats TRUNCATE as an ordinary transactional statement. MySQL does not — there it implicitly commits."}],
 "recall": [{"prompt": "Which command empties a table fastest without firing row triggers?",
             "answer": "TRUNCATE", "accept": ["truncate", "TRUNCATE TABLE"],
             "why": "It drops the storage rather than deleting rows one at a time."}],
},

# ====================== s12 · Constraints & keys ======================
{
 "id": "s12-001", "topic": "s12", "name": "UNIQUE allows many NULLs",
 "summary": (
  "A UNIQUE constraint stops duplicate values — but NULL is not a value, and two "
  "NULLs are not considered duplicates. So a unique column can hold any number "
  "of NULL rows.\n\n"
  "    CREATE TABLE u (email text UNIQUE);\n"
  "    INSERT INTO u VALUES (NULL), (NULL), (NULL);   -- all fine\n\n"
  "That is standard behaviour and usually what you want for an optional field. "
  "It becomes a bug when the column is a de-facto key and the application "
  "sometimes writes NULL.\n\n"
  "Postgres 15 added UNIQUE NULLS NOT DISTINCT, which treats NULLs as equal and "
  "allows only one. Before that the workaround is a partial unique index, or "
  "simply NOT NULL.\n\n"
  "A PRIMARY KEY is UNIQUE plus NOT NULL, which is why it does not have this "
  "problem."
 ),
 "confusable": [{
   "prompt": "How many NULL rows can a plain UNIQUE column hold?",
   "options": ["Any number", "One", "None", "It depends on the row count"],
   "answer": 0,
   "explain": "NULLs are not equal to each other, so they never collide. PRIMARY KEY adds NOT NULL, which is why it differs."}],
 "recall": [{"prompt": "A PRIMARY KEY is equivalent to which two constraints combined?",
             "answer": "UNIQUE and NOT NULL",
             "accept": ["unique and not null", "NOT NULL and UNIQUE", "unique + not null"],
             "why": "That is exactly what it enforces; a table may have only one."}],
},
{
 "id": "s12-002", "topic": "s12", "name": "Foreign keys and ON DELETE",
 "summary": (
  "A foreign key says a value here must exist there. What happens when the "
  "referenced row is deleted is up to you.\n\n"
  "    ON DELETE RESTRICT    refuse the delete (the default is NO ACTION,\n"
  "                          which is RESTRICT deferred to end of statement)\n"
  "    ON DELETE CASCADE     delete the referencing rows too\n"
  "    ON DELETE SET NULL    keep them, blank the reference\n\n"
  "CASCADE is convenient and worth respecting: deleting one customer can quietly "
  "remove every order, payment and invoice beneath them. It is the right choice "
  "for genuinely owned children and a poor one for anything you would want to "
  "audit.\n\n"
  "Postgres does not index the referencing column automatically. Without an "
  "index there, every delete on the parent scans the child table — a very common "
  "cause of mysteriously slow deletes."
 ),
 "confusable": [{
   "prompt": "Deletes on a parent table have become very slow. What is the classic cause?",
   "options": ["No index on the child's foreign-key column", "Too many NULLs in the parent",
               "The FK is declared RESTRICT", "Missing ANALYZE on the parent"],
   "answer": 0,
   "explain": "Postgres indexes the referenced key, not the referencing column. Each parent delete then scans the child table."}],
 "fill": [{"code": "-- delete the lines with the order\nFOREIGN KEY (order_id) REFERENCES orders(id)\n  ON DELETE __;",
           "answer": "CASCADE", "accept": ["cascade"], "hint": "follow the delete down"}],
},

# ================== s13 · Transactions & isolation ==================
{
 "id": "s13-001", "topic": "s13", "name": "The four isolation levels",
 "summary": (
  "Isolation controls what one transaction can see of another's uncommitted or "
  "concurrent work. The standard names four levels by the anomalies they "
  "permit.\n\n"
  "    READ UNCOMMITTED   dirty reads allowed\n"
  "    READ COMMITTED     no dirty reads; non-repeatable reads possible\n"
  "    REPEATABLE READ    reads stay stable; phantoms possible in theory\n"
  "    SERIALIZABLE       as if transactions ran one at a time\n\n"
  "Postgres defaults to READ COMMITTED, and has no true READ UNCOMMITTED — "
  "asking for it gives you READ COMMITTED, so dirty reads never happen. Its "
  "REPEATABLE READ is snapshot isolation and also prevents phantoms.\n\n"
  "MySQL InnoDB defaults to REPEATABLE READ instead, which is a real behavioural "
  "difference between the two when porting."
 ),
 "recall": [{"prompt": "What is PostgreSQL's default transaction isolation level?",
             "answer": "READ COMMITTED", "accept": ["read committed"],
             "why": "MySQL InnoDB defaults to REPEATABLE READ, which is a genuine porting difference."}],
 "confusable": [{
   "prompt": "Which anomaly can never happen in PostgreSQL, at any isolation level?",
   "options": ["A dirty read", "A non-repeatable read", "A phantom read",
               "A serialization failure"],
   "answer": 0,
   "explain": "Postgres has no true READ UNCOMMITTED — its MVCC snapshots never expose uncommitted rows."}],
},
{
 "id": "s13-002", "topic": "s13", "name": "SELECT FOR UPDATE and lost updates",
 "summary": (
  "Read a balance, add to it in application code, write it back — and two "
  "concurrent sessions both read 100, both write 150, and one increment "
  "vanishes. That is a lost update, and READ COMMITTED does not prevent it.\n\n"
  "Three fixes, in order of preference:\n\n"
  "    UPDATE acct SET bal = bal + 50 WHERE id = 1;   -- do it in SQL\n"
  "    SELECT bal FROM acct WHERE id = 1 FOR UPDATE;  -- lock the row\n"
  "    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;  -- let the db detect it\n\n"
  "The first is best where it fits: a single statement is atomic, so there is no "
  "window. FOR UPDATE takes a row lock that other FOR UPDATE readers wait on.\n\n"
  "SERIALIZABLE catches everything but can abort your transaction with a "
  "serialization failure, so the application must be prepared to retry."
 ),
 "fill": [{"code": "-- lock the row; others wait\nSELECT bal FROM acct WHERE id = 1 FOR __;",
           "answer": "UPDATE", "accept": ["update", "NO KEY UPDATE"], "hint": "the strong row lock"}],
 "confusable": [{
   "prompt": "Two sessions read a balance, add 50 in application code, and write it back. What is lost?",
   "options": ["One of the two increments", "Nothing — the database serialises writes",
               "Both, and the row keeps its old value", "The transaction, with an error"],
   "answer": 0,
   "explain": "A lost update. Do the arithmetic in SQL, take FOR UPDATE, or use SERIALIZABLE and retry."}],
},
{
 "id": "s13-003", "topic": "s13", "name": "Deadlocks",
 "summary": (
  "A deadlock is two transactions each holding a lock the other wants. Neither "
  "can proceed, so the database picks a victim and aborts it.\n\n"
  "    session 1: UPDATE a ... then UPDATE b\n"
  "    session 2: UPDATE b ... then UPDATE a\n\n"
  "Postgres detects the cycle after a short delay and raises a deadlock detected "
  "error on one side. That is a normal, survivable condition — not corruption.\n\n"
  "The standard prevention is ordering: always take locks in a consistent order, "
  "usually by primary key ascending. If every transaction updates rows in the "
  "same order, a cycle cannot form.\n\n"
  "Applications should retry on a deadlock rather than fail. The same is true of "
  "serialization failures under SERIALIZABLE — both mean try again, not "
  "something is broken."
 ),
 "confusable": [{
   "prompt": "What is the standard way to prevent deadlocks between two transactions?",
   "options": ["Take locks in a consistent order", "Use shorter transactions",
               "Raise the isolation level", "Add an index on every column"],
   "answer": 0,
   "explain": "If every transaction locks rows in the same order (by primary key, say), no cycle can form."}],
 "recall": [{"prompt": "What should an application do when it gets a deadlock error?",
             "answer": "retry the transaction",
             "accept": ["retry", "retry it", "roll back and retry"],
             "why": "A deadlock is a normal concurrency outcome, not corruption. The same applies to serialization failures."}],
},

# ====================== s14 · Indexes & EXPLAIN ======================
{
 "id": "s14-001", "topic": "s14", "name": "Wrapping a column kills the index",
 "summary": (
  "An index on a column can only be used when the query compares the column "
  "itself. Wrap it in a function and the index is unusable — the index stores "
  "col, not f(col).\n\n"
  "    WHERE lower(email) = 'a@b.com'      no index on email is used\n"
  "    WHERE created::date = '2026-01-01'  no index on created is used\n"
  "    WHERE created >= '2026-01-01'\n"
  "      AND created <  '2026-01-02'       index used\n\n"
  "This is what sargable means: the predicate can be turned into an index range "
  "scan.\n\n"
  "Two ways out. Rewrite as a range, as above. Or build an expression index that "
  "stores exactly what you search: CREATE INDEX ON users (lower(email)) makes "
  "the first query fast again.\n\n"
  "The same applies to a leading wildcard: LIKE '%foo' cannot use a b-tree, "
  "while LIKE 'foo%' can."
 ),
 "confusable": [{
   "prompt": "Which predicate can use a plain b-tree index on created?",
   "options": ["created >= '2026-01-01'", "date(created) = '2026-01-01'",
               "extract(year FROM created) = 2026", "created::text LIKE '2026%'"],
   "answer": 0,
   "explain": "The index stores created. Any function around it means the index no longer matches the predicate."}],
 "recall": [{"prompt": "Which LIKE pattern can use a b-tree index, 'foo%' or '%foo'?",
             "answer": "'foo%'", "accept": ["foo%", "the leading-wildcard-free one", "'foo%' can"],
             "why": "A b-tree is ordered by prefix, so a known prefix is a range. A leading wildcard is not."}],
},
{
 "id": "s14-002", "topic": "s14", "name": "Composite index column order",
 "summary": (
  "An index on (a, b) is sorted by a first, then by b within each a. That "
  "ordering decides which queries it can serve.\n\n"
  "    WHERE a = 1            uses it\n"
  "    WHERE a = 1 AND b = 2  uses it, best case\n"
  "    WHERE b = 2            cannot use it efficiently\n\n"
  "The rule is the leftmost prefix: you can use a, or a and b, but not b alone. "
  "A phone book sorted by surname then first name is useless for finding "
  "everyone called Grace.\n\n"
  "So an index on (a, b) makes a separate index on a redundant, while one on b "
  "may still be needed.\n\n"
  "Put the equality column first and the range column second. With WHERE a = 1 "
  "AND b > 5, the order (a, b) gives a single contiguous range; (b, a) does not."
 ),
 "confusable": [{
   "prompt": "You have an index on (a, b). Which query cannot use it efficiently?",
   "options": ["WHERE b = 2", "WHERE a = 1", "WHERE a = 1 AND b = 2",
               "WHERE a = 1 AND b > 5"],
   "answer": 0,
   "explain": "Leftmost prefix: the index is sorted by a first, so a query on b alone has no ordered range to scan."}],
 "recall": [{"prompt": "In a composite index, should the equality column or the range column come first?",
             "answer": "the equality column",
             "accept": ["equality", "the equality one", "equality first"],
             "why": "Equality on the leading column leaves a single contiguous range for the second."}],
},
{
 "id": "s14-003", "topic": "s14", "name": "Reading EXPLAIN",
 "summary": (
  "    EXPLAIN              show the plan the planner would choose\n"
  "    EXPLAIN ANALYZE      actually run it and report real timings\n\n"
  "ANALYZE really executes the statement, so wrap a write in BEGIN and ROLLBACK "
  "unless you want it to happen.\n\n"
  "What to look at first: estimated rows against actual rows. A large gap means "
  "the planner's statistics are wrong, and every choice downstream of that "
  "estimate is likely wrong too. Run ANALYZE on the table.\n\n"
  "A sequential scan is not automatically bad. Reading 80% of a table is faster "
  "sequentially than through an index, and the planner knows that. A seq scan "
  "returning three rows out of ten million is the one to worry about.\n\n"
  "EXPLAIN (ANALYZE, BUFFERS) adds cache and disk-read counts, which is how you "
  "tell a slow query from a cold one."
 ),
 "confusable": [{
   "prompt": "In EXPLAIN ANALYZE output, which discrepancy matters most?",
   "options": ["Estimated rows far from actual rows", "Any sequential scan",
               "A high total cost number", "More than three nested loops"],
   "answer": 0,
   "explain": "Bad estimates make every downstream choice suspect. Fix the statistics with ANALYZE before tuning anything else."}],
 "recall": [{"prompt": "What does EXPLAIN ANALYZE do that plain EXPLAIN does not?",
             "answer": "it actually runs the query",
             "accept": ["runs the query", "executes it and reports real timings",
                        "it executes the statement"],
             "why": "So wrap writes in BEGIN ... ROLLBACK, or they take effect."}],
},

# =================== deepening batch: predict and rows ===================
# Every output below is checked against PostgreSQL 16 by tools/verify_sql.py.
# The authored answers in this batch all held up; what the verifier actually
# caught was three faults in ITSELF -- psql command tags leaking into
# multi-statement output, a rows wrapper that cannot contain DELETE ...
# RETURNING, and mutating cards contaminating the fixture for later queries.

{
 "id": "s1-004", "topic": "s1", "name": "DISTINCT applies to the whole row",
 "summary": (
  "DISTINCT is not a function you apply to one column. It de-duplicates the "
  "entire selected row, so adding a column changes what counts as a duplicate.\n\n"
  "    SELECT DISTINCT dept FROM employees;        3 rows\n"
  "    SELECT DISTINCT dept, sal FROM employees;   4 rows\n\n"
  "The second returns everything, because no two employees share both a "
  "department and a salary. People write SELECT DISTINCT id, name expecting the "
  "distinct to apply to name, and get every row back.\n\n"
  "When you really do want one row per key, Postgres has DISTINCT ON:\n\n"
  "    SELECT DISTINCT ON (dept) dept, name\n"
  "    FROM employees ORDER BY dept, sal DESC;\n\n"
  "which keeps the first row per dept in the given order. It is a Postgres "
  "extension; elsewhere you use row_number in a subquery."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT DISTINCT dept FROM employees\nORDER BY dept;",
              "output": "10\n20\nNULL",
              "why": "Two 10s collapse to one. NULL forms its own group here, and sorts last in ascending order by default."}],
 "rows": [{"code": "SELECT DISTINCT dept, sal FROM employees;",
           "answer": "4",
           "why": "No two employees share both values, so DISTINCT removes nothing. The distinct applies to the whole row, not to dept."}],
},
{
 "id": "s1-005", "topic": "s1", "name": "Where NULLs sort",
 "summary": (
  "Postgres treats NULL as larger than any value for ordering purposes. So the "
  "defaults are:\n\n"
  "    ORDER BY col            NULLS LAST\n"
  "    ORDER BY col DESC       NULLS FIRST\n\n"
  "which means reversing the sort also moves the NULLs from one end to the "
  "other. A top-10 list ordered by a nullable column descending starts with the "
  "rows that have no value at all.\n\n"
  "    ORDER BY col DESC NULLS LAST\n\n"
  "is almost always what you meant. The clause is per-column, so a multi-column "
  "sort needs it on each nullable one.\n\n"
  "This is a real dialect difference: MySQL and SQLite sort NULLs first in "
  "ascending order, the opposite of Postgres."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT name FROM employees\nORDER BY dept DESC, id;",
              "output": "Barbara\nLinus\nAda\nGrace",
              "why": "Descending puts NULLs FIRST in Postgres, so Barbara leads. The trailing id is what makes the Ada/Grace tie on dept 10 come out the same way every time."}],
 "confusable": [{
   "prompt": "In PostgreSQL, where do NULLs go in a plain ascending ORDER BY?",
   "options": ["Last", "First", "They are excluded", "It depends on the index"],
   "answer": 0,
   "explain": "NULL sorts as larger than everything, so ascending puts them last and descending puts them first. MySQL and SQLite do the opposite."}],
},
{
 "id": "s2-004", "topic": "s2", "name": "NULL propagates through expressions",
 "summary": (
  "Almost every operator returns NULL if any input is NULL. That includes string "
  "concatenation and arithmetic, which surprises people who expect an empty "
  "string or a zero.\n\n"
  "    'a' || NULL      -> NULL, not 'a'\n"
  "    1 + NULL         -> NULL\n"
  "    concat('a',NULL) -> 'a'   (the function IS null-tolerant)\n\n"
  "So building an address line by concatenating fields with || gives NULL for "
  "the whole line if any part is missing. The fixes are coalesce on each part, "
  "or the concat function, or concat_ws which also handles the separators.\n\n"
  "This is why a report shows a blank where you expected a partial value: one "
  "missing field poisoned the whole expression, and nothing warned you."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT name || '-' || dept FROM employees\nORDER BY id;",
              "output": "Ada-10\nGrace-10\nLinus-20\nNULL",
              "why": "Barbara's dept is NULL, and || returns NULL if any operand is NULL, so her whole line is NULL rather than 'Barbara-'."}],
 "confusable": [{
   "prompt": "Which of these returns 'a' when the second argument is NULL?",
   "options": ["concat('a', NULL)", "'a' || NULL", "'a' + NULL", "'a'::text || NULL::text"],
   "answer": 0,
   "explain": "The concat function ignores NULL arguments; the || operator propagates NULL through the whole expression."}],
},
{
 "id": "s2-005", "topic": "s2", "name": "IS DISTINCT FROM",
 "summary": (
  "Ordinary comparison cannot answer are these two values different when either "
  "might be NULL. IS DISTINCT FROM can: it compares treating NULL as an ordinary "
  "value that equals itself.\n\n"
  "    NULL =  NULL                     -> NULL\n"
  "    NULL IS NOT DISTINCT FROM NULL   -> true\n"
  "    1    IS DISTINCT FROM NULL       -> true\n"
  "    1    <> NULL                     -> NULL\n\n"
  "It is the right tool for change detection: a trigger or a diff query asking "
  "did this column change has to treat NULL to 5 as a change, and = cannot.\n\n"
  "Postgres, SQLite and modern MySQL all have it. MySQL also has the <=> "
  "operator, which is IS NOT DISTINCT FROM under a different name."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM employees\nWHERE dept IS DISTINCT FROM 10;",
           "answer": "2",
           "why": "Linus (20) and Barbara (NULL). Plain dept <> 10 would return only Linus, because NULL <> 10 is unknown."}],
 "predict": [{"code": "SELECT NULL IS NOT DISTINCT FROM NULL;",
              "fixture": NO_TABLES,
              "output": "t",
              "why": "IS NOT DISTINCT FROM treats NULL as equal to itself, so this is true. NULL = NULL would be NULL."}],
},
{
 "id": "s3-006", "topic": "s3", "name": "The anti-join",
 "summary": (
  "Finding rows on one side with no match on the other is the anti-join, and it "
  "has two idiomatic spellings.\n\n"
  "    SELECT o.* FROM orders o\n"
  "    LEFT JOIN items i ON i.ord = o.id\n"
  "    WHERE i.ord IS NULL;\n\n"
  "    SELECT o.* FROM orders o\n"
  "    WHERE NOT EXISTS (SELECT 1 FROM items i WHERE i.ord = o.id);\n\n"
  "Both find orders with no items. The LEFT JOIN form works by keeping the "
  "unmatched rows and then filtering for exactly the NULL-filled ones — which is "
  "the one case where a WHERE on the right-hand table is correct rather than a "
  "bug.\n\n"
  "NOT EXISTS reads more clearly and cannot fan out. Prefer it unless you need "
  "columns from the right side."
 ),
 "fixture": ORD,
 "rows": [{"code": "SELECT o.* FROM orders o\nLEFT JOIN items i ON i.ord = o.id\nWHERE i.ord IS NULL;",
           "answer": "1",
           "why": "Only order 3 has no items. The LEFT JOIN keeps it with NULLs on the right, and the IS NULL test selects exactly those."}],
 "confusable": [{
   "prompt": "In an anti-join, why is the WHERE clause on the right-hand table not a bug?",
   "options": ["Selecting the NULL-filled rows is the point",
               "WHERE and ON are the same for LEFT JOIN", "It only works with IS NULL",
               "The optimiser rewrites it"],
   "answer": 0,
   "explain": "Normally a WHERE on the right side undoes the outer join. Here that is exactly what you want: the unmatched rows are the answer."}],
},
{
 "id": "s3-007", "topic": "s3", "name": "Fan-out inflates a sum",
 "summary": (
  "Join one order to its three items and the order row is repeated three times. "
  "Sum the order total across that join and you count it three times.\n\n"
  "    SELECT sum(o.total)\n"
  "    FROM orders o JOIN items i ON i.ord = o.id;\n\n"
  "gives 350, not 180: 100 counted three times plus 50 counted once, with order "
  "3 dropped entirely by the inner join.\n\n"
  "The number is plausible, which is what makes it dangerous — nothing errors "
  "and the total is simply wrong.\n\n"
  "The fix is to aggregate before joining, so each side has one row per key:\n\n"
  "    SELECT sum(total) FROM orders;                        -- 180\n"
  "    ... or join to (SELECT ord, sum(qty) FROM items GROUP BY ord)\n\n"
  "When a total is too large by an oddly round factor, suspect a fan-out first."
 ),
 "fixture": ORD,
 "predict": [{"code": "SELECT sum(o.total)\nFROM orders o JOIN items i ON i.ord = o.id;",
              "output": "350",
              "why": "Order 1 (100) is repeated once per item, so 300, plus order 2's 50. Order 3 has no items and the inner join drops it."}],
 "rows": [{"code": "SELECT * FROM orders o\nLEFT JOIN items i ON i.ord = o.id;",
           "answer": "5",
           "why": "Order 1 fans out to three rows, order 2 to one, and order 3 survives as a single NULL-filled row."}],
},
{
 "id": "s4-004", "topic": "s4", "name": "count(DISTINCT) after a join",
 "summary": (
  "Once a join has fanned rows out, count(*) counts join rows, not the thing you "
  "meant to count. count(DISTINCT key) counts the thing.\n\n"
  "    SELECT count(*)                 -- 4: one per item\n"
  "    SELECT count(DISTINCT o.id)     -- 2: one per order\n"
  "    FROM orders o JOIN items i ON i.ord = o.id;\n\n"
  "Both are correct answers to different questions, and only one of them is the "
  "question you asked.\n\n"
  "count(DISTINCT ...) is noticeably more expensive than count(*) — it has to "
  "sort or hash the values — so on a large table it is worth checking whether "
  "aggregating before the join gets the same answer more cheaply.\n\n"
  "And as always, DISTINCT skips NULLs, because count of a column always does."
 ),
 "fixture": ORD,
 "predict": [{"code": "SELECT count(*), count(DISTINCT o.id)\nFROM orders o JOIN items i ON i.ord = o.id;",
              "output": "4|2",
              "accept": ["4 | 2"],
              "why": "Four join rows, from two distinct orders. Order 3 is absent because the inner join drops it."}],
 "rows": [{"code": "SELECT o.cust, count(*)\nFROM orders o JOIN items i ON i.ord = o.id\nGROUP BY o.cust;",
           "answer": "2",
           "why": "One group per customer that has any items: Ada and Grace. Linus has no items, so the inner join leaves him out entirely."}],
},
{
 "id": "s4-005", "topic": "s4", "name": "string_agg collects a group",
 "summary": (
  "Sometimes you want the members of a group, not a count of them. string_agg "
  "concatenates them into one value.\n\n"
  "    SELECT dept, string_agg(name, ',' ORDER BY name)\n"
  "    FROM employees GROUP BY dept;\n\n"
  "The ORDER BY inside the aggregate is what makes the output stable — without "
  "it the members appear in whatever order the group was built, which can change "
  "between runs. It is easy to leave out and produces a value that looks "
  "deterministic and is not.\n\n"
  "array_agg does the same thing into an array, which is usually better if the "
  "result is going back to an application rather than to a human.\n\n"
  "MySQL calls it GROUP_CONCAT, SQLite calls it group_concat, and neither takes "
  "the same argument shape — this one does not port."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT string_agg(name, ',' ORDER BY name)\nFROM employees WHERE dept = 10;",
              "output": "Ada,Grace",
              "why": "The two Eng employees, joined in name order. Without the ORDER BY inside the aggregate the order would be unspecified."}],
 "recall": [{"prompt": "What makes string_agg output deterministic?",
             "answer": "an ORDER BY inside the aggregate",
             "accept": ["ORDER BY inside the aggregate", "ordering the aggregate",
                        "an ORDER BY in the aggregate call"],
             "why": "Without it the members appear in whatever order the group was assembled."}],
},
{
 "id": "s5-003", "topic": "s5", "name": "A scalar subquery per row",
 "summary": (
  "A subquery in the SELECT list must return one row and one column. It runs "
  "conceptually once per outer row, and returns NULL rather than nothing when it "
  "finds no match.\n\n"
  "    SELECT o.cust,\n"
  "           (SELECT count(*) FROM items i WHERE i.ord = o.id)\n"
  "    FROM orders o;\n\n"
  "count is the special case: it returns 0 for an empty set, so the order with "
  "no items shows 0 rather than NULL. Any other aggregate — sum, max — would "
  "give NULL there, which is the usual source of a surprising blank.\n\n"
  "The alternative is a LEFT JOIN with GROUP BY, which is one pass rather than "
  "one per row, but needs coalesce to turn the missing side into 0. Postgres "
  "often plans both the same way."
 ),
 "fixture": ORD,
 "predict": [{"code": "SELECT (SELECT count(*) FROM items i\n        WHERE i.ord = o.id)\nFROM orders o\nORDER BY o.id;",
              "output": "3\n1\n0",
              "why": "Orders 1, 2 and 3 have three, one and no items. count returns 0 for the empty set; sum or max would have returned NULL."}],
 "confusable": [{
   "prompt": "A correlated sum(...) subquery finds no matching rows. What does that row show?",
   "options": ["NULL", "0", "An empty string", "The row is dropped"],
   "answer": 0,
   "explain": "Only count returns 0 over an empty set. sum, avg, max and min all return NULL — wrap in coalesce if you need a number."}],
},
{
 "id": "s6-003", "topic": "s6", "name": "How much UNION removes",
 "summary": (
  "The cost of UNION is proportional to what it has to look at, not to what it "
  "removes. Two branches with no overlap still pay for a full de-duplication "
  "pass that finds nothing.\n\n"
  "    SELECT dept FROM employees\n"
  "    UNION ALL\n"
  "    SELECT id FROM departments;     -- 7 rows\n\n"
  "    ... UNION ...                   -- 4 rows\n\n"
  "The ALL version keeps all four employee departments (including the NULL) and "
  "all three department ids. UNION collapses the duplicate 10s and the 10, 20 "
  "appearing on both sides, and treats the two NULLs as one.\n\n"
  "That last part is worth noticing: set operations are null-safe, so UNION "
  "de-duplicates NULLs even though NULL = NULL is not true."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT dept FROM employees\nUNION ALL\nSELECT id FROM departments;",
           "answer": "7",
           "why": "Four rows from employees, including the NULL, plus three department ids. ALL removes nothing."}],
 "predict": [{"code": "SELECT dept FROM employees\nUNION\nSELECT id FROM departments\nORDER BY 1;",
              "output": "10\n20\n30\nNULL",
              "why": "Duplicated 10s collapse, 10 and 20 appear on both sides, and the two NULLs count as one — set operations are null-safe."}],
},
{
 "id": "s7-003", "topic": "s7", "name": "Chained CTEs read top to bottom",
 "summary": (
  "Each CTE can refer to the ones declared before it, so a query that would be "
  "three levels of nesting becomes three named steps in the order they happen.\n\n"
  "    WITH per_order AS (\n"
  "      SELECT ord, sum(qty) AS q\n"
  "      FROM items GROUP BY ord\n"
  "    ), big AS (\n"
  "      SELECT * FROM per_order WHERE q > 1\n"
  "    )\n"
  "    SELECT count(*) FROM big;\n\n"
  "That is the aggregate-then-join pattern from the fan-out card, written so "
  "each stage is visible and separately checkable — you can run the query with "
  "SELECT * FROM per_order to see the intermediate result.\n\n"
  "The steps are declarations, not execution order: Postgres still plans the "
  "whole thing as one query and may inline every stage."
 ),
 "fixture": ORD,
 "predict": [{"code": "WITH per_order AS (\n  SELECT ord, sum(qty) AS q\n  FROM items GROUP BY ord\n)\nSELECT q FROM per_order ORDER BY ord;",
              "output": "6\n1",
              "why": "Order 1's items are 2, 1 and 3, so 6; order 2 has a single item of 1. Order 3 has no items and so no group."}],
 "rows": [{"code": "WITH per_order AS (\n  SELECT ord, sum(qty) AS q\n  FROM items GROUP BY ord\n)\nSELECT * FROM orders o\nLEFT JOIN per_order p ON p.ord = o.id;",
           "answer": "3",
           "why": "Aggregating first means one row per order, so the join cannot fan out. Three orders in, three rows out."}],
},
{
 "id": "s8-004", "topic": "s8", "name": "Running totals",
 "summary": (
  "Adding ORDER BY inside OVER turns an aggregate into a running one. Without "
  "it, the aggregate covers the whole partition; with it, each row sees "
  "everything up to and including itself.\n\n"
  "    sum(amt) OVER ()                    -- the grand total, on every row\n"
  "    sum(amt) OVER (ORDER BY mon)        -- running total\n\n"
  "That difference catches people out, because the two look almost identical and "
  "one of them is a constant.\n\n"
  "The reason is the default frame: with ORDER BY it is RANGE BETWEEN UNBOUNDED "
  "PRECEDING AND CURRENT ROW, and without ORDER BY it is the whole partition.\n\n"
  "Both forms are useful. sum(x) OVER () beside each row is the neat way to show "
  "each row's share of the total without a self-join."
 ),
 "fixture": SALES,
 "predict": [{"code": "SELECT sum(amt) OVER (ORDER BY mon)\nFROM sales\nORDER BY mon;",
              "output": "100\n250\n340\n540",
              "why": "A running total: 100, then 100+150, then +90, then +200. Adding ORDER BY inside OVER is what makes it cumulative."}],
 "confusable": [{
   "prompt": "What does sum(amt) OVER () — no ORDER BY — put on each row?",
   "options": ["The grand total, the same on every row", "A running total",
               "The row's own value", "NULL"],
   "answer": 0,
   "explain": "With no ORDER BY the frame is the whole partition, so every row sees the same total. ORDER BY makes it cumulative."}],
},
{
 "id": "s8-005", "topic": "s8", "name": "LAG and LEAD",
 "summary": (
  "LAG reaches backwards in the ordered window, LEAD forwards. They are how you "
  "compare a row with its neighbour without a self-join.\n\n"
  "    lag(amt) OVER (ORDER BY mon)          the previous month's value\n"
  "    amt - lag(amt) OVER (ORDER BY mon)    the change\n\n"
  "The first row has no previous row, so LAG returns NULL — and subtracting NULL "
  "gives NULL, so the first change is blank rather than zero. That is usually "
  "correct, and if you want a number, LAG takes a default:\n\n"
  "    lag(amt, 1, 0) OVER (ORDER BY mon)\n\n"
  "The second argument is the offset, the third the default. Reaching two rows "
  "back is lag(amt, 2)."
 ),
 "fixture": SALES,
 "predict": [{"code": "SELECT amt - lag(amt) OVER (ORDER BY mon)\nFROM sales\nORDER BY mon;",
              "output": "NULL\n50\n-60\n110",
              "why": "The first row has no predecessor, so lag is NULL and the subtraction is NULL. Then 150-100, 90-150, 200-90."}],
 "fill": [{"code": "-- previous amount, or 0 for month 1\nSELECT lag(amt, 1, __) OVER (ORDER BY mon)\nFROM sales;",
           "answer": "0", "hint": "the third argument is the default"}],
},
{
 "id": "s8-006", "topic": "s8", "name": "The last_value trap",
 "summary": (
  "first_value works as expected inside an ordered window. last_value usually "
  "does not, and the reason is the default frame.\n\n"
  "    last_value(amt) OVER (ORDER BY mon)\n\n"
  "returns each row's own value, not the final one, because the default frame "
  "ends at the current row — so the last row of the frame IS the current row.\n\n"
  "The fix is to state the frame explicitly:\n\n"
  "    last_value(amt) OVER (\n"
  "      ORDER BY mon\n"
  "      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)\n\n"
  "This is the clearest example of why frames are worth understanding rather "
  "than memorising which functions misbehave. Nothing is wrong with last_value; "
  "the frame is simply smaller than you assumed."
 ),
 "fixture": SALES,
 "predict": [{"code": "SELECT last_value(amt) OVER (ORDER BY mon)\nFROM sales\nORDER BY mon;",
              "output": "100\n150\n90\n200",
              "why": "The default frame ends at the current row, so the last value in the frame is the row's own. Widen the frame to UNBOUNDED FOLLOWING to get 200 throughout."}],
 "confusable": [{
   "prompt": "Why does last_value() with a plain ORDER BY return each row's own value?",
   "options": ["The default frame ends at the current row", "last_value ignores ORDER BY",
               "It needs PARTITION BY", "It is a Postgres bug"],
   "answer": 0,
   "explain": "The default is RANGE UNBOUNDED PRECEDING TO CURRENT ROW. State ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING."}],
},
{
 "id": "s9-003", "topic": "s9", "name": "Carrying depth through a recursion",
 "summary": (
  "The recursive branch can build up a value as it walks, which is how you get "
  "the depth of each node or the path to it.\n\n"
  "    WITH RECURSIVE t AS (\n"
  "      SELECT id, name, 1 AS depth FROM node WHERE parent IS NULL\n"
  "      UNION ALL\n"
  "      SELECT n.id, n.name, t.depth + 1\n"
  "      FROM node n JOIN t ON n.parent = t.id\n"
  "    )\n"
  "    SELECT depth FROM t ORDER BY id;\n\n"
  "The base row starts at 1 and each step adds one. The same trick with an array "
  "instead of an integer builds the full path, which is what the cycle detection "
  "on the previous card needs.\n\n"
  "Note the join is on n.parent = t.id: each round takes the rows found last "
  "time and looks for their children."
 ),
 "fixture": TREE,
 "predict": [{"code": "WITH RECURSIVE t AS (\n  SELECT id, 1 AS d FROM node\n  WHERE parent IS NULL\n  UNION ALL\n  SELECT n.id, t.d + 1 FROM node n\n  JOIN t ON n.parent = t.id\n)\nSELECT d FROM t ORDER BY id;",
              "output": "1\n2\n2\n3\n4",
              "why": "root is depth 1, a and b are 2, a1 is 3 and a1x is 4. Ordering by id lines them up with the table."}],
 "rows": [{"code": "WITH RECURSIVE t AS (\n  SELECT id FROM node WHERE id = 2\n  UNION ALL\n  SELECT n.id FROM node n\n  JOIN t ON n.parent = t.id\n)\nSELECT * FROM t;",
           "answer": "3",
           "why": "Starting at a: itself, a1, and a1x. Starting the recursion anywhere gives that subtree."}],
},
{
 "id": "s10-004", "topic": "s10", "name": "CASE stops at the first match",
 "summary": (
  "CASE evaluates its WHEN branches in order and takes the first that is true. "
  "Later branches are not considered, even if they would also match.\n\n"
  "    CASE WHEN sal > 50  THEN 'ok'\n"
  "         WHEN sal > 95  THEN 'high'\n"
  "         ELSE 'low' END\n\n"
  "Nothing is ever 'high' here, because anything over 95 is already over 50 and "
  "matched the first branch. Ordering overlapping conditions from narrowest to "
  "widest is the whole discipline of writing CASE.\n\n"
  "This makes CASE useful as a fall-through ladder, and makes a mis-ordered one "
  "silently wrong — it produces a plausible value for every row and never errors."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT CASE WHEN sal > 50 THEN 'ok'\n            WHEN sal > 95 THEN 'high'\n            ELSE 'low' END\nFROM employees ORDER BY id;",
              "output": "ok\nok\nok\nok",
              "why": "Every salary is over 50, so the first branch always wins and the 'high' branch is unreachable. Order the conditions narrowest first."}],
 "confusable": [{
   "prompt": "In a CASE with two overlapping WHEN branches, which one applies?",
   "options": ["The first one written", "The most specific one", "The last one written",
               "It is an error"],
   "answer": 0,
   "explain": "Branches are tested in order and the first true one wins, so a wider condition placed first makes narrower ones unreachable."}],
},
{
 "id": "s11-004", "topic": "s11", "name": "RETURNING hands rows back",
 "summary": (
  "Postgres lets INSERT, UPDATE and DELETE return the rows they touched, so you "
  "do not need a second query to find out what happened.\n\n"
  "    INSERT INTO orders (id, cust, total)\n"
  "    VALUES (4, 'Bela', 70) RETURNING id;\n\n"
  "    UPDATE orders SET total = total + 10\n"
  "    WHERE cust = 'Ada' RETURNING id, total;\n\n"
  "For an UPDATE, RETURNING gives the NEW values by default; the old ones are "
  "available through the special OLD alias only in triggers, not here.\n\n"
  "It matters most for generated keys: RETURNING id is how you learn the "
  "identity of a row you just inserted without a round trip and without a "
  "sequence-currval race. It is also what makes data-modifying CTEs possible."
 ),
 "fixture": ORD,
 "predict": [{"code": "UPDATE orders SET total = total + 10\nWHERE cust = 'Ada'\nRETURNING total;",
              "output": "110",
              "why": "RETURNING gives the new value, not the old one. One row matched, so one row comes back."}],
 "rows": [{"code": "DELETE FROM items WHERE ord = 1 RETURNING *;",
           "answer": "3",
           "why": "Order 1 has three items, so three rows are deleted and three are returned."}],
},
{
 "id": "s12-003", "topic": "s12", "name": "A CHECK constraint passes on NULL",
 "summary": (
  "A CHECK constraint rejects a row only when the condition evaluates to false. "
  "NULL is not false, so a NULL sails straight through.\n\n"
  "    CREATE TABLE t (qty int CHECK (qty > 0));\n"
  "    INSERT INTO t VALUES (NULL);   -- accepted\n\n"
  "The condition is NULL > 0, which is unknown, and unknown is not a violation. "
  "That is the standard behaviour and it is the same three-valued logic as "
  "everywhere else — but a constraint that looks like it guarantees a positive "
  "quantity guarantees nothing about missing ones.\n\n"
  "If you meant it, say NOT NULL as well. The two constraints do different jobs "
  "and a column often needs both."
 ),
 "fixture": NO_TABLES,
 "predict": [{"code": "CREATE TEMP TABLE t (\n  qty int CHECK (qty > 0));\nINSERT INTO t VALUES (NULL);\nSELECT count(*) FROM t;",
              "output": "1",
              "why": "NULL > 0 is unknown, not false, and CHECK only rejects false. The row is accepted; NOT NULL is a separate constraint."}],
 "confusable": [{
   "prompt": "A column has CHECK (qty > 0). Can it hold NULL?",
   "options": ["Yes — CHECK only rejects false", "No — NULL fails the check",
               "Only if the column has a default", "Only in a transaction"],
   "answer": 0,
   "explain": "NULL > 0 is unknown, and a CHECK rejects only a definite false. Add NOT NULL if you need one."}],
},
{
 "id": "s13-004", "topic": "s13", "name": "Savepoints roll back part of a transaction",
 "summary": (
  "A savepoint is a marker inside a transaction you can roll back to without "
  "abandoning the whole thing.\n\n"
  "    BEGIN;\n"
  "    INSERT INTO t VALUES (1);\n"
  "    SAVEPOINT s;\n"
  "    INSERT INTO t VALUES (2);\n"
  "    ROLLBACK TO s;      -- undoes only the second insert\n"
  "    COMMIT;             -- the first one is committed\n\n"
  "It matters more than it looks, because in Postgres any error aborts the entire "
  "transaction: every later statement fails with current transaction is aborted "
  "until you roll back. A savepoint before a statement that might fail lets you "
  "recover and carry on.\n\n"
  "That is exactly what psql's ON_ERROR_ROLLBACK does, and what most drivers use "
  "to implement nested transactions — there is no real nesting underneath."
 ),
 "fixture": NO_TABLES,
 "predict": [{"code": "CREATE TEMP TABLE t (n int);\nBEGIN;\nINSERT INTO t VALUES (1);\nSAVEPOINT s;\nINSERT INTO t VALUES (2);\nROLLBACK TO s;\nCOMMIT;\nSELECT n FROM t ORDER BY n;",
              "output": "1",
              "why": "Rolling back to the savepoint undoes only what happened after it. The first insert survives the commit."}],
 "recall": [{"prompt": "In PostgreSQL, what happens to the rest of a transaction after any statement errors?",
             "answer": "it is aborted until you roll back",
             "accept": ["the whole transaction aborts", "every later statement fails",
                        "the transaction is aborted"],
             "why": "A SAVEPOINT taken before the risky statement is what lets you recover and continue."}],
},

# ============ second deepening batch: the thin topics ============
{
 "id": "s3-008", "topic": "s3", "name": "Self-join and USING",
 "summary": (
  "A table can be joined to itself, as long as each side gets its own alias. It "
  "is how you compare rows within one table.\n\n"
  "    SELECT a.name, b.name\n"
  "    FROM employees a JOIN employees b\n"
  "      ON a.dept = b.dept AND a.id < b.id;\n\n"
  "The a.id < b.id is doing real work: without it every employee pairs with "
  "themselves and each pair appears twice, once in each order.\n\n"
  "When both sides name the join column identically, USING is shorter and "
  "collapses the two columns into one in the output:\n\n"
  "    FROM orders JOIN items USING (ord)     -- if both called it ord\n\n"
  "USING also means SELECT * returns the key once rather than twice, which is "
  "the main practical difference from ON."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT a.name, b.name\nFROM employees a JOIN employees b\n  ON a.dept = b.dept AND a.id < b.id;",
           "answer": "1",
           "why": "Only Ada and Grace share a department. a.id < b.id keeps one row per pair instead of two, and stops anyone pairing with themselves."}],
 "confusable": [{
   "prompt": "What does USING (id) do that ON a.id = b.id does not?",
   "options": ["It returns the join column once in SELECT *", "It allows outer joins",
               "It is faster", "It permits different column names"],
   "answer": 0,
   "explain": "USING merges the two identically named columns into one output column. ON leaves both."}],
},
{
 "id": "s4-006", "topic": "s4", "name": "GROUP BY several columns",
 "summary": (
  "Grouping by two columns makes one group per distinct combination that "
  "actually occurs. Combinations with no rows do not appear — GROUP BY never "
  "invents a group.\n\n"
  "    SELECT dept, sal, count(*)\n"
  "    FROM employees GROUP BY dept, sal;\n\n"
  "That is four groups here, because no two employees share both values.\n\n"
  "The consequence people trip on is a report with gaps: group sales by month "
  "and a month with no sales is simply missing, rather than showing zero. The "
  "fix is to generate the full set of keys and LEFT JOIN the aggregate onto it — "
  "generate_series is the usual source for dates.\n\n"
  "ROLLUP and GROUPING SETS add subtotal rows on top of the ordinary grouping, "
  "which is a different job from filling gaps."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT dept, sal FROM employees\nGROUP BY dept, sal;",
           "answer": "4",
           "why": "One group per combination that occurs, and all four employees differ in salary. Grouping by dept alone would give three."}],
 "confusable": [{
   "prompt": "You group sales by month. A month with no sales shows what?",
   "options": ["Nothing — the row is absent", "A row with 0", "A row with NULL",
               "An error"],
   "answer": 0,
   "explain": "GROUP BY only produces groups that have rows. Generate the months and LEFT JOIN the aggregate onto them."}],
},
{
 "id": "s5-004", "topic": "s5", "name": "IN is = ANY in disguise",
 "summary": (
  "IN (a, b, c) is shorthand for = ANY, and Postgres also lets you pass an array "
  "instead of a list.\n\n"
  "    WHERE dept IN (10, 20)\n"
  "    WHERE dept = ANY (ARRAY[10, 20])\n"
  "    WHERE dept = ANY (SELECT id FROM departments)\n\n"
  "The array form is worth knowing because a driver can bind one parameter for "
  "the whole list. Building an IN list by string concatenation is the classic "
  "way to end up with an injection hole and a query the planner cannot cache.\n\n"
  "The mirror image is <> ALL, which is what NOT IN expands to — and which is "
  "why one NULL in the list makes the whole thing unknown.\n\n"
  "There is no equivalent shorthand for the NULL-safe case; that is what NOT "
  "EXISTS is for."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT * FROM employees\nWHERE dept = ANY (ARRAY[10, 20]);",
           "answer": "3",
           "why": "Identical to dept IN (10, 20). Barbara's NULL matches neither, so she is excluded."}],
 "recall": [{"prompt": "NOT IN (a, b) expands to which comparison?",
             "answer": "<> ALL", "accept": ["<> ALL (a, b)", "not equal to all of them",
                                            "col <> ALL"],
             "why": "That expansion is why a NULL anywhere in the list makes every row unknown."}],
},
{
 "id": "s5-005", "topic": "s5", "name": "LATERAL sees the row beside it",
 "summary": (
  "An ordinary subquery in FROM cannot refer to the other tables in the same "
  "FROM. LATERAL lifts that restriction, so the subquery runs per outer row.\n\n"
  "    SELECT o.cust, t.sku\n"
  "    FROM orders o\n"
  "    LEFT JOIN LATERAL (\n"
  "      SELECT sku FROM items i\n"
  "      WHERE i.ord = o.id ORDER BY qty DESC LIMIT 1\n"
  "    ) t ON true;\n\n"
  "That is the clean way to do top-N-per-group when N is small: the subquery is "
  "an ordinary ORDER BY ... LIMIT, run once per order.\n\n"
  "LEFT JOIN LATERAL ... ON true keeps outer rows whose subquery found nothing; "
  "a plain comma or CROSS JOIN LATERAL would drop them. It is the lateral "
  "equivalent of the difference between INNER and LEFT."
 ),
 "fixture": ORD,
 "rows": [{"code": "SELECT o.cust, t.sku\nFROM orders o\nLEFT JOIN LATERAL (\n  SELECT sku FROM items i WHERE i.ord = o.id\n  ORDER BY qty DESC LIMIT 1\n) t ON true;",
           "answer": "3",
           "why": "One row per order. LEFT ... ON true keeps order 3, whose subquery found nothing, with a NULL sku."}],
 "fill": [{"code": "-- keep orders whose subquery finds nothing\nFROM orders o\nLEFT JOIN __ (SELECT 1) t ON true;",
           "answer": "LATERAL", "accept": ["lateral"],
           "hint": "the keyword that lets a subquery see the outer row"}],
},
{
 "id": "s6-004", "topic": "s6", "name": "INTERSECT and EXCEPT in practice",
 "summary": (
  "The quickest way to diff two result sets is to run EXCEPT both ways round.\n\n"
  "    SELECT id FROM expected EXCEPT SELECT id FROM actual;   -- missing\n"
  "    SELECT id FROM actual EXCEPT SELECT id FROM expected;   -- extra\n\n"
  "Both compare whole rows and both de-duplicate, so a row appearing twice on "
  "one side and once on the other looks identical to them. EXCEPT ALL and "
  "INTERSECT ALL keep the multiplicity if that matters.\n\n"
  "They are null-safe, unlike IN and NOT IN, which is what makes them reliable "
  "for a migration check on nullable columns.\n\n"
  "The branches must line up by position, not by name: the first column of one "
  "is compared with the first column of the other, whatever they are called."
 ),
 "fixture": EMP,
 "rows": [{"code": "SELECT dept FROM employees\nEXCEPT\nSELECT id FROM departments;",
           "answer": "1",
           "why": "Employee departments are 10, 10, 20 and NULL. Removing 10, 20 and 30 leaves NULL — one row, because EXCEPT is null-safe and de-duplicates."}],
 "predict": [{"code": "SELECT dept FROM employees\nINTERSECT\nSELECT id FROM departments\nORDER BY 1;",
              "output": "10\n20",
              "why": "Only the departments that both appear in employees and exist in departments. Legal (30) has no employees, and NULL matches nothing on the right."}],
},
{
 "id": "s7-004", "topic": "s7", "name": "One snapshot for the whole statement",
 "summary": (
  "Every branch of a statement sees the database as it was when the statement "
  "began. A data-modifying CTE therefore cannot see its own effects, and neither "
  "can the query that reads from it.\n\n"
  "    WITH gone AS (\n"
  "      DELETE FROM items WHERE ord = 1\n"
  "      RETURNING *\n"
  "    )\n"
  "    SELECT count(*) FROM items;\n\n"
  "returns 4, not 1: the outer SELECT reads the snapshot from before the delete. "
  "To count what survived, count from the CTE's RETURNING rows instead, or use "
  "two statements.\n\n"
  "This is not a quirk to work around so much as the rule that makes the whole "
  "thing safe: with one snapshot, the order in which branches happen to run "
  "cannot change the result."
 ),
 "fixture": ORD,
 "predict": [{"code": "WITH gone AS (\n  DELETE FROM items WHERE ord = 1\n  RETURNING *\n)\nSELECT count(*) FROM items;",
              "output": "4",
              "why": "The outer SELECT reads the snapshot taken before the statement ran, so it still sees all four items. The delete does take effect afterwards."}],
 "confusable": [{
   "prompt": "A data-modifying CTE deletes rows. What does the outer SELECT from the same table see?",
   "options": ["The rows as they were before the statement", "The rows after the delete",
               "An error", "It depends on declaration order"],
   "answer": 0,
   "explain": "All branches share one snapshot taken at the start, so no branch sees another's changes."}],
},
{
 "id": "s8-007", "topic": "s8", "name": "PARTITION BY keeps every row",
 "summary": (
  "A window function adds a column; it never removes a row. That is the whole "
  "difference from GROUP BY, and the reason both exist.\n\n"
  "    SELECT dept, count(*) FROM employees\nGROUP BY dept;\n"
  "    -- 3 rows: one per department\n\n"
  "    SELECT dept,\n"
  "      count(*) OVER (PARTITION BY dept)\n"
  "    FROM employees;\n"
  "    -- 4 rows: every employee, with their department's size beside them\n\n"
  "So the window form is what you want when the detail matters: each employee "
  "next to their department average, each order next to its share of the day's "
  "total.\n\n"
  "A NULL partition key forms its own partition, exactly as it forms its own "
  "GROUP BY group."
 ),
 "fixture": EMP,
 "predict": [{"code": "SELECT count(*) OVER (PARTITION BY dept)\nFROM employees\nORDER BY id;",
              "output": "2\n2\n1\n1",
              "why": "Ada and Grace are both in a department of two; Linus is alone in 20; Barbara's NULL forms a partition of one."}],
 "rows": [{"code": "SELECT dept,\n  count(*) OVER (PARTITION BY dept)\nFROM employees;",
           "answer": "4",
           "why": "One row per employee. GROUP BY dept would collapse them to three."}],
},
{
 "id": "s10-005", "topic": "s10", "name": "round, trunc and casting",
 "summary": (
  "Casting to an integer rounds; truncating discards. They differ on exactly the "
  "values you are most likely to test with.\n\n"
  "    SELECT 2.5::int;        -- 3   (half away from zero)\n"
  "    SELECT trunc(2.9);      -- 2\n"
  "    SELECT round(2.5);      -- 3\n"
  "    SELECT 5 / 2;           -- 2   (integer division truncates)\n\n"
  "So integer division truncates while an integer cast rounds, which means "
  "(5/2)::int and 5::numeric/2 give different answers from the same numbers.\n\n"
  "round takes a second argument for decimal places, but only on numeric — "
  "round(x, 2) on a double precision value is an error in Postgres, and casting "
  "to numeric first is the fix. That error appears the first time real data "
  "arrives as a float."
 ),
 "fixture": NO_TABLES,
 "predict": [{"code": "SELECT 5 / 2, 5.0 / 2, 2.5::int;",
              "output": "2|2.5000000000000000|3",
              "accept": ["2 | 2.5000000000000000 | 3"],
              "why": "Integer division truncates to 2; one numeric operand gives exact decimal; casting 2.5 to int rounds half away from zero, to 3."}],
 "confusable": [{
   "prompt": "Why does round(x, 2) sometimes fail in Postgres?",
   "options": ["Two-argument round needs numeric, not double precision",
               "round takes only one argument", "x must be positive",
               "It needs an explicit locale"],
   "answer": 0,
   "explain": "There is no round(double precision, int). Cast to numeric first — which you want for money anyway."}],
},
{
 "id": "s11-005", "topic": "s11", "name": "UPDATE ... FROM",
 "summary": (
  "Updating one table from another does not use a JOIN clause in Postgres. It "
  "uses FROM, and the join condition goes in WHERE.\n\n"
  "    UPDATE orders o\n"
  "    SET total = total + i.qty\n"
  "    FROM items i\n"
  "    WHERE i.ord = o.id;\n\n"
  "The trap is that if the FROM side matches a target row more than once, the "
  "target is updated only ONCE, using an arbitrary one of the matching rows. No "
  "error, no warning, no indication which one won.\n\n"
  "So an update meant to add every item's quantity adds exactly one of them. "
  "When the source can match more than once, aggregate it first:\n\n"
  "    FROM (SELECT ord, sum(qty) q FROM items GROUP BY ord) i\n\n"
  "This is a genuine dialect difference — MySQL writes UPDATE ... JOIN, and its "
  "behaviour here is not the same."
 ),
 "fixture": ORD,
 # Deliberately a rows question, not a predict. Which of the three matching
 # items wins is genuinely arbitrary, so asking for the resulting total would
 # be asking the learner to predict something undefined. How MANY rows are
 # updated is defined, and is the actual lesson: one per target row, not one
 # per match.
 "rows": [{"code": "UPDATE orders o SET total = total + i.qty\nFROM items i WHERE i.ord = o.id\nRETURNING o.id, o.total;",
           "answer": "2",
           "why": "Orders 1 and 2 each update exactly once, even though order 1 matches three items — so the total gains one arbitrary quantity, not the sum. Order 3 matches nothing."}],
 "confusable": [{
   "prompt": "In UPDATE ... FROM, the source matches a target row three times. What happens?",
   "options": ["The target is updated once, from an arbitrary match",
               "It is updated three times, cumulatively", "Postgres raises an error",
               "The target row is skipped"],
   "answer": 0,
   "explain": "One update per target row, using an unspecified matching source row. Aggregate the source when it can match more than once."}],
},
{
 "id": "s12-004", "topic": "s12", "name": "Composite unique constraints",
 "summary": (
  "A unique constraint on two columns forbids duplicate PAIRS, not duplicate "
  "values in either column.\n\n"
  "    UNIQUE (ord, sku)\n\n"
  "allows the same order many times and the same sku many times, and forbids the "
  "same sku appearing twice on one order — which is usually exactly the rule you "
  "want for a line-items table.\n\n"
  "Like any unique constraint it is null-permissive: a row with a NULL sku "
  "collides with nothing, so several NULL skus can sit on the same order.\n\n"
  "It also creates an index on (ord, sku), which follows the leftmost-prefix "
  "rule — so it can serve lookups by ord, and by ord and sku together, but not "
  "by sku alone."
 ),
 "fixture": ORD,
 "rows": [{"code": "SELECT ord, sku FROM items\nGROUP BY ord, sku HAVING count(*) > 1;",
           "answer": "0",
           "why": "No pair repeats, so UNIQUE (ord, sku) would be satisfiable. Sku A appears twice but on different orders, which the constraint permits."}],
 "confusable": [{
   "prompt": "A table has UNIQUE (a, b). Which insert is rejected?",
   "options": ["A second row with the same a AND the same b",
               "A second row with the same a", "A second row with the same b",
               "Any row where a is NULL"],
   "answer": 0,
   "explain": "The constraint is on the pair. Either column may repeat freely as long as the combination does not."}],
},
{
 "id": "s13-005", "topic": "s13", "name": "Reading your own writes",
 "summary": (
  "Inside a transaction you always see your own uncommitted changes, whatever "
  "the isolation level. Isolation governs what you see of OTHER transactions.\n\n"
  "    BEGIN;\n"
  "    INSERT INTO t VALUES (1);\n"
  "    SELECT count(*) FROM t;   -- 1, your own row is visible\n"
  "    ROLLBACK;\n"
  "    SELECT count(*) FROM t;   -- 0\n\n"
  "This is why a test that inserts and then reads back inside one transaction "
  "always passes, and tells you nothing about whether the data was committed.\n\n"
  "The exception, from the CTE card, is within a single statement: branches of "
  "one statement share a snapshot and do not see each other's writes. Between "
  "statements in the same transaction, you do."
 ),
 "fixture": NO_TABLES,
 "predict": [{"code": "CREATE TEMP TABLE t (n int);\nBEGIN;\nINSERT INTO t VALUES (1);\nSELECT count(*) FROM t;",
              "output": "1",
              "why": "A transaction always sees its own uncommitted writes. Isolation levels only control visibility of OTHER transactions."}],
 "confusable": [{
   "prompt": "Inside an uncommitted transaction, can you SELECT the rows you just inserted?",
   "options": ["Yes, always", "Only at READ UNCOMMITTED", "Only after a savepoint",
               "No, not until COMMIT"],
   "answer": 0,
   "explain": "Isolation controls what you see of other transactions. Your own writes are always visible to you."}],
},
{
 "id": "s14-004", "topic": "s14", "name": "Partial and expression indexes",
 "summary": (
  "An index does not have to cover the whole table or store the column as-is.\n\n"
  "    CREATE INDEX ON orders (cust) WHERE total > 100;\n"
  "    CREATE INDEX ON users (lower(email));\n\n"
  "A partial index only holds rows matching its WHERE, so it is smaller, faster "
  "to scan and cheaper to maintain. The planner uses it only when it can prove "
  "your query implies the index's condition — so a query for total > 200 can use "
  "it, and one with no total predicate cannot.\n\n"
  "An expression index stores the computed value, which is what makes "
  "lower(email) = ... indexable at all. The expression in the query has to match "
  "the one in the index exactly.\n\n"
  "The common real use is indexing only the interesting rows: WHERE status = "
  "'pending' on a table where almost everything is done."
 ),
 "confusable": [{
   "prompt": "You have CREATE INDEX ON t (a) WHERE done = false. Which query can use it?",
   "options": ["WHERE a = 1 AND done = false", "WHERE a = 1",
               "WHERE done = true", "WHERE a = 1 OR done = false"],
   "answer": 0,
   "explain": "The planner uses a partial index only when the query provably implies its predicate. Without done = false it cannot know the index holds the needed rows."}],
 "recall": [{"prompt": "Which kind of index makes lower(email) = ... fast?",
             "answer": "an expression index",
             "accept": ["expression index", "a functional index", "functional index",
                        "an index on lower(email)"],
             "why": "It stores the computed value, so the predicate matches what the index holds."}],
},
{
 "id": "s14-005", "topic": "s14", "name": "Index-only scans",
 "summary": (
  "If an index contains every column a query needs, Postgres can answer from the "
  "index alone and never touch the table. EXPLAIN calls that an Index Only Scan.\n\n"
  "    CREATE INDEX ON orders (cust) INCLUDE (total);\n"
  "    SELECT total FROM orders WHERE cust = 'Ada';\n\n"
  "INCLUDE adds payload columns that are stored but not part of the sort key, so "
  "they do not affect the leftmost-prefix rule and do not bloat the comparisons.\n\n"
  "The catch is the visibility map. Postgres still has to know each row is "
  "visible to your transaction, and that information lives in the table. On a "
  "table that has not been vacuumed recently, an index-only scan degrades into "
  "heap fetches — which EXPLAIN reports as Heap Fetches, and which is why an "
  "index-only scan can be fast in testing and slow in production."
 ),
 "confusable": [{
   "prompt": "An Index Only Scan is reporting many Heap Fetches. What is the usual cause?",
   "options": ["The visibility map is stale — the table needs vacuuming",
               "The index is missing a column", "Statistics are out of date",
               "The query lacks an ORDER BY"],
   "answer": 0,
   "explain": "Visibility lives in the table, not the index. Until VACUUM marks pages all-visible, each row still needs a heap lookup."}],
 "recall": [{"prompt": "Which index clause adds payload columns without making them part of the sort key?",
             "answer": "INCLUDE", "accept": ["include", "the INCLUDE clause"],
             "why": "They are stored for index-only scans but do not affect the leftmost-prefix rule."}],
},
]
