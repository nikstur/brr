#!/usr/bin/env nix-shell
#!nix-shell -p python3 -p ninja -p tmux -i python3

import subprocess
import argparse
import json
import typing
import time
import io
import selectors
import sys
import graphlib
from pathlib import Path

BUILDDIR = "builddir"


def nix_expr(attr) -> str:
    return "(import ./. { })." + attr


class Job(typing.NamedTuple):
    name: str
    deps: set[str] = set()


def eval_jobs(attr: str) -> dict[str, Job]:
    print(f"Evaluating {attr}...")
    p = subprocess.Popen(
        [
            "nix-eval-jobs",
            "--impure",
            "--expr",
            nix_expr(attr),
            "--meta",
            "--quiet",
            "--workers",
            "8",
            "--show-trace",
            "--force-recurse",
        ],
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    jobs = {}

    buf = io.StringIO()

    def handle_output(stream, *_):
        line = stream.readline()
        if not line:
            return

        try:
            json_line = json.loads(line)
            drv_path = json_line["drvPath"]
            print(drv_path)
            jobs[drv_path] = Job(name=drv_path)
        except Exception:
            print("Failed to parse nix-eval-jobs line")
            print(line)

    if not p.stdout:
        raise Exception("nix-eval-jobs didn't write anything to stdout")
    selector = selectors.DefaultSelector()
    selector.register(p.stdout, selectors.EVENT_READ, handle_output)

    while p.poll() is None:
        events = selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

    returncode = p.wait()
    selector.close()
    buf.close()

    if returncode != 0:
        if not p.stderr:
            raise Exception("nix-eval-jobs didn't write anything to stderr")
        sys.stdout.write(p.stderr.read())
        raise Exception("Failed to evaluate a job")

    if len(jobs) > 0:
        print(f"Successfully evaluated {len(jobs)} derivation(s)")

    return jobs


def toposort(jobs: dict[str, Job]) -> dict[str, Job]:
    print("Toposorting builds...")

    drv_info = json.loads(
        subprocess.run(
            ["nix", "derivation", "show", "-r", *jobs.keys()],
            capture_output=True,
            check=True,
        ).stdout.decode()
    )

    deps = {}
    for drv, info in drv_info.items():
        deps[drv] = set(info["inputDrvs"].keys())
    for n in graphlib.TopologicalSorter(deps).static_order():
        for d in tuple(deps[n]):
            deps[n].update(deps[d])
    return {d: j._replace(deps=deps[d] & jobs.keys()) for d, j in jobs.items()}


class Timer:
    def __init__(self, s: str):
        self.s = s

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.time = time.perf_counter() - self.start
        print(f"{self.s} in {self.time:.2f}s")


def ninja_build_edge(idx: int, drv: str, job: Job):
    return f"""build {drv} : nixbuild {" ".join(job.deps)}
  path = {job.name}
  e = result-{idx}
  pool = default"""


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=16, required=False)
    parser.add_argument("--tmux", action="store_true")
    parser.add_argument("--toposort", action="store_true")
    parser.add_argument("--build-cores", type=int, default=0, required=False)
    parser.add_argument("--store", type=str, default="", required=False)
    parser.add_argument("--extra-args", type=str, default="", required=False)
    parser.add_argument("attr")
    args = parser.parse_args()

    with Timer("Evaluated"):
        jobs = eval_jobs(args.attr)

    if args.toposort:
        with Timer("Toposorted"):
            jobs = toposort(jobs)

    nix_build_args = [
        "nix build --no-link '${out}^*'",
        f"--cores {args.build_cores}",
    ]

    if args.store:
        nix_build_args.append(f"--eval-store auto --store {args.store}")

    if args.extra_args:
        nix_build_args.append(args.extra_args)

    nix_build_command = " ".join(nix_build_args)

    if args.tmux:
        command = f"""rm -f $e && mkfifo $e && $
            tmux split -dbl1 " $
              {nix_build_command}; $
              echo \\$$? > $e $
            " \\; select-layout tiled && $
            exit $$(cat $e; rm $e; tmux select-layout tiled)"""
    else:
        command = nix_build_command

    ninja = f"""pool default
  depth = {args.jobs}

rule nixbuild
  command = {command}
  description = build $path

build all : phony $
  {" $\n  ".join((k for k in jobs.keys()))}

{"\n\n".join((ninja_build_edge(idx, drv, job) for idx, (drv, job) in enumerate(jobs.items())))}
"""

    Path(BUILDDIR).mkdir(exist_ok=True)

    with open(f"{BUILDDIR}/build.ninja", "w") as f:
        f.write(ninja)

    with Timer("Built derivations"):
        subprocess.run(
            ["ninja", "-C", BUILDDIR, "-k0", f"-j{args.jobs}"],
        )


def main():
    with Timer("Finished"):
        run()


if __name__ == "__main__":
    main()
