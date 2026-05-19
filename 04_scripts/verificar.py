"""
NTTDATA IBM TWX Suite — Verificador de instalacion
Uso: python verificar.py
"""
import sys, subprocess, importlib, shutil
from pathlib import Path

CYAN  = "\033[96m"
GRN   = "\033[92m"
RED   = "\033[91m"
YLW   = "\033[93m"
DIM   = "\033[2m"
RST   = "\033[0m"
BOLD  = "\033[1m"

checks = []

def ok(msg):  checks.append((True,  msg)); print(f"  {GRN}✓{RST} {msg}")
def err(msg): checks.append((False, msg)); print(f"  {RED}✗{RST} {msg}")

print(f"\n{CYAN}{BOLD}NTTDATA IBM TWX Suite — Verificacion de instalacion{RST}\n")

# Python version
v = sys.version_info
if v >= (3, 10):
    ok(f"Python {v.major}.{v.minor}.{v.micro}")
else:
    err(f"Python {v.major}.{v.minor} — se requiere 3.10+")

# Modulo importable
try:
    import ibm_twx_tools
    ok(f"ibm_twx_tools v{ibm_twx_tools.__version__} importado correctamente")
except ImportError as e:
    err(f"ibm_twx_tools no encontrado: {e}")

# Comando CLI en PATH
if shutil.which("nttdata-ibm-twx"):
    ok("nttdata-ibm-twx disponible en PATH")
else:
    err("nttdata-ibm-twx NO en PATH — ejecuta: pip install -e 01_herramientas_python/")

# Módulos internos
for mod in ["twx_parser","entity_extractor","service_extractor","flow_mapper","doc_generator","banner"]:
    try:
        importlib.import_module(f"ibm_twx_tools.{mod}")
        ok(f"ibm_twx_tools.{mod}")
    except ImportError:
        err(f"ibm_twx_tools.{mod} no encontrado")

# Herramientas externas
for tool in ["git", "node", "npm", "code", "gh"]:
    if shutil.which(tool):
        try:
            out = subprocess.check_output([tool, "--version"],
                                          stderr=subprocess.STDOUT, text=True).strip().splitlines()[0]
            ok(f"{tool}: {out}")
        except Exception:
            ok(f"{tool} disponible")
    else:
        err(f"{tool} no encontrado")

# Test funcional con TWX sintético
try:
    import zipfile, io, tempfile, os
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("META-INF/MANIFEST.MF",
                    "Process-App-Name: VerifyTest\nSnapshot-Name: v1.0\n")
        zf.writestr("test/Demo.service",
                    "<service name='Demo'><input name='x' type='String'/></service>")
    buf.seek(0)
    tmp = Path(tempfile.mktemp(suffix=".twx"))
    tmp.write_bytes(buf.read())
    from ibm_twx_tools.twx_parser import TWXParser
    pkg = TWXParser(str(tmp)).parse()
    tmp.unlink()
    ok(f"Test funcional TWX: app='{pkg.app_name}', artefactos={len(pkg.artifacts)}")
except Exception as e:
    err(f"Test funcional fallido: {e}")

# Resumen
total  = len(checks)
passed = sum(1 for c in checks if c[0])
failed = total - passed
print(f"\n{'═'*50}")
if failed == 0:
    print(f"{GRN}{BOLD}  ✅  Todo OK — {passed}/{total} verificaciones pasadas{RST}")
else:
    print(f"{YLW}  ⚠️  {passed}/{total} OK — {failed} problema(s) encontrado(s){RST}")
print(f"{'═'*50}\n")
sys.exit(0 if failed == 0 else 1)
