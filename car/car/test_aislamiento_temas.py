#!/usr/bin/env python3
"""Prueba de aislamiento de temas. Solo lectura, no requiere Django."""
import ast
import re
from pathlib import Path
from tinycss2 import parse_stylesheet
source = Path(__file__).with_name('views_estilos.py').read_text(encoding='utf-8')
tree = ast.parse(source)
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('parse_blocks','resolver_valor_visual','groups_for')]
namespace = {'re': re, 'THEMES': {'base': ':root', 'piedra': 'html.theme-piedra', 'sand': 'html.theme-sand'}, 'LABELS': {}}
exec(compile(ast.Module(body=funcs, type_ignores=[]), '<funciones>', 'exec'), namespace)
css = """
:root { --ui-accent-strong: #cc3300; --clock-text-color: var(--ui-accent-strong); }
html.theme-piedra { --clock-text-color: #0000ff; }
html.theme-sand, html.theme-claro { --clock-text-color: #ff0000; }
"""
parsed = namespace['parse_blocks'](css)
values = {theme: next(item['value'] for group in namespace['groups_for'](theme,parsed) for item in group['items'] if item['key']=='--clock-text-color') for theme in ('base','piedra','sand')}
assert values == {'base':'#cc3300','piedra':'#0000ff','sand':'#ff0000'}, values
print('OK: Piedra azul, Sand rojo, Base independiente. No se modificó ningún archivo del proyecto.')
