"""
test_generator.py — Smoke test para el appian_generator

Genera un paquete ZIP de prueba con constantes extraídas del análisis del
NCI Redención Bono y valida que la estructura del ZIP sea correcta.
"""
import sys
import zipfile
from pathlib import Path

# Agregar el path del módulo
sys.path.insert(0, str(Path(__file__).parent.parent))

from appian_generator.uuid_registry import UUIDRegistry
from appian_generator.manifest_builder import ManifestBuilder
from appian_generator.constants_builder import ConstantsBuilder
from appian_generator.zip_packager import ZipPackager

def test_basic_package():
    print("=== TEST: appian_generator básico ===\n")

    # Setup
    registry = UUIDRegistry()
    manifest_builder = ManifestBuilder(registry)
    manifest = manifest_builder.create_manifest(
        app_name="TEST Redención Bono",
        app_prefix="TEST_RB",
        appian_version="26.3.165.0"
    )
    constants_builder = ConstantsBuilder(
        registry=registry,
        app_prefix="TEST_RB",
        default_parent_uuid=""
    )
    packager = ZipPackager(manifest, manifest_builder)

    # Crear carpeta de constantes
    folder = constants_builder.create_folder(
        folder_name="TEST_RB Constants",
        description="Constantes de prueba para Redención de Bono"
    )
    folder_xml = constants_builder.to_xml(folder)
    packager.add_content(folder.uuid, folder_xml)
    print(f"✓ Folder creado: {folder.name} [{folder.uuid}]")

    # Crear constantes de prueba
    test_constants = [
        ("TXT_SNAPSHOT",     "String",  "Profuturo Redencion Bono V 1.0", False),
        ("TXT_FILE_PATH",    "String",  "/NCI/RCDI/REDBON/INF/",          True),
        ("INT_RESULT_ID",    "Integer", "0",                               False),
        ("INT_MAX_MONTO",    "Decimal", "999999.99",                       False),
    ]

    for name, ibm_type, value, is_env in test_constants:
        const = constants_builder.from_ibm_variable(
            name=name,
            ibm_type=ibm_type,
            value=value,
            description=f"Constante de prueba: {name}",
            parent_uuid=folder.uuid,
            is_env_specific=is_env
        )
        xml = constants_builder.to_xml(const)
        packager.add_content(const.uuid, xml)
        env_flag = " [ENV-SPECIFIC]" if is_env else ""
        print(f"✓ Constant: {const.name} [{ibm_type}] = {value}{env_flag}")

    # Generar ZIP
    output_path = Path(__file__).parent / "test_output" / "TEST_RedencionBono.zip"
    zip_path = packager.build(str(output_path))
    print(f"\n✓ ZIP generado: {zip_path}")

    # Validar ZIP
    print("\n=== CONTENIDO DEL ZIP ===")
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in sorted(zf.namelist()):
            info = zf.getinfo(name)
            print(f"  {name:60s} {info.file_size:>8d} bytes")

    # Verificar estructura
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert "META-INF/MANIFEST.MF" in names, "Missing MANIFEST.MF"
        assert any(n.startswith("application/") for n in names), "Missing application/"
        assert any(n.startswith("content/") for n in names), "Missing content/"
        print(f"\n✓ Estructura validada: {len(names)} archivos en el ZIP")

    # Summary
    print(f"\n=== RESUMEN ===")
    s = packager.summary()
    for k, v in s.items():
        print(f"  {k}: {v}")

    print("\n✅ PRUEBA EXITOSA")
    return zip_path


if __name__ == "__main__":
    test_basic_package()
