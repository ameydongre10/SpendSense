"""SpendSense — Frontend Single Source of Truth Synchronization Script

Copies the canonical frontend assets (frontend/index.html, frontend/css, frontend/js)
to docs/ (for GitHub Pages free hosting) and public/ (for Vercel serverless deployment),
ensuring zero code drift across deployment targets.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
DOCS_DIR = ROOT / "docs"
PUBLIC_DIR = ROOT / "public"


def sync_assets():
    print(f"[*] Synchronizing canonical frontend assets from {FRONTEND_DIR}...")

    for target in [DOCS_DIR, PUBLIC_DIR]:
        target.mkdir(parents=True, exist_ok=True)

        # 1. Copy index.html
        src_html = FRONTEND_DIR / "index.html"
        dst_html = target / "index.html"
        shutil.copy2(src_html, dst_html)
        print(f"  -> Copied index.html to {target.name}/")

        # 2. Copy css/
        src_css = FRONTEND_DIR / "css"
        dst_css = target / "css"
        if dst_css.exists():
            shutil.rmtree(dst_css)
        shutil.copytree(src_css, dst_css)
        print(f"  -> Synchronized css/ to {target.name}/css/")

        # 3. Copy js/
        src_js = FRONTEND_DIR / "js"
        dst_js = target / "js"
        if dst_js.exists():
            shutil.rmtree(dst_js)
        shutil.copytree(src_js, dst_js)
        print(f"  -> Synchronized js/ to {target.name}/js/")

        # 4. Copy deliverables/ (Executive PPTX presentation)
        src_deliv = FRONTEND_DIR / "deliverables"
        dst_deliv = target / "deliverables"
        if src_deliv.exists():
            if dst_deliv.exists():
                shutil.rmtree(dst_deliv)
            shutil.copytree(src_deliv, dst_deliv)
            print(f"  -> Synchronized deliverables/ to {target.name}/deliverables/")

    print(
        "[+] Synchronization complete! Zero drift across frontend/, docs/, and public/."
    )


if __name__ == "__main__":
    sync_assets()
