import argparse
import sys
import re
import html
from datetime import date
from pathlib import Path
from string import Template



IFRAME_HEIGHT = 750


# --------------------------------------------------
# ISO week → dates (Mon–Sat)
# --------------------------------------------------
def get_week_dates(year, week):
    monday = date.fromisocalendar(year, week, 1)
    sunday = date.fromisocalendar(year, week, 7)
    fmt = "%d. %B %Y"
    return monday.strftime(fmt), sunday.strftime(fmt)


# --------------------------------------------------
# Embed figures via srcdoc (with resize bridge)
# --------------------------------------------------
def embed_figures(content: str, base_dir: Path) -> str:

    def replace_iframe(match):
        tag = match.group(0)
        m = re.search(r'data-src="([^"]+)"', tag)
        if not m:
            return tag

        rel_path = m.group(1)
        abs_path = (base_dir / rel_path).resolve()

        if not abs_path.exists():
            print(f"⚠️ Missing plot: {abs_path}")

            fallback_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    margin: 0;
                    font-family: monospace;
                    background: #f5f6f7;
                    color: #531a46;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                }}
                .box {{
                    border: 2px dashed #9f1e34;
                    padding: 30px;
                    text-align: center;
                    background: #fff;
                }}
                .box h3 {{
                    margin: 0 0 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="box">
                <h3>⚠ Chart unavailable</h3>
                <div>{abs_path.name}</div>
                <div>Not generated for this period</div>
            </div>
        </body>
        </html>
        """

            escaped = html.escape(fallback_html)

            tag = re.sub(
                r'data-src="[^"]+"',
                lambda _: f'data-html="{escaped}"',
                tag
            )
            tag = re.sub(r'\s+src="[^"]+"', "", tag)

            return tag


        print(f"📦 Embedding {abs_path.name}")
        plot_html = abs_path.read_text(encoding="utf-8")

        # --- Inject resize listener INTO embedded document ---
        resize_bridge = f"""
<script>
window.addEventListener("message", function(e) {{
    if (!e.data || !e.data.iframeHeight) return;

    const h = e.data.iframeHeight;

    document.documentElement.style.height = h + "px";
    document.body.style.height = h + "px";

    if (window.Plotly) {{
        const gd = document.querySelector(".plotly-graph-div");
        if (gd) {{
            Plotly.relayout(gd, {{ height: h }});
        }}
    }}
}});
</script>
"""

        if "</body>" in plot_html:
            plot_html = plot_html.replace("</body>", resize_bridge + "\n</body>")
        else:
            plot_html += resize_bridge

        escaped = html.escape(plot_html)

        tag = re.sub(
            r'data-src="[^"]+"',
            lambda _: f'data-html="{escaped}"',
            tag
        )

        tag = re.sub(r'\s+src="[^"]+"', "", tag)

        return tag

    return re.sub(r"<iframe[^>]+>", replace_iframe, content)


# --------------------------------------------------
# Replace JS logic
# --------------------------------------------------
def update_script(content: str) -> str:
    tpl = Template("""
<script>
    const IFRAME_HEIGHT = $IFRAME_HEIGHT;

    function sendResize(frame) {
        if (!frame || !frame.contentWindow) return;
        frame.contentWindow.postMessage(
            { iframeHeight: Math.floor(IFRAME_HEIGHT * 0.95) },
            "*"
        );
    }

    function loadIframe(iframe) {
        if (!iframe) return;

        // already loaded
        if (iframe.srcdoc) return;

        const html = iframe.getAttribute("data-html");
        if (!html) return;

        iframe.srcdoc = html;

        iframe.onload = function () {
            sendResize(iframe);
        };
    }

    function openMainTab(tabId) {
        document.querySelectorAll(".tab-content").forEach(t => {
            t.classList.remove("active");
        });

        document.querySelectorAll(".main-tab-btn").forEach(b => {
            b.classList.remove("active");
        });

        const tab = document.getElementById(tabId);
        tab.classList.add("active");

        if (event && event.currentTarget) {
            event.currentTarget.classList.add("active");
        }

        const frame = tab.querySelector("iframe.active");
        if (frame) {
            setTimeout(() => {
                loadIframe(frame);
                sendResize(frame);
            }, 100);
        }
    }

    function openSubTab(parentId, frameId) {
        const parent = document.getElementById(parentId);

        parent.querySelectorAll(".sub-tab-btn").forEach(b =>
            b.classList.remove("active")
        );

        parent.querySelectorAll("iframe").forEach(f =>
            f.classList.remove("active")
        );

        event.currentTarget.classList.add("active");

        const frame = document.getElementById(frameId);
        frame.classList.add("active");

        setTimeout(() => {
            loadIframe(frame);
            sendResize(frame);
        }, 100);
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("iframe.active").forEach(frame => {
            setTimeout(() => {
                loadIframe(frame);
                sendResize(frame);
            }, 100);
        });
    });
</script>
""")

    script = tpl.substitute(IFRAME_HEIGHT=IFRAME_HEIGHT)

    return re.sub(
        r"<script>.*?</script>",
        script,
        content,
        flags=re.DOTALL
    )





# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--header", default="STEEL ARENA MONITORING")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    template = script_dir / "report_v2.html"
    out_dir = script_dir.parent.parent / "reports"
    out_dir.mkdir(exist_ok=True)

    content = template.read_text(encoding="utf-8")

    start, end = get_week_dates(args.year, args.week)

    content = content.replace("{YEAR}", str(args.year))
    content = content.replace("{ISOWEEK}", str(args.week))
    content = content.replace("{2025}", str(args.year))
    content = content.replace("{50}", str(args.week))

    dates = re.findall(r"\{\d{1,2}\.\s+\w+\s+\d{4}\}", content)
    if dates:
        content = content.replace(dates[0], start, 1)
    if len(dates) > 1:
        content = content.replace(dates[1], end, 1)

    content = content.replace("STEEL ARENA MONITORING", args.header)

    print("📦 Embedding figures...")
    content = embed_figures(content, script_dir)

    print("🔁 Updating JS...")
    content = update_script(content)

    out = out_dir / f"{args.year}W{args.week:02d}_PRJ16_report.html"
    out.write_text(content, encoding="utf-8")

    print(f"✅ Done: {out}")


if __name__ == "__main__":
    main()
