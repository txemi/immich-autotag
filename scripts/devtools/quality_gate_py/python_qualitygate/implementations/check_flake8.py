
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckFlake8(Check):
    name = 'check_flake8'

    def _get_flake8_config(self, level) -> tuple[list[str], str | None]:
        from python_qualitygate.core.enums_level import QualityGateLevel

        base_ignore = ['E203', 'W503']
        flake8_select = None
        match level:
            case QualityGateLevel.STRICT:
                flake8_ignore = base_ignore
            case QualityGateLevel.STANDARD:
                # OPTION #3 ACTIVATED: Block all errors (not just F*), except E501
                flake8_ignore = base_ignore + ['E501']
            case QualityGateLevel.TARGET:
                # OPTION #3 ACTIVATED: Block all errors (not just F*), except E501
                flake8_ignore = base_ignore + ['E501']
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {level}")
        return flake8_ignore, flake8_select

    def _build_cmd(
        self,
        args: QualityGateArgs,
        flake8_ignore: list[str],
        flake8_select: str | None,
    ) -> list[str]:
        cmd = [args.py_bin, '-m', 'flake8', '--max-line-length', str(args.line_length)]
        if flake8_select:
            cmd.extend(['--select', flake8_select])
        cmd.extend(
            [
                '--extend-ignore',
                ','.join(flake8_ignore),
                '--exclude',
                '.venv,immich-client,scripts,jenkins_logs',
                str(args.target_dir),
            ]
        )
        return cmd

    def _parse_findings(self, output: str, target_dir: str) -> list[Finding]:
        from pathlib import Path

        findings: list[Finding] = []
        for line in output.splitlines():
            parts = line.split(':', 3)
            if len(parts) == 4:
                file_path, line_num, col, rest = parts
                code_msg = rest.strip().split(' ', 1)
                code = code_msg[0] if code_msg else ''
                msg = code_msg[1] if len(code_msg) > 1 else ''
                findings.append(
                    Finding(
                        file_path=Path(file_path),
                        line_number=int(line_num),
                        message=msg,
                        code=code,
                    )
                )
            else:
                findings.append(
                    Finding(
                        file_path=Path(target_dir),
                        line_number=0,
                        message=line.strip(),
                        code="flake8-parse",
                    )
                )
        return findings

    def check(self, args: QualityGateArgs) -> CheckResult:
        from python_qualitygate.core.enums_level import QualityGateLevel
        flake8_ignore, flake8_select = self._get_flake8_config(args.level)
        cmd = self._build_cmd(args, flake8_ignore, flake8_select)
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            findings = self._parse_findings(result.stdout, str(args.target_dir))
        else:
            findings = []
        match args.level:
            case QualityGateLevel.STRICT:
                return CheckResult(findings=findings)
            case QualityGateLevel.STANDARD:
                # STANDARD now blocks F* errors (same as TARGET)
                return CheckResult(findings=findings)
            case QualityGateLevel.TARGET:
                return CheckResult(findings=findings)
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # Flake8 no modifica archivos, solo check
        return self.check(args)
