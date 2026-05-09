from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CMAKE = PACKAGE_ROOT / "CMakeLists.txt"
PACKAGE_XML = PACKAGE_ROOT / "package.xml"


def _registered_interfaces():
    source = CMAKE.read_text(encoding="utf-8")
    return re.findall(r'"((?:msg|srv|action)/[^"]+\.(?:msg|srv|action))"', source)


def _declared_dependencies():
    package = ET.parse(PACKAGE_XML).getroot()
    return {
        element.text.strip()
        for element in package
        if element.tag in {"depend", "build_depend", "exec_depend"} and element.text
    }


def _local_message_types():
    return {path.stem for path in (PACKAGE_ROOT / "msg").glob("*.msg")}


def _field_base_type(field_type):
    return field_type.split("[", 1)[0]


class InterfaceContractStaticTest(unittest.TestCase):
    def test_cmake_registers_every_interface_file_once(self):
        registered = _registered_interfaces()
        interface_files = sorted(
            str(path.relative_to(PACKAGE_ROOT))
            for folder in ("msg", "srv", "action")
            for path in (PACKAGE_ROOT / folder).glob(f"*.{folder}")
        )

        self.assertEqual(sorted(registered), interface_files)
        self.assertEqual(len(registered), len(set(registered)))

    def test_registered_interface_paths_exist(self):
        for relative_path in _registered_interfaces():
            with self.subTest(interface=relative_path):
                self.assertTrue((PACKAGE_ROOT / relative_path).is_file())

    def test_package_declares_runtime_and_field_type_dependencies(self):
        package_source = PACKAGE_XML.read_text(encoding="utf-8-sig")
        cmake_source = CMAKE.read_text(encoding="utf-8")
        dependencies = _declared_dependencies()

        self.assertIn("<buildtool_depend>rosidl_default_generators</buildtool_depend>", package_source)
        self.assertIn("<exec_depend>rosidl_default_runtime</exec_depend>", package_source)
        self.assertIn("<member_of_group>rosidl_interface_packages</member_of_group>", package_source)
        self.assertIn("ament_export_dependencies(rosidl_default_runtime)", cmake_source)

        for dependency in ("std_msgs", "geometry_msgs"):
            with self.subTest(dependency=dependency):
                self.assertIn(dependency, dependencies)
                self.assertIn(f"find_package({dependency} REQUIRED)", cmake_source)

    def test_interface_fields_do_not_reference_undeclared_external_packages(self):
        dependencies = _declared_dependencies()
        local_message_types = _local_message_types()
        builtins = {
            "bool",
            "byte",
            "char",
            "float32",
            "float64",
            "int8",
            "uint8",
            "int16",
            "uint16",
            "int32",
            "uint32",
            "int64",
            "uint64",
            "string",
        }

        for relative_path in _registered_interfaces():
            source = (PACKAGE_ROOT / relative_path).read_text(encoding="utf-8")
            for line in source.splitlines():
                line = line.split("#", 1)[0].strip()
                if not line or line == "---":
                    continue
                field_type = _field_base_type(line.split()[0])
                if "/" not in field_type and field_type in builtins:
                    continue
                package = field_type.split("/", 1)[0] if "/" in field_type else None
                if package:
                    with self.subTest(interface=relative_path, field_type=field_type):
                        self.assertIn(package, dependencies)
                else:
                    with self.subTest(interface=relative_path, field_type=field_type):
                        self.assertIn(field_type, local_message_types)


if __name__ == "__main__":
    unittest.main()
