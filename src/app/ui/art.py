"""Vlastní kresby pro úvod (siluety) – SVG jako bajty pro ft.Image."""
from __future__ import annotations

PARTY = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 170" preserveAspectRatio="xMidYMax slice">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b1a10"/>
<stop offset=".55" stop-color="#b4512a"/><stop offset="1" stop-color="#f0a24c"/></linearGradient></defs>
<rect width="300" height="170" fill="url(#sky)"/>
<circle cx="150" cy="128" r="46" fill="#ffd27a" opacity=".55"/>
<path d="M0 150 Q60 128 120 146 T240 140 T300 146 V170 H0Z" fill="#2a120a"/>
<g fill="#0b0705">
<circle cx="70" cy="86" r="9"/><path d="M58 98 h24 l4 40 h-10 l-2 26 h-8 l-2-26 h-10z"/>
<rect x="84" y="60" width="4" height="52" transform="rotate(14 86 86)"/><rect x="80" y="104" width="12" height="4"/>
<circle cx="118" cy="82" r="8"/><path d="M110 92 h16 l3 44 h-8 l-1 28 h-6 l-1-28 h-7z"/>
<path d="M135 66 q16 30 0 60" stroke="#0b0705" stroke-width="3" fill="none"/>
<line x1="135" y1="66" x2="135" y2="126" stroke="#0b0705" stroke-width="1"/>
<path d="M176 52 l12 26 h-24z"/><circle cx="176" cy="84" r="8"/><path d="M164 92 h24 l8 72 h-40z"/>
<rect x="196" y="58" width="3.5" height="106"/><circle cx="198" cy="56" r="5" fill="#ffe39a"/>
<circle cx="232" cy="106" r="9"/>
<path d="M220 116 h24 l4 30 h-9 l-1 18 h-6 l-1-18 h-6 l-1 18 h-6 l-1-18 h-6z"/><path d="M226 112 q6 14 12 0z"/>
<rect x="250" y="88" width="3.5" height="56"/><path d="M253 88 q14 6 0 20z"/>
</g></svg>'''

PUPPETEER = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 170" preserveAspectRatio="xMidYMax slice">
<defs><radialGradient id="moon" cx=".5" cy=".35" r=".8"><stop offset="0" stop-color="#5a3a7a"/>
<stop offset=".6" stop-color="#24142e"/><stop offset="1" stop-color="#0d0812"/></radialGradient></defs>
<rect width="300" height="170" fill="url(#moon)"/>
<circle cx="230" cy="40" r="20" fill="#e9d9a6" opacity=".8"/>
<g fill="#05080c">
<path d="M70 40 q14-24 30 0 l6 24 h-42z"/><path d="M60 64 h52 l14 106 h-80z"/>
<path d="M104 72 l40 -22 l4 6 l-38 24z"/>
<rect x="134" y="44" width="56" height="5" rx="2"/><rect x="159" y="30" width="5" height="34" rx="2"/>
</g>
<g stroke="#e8d7b0" stroke-width=".9" opacity=".85">
<line x1="136" y1="49" x2="168" y2="108"/><line x1="188" y1="49" x2="206" y2="108"/>
<line x1="161" y1="64" x2="186" y2="92"/><line x1="150" y1="49" x2="176" y2="130"/>
<line x1="176" y1="49" x2="200" y2="132"/></g>
<g fill="#05080c">
<circle cx="186" cy="98" r="7"/><path d="M176 106 h20 l2 26 h-24z"/><path d="M168 108 l8 -2 l2 14 l-8 4z"/>
<path d="M204 108 l-8 -2 l-2 14 l8 4z"/>
<rect x="176" y="132" width="7" height="22"/><rect x="189" y="132" width="7" height="22"/>
<rect x="206" y="96" width="3" height="30" transform="rotate(20 207 111)"/>
</g></svg>'''


def party() -> bytes:
    return PARTY.encode("utf-8")


def puppeteer() -> bytes:
    return PUPPETEER.encode("utf-8")
