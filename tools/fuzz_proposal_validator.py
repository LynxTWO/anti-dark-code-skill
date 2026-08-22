#!/usr/bin/env python3
"""Fuzz the flow-back proposal validator, this repository's only untrusted input boundary.

Everything else here reads content the operator already trusts. A proposal arrives
from a stranger, as a file in a pull request, and this repository's own README says
plainly that skill text becomes instructions executed by an assistant with its
operator's authority. The validator is what stands between those two facts, so it
gets fuzzed rather than sampled.

Four invariants, each a real failure mode rather than a style preference:

- I1 It never raises. A crash on hostile bytes is a denial of service against
  contributors' pull-request checks, and an exception escaping into a harness that
  catches broadly can be read as a pass.
- I2 It never hangs. The validator runs several regular expressions over attacker
  controlled text, and catastrophic backtracking is the classic way a validator
  becomes a weapon. A hang is reported separately from a failure because it blocks
  every later proof.
- I3 It fails closed. Anything that is not byte-for-byte a known-good proposal must
  produce at least one error. Silence on malformed input is the dangerous outcome:
  an empty error list means accepted.
- I4 It can still say yes. A known-good proposal must produce zero errors, or the
  other three invariants are satisfied by a validator that rejects everything and
  proves nothing.

Deterministic: the same seed replays the same corpus. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import signal
import sys
from contextlib import contextmanager
from pathlib import Path


def load_adc(repo: Path):
    spec = importlib.util.spec_from_file_location("adc", repo / "anti-dark-code" / "scripts" / "adc.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Timeout(Exception):
    pass


@contextmanager
def time_limit(seconds: int):
    """Bound one call. Catastrophic backtracking does not yield to a thread timeout."""
    def handler(signum, frame):
        raise Timeout()

    previous = signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


# Patterns chosen because each is a documented way to smuggle meaning past a reader:
# terminal control, bidirectional overrides, zero-width joiners, homoglyph domains,
# and shapes that make naive regular expressions backtrack.
ADVERSARIAL_FRAGMENTS = [
    b"\x1b[31mred\x1b[0m",
    b"\xe2\x80\xae" + b"gnp.exe",
    b"\xe2\x80\x8b\xe2\x80\x8c\xe2\x80\x8d",
    b"\xef\xbb\xbf",
    b"https://exa\xd0\xbcple.com/",
    b"http://user:hunter2@example.com/",
    b"AKIA" + b"I" * 16,
    b"-----BEGIN PRIVATE KEY-----",
    b"/home/someone/secret/path",
    b"C:\\Users\\someone\\secret",
    b"<script>alert(1)</script>",
    b"![img](http://example.com/a.png)",
    b"javascript:alert(1)",
    b"a" * 4000,
    b"(" * 200 + b")" * 200,
    b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!" * 40,
    b"\x00",
    b"\xff\xfe\xfd",
    b"\r\n",
    b"## ADC-LOCAL-001: " + b"x" * 500,
]

FILENAME_ATTACKS = [
    "flowback-000000000000.md",
    "../../etc/passwd",
    "flowback-../../x.md",
    "flowback-0000000000000.md",
    "flowback-ZZZZZZZZZZZZ.md",
    "",
    "flowback-0000_0000000.md",
    "a" * 300 + ".md",
]


def mutate(rng: random.Random, seed_bytes: bytes) -> bytes:
    """Corrupt a valid proposal the way a hostile or careless contributor might."""
    data = bytearray(seed_bytes)
    for _ in range(rng.randint(1, 6)):
        choice = rng.random()
        if not data:
            data = bytearray(b"x")
        if choice < 0.25:
            index = rng.randrange(len(data))
            data[index] = rng.randrange(256)
        elif choice < 0.45:
            index = rng.randrange(len(data))
            del data[index : index + rng.randint(1, 64)]
        elif choice < 0.70:
            index = rng.randrange(len(data) + 1)
            data[index:index] = rng.choice(ADVERSARIAL_FRAGMENTS)
        elif choice < 0.85:
            lines = bytes(data).split(b"\n")
            if len(lines) > 2:
                index = rng.randrange(len(lines))
                lines.insert(index, lines[rng.randrange(len(lines))])
                data = bytearray(b"\n".join(lines))
        else:
            index = rng.randrange(len(data) + 1)
            data[index:index] = bytes(rng.randrange(256) for _ in range(rng.randint(1, 32)))
    return bytes(data)


def generate(rng: random.Random, seeds: list[tuple[bytes, str]]) -> tuple[bytes, str, str]:
    seed_bytes, seed_name = rng.choice(seeds)
    strategy = rng.choice(["mutate", "random", "adversarial", "truncate", "filename"])
    if strategy == "mutate":
        return mutate(rng, seed_bytes), seed_name, strategy
    if strategy == "random":
        return bytes(rng.randrange(256) for _ in range(rng.randint(0, 3000))), seed_name, strategy
    if strategy == "adversarial":
        body = rng.choice(ADVERSARIAL_FRAGMENTS) * rng.randint(1, 20)
        return body, seed_name, strategy
    if strategy == "truncate":
        cut = rng.randrange(len(seed_bytes) + 1)
        return seed_bytes[:cut], seed_name, strategy
    return seed_bytes, rng.choice(FILENAME_ATTACKS), strategy


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fuzz the flow-back proposal validator.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=5, help="Seconds allowed per input")
    parser.add_argument("--save-failures", help="Directory to write reproducers into")
    parser.add_argument("--json", help="Write a summary here")
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    adc = load_adc(repo)

    # Seeds must be proposals the validator actually accepts. The inbox also holds
    # local-mode and hand-written proposals, which are legitimately not valid public
    # submissions; using one as a control would report a false failure.
    candidates: list[tuple[bytes, str]] = []
    incoming = repo / "anti-dark-code" / "incoming"
    if incoming.is_dir():
        for path in sorted(incoming.glob("flowback-*.md")):
            candidates.append((path.read_bytes(), path.name))

    seeds: list[tuple[bytes, str]] = []
    rejected: list[str] = []
    for data, name in candidates:
        if adc.validate_flowback_proposal_bytes(data, name, public_only=True):
            rejected.append(name)
        else:
            seeds.append((data, name))

    if not seeds:
        # I4 cannot run without a valid control, and a validator that rejects
        # everything would otherwise look healthy against the other three invariants.
        print(
            "No known-good public proposal available as a control. "
            f"Inspected {len(candidates)} file(s); none validate clean.",
            file=sys.stderr,
        )
        return 2
    print(f"control: {len(seeds)} known-good proposal(s) validate clean" +
          (f"; skipped {len(rejected)} non-public or hand-written file(s)" if rejected else ""))

    rng = random.Random(args.seed)
    failures: list[dict] = []
    accepted_junk = 0
    for iteration in range(1, args.iterations + 1):
        data, name, strategy = generate(rng, seeds)
        is_known_good = any(data == s and name == n for s, n in seeds)
        try:
            with time_limit(args.timeout):
                errors = adc.validate_flowback_proposal_bytes(data, name, public_only=True)
        except Timeout:
            failures.append({"invariant": "I2-hang", "strategy": strategy, "filename": name,
                             "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
            continue
        except Exception as exc:  # noqa: BLE001 - any escape is the finding
            failures.append({"invariant": "I1-raised", "strategy": strategy, "filename": name,
                             "exception": exc.__class__.__name__,
                             "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
            continue
        if not isinstance(errors, list):
            failures.append({"invariant": "I1-type", "strategy": strategy, "filename": name,
                             "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
            continue
        if not errors and not is_known_good:
            accepted_junk += 1
            failures.append({"invariant": "I3-accepted", "strategy": strategy, "filename": name,
                             "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
            if args.save_failures:
                out = Path(args.save_failures)
                out.mkdir(parents=True, exist_ok=True)
                (out / f"accepted-{hashlib.sha256(data).hexdigest()[:12]}.bin").write_bytes(data)

    total = args.iterations
    print(f"fuzzed {total} inputs (seed {args.seed}) | failures {len(failures)} | junk accepted {accepted_junk}")
    for item in failures[:20]:
        print(f"  {item['invariant']:12s} strategy={item['strategy']:11s} size={item['size']:6d} {item.get('exception','')}")
    if args.json:
        Path(args.json).write_text(
            json.dumps({"iterations": total, "seed": args.seed, "failures": failures}, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
