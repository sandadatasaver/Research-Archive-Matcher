import os
import datetime

class HTMLReporter:
    """
    Generates an elegant, interactive standalone HTML report for the matching results.
    Includes summary statistics, pie/donut indicators (via CSS), and searchable tables.
    """
    @staticmethod
    def generate_report(results: dict, db_stats: dict, output_path: str = "matching_report.html") -> str:
        matched_list = results.get("matched", [])
        unmatched_list = results.get("unmatched", [])
        
        matched_count = len(matched_list)
        unmatched_count = len(unmatched_list)
        total_targets = matched_count + unmatched_count
        match_rate = (matched_count / total_targets * 100) if total_targets > 0 else 0
        
        # HTML Template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Archive Matcher (RAM) - Report</title>
    <style>
        :root {{
            --primary: #1f4e79;
            --primary-light: #ebf1f5;
            --success: #2e7d32;
            --warning: #c62828;
            --text: #333333;
            --bg: #f8f9fa;
            --card-bg: #ffffff;
            --border: #e0e0e0;
        }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            color: var(--text);
            background-color: var(--bg);
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--primary) 0%, #34495e 100%);
            color: white;
            padding: 2.5rem 2rem;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        header h1 {{
            margin: 0;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        
        header p {{
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        
        .stat-card {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-top: 4px solid var(--primary);
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
        }}
        
        .stat-card.success-card {{
            border-top-color: var(--success);
        }}
        
        .stat-card.warning-card {{
            border-top-color: var(--warning);
        }}
        
        .stat-card .value {{
            font-size: 2rem;
            font-weight: 700;
            margin: 0.5rem 0;
        }}
        
        .stat-card .label {{
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #7f8c8d;
        }}
        
        /* Tabs and Navigation */
        .tabs {{
            display: flex;
            border-bottom: 2px solid var(--border);
            margin-bottom: 1.5rem;
        }}
        
        .tab-btn {{
            background: none;
            border: none;
            padding: 0.75rem 1.5rem;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            color: #7f8c8d;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            transition: all 0.2s;
        }}
        
        .tab-btn:hover {{
            color: var(--primary);
        }}
        
        .tab-btn.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        /* Search Box */
        .search-box {{
            margin-bottom: 1.5rem;
            display: flex;
            gap: 0.5rem;
        }}
        
        .search-box input {{
            flex: 1;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border);
            border-radius: 4px;
            font-size: 1rem;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        }}
        
        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        th {{
            background-color: var(--primary-light);
            color: var(--primary);
            font-weight: 600;
        }}
        
        tr:hover {{
            background-color: #fcfcfc;
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            text-align: center;
        }}
        
        .badge.success {{
            background-color: #e8f5e9;
            color: var(--success);
        }}
        
        .badge.warning {{
            background-color: #ffebee;
            color: var(--warning);
        }}
        
        .score {{
            font-weight: bold;
        }}
        
        .score-high {{ color: var(--success); }}
        .score-med {{ color: #e67e22; }}
        .score-low {{ color: var(--warning); }}
        
        footer {{
            text-align: center;
            padding: 2rem 0;
            color: #7f8c8d;
            border-top: 1px solid var(--border);
            margin-top: 3rem;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>

    <header>
        <h1>Research Archive Matcher (RAM)</h1>
        <p>Matching Summary Report — Generated {datetime.date.today().strftime("%B %d, %Y")}</p>
    </header>

    <div class="container">
        
        <!-- Summary Dashboard -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{db_stats.get("total_docs", 0)}</div>
                <div class="label">Indexed Library PDFs</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_targets}</div>
                <div class="label">Target Publications</div>
            </div>
            <div class="stat-card success-card">
                <div class="value">{matched_count}</div>
                <div class="label">Successfully Matched</div>
            </div>
            <div class="stat-card warning-card">
                <div class="value">{unmatched_count}</div>
                <div class="label">Unmatched</div>
            </div>
            <div class="stat-card success-card">
                <div class="value">{match_rate:.1f}%</div>
                <div class="label">Match Success Rate</div>
            </div>
        </div>

        <!-- Section Tabs -->
        <div class="tabs">
            <button class="tab-btn active" onclick="openTab('matched-tab')">Successful Matches ({matched_count})</button>
            <button class="tab-btn" onclick="openTab('unmatched-tab')">Unmatched Publications ({unmatched_count})</button>
        </div>

        <!-- Search Box -->
        <div class="search-box">
            <input type="text" id="searchInput" onkeyup="filterTables()" placeholder="Search tables for keywords, authors, journals...">
        </div>

        <!-- Matched Content Tab -->
        <div id="matched-tab" class="tab-content active">
            <table id="matchedTable">
                <thead>
                    <tr>
                        <th style="width: 35%;">Target Citation / Publication</th>
                        <th style="width: 35%;">Matched PDF Document</th>
                        <th>Score</th>
                        <th>Method</th>
                        <th>Doc Type</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in matched_list:
            score = item["score"]
            score_class = "score-high" if score >= 85 else ("score-med" if score >= 70 else "score-low")
            
            html += f"""
                    <tr>
                        <td>
                            <strong>{item['target_title']}</strong><br>
                            <span style="font-size: 0.85rem; color: #7f8c8d;">{item['target_raw'][:150]}</span>
                        </td>
                        <td>
                            <strong>{item['matched_title']}</strong><br>
                            <span style="font-size: 0.85rem; color: #7f8c8d;">
                                Authors: {item['matched_authors'] or 'N/A'}<br>
                                Journal: {item['matched_journal'] or 'N/A'} ({item['matched_year'] or 'N/A'})
                            </span>
                        </td>
                        <td><span class="score {score_class}">{score}%</span></td>
                        <td><span class="badge success">{item['method']}</span></td>
                        <td><span class="badge" style="background-color: #ebf1f5; color: #1f4e79;">{item['matched_type']}</span></td>
                    </tr>
            """
            
        if not matched_list:
            html += """<tr><td colspan="5" style="text-align: center;">No matches found above the confidence threshold.</td></tr>"""
            
        html += """
                </tbody>
            </table>
        </div>

        <!-- Unmatched Content Tab -->
        <div id="unmatched-tab" class="tab-content">
            <table id="unmatchedTable">
                <thead>
                    <tr>
                        <th style="width: 45%;">Unmatched Publication</th>
                        <th style="width: 45%;">Best Library Candidate</th>
                        <th>Best Score</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in unmatched_list:
            score = item["best_candidate_score"]
            score_class = "score-high" if score >= 85 else ("score-med" if score >= 70 else "score-low")
            
            html += f"""
                    <tr>
                        <td>
                            <strong>{item['target_title']}</strong><br>
                            <span style="font-size: 0.85rem; color: #7f8c8d;">{item['target_raw'][:150]}</span>
                        </td>
                        <td>
                            <strong>{item['best_candidate_title'] or 'No reasonable candidate'}</strong>
                        </td>
                        <td><span class="score {score_class}">{score}%</span></td>
                    </tr>
            """
            
        if not unmatched_list:
            html += """<tr><td colspan="3" style="text-align: center;">All publication targets matched successfully!</td></tr>"""
            
        html += f"""
                </tbody>
            </table>
        </div>

        <footer>
            Research Archive Matcher (RAM) — Offline Research Document Intelligence Platform<br>
            © {datetime.date.today().year} Sandadatasaver
        </footer>

    </div>

    <script>
        function openTab(tabId) {{
            // Hide all tab contents
            var contents = document.getElementsByClassName('tab-content');
            for (var i = 0; i < contents.length; i++) {{
                contents[i].classList.remove('active');
            }}
            // Remove active style from all tab buttons
            var buttons = document.getElementsByClassName('tab-btn');
            for (var i = 0; i < buttons.length; i++) {{
                buttons[i].classList.remove('active');
            }}
            // Show selected tab content and button style
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }}

        function filterTables() {{
            var input, filter, matchedTable, unmatchedTable, tr, td, i, txtValue;
            input = document.getElementById("searchInput");
            filter = input.value.toUpperCase();
            
            // Filter matched table
            matchedTable = document.getElementById("matchedTable");
            tr = matchedTable.getElementsByTagName("tr");
            for (i = 1; i < tr.length; i++) {{
                var showRow = false;
                td = tr[i].getElementsByTagName("td");
                for (var j = 0; j < td.length; j++) {{
                    if (td[j]) {{
                        txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                            showRow = true;
                            break;
                        }}
                    }}
                }}
                tr[i].style.display = showRow ? "" : "none";
            }}
            
            // Filter unmatched table
            unmatchedTable = document.getElementById("unmatchedTable");
            tr = unmatchedTable.getElementsByTagName("tr");
            for (i = 1; i < tr.length; i++) {{
                var showRow = false;
                td = tr[i].getElementsByTagName("td");
                for (var j = 0; j < td.length; j++) {{
                    if (td[j]) {{
                        txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                            showRow = true;
                            break;
                        }}
                    }}
                }}
                tr[i].style.display = showRow ? "" : "none";
            }}
        }}
    </script>
</body>
</html>
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path
