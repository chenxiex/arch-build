#!/usr/bin/env python3
"""Prepare an isolated nvchecker run and publish its records after builds succeed."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tomllib

EMPTY_RECORD = '{"version": 2, "data": {}}\n'


def run(*args):
    return subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE).stdout


def prepare(repository: Path, snapshot: Path):
    snapshot.mkdir(parents=True, exist_ok=False)
    for directory in ("nvchecker", "packages"):
        source = repository / directory
        if source.exists():
            shutil.copytree(source, snapshot / directory)

    configs = [Path("nvchecker/nvchecker.toml")]
    configs.extend(sorted(p.relative_to(repository) for p in (repository / "packages").glob("*/nvchecker.toml")))
    records = []
    aur_updates = []
    nonaur_updates = []
    for relative_config in configs:
        config = snapshot / relative_config
        with config.open("rb") as stream:
            settings = tomllib.load(stream).get("__config__", {})
        config_records = []
        for key in ("oldver", "newver"):
            value = settings.get(key)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{relative_config}: explicit {key} is required")
            expanded = Path(os.path.expandvars(os.path.expanduser(value)))
            path = (config.parent / expanded).resolve()
            if expanded.is_absolute() or not path.is_relative_to(snapshot.resolve()):
                raise ValueError(f"{relative_config}: {key} must stay inside the snapshot")
            relative_path = path.relative_to(snapshot.resolve())
            if relative_path in records or relative_path in config_records:
                raise ValueError(f"{relative_config}: version record is shared or duplicated: {relative_path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(EMPTY_RECORD)
            config_records.append(relative_path)
        records.extend(config_records)
        run("nvchecker", "--failures", "-c", str(config))
        updates = json.loads(run("nvcmp", "-c", str(config), "-q", "-j"))
        if relative_config == configs[0]:
            aur_updates = updates
        elif updates:
            package_dir = relative_config.parent
            if not (repository / package_dir / "PKGBUILD").is_file():
                raise ValueError(f"Missing PKGBUILD: {package_dir}")
            nonaur_updates.append({"name": package_dir.name, "path": str(package_dir)})

    (snapshot / "manifest.json").write_text(json.dumps({
        "configs": [str(p) for p in configs],
        "records": [str(p) for p in records],
    }))
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        output.write(f"aur_updates={json.dumps(aur_updates, separators=(',', ':'))}\n")
        output.write(f"nonaur_updates={json.dumps(nonaur_updates, separators=(',', ':'))}\n")


def apply(repository: Path, snapshot: Path, base: str):
    manifest = json.loads((snapshot / "manifest.json").read_text())
    paths = ["nvchecker", "packages", *manifest["records"]]
    # A concurrent version update must never be silently overwritten.
    subprocess.run(["git", "diff", "--exit-code", base, "HEAD", "--", *paths], cwd=repository, check=True)
    for config in manifest["configs"]:
        run("nvtake", "-c", str(snapshot / config), "--all")
    for record in manifest["records"]:
        destination = repository / record
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(snapshot / record, destination)
    subprocess.run(["git", "add", "--", *manifest["records"]], cwd=repository, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "apply"))
    parser.add_argument("repository", type=Path)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--base")
    args = parser.parse_args()
    repository = args.repository.resolve()
    snapshot = args.snapshot.resolve()
    if args.action == "prepare":
        prepare(repository, snapshot)
    else:
        if not args.base:
            parser.error("apply requires --base")
        apply(repository, snapshot, args.base)


if __name__ == "__main__":
    main()
