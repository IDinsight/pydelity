#!/usr/bin/env python3
"""Check that each .env file and its .template.env partner declare the same variables.

Run it from the repo root, as the env-template-sync hook does. Only variable names are
read and printed, never values.
"""

# Standard Library
import sys

from pathlib import Path

# Specify which file pairs to compare in each section. These are the files .envrc
# loads: .env, then the one for PROJECT_ENV.
FILE_PAIRS = [
    (".env", ".template.env"),
    (".env.local", ".template.env.local"),
    (".env.development", ".template.env.development"),
    (".env.production", ".template.env.production"),
]

# Folders that have paired .env.* / .template.env.* files, relative to the repo root
# (the hook runs from there).
SECTIONS = [
    Path("."),
]


def keys(*, path: Path) -> set[str]:
    """Return the variable names declared in a .env-style file.

    A name is the text before the first '='; blank lines and comments are ignored.

    Parameters
    ----------
    path
        The path to the .env file to read.

    Returns
    -------
    set[str]
        A set of variable names found in the file.
    """

    out = set()
    with path.open() as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            out.add(line.split("=", 1)[0].strip())
    return out


def main() -> int:
    """Compare each .env file with its .template.env partner.

    Report every variable that one file of a pair declares and the other does not.

    Returns
    -------
    int
        0 if no errors were found, 1 if there were errors.
    """

    had_errors = False

    for section in SECTIONS:
        for env_name, template_name in FILE_PAIRS:
            env_file = section / env_name
            template_file = section / template_name

            if not (env_file.is_file() and template_file.is_file()):
                print(
                    f"Skipping {section} ({env_name} <-> {template_file}) - "
                    "missing one or both files"
                )
                continue

            env_keys = keys(path=env_file)
            template_keys = keys(path=template_file)

            missing_in_template = env_keys - template_keys
            extra_in_template = template_keys - env_keys

            rel = section.as_posix() or "."

            if missing_in_template:
                had_errors = True
                print(
                    f"\n{rel} - The following variables are in .env.* but missing in "
                    f"its corresponding .template.env.*:"
                )
                for k in sorted(missing_in_template):
                    print(f"  {k}")

            if extra_in_template:
                had_errors = True
                print(
                    f"\n{rel} - The following variables are in .template.env.* but not "
                    f"in its corresponding .env.*:"
                )
                for k in sorted(extra_in_template):
                    print(f"  {k}")

    return 1 if had_errors else 0


if __name__ == "__main__":
    sys.exit(main())
