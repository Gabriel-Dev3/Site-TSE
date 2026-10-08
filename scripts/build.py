"""Embute dados.json no template e grava o HTML final.

uso: python -I build.py template.html dados.json saida.html [--artifact]
--artifact: remove doctype/html/head/body (o publicador de Artifacts adiciona o esqueleto).
"""
import re
import sys

tpl, dados, out = sys.argv[1:4]
artifact = '--artifact' in sys.argv[4:]
html = open(tpl, encoding='utf-8').read()
js = open(dados, encoding='utf-8').read().replace('</', '<\\/')
assert html.count('__DADOS__') == 1
html = html.replace('__DADOS__', js)
if artifact:
    html = re.sub(r'^\s*<!doctype html>\s*<html[^>]*>\s*<head>\s*', '', html, flags=re.I)
    html = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>\s*', '', html, count=1)
    html = html.replace('</head>\n<body>\n', '', 1)
    html = re.sub(r'</body>\s*</html>\s*$', '', html)
open(out, 'w', encoding='utf-8', newline='\n').write(html)
print('ok', out)
