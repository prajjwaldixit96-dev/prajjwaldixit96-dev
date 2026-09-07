import os
import json
import urllib.request

GITHUB_TOKEN = os.environ["GH_TOKEN"]
USERNAME = os.environ["GH_USERNAME"]

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        primaryLanguage { name color }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { contributionCount date }
        }
      }
    }
  }
}
"""

def fetch_data():
    body = json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["data"]["user"]


def rank(value, thresholds):
    for min_v, label in thresholds:
        if value >= min_v:
            return label
    return thresholds[-1][1]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_stats_card(name, stars, commits, prs, issues, contributions):
    overall = rank(
        stars * 2 + commits + prs * 3 + issues,
        [(300, "S"), (150, "A"), (60, "B"), (0, "C")],
    )
    rows = [
        ("Total Stars", stars),
        ("Total Commits (last yr)", commits),
        ("Total PRs", prs),
        ("Total Issues", issues),
        ("Contributions (last yr)", contributions),
    ]
    row_svg = ""
    y = 70
    for label, value in rows:
        row_svg += f'''
  <text x="30" y="{y}" class="label">{esc(label)}</text>
  <text x="330" y="{y}" text-anchor="end" class="value">{value}</text>'''
        y += 32

    return f'''<svg width="380" height="{y + 20}" viewBox="0 0 380 {y + 20}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .card {{ fill: #1a1b27; stroke: #414868; stroke-width: 1; }}
    .title {{ font: 600 18px 'Segoe UI', sans-serif; fill: #bb9af7; }}
    .label {{ font: 400 14px 'Segoe UI', sans-serif; fill: #c0caf5; }}
    .value {{ font: 600 14px 'Segoe UI', sans-serif; fill: #7aa2f7; }}
    .rank {{ font: 700 30px 'Segoe UI', sans-serif; fill: #f7768e; }}
    .rank-ring {{ fill: none; stroke: #414868; stroke-width: 5; }}
  </style>
  <rect x="0.5" y="0.5" width="379" height="{y + 19}" rx="12" class="card"/>
  <text x="30" y="34" class="title">{esc(name or USERNAME)}'s GitHub stats</text>
  {row_svg}
  <circle cx="345" cy="34" r="24" class="rank-ring"/>
  <text x="345" y="41" text-anchor="middle" class="rank">{overall}</text>
</svg>'''


def build_languages_card(repos):
    counts = {}
    colors = {}
    for r in repos:
        lang = r.get("primaryLanguage")
        if not lang:
            continue
        counts[lang["name"]] = counts.get(lang["name"], 0) + 1
        colors[lang["name"]] = lang.get("color") or "#7aa2f7"

    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:6]
    total = sum(c for _, c in top) or 1

    bars = ""
    y = 60
    for name, count in top:
        pct = round(count / total * 100)
        bar_w = round(pct * 2.4)
        color = colors[name]
        bars += f'''
  <text x="30" y="{y}" class="label">{esc(name)}</text>
  <text x="330" y="{y}" text-anchor="end" class="value">{pct}%</text>
  <rect x="30" y="{y + 8}" width="300" height="8" rx="4" fill="#292e42"/>
  <rect x="30" y="{y + 8}" width="{bar_w}" height="8" rx="4" fill="{color}"/>'''
        y += 40

    return f'''<svg width="380" height="{y + 10}" viewBox="0 0 380 {y + 10}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .card {{ fill: #1a1b27; stroke: #414868; stroke-width: 1; }}
    .title {{ font: 600 18px 'Segoe UI', sans-serif; fill: #bb9af7; }}
    .label {{ font: 400 13px 'Segoe UI', sans-serif; fill: #c0caf5; }}
    .value {{ font: 600 13px 'Segoe UI', sans-serif; fill: #7aa2f7; }}
  </style>
  <rect x="0.5" y="0.5" width="379" height="{y + 9}" rx="12" class="card"/>
  <text x="30" y="34" class="title">Most used languages</text>
  {bars}
</svg>'''


def build_trophy_card(stars, commits, repos_count, followers):
    trophies = [
        ("Stars", stars, [(200, "SSS"), (80, "SS"), (30, "S"), (10, "A"), (1, "B"), (0, "C")]),
        ("Commits", commits, [(1000, "SSS"), (500, "SS"), (200, "S"), (80, "A"), (20, "B"), (0, "C")]),
        ("Repos", repos_count, [(50, "SSS"), (30, "SS"), (15, "S"), (8, "A"), (3, "B"), (0, "C")]),
        ("Followers", followers, [(200, "SSS"), (80, "SS"), (30, "S"), (10, "A"), (1, "B"), (0, "C")]),
    ]
    colors = {"SSS": "#f7768e", "SS": "#e0af68", "S": "#e0af68", "A": "#9ece6a", "B": "#7aa2f7", "C": "#565f89"}

    boxes = ""
    x = 20
    for label, value, thresholds in trophies:
        tier = rank(value, thresholds)
        color = colors[tier]
        boxes += f'''
  <g transform="translate({x},20)">
    <rect width="130" height="120" rx="10" fill="#1a1b27" stroke="{color}" stroke-width="2"/>
    <text x="65" y="30" text-anchor="middle" class="label">{esc(label)}</text>
    <text x="65" y="72" text-anchor="middle" class="tier" fill="{color}">{tier}</text>
    <text x="65" y="100" text-anchor="middle" class="value">{value}</text>
  </g>'''
        x += 140

    return f'''<svg width="{x + 20}" height="160" viewBox="0 0 {x + 20} 160" xmlns="http://www.w3.org/2000/svg">
  <style>
    .label {{ font: 500 13px 'Segoe UI', sans-serif; fill: #c0caf5; }}
    .value {{ font: 400 12px 'Segoe UI', sans-serif; fill: #9aa5ce; }}
    .tier {{ font: 700 34px 'Segoe UI', sans-serif; }}
  </style>
  <rect x="0.5" y="0.5" width="{x + 19}" height="159" rx="12" fill="#0f1017" stroke="#414868"/>
  {boxes}
</svg>'''


def build_activity_card(weeks):
    month_counts = {}
    order = []
    for week in weeks:
        for day in week["contributionDays"]:
            month = day["date"][:7]
            if month not in month_counts:
                month_counts[month] = 0
                order.append(month)
            month_counts[month] += day["contributionCount"]

    months = order[-12:]
    values = [month_counts[m] for m in months]
    max_val = max(values) if values and max(values) > 0 else 1

    chart_w, chart_h = 320, 130
    x0, y0 = 30, 40
    step = chart_w / max(len(months) - 1, 1)

    points = []
    for i, v in enumerate(values):
        x = x0 + i * step
        y = y0 + chart_h - (v / max_val * chart_h)
        points.append((x, y))

    path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area_d = path_d + f" L {points[-1][0]:.1f},{y0 + chart_h} L {points[0][0]:.1f},{y0 + chart_h} Z"

    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#7aa2f7"/>' for x, y in points
    )
    labels = "".join(
        f'<text x="{x0 + i * step:.1f}" y="{y0 + chart_h + 20}" text-anchor="middle" class="axis">{months[i][5:]}</text>'
        for i in range(0, len(months), max(1, len(months) // 6))
    )

    return f'''<svg width="380" height="{y0 + chart_h + 40}" viewBox="0 0 380 {y0 + chart_h + 40}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .card {{ fill: #1a1b27; stroke: #414868; stroke-width: 1; }}
    .title {{ font: 600 18px 'Segoe UI', sans-serif; fill: #bb9af7; }}
    .axis {{ font: 400 10px 'Segoe UI', sans-serif; fill: #9aa5ce; }}
  </style>
  <rect x="0.5" y="0.5" width="379" height="{y0 + chart_h + 39}" rx="12" class="card"/>
  <text x="30" y="26" class="title">Contribution activity (last 12 months)</text>
  <path d="{area_d}" fill="#7aa2f7" opacity="0.15"/>
  <path d="{path_d}" fill="none" stroke="#7aa2f7" stroke-width="2"/>
  {dots}
  {labels}
</svg>'''


def main():
    user = fetch_data()
    cc = user["contributionsCollection"]
    repos = user["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)
    commits = cc["totalCommitContributions"]
    prs = cc["totalPullRequestContributions"]
    issues = cc["totalIssueContributions"]
    contributions = cc["contributionCalendar"]["totalContributions"]
    followers = user["followers"]["totalCount"]
    repos_count = user["repositories"]["totalCount"]

    os.makedirs("assets", exist_ok=True)

    with open("assets/stats-card.svg", "w", encoding="utf-8") as f:
        f.write(build_stats_card(user.get("name"), stars, commits, prs, issues, contributions))

    with open("assets/languages-card.svg", "w", encoding="utf-8") as f:
        f.write(build_languages_card(repos))

    with open("assets/trophy-card.svg", "w", encoding="utf-8") as f:
        f.write(build_trophy_card(stars, commits, repos_count, followers))

    with open("assets/activity-graph.svg", "w", encoding="utf-8") as f:
        f.write(build_activity_card(cc["contributionCalendar"]["weeks"]))

    print("Generated stats-card.svg, languages-card.svg, trophy-card.svg, activity-graph.svg")


if __name__ == "__main__":
    main()
