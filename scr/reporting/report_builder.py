import argparse
import sys
import os
import re
import html
from datetime import date, timedelta
from pathlib import Path

def get_week_dates(year, week):
    """
    Calculate the start (Monday) and end (Saturday) dates for a given ISO year and week.
    Returns strings formatted like '01. December 2025'.
    
    Using start=Monday and end=Sunday per ISO standard, 
    but based on template example '01' to '06', it might be Mon-Sat.
    We will output Mon and Sun to be safe/standard, or Mon and Sat?
    Template had 01 (Mon) to 06 (Sat) for W50 2025?
    Dec 1 2025 is Monday. Dec 6 is Saturday.
    So the template implies a 6-day coverage.
    I will use Monday to Sunday to be complete, or stick to the template's likely Mon-Sat convention?
    I'll output Monday and Sunday.
    """
    # ISO week calculation
    # Monday of the week
    monday = date.fromisocalendar(year, week, 1)
    # Sunday of the week
    sunday = date.fromisocalendar(year, week, 7)
    
    # Format: "dd. Month YYYY"
    # Python strftime %B is full month name.
    fmt = "%d. %B %Y"
    return monday.strftime(fmt), sunday.strftime(fmt)

def resolve_path(base_dir, rel_path):
    return (base_dir / rel_path).resolve()

def embed_figures(content, template_dir):
    """
    Finds iframes with data-src, reads the target file, 
    and replaces data-src with data-html containing the escaped HTML content.
    We use data-html (lazy load) instead of srcdoc (eager load) to ensure
    Plotly charts render correctly only when the iframe becomes visible.
    """
    base_path = template_dir

    def replace_iframe(match):
        full_tag = match.group(0)
        src_match = re.search(r'data-src="([^"]+)"', full_tag)
        
        if not src_match:
            return full_tag
            
        rel_path = src_match.group(1)
        abs_path = resolve_path(base_path, rel_path)
        
        if not abs_path.exists():
            print(f"Warning: Plot file not found: {abs_path}")
            return full_tag
            
        print(f"Embedding: {abs_path.name}")
        try:
            file_content = abs_path.read_text(encoding='utf-8')
            
            # Injection: Force html, body to 100% height/width
            # This fixes the issue where Plotly charts with height:100% collapse in srcdoc
            # because the body doesn't have an explicit height.
            style_injection = '<style>html, body { width: 100%; height: 100%; margin: 0; padding: 0; }</style>'
            
            # Insert style before </head> if it exists, otherwise prepend to content
            if '</head>' in file_content:
                file_content = file_content.replace('</head>', f'{style_injection}</head>')
            else:
                file_content = style_injection + file_content

            # Escape for HTML attribute
            escaped_content = html.escape(file_content)
            
            # Use lambda to prevent re.sub from processing backslashes in the content
            # We replace data-src with data-html. 
            new_tag = re.sub(r'data-src="[^"]+"', lambda _: f'data-html="{escaped_content}"', full_tag)
            
            # Remove src attribute if it exists
            new_tag = re.sub(r'\s+src="[^"]+"', '', new_tag)
            
            return new_tag
        except Exception as e:
            print(f"Error reading {abs_path}: {e}")
            return full_tag

    return re.sub(r'<iframe[^>]+>', replace_iframe, content)

def update_script(content):
    """
    Replaces the script section to handle lazy loading of data-html content.
    """
    new_script = """
    <script>
        function loadIframe(iframe) {
            if (!iframe) return;
            // If already loaded, skipping
            if (iframe.getAttribute('src') || iframe.getAttribute('srcdoc')) return;

            // Priority to data-html (embedded) - lazy load into srcdoc
            if (iframe.getAttribute('data-html')) {
                iframe.srcdoc = iframe.getAttribute('data-html');
            } else if (iframe.getAttribute('data-src')) {
                iframe.src = iframe.dataset.src;
            }
        }

        function openMainTab(tabId) {
            // Hide all main tabs
            var tabs = document.getElementsByClassName("tab-content");
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove("active");
            }

            // Deactivate all main buttons
            var btns = document.getElementsByClassName("main-tab-btn");
            for (var i = 0; i < btns.length; i++) {
                btns[i].classList.remove("active");
            }

            // Show target tab
            var target = document.getElementById(tabId);
            target.classList.add("active");

            // Activate button
            if (event && event.currentTarget) {
                event.currentTarget.classList.add("active");
            }

            // --- SAFELY LOAD ACTIVE IFRAME ---
            var activeFrame = target.querySelector("iframe.active");
            if (activeFrame) {
                setTimeout(() => {
                    loadIframe(activeFrame);
                }, 50);
            }
        }

        function openSubTab(parentId, frameId) {
            // Parent context
            var parent = document.getElementById(parentId);

            // Deactivate sub-buttons
            var btns = parent.querySelectorAll(".sub-tab-btn");
            for (var i = 0; i < btns.length; i++) {
                btns[i].classList.remove("active");
            }

            // Hide all iframes
            var frames = parent.getElementsByTagName("iframe");
            for (var i = 0; i < frames.length; i++) {
                frames[i].classList.remove("active");
            }

            // Activate clicked button
            event.currentTarget.classList.add("active");

            // Show target iframe and load content
            var targetFrame = document.getElementById(frameId);
            targetFrame.classList.add("active");
            
            loadIframe(targetFrame);
        }

        // Init state
        document.addEventListener("DOMContentLoaded", function () {
            // Auto-load initial active iframes
            var activeFrames = document.querySelectorAll("iframe.active");
            activeFrames.forEach(function (f) {
                loadIframe(f);
            });
        });
    </script>
    """
    
    # Robust replacement of the script block
    # We assume there is one main script block at the end.
    # Matches <script>... content ...</script>
    # DOTALL needs to be simulated or passed.
    
    pattern = r'<script>.*?</script>'
    # re.DOTALL makes . match newlines
    
    # Check if we find it
    if re.search(pattern, content, re.DOTALL):
        return re.sub(pattern, new_script, content, flags=re.DOTALL)
    else:
        print("Warning: Could not find script block to replace.")
        return content

def main():
    parser = argparse.ArgumentParser(description="Generate SHM Weekly Report")
    parser.add_argument("--year", type=int, required=True, help="Year of the report (e.g., 2025)")
    parser.add_argument("--week", type=int, required=True, help="ISO Week number (e.g., 50)")
    parser.add_argument("--header", type=str, default="STEEL ARENA MONITORING", help="Header text for the report")
    
    args = parser.parse_args()
    
    # Setup paths
    # Assuming script is in scr/reporting/
    script_dir = Path(__file__).resolve().parent
    template_path = script_dir / "report_v2.html"
    project_root = script_dir.parent.parent # scr/reporting -> scr -> root
    reports_dir = project_root / "reports"
    
    if not reports_dir.exists():
        reports_dir.mkdir(parents=True)
        
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
        
    print(f"Reading template from {template_path}")
    content = template_path.read_text(encoding='utf-8')
    
    # 1. Calculate Dates
    start_date, end_date = get_week_dates(args.year, args.week)
    
    # 2. Text Replacements
    content = content.replace("{YEAR}", str(args.year))
    content = content.replace("{ISOWEEK}", str(args.week))
    content = content.replace("{2025}", str(args.year))
    content = content.replace("{50}", str(args.week))
    
    date_pattern = r'\{\d{1,2}\.\s+\w+\s+\d{4}\}'
    dates_found = re.findall(date_pattern, content)
    
    if len(dates_found) >= 1:
        content = content.replace(dates_found[0], start_date, 1)
    
    dates_remaining = re.findall(date_pattern, content)
    if dates_remaining:
        content = content.replace(dates_remaining[0], end_date, 1)
        
    content = content.replace("STEEL ARENA MONITORING", args.header)
    
    # 3. Embed Figures (Lazy Load)
    print("Embedding figures...")
    content = embed_figures(content, script_dir)
    
    # 4. Update Javascript for Lazy Loading
    print("Updating script logic...")
    content = update_script(content)
    
    # 5. Save Report
    filename = f"{args.year}W{args.week}_PRJ16_report.html"
    output_path = reports_dir / filename
    
    print(f"Saving report to {output_path}")
    output_path.write_text(content, encoding='utf-8')
    print("Done.")

if __name__ == "__main__":
    main()
