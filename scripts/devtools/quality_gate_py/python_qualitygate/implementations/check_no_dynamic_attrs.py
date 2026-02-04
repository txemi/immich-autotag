import re
from pathlib import Path
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckNoDynamicAttrs(Check):
    _name: str = attr.ib(default='check_no_dynamic_attrs', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        """
        Forbids the use of getattr/hasattr for static typing safety.
        Policy enforcement: disallow dynamic attribute access via getattr() and hasattr()
        
        Activation by quality level:
        - STANDARD: ENABLED (blocks if getattr/hasattr detected)
        - TARGET: ENABLED (blocks if getattr/hasattr detected)
        - STRICT: ENABLED (blocks if getattr/hasattr detected)
        """
        from python_qualitygate.core.enums_level import QualityGateLevel
        
        # Defensive programming: explicitly evaluate all quality level cases
        match args.level:
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET | QualityGateLevel.STRICT:
                pass
            case _:
                # Defensive: unknown level should fail hard
                raise ValueError(
                    f"Unknown quality level: {args.level}. Expected STANDARD, TARGET, or STRICT."
                )
        
        # Collect findings for TARGET and STRICT
        findings = []
        for pyfile in Path(args.target_dir).rglob('*.py'):
            # Skip excluded directories
            if any(skip in str(pyfile) for skip in ['.venv', 'immich-client', 'scripts', 'jenkins_logs']):
                continue
            with open(pyfile, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if 'getattr(' in line or 'hasattr(' in line:
                        findings.append(Finding(
                            file_path=str(pyfile), 
                            line_number=i, 
                            message=line.strip(), 
                            code="no_dynamic_attrs"
                        ))

        print(f"[{args.level.name} MODE] getattr/hasattr policy enforcement is ENABLED.")
        return QualityGateResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        # Solo checkea, no modifica
        return self.check(args)
