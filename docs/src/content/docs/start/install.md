---
title: Install pydelity
description:
  Install pydelity on Windows, macOS or Linux and set the API key for your model
  provider.
---

pydelity needs Python 3.13 or 3.14. It runs on Windows, macOS and Linux, and
every change is checked by installing and running it on all three.

## Check your Python

pydelity works with Python 3.13 and 3.14, with two limits:

- On a Mac, Python 3.14 needs macOS 14 (Sonoma) or later. On macOS 13, use
  Python 3.13.
- Python 3.15 isn't supported yet. PyMuPDF, which pydelity uses to read PDFs,
  needs [onnxruntime](https://pypi.org/project/onnxruntime/), and onnxruntime
  has no release for Python 3.15 yet.

On Python 3.15, installing pydelity fails with an error that names
`onnxruntime`. The commands below choose Python 3.13, which works everywhere
pydelity does.

## Check your platform

pydelity reads PDFs with [PyMuPDF](https://pymupdf.readthedocs.io/) 2.1 or
later. PyMuPDF 2 ships ready-built packages for most computers, but not for:

- Macs with an Intel processor
- Windows on ARM
- 32-bit Windows
- Linux distributions that use musl, such as Alpine

On these, installing PyMuPDF needs a build from source, which usually fails. Use
a computer with a supported platform, or a Linux container based on Debian or
Ubuntu.

## Install the command

To use the `pydelity` command from any folder, install it as a tool with
[uv](https://docs.astral.sh/uv/getting-started/installation/). The
`--python 3.13` option makes uv run pydelity with Python 3.13, which uv
downloads if you don't have it.

```sh
uv tool install --python 3.13 pydelity
```

Then check that it works:

```sh
pydelity --version
```

If your shell can't find `pydelity`, run `uv tool update-shell` and open a new
terminal. To upgrade later, run `uv tool upgrade pydelity`.

[pipx](https://pipx.pypa.io/) works the same way, as long as it uses Python 3.13
or 3.14: `pipx install --python python3.13 pydelity`.

## Install it for Python code

To call pydelity from your own code or a notebook, install it into that
project's environment.

With uv:

```sh
uv add pydelity
```

uv uses the project's Python, which must be 3.13 or 3.14.

With pip, in a virtual environment on macOS or Linux:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
pip install pydelity
```

On Windows, in PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install pydelity
```

Installing pydelity also installs the `pydelity` command in that environment.

## Set your API key

pydelity sends the PDF to Anthropic or OpenAI, so you need an API key from the
provider whose model you use. It reads the key from an environment variable:

| Provider  | Environment variable | Used for                                            |
| --------- | -------------------- | --------------------------------------------------- |
| Anthropic | `ANTHROPIC_API_KEY`  | Models named `anthropic:...`, including the default |
| OpenAI    | `OPENAI_API_KEY`     | Models named `openai:...`                           |

pydelity does not read `.env` files, and it never writes your key to its output
files. Replace `[API_KEY]` below with your own key.

### For the current terminal

macOS and Linux:

```sh
export ANTHROPIC_API_KEY="[API_KEY]"
```

Windows PowerShell:

```powershell
$env:ANTHROPIC_API_KEY = "[API_KEY]"
```

Windows Command Prompt:

```bat
set ANTHROPIC_API_KEY=[API_KEY]
```

The key is gone when you close the terminal.

### For every new terminal

On macOS and Linux, add the `export` line to your shell's startup file, such as
`~/.zshrc` or `~/.bashrc`, and open a new terminal.

On Windows, run this once in PowerShell or Command Prompt, then open a new
terminal:

```bat
setx ANTHROPIC_API_KEY "[API_KEY]"
```

A key saved this way can be read by any program you run, so keep it on a
computer only you use.

### In Python

If your code loads keys some other way, such as from a secrets manager, set the
variable before calling pydelity:

```python
import os

# Assumes your code already holds the key in api_key.
os.environ["ANTHROPIC_API_KEY"] = api_key
```

You only need the key when pydelity calls a model. Measuring a PDF, estimating
the cost and reading an output folder work without one.

## License

pydelity is MIT-licensed. PyMuPDF, which it depends on, is licensed under the
[AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html) or a commercial license
from [Artifex](https://artifex.com/licensing). The AGPL has conditions for
software that you share or offer as a network service. Check that they fit your
use before you build pydelity into something you distribute.

## Next

[Run your first survey](../first-survey/).
