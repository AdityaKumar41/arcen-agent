from pathlib import Path

from setuptools import setup


def _data_tree(root: str) -> list[tuple[str, list[str]]]:
    base = Path(root)
    if not base.exists():
        return []
    return [
        (str(path.parent), [str(path)])
        for path in sorted(base.rglob("*"))
        if path.is_file()
    ]


# These are bare data directories rather than import packages. They need to be
# present in wheels as data_files so arcen_constants._get_packaged_data_dir()
# can find them after pip/pipx installation.
setup(
    data_files=[
        *_data_tree("locales"),
        *_data_tree("skills"),
        *_data_tree("optional-skills"),
        *_data_tree("public"),
    ],
)
