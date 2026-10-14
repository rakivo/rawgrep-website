# gen_tables.py
# Reads index.template.html, replaces @@WALL@@ and @@MEM@@ with the rendered
# benchmark table rows, writes index.html. Run again whenever the numbers change.
#
# Flat arrays only. Row layout in ROWS:
#   group, scen, wallRawgrep, wallFff, wallRipgrep, memRawgrep, memRipgrep

import math

TREE = ["Chromium (~500k files)", "Linux (~100k files)"]
PATTERN = [
    "TODO",
    r"(?i)\bTODO\((?:crbug\.com/\d+|[a-zA-Z][\w.-]*)\)",
    "[A-Z]+_SUSPEND",
]

# The four modes, in row order. OSC = OS cache state, TC = tool cache state.
OSC = ["warm", "warm", "cold", "cold"]
TC  = ["on",   "off",  "off",  "on"]

# A group is a tree and a pattern. Rows are listed group by group.
GROUP_TREE = [0, 0, 1, 1]
GROUP_PAT  = [0, 1, 0, 2]

ROWS = [
    [0, 0,    67.4,   173.1,   345.9,   64.6,  85.4],
    [0, 1,   218.3,   301.5,   346.3,   67.1,  85.4],
    [0, 2,  8558.4, 10004.1, 11890.0,   60.6,  79.3],
    [0, 3,  1545.7,  1590.2, 11950.1,   58.4,  79.3],
    [1, 0,    57.2,   137.7,   356.2,   63.9,  81.1],
    [1, 1,   221.5,   333.9,   357.3,   70.9,  81.1],
    [1, 2,  8564.3, 10087.2, 11887.8,   66.2,  74.2],
    [1, 3,  1213.8,   553.0, 11903.3,   60.2,  74.2],
    [2, 0,    20.2,    70.9,   109.0,   33.6,  11.5],
    [2, 1,   107.9,   111.2,   109.3,   30.8,  11.5],
    [2, 2,  3092.7,  3296.9,  3720.7,   29.7,  11.8],
    [2, 3,   332.7,   318.2,  3814.5,   33.7,  11.8],
    [3, 0,    28.2,    69.1,   109.5,   37.8,  11.9],
    [3, 1,   118.8,   111.5,   109.9,   33.8,  11.9],
    [3, 2,  3138.5,  3328.3,  3702.5,   33.7,  11.9],
    [3, 3,   355.6,   275.3,  3742.1,   37.9,  11.9],
]

# Win color: shade positions come from ranking the leads (the "rank" mode of
# the old script). A lead is runner-up / winner in a row.
WIN_LO = [229, 237, 223]  # palest green
WIN_HI = [53, 89, 61]     # deepest green
WHITE_BIAS = 2.2          # above 1 switches to white text sooner


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def js_round(x):
    return int(math.floor(x + 0.5))


def lin(c):
    c = c / 255.0
    if c <= 0.03928:
        return c / 12.92
    return math.pow((c + 0.055) / 1.055, 2.4)


# leads: one per row. Returns a position in [0, 1] per row, 0 = palest.
def shades(leads):
    n = len(leads)
    lg = [math.log(x) for x in leads]
    sorted_lg = sorted(lg)
    t = []
    for i in range(n):
        if n > 1:
            v = sorted_lg.index(lg[i]) / float(n - 1)
        else:
            v = 1.0
        t.append(max(0.0, min(1.0, v)))
    return t


def win_style(t):
    rgb = [js_round(WIN_LO[i] + (WIN_HI[i] - WIN_LO[i]) * t) for i in range(3)]
    lum = 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2])
    on_white = 1.05 / (lum + 0.05)
    on_dark = (lum + 0.05) / (0.0087 + 0.05)
    if on_white * WHITE_BIAS > on_dark:
        fg = "#fff"
    else:
        fg = "#101a13"
    return "background:rgb(%d,%d,%d);color:%s" % (rgb[0], rgb[1], rgb[2], fg)


# first = index of first value column in a row, n = number of value columns.
def render(first, n, heads):
    count = len(ROWS)
    best = [0.0] * count
    lead = [0.0] * count
    for r in range(count):
        b = float("inf")
        s = float("inf")
        for c in range(n):
            x = ROWS[r][first + c]
            if x < b:
                s = b
                b = x
            elif x < s:
                s = x
        best[r] = b
        lead[r] = s / b
    shade = shades(lead)

    out = []
    out.append('<tr><th class="lab">OS cache</th><th class="lab">Tool cache</th>'
               + "".join("<th>%s</th>" % h for h in heads) + "</tr>")

    last = -1
    for r in range(count):
        row = ROWS[r]
        g = row[0]
        if g != last:
            out.append('<tr class="grp"><td colspan="%d">%s, pattern: <span class="pat">%s</span></td></tr>'
                       % (n + 2, TREE[GROUP_TREE[g]], esc(PATTERN[GROUP_PAT[g]])))
            last = g

        cells = '<td class="lab">%s</td><td class="lab">%s</td>' % (OSC[row[1]], TC[row[1]])
        for c in range(n):
            v = row[first + c]
            if v == best[r]:
                cells += '<td class="best" style="%s" title="%.2fx ahead of runner-up">%.1f</td>' % (
                    win_style(shade[r]), lead[r], v)
            else:
                cells += "<td>%.1f</td>" % v
        out.append('<tr class="s%d">%s</tr>' % (row[1], cells))

    return "\n" + "\n".join(out) + "\n"


def main():
    with open("index.template.html", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("@@WALL@@", render(2, 3, ["rawgrep", "fff", "ripgrep"]))
    html = html.replace("@@MEM@@", render(5, 2, ["rawgrep", "ripgrep"]))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)


main()
