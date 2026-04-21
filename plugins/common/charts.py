import base64
import math
from typing import Dict

_STATUS_COLORS = {
    'APPROVED': '#5cb85c',
    'APPROVED_WITH_SUGGESTIONS': '#5cb85c',
    'NEEDS_WORK': '#f0ad4e',
    'WAITING_FOR_AUTHOR': '#f0ad4e',
    'NO_VOTE': '#999999',
    'UNAPPROVED': '#999999',
    'REJECTED': '#d9534f',
}


def status_pie_chart_base64(status_counts: Dict, size: int = 20) -> str:
    color_totals: Dict[str, int] = {}
    for status, count in status_counts.items():
        color = _STATUS_COLORS.get(status.name if hasattr(status, 'name') else status, '#999999')
        color_totals[color] = color_totals.get(color, 0) + count

    total = sum(color_totals.values())
    if total == 0:
        return None

    cx = cy = size / 2
    r = size / 2 - 0.5

    pairs = [(c, n) for c, n in color_totals.items() if n > 0]

    if len(pairs) == 1:
        segments = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{pairs[0][0]}"/>']
    else:
        segments = []
        start = -math.pi / 2
        for color, count in pairs:
            angle = 2 * math.pi * count / total
            end = start + angle
            x1 = cx + r * math.cos(start)
            y1 = cy + r * math.sin(start)
            x2 = cx + r * math.cos(end)
            y2 = cy + r * math.sin(end)
            large_arc = 1 if angle > math.pi else 0
            d = f'M {cx} {cy} L {x1:.3f} {y1:.3f} A {r} {r} 0 {large_arc} 1 {x2:.3f} {y2:.3f} Z'
            segments.append(f'<path d="{d}" fill="{color}"/>')
            start = end

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
        f'{"".join(segments)}'
        f'</svg>'
    )
    return base64.b64encode(svg.encode()).decode()
