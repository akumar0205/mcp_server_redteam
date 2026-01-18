from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from mcp_redteam.runner.trace import RunReport


def write_junit(report: RunReport, output_dir: Path) -> Path:
    testsuite = ET.Element("testsuite", name=report.suite_name or report.mode)
    testsuite.set("tests", str(len(report.test_results)))
    testsuite.set("failures", str(len(report.findings)))
    for result in report.test_results:
        case = ET.SubElement(testsuite, "testcase", name=result.name, classname=result.test_id)
        if result.findings:
            failure = ET.SubElement(case, "failure", message="Findings detected")
            failure.text = "\n".join(f"{f.id}: {f.title}" for f in result.findings)
    tree = ET.ElementTree(testsuite)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "report.junit.xml"
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path
