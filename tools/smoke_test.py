from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

from core.character import load_character
from core.clipboard_service import classify_text
from core.skeletal_animator import SkeletalAnimator

for style in ("anime", "pixel"):
    c = load_character("luoxi", art_style=style)
    a = SkeletalAnimator(c)
    assert c.parts_dir.is_dir(), c.parts_dir
    a.play("idle")
    a.play_chain("greet_flow")
    a._emit_frame()
    pix = a.skeleton.render(0.1, 0.0, 0.4)
    out = Path(f"characters/luoxi/variants/{style}/preview.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(ROOT / out))
    n = len(list(c.parts_dir.glob("*.png")))
    print(style, "parts", n, "size", pix.width(), pix.height(), "actions", len(a.list_actions()))

assert classify_text("https://x.com") == "url"
print("ALL_OK")
