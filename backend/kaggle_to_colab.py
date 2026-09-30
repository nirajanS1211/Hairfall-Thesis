"""Generate the Google Colab versions of the Kaggle step files.

    cd backend && .venv/bin/python kaggle_to_colab.py

Reads backend/kaggle/Step_*_kaggle.py and writes backend/colab/Step_*_colab.py. Only the environment-specific
parts change (paths, secrets, data location, GPU message, download); the step code itself is identical.
Re-run this after editing a Kaggle file so both stay in sync.
"""
import py_compile
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC, DST = HERE / "kaggle", HERE / "colab"

SECRETS = '''try:
    from google.colab import userdata   # Colab: left sidebar > key icon > add HF_TOKEN and TABPFN_TOKEN, "Notebook access" on
    for _k in ("HF_TOKEN", "TABPFN_TOKEN"):
        try:
            os.environ[_k] = userdata.get(_k)
        except Exception:
            pass
except ImportError:
    pass
'''

COPY_STEPS = '''import zipfile
for z in glob.glob("/content/Step_*.zip"):   # zips downloaded from earlier steps: upload them to the Colab Files panel
    with zipfile.ZipFile(z) as zf:
        zf.extractall(PROJECT)
for d in glob.glob("/content/**/Step_*", recursive=True):   # or upload the unzipped Step_* folders
    if os.path.isdir(d) and not (PROJECT / os.path.basename(d)).exists() and os.path.basename(d) != STEP:
        shutil.copytree(d, PROJECT / os.path.basename(d))
'''

LOAD_DF = '''def _load_df(table):
    for p in ("/content/data.csv", "/content/drive/MyDrive/data.csv", *glob.glob("/content/*/data.csv")):
        if os.path.exists(p) and "sample_data" not in p:
            return pd.read_csv(p)
    raise AssertionError("data.csv not found - upload it to the Colab Files panel (left sidebar > folder icon > upload) so it is /content/data.csv")
'''

DOWNLOAD = '''from google.colab import files
files.download(ZIP)
'''


def convert(text: str, name: str) -> str:
    t = text
    t = re.sub(r"try:\n    from kaggle_secrets import UserSecretsClient\n.*?except Exception:\n    pass\n", SECRETS, t, flags=re.S)
    t = t.replace('Path("/kaggle/working/thesis_project")', 'Path("/content/thesis_project")')
    t = re.sub(r"for d in glob\.glob\(\"/kaggle/input/\*\*/Step_\*\", recursive=True\):\n.*?shutil\.copytree\(d, PROJECT / os\.path\.basename\(d\)\)\n",
               COPY_STEPS, t, flags=re.S)
    t = re.sub(r"def _load_df\(table\):\n.*?return pd\.read_csv\(hits\[0\]\)\n", LOAD_DF, t, flags=re.S)
    t = t.replace('"/kaggle/working/lab.py"', '"/content/lab.py"')
    t = t.replace('f"/kaggle/working/{STEP}"', 'f"/content/{STEP}"').replace('f"/kaggle/working/{STEP}.zip"', 'f"/content/{STEP}.zip"')
    t = t.replace("No GPU - Notebook settings > Accelerator > GPU", "No GPU - Runtime > Change runtime type > T4 GPU")
    t = t.replace("Kaggle", "Colab")   # in comments / messages; import_kaggle_run.py is the same importer for both
    # replace the Kaggle base64 download link with Colab's own download
    t = re.sub(r"b64 = base64\.b64encode.*\Z", DOWNLOAD, t, flags=re.S)
    t = t.replace("from IPython.display import HTML, FileLink, display\nimport html", "from IPython.display import HTML, display\nimport html")
    t = t.replace("import base64, glob,", "import glob,")
    left = [m for m in ("/kaggle", "kaggle_secrets", "UserSecretsClient", "/colab/") if m in t]
    if left:
        raise SystemExit(f"{name}: unconverted {left}")
    return t


def main():
    DST.mkdir(exist_ok=True)
    files = sorted(SRC.glob("Step_*_kaggle.py"))
    for f in files:
        out = DST / f.name.replace("_kaggle.py", "_colab.py")
        out.write_text(convert(f.read_text(), f.name))
        py_compile.compile(str(out), doraise=True)
    print(f"wrote {len(files)} files to {DST}")


if __name__ == "__main__":
    main()
