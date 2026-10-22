"""Small real PSD fixtures are generated outside the repository, never mocked."""

from pathlib import Path

import pytest
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import Group, PixelLayer


@pytest.fixture
def synthetic_psd(tmp_path: Path) -> Path:
    psd = PSDImage.new("RGBA", (12, 10))
    bottom = Image.new("RGBA", (8, 7))
    bottom.paste((255, 0, 0, 255), (1, 2, 7, 6))
    PixelLayer.frompil(bottom, psd, name="same", left=-2, top=1)
    PixelLayer.frompil(Image.new("RGBA", (2, 2)), psd, name="empty")
    group = Group.new(psd, "group/한글")
    # PSD legacy Pascal name is MacRoman; the Unicode tagged name stays intact.
    group._record.name = "group"
    nested = Group.new(group, "nested")
    top = PixelLayer.frompil(
        Image.new("RGBA", (3, 3), (0, 0, 255, 128)),
        nested,
        name="same",
        left=2,
        top=4,
    )
    top.opacity = 128
    hidden = PixelLayer.frompil(
        Image.new("RGBA", (2, 2), "green"),
        psd,
        name="",
        left=8,
        top=2,
    )
    hidden.visible = False
    path = tmp_path / "synthetic.psd"
    psd.save(path)
    return path
