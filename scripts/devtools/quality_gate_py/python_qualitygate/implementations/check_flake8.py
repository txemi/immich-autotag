
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.core.enums_level import QualityGateLevel
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckFlake8(Check):
    _name: str = attr.ib(default='check_flake8', init=False)

    def get_name(self) -> str:
        return self._name

    def _get_flake8_config(self, level: QualityGateLevel) -> tuple[list[str], str | None]:
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
                file_path, line_num, _col, rest = parts
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

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        flake8_ignore, flake8_select = self._get_flake8_config(args.level)
        cmd = self._build_cmd(args, flake8_ignore, flake8_select)
        print(f"[RUN] {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            findings = []
        except subprocess.CalledProcessError as e:
            # This means flake8 ran, but found lint errors (expected for findings)
            findings = self._parse_findings(e.stdout, str(args.target_dir))
        except FileNotFoundError as e:
            # flake8 or python executable not found: this is a setup/execution error
            raise RuntimeError(f"flake8 executable not found: {e}") from e
        except Exception as e:
            # Any other unexpected error
            raise RuntimeError(f"Error running flake8: {e}") from e
        match args.level:
            case QualityGateLevel.STRICT:
                return QualityGateResult(findings=findings)
            case QualityGateLevel.STANDARD:
                return QualityGateResult(findings=findings)
            case QualityGateLevel.TARGET:
                return QualityGateResult(findings=findings)
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        # Flake8 no modifica archivos, solo check
        return self.check(args)
