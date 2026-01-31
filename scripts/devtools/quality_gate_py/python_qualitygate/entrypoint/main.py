
import sys

# Install typeguard import hook before any project imports
from python_qualitygate.utils.typeguard_hook import install_typeguard_import_hook
install_typeguard_import_hook("python_qualitygate")


from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.batteries.battery import Battery
from python_qualitygate.batteries.registry import CHECKS, BATTERY_ORDER
from python_qualitygate.core.enums_mode import QualityGateMode
from python_qualitygate.core.enums_level import QualityGateLevel
from python_qualitygate.cli.parse_args import parse_args
import sys
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.batteries.battery import Battery
from python_qualitygate.batteries.registry import CHECKS, BATTERY_ORDER
from python_qualitygate.core.enums_mode import QualityGateMode
from python_qualitygate.core.enums_level import QualityGateLevel
from python_qualitygate.cli.parse_args import parse_args



# Move run_quality_gate to a separate module
from python_qualitygate.entrypoint.run_quality_gate import run_quality_gate

def main():
    run_quality_gate()
