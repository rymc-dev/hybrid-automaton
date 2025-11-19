from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, List
import subprocess
from pathlib import Path
import logging
from hybraut_models import HybridAutomaton
from hybraut_models.core import ModeRegistry, Mode
from hybraut_models.core.transitions import TransitionRegistry, Transition
import yaml

from hybraut_diag_gen.config import Theme, Background, OutputFormat, DiagramConfig
from hybraut_diag_gen.exceptions import MermaidDiagramGeneratorError
from hybraut_diag_gen.mermaid_utils import (
    add_goal_states,
    add_initial_state,
    add_modes,
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybrautDiag:
    def __init__(self, output_directory: Optional[str] = None):
        self._output_dir = self._setup_output_directory(output_directory)
        self._ensure_mermaid_cli()

    def generate_mermaid_diagrams(
        self, automaton_model: HybridAutomaton, config: Optional[DiagramConfig] = None
    ) -> Tuple[str, str]:
        config = config or DiagramConfig()
        try:
            automaton_name = automaton_model.get_name()
            automaton_version = automaton_model.get_version()
            mermaid_lines = self._generate_mermaid_content(
                automaton_name, automaton_version, automaton_model
            )
            mmd_path = self._save_mermaid_file(mermaid_lines, automaton_name)
            output_path = self._convert_diagram(mmd_path, automaton_name, config)
            logger.info(f"Successfully generated diagram: {output_path}")
            return mmd_path, output_path
        except Exception as e:
            raise MermaidDiagramGeneratorError(
                f"Failed to generate diagram: {e}"
            ) from e

    def _setup_output_directory(self, output_directory: Optional[str]) -> Path:
        output_dir = (
            Path(output_directory)
            if output_directory
            else (Path(__file__).parent / ".." / ".github" / "assets" / "diagrams")
        )
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        return output_dir

    def _ensure_mermaid_cli(self) -> None:
        try:
            subprocess.run(
                ["mmdc", "--version"], capture_output=True, check=True, timeout=10
            )
            logger.info("Mermaid CLI is available")
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ) as e:
            msg = "Mermaid CLI not found or not working. Install with: npm install -g @mermaid-js/mermaid-cli"
            logger.error(msg)
            raise MermaidDiagramGeneratorError(msg) from e

    def _generate_mermaid_content(
        self,
        automaton_name: str,
        automaton_version: str,
        automaton_model: HybridAutomaton,
    ) -> List[str]:
        mermaid = [
            "stateDiagram-v2",
            f"    %% {automaton_name}:{automaton_version} State Diagram",
            "",
        ]
        init_mode = automaton_model.get_initial_mode()
        goal_modes = automaton_model.get_goal_modes()
        add_initial_state(mermaid, init_mode)
        add_modes(
            mermaid,
            automaton_model._mode_registry,
            automaton_model._transition_registry,
        )
        add_goal_states(mermaid, goal_modes)

        return mermaid

    def _save_mermaid_file(self, mermaid_lines: List[str], automaton_name: str) -> str:
        filename = f"{automaton_name}.famd.mmd"
        file_path = self._output_dir / filename
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(mermaid_lines))
            logger.info(f"Mermaid diagram saved to: {file_path}")
            return str(file_path)
        except IOError as e:
            raise MermaidDiagramGeneratorError(f"Failed to save .mmd file: {e}") from e

    def _convert_diagram(
        self, mmd_path: str, automaton_name: str, config: DiagramConfig
    ) -> str:
        output_filename = f"{automaton_name}.famd.{config.output_format.value}"
        output_path = self._output_dir / output_filename
        cmd = [
            "mmdc",
            "-i",
            mmd_path,
            "-o",
            str(output_path),
            "-t",
            config.theme.value,
            "-b",
            config.background.value,
            "--scale",
            str(config.scale),
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=30
            )
            logger.info(
                f"Successfully converted to {config.output_format.value}: {output_path}"
            )
            if result.stdout:
                logger.debug(f"mmdc output: {result.stdout}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            msg = f"Failed to convert diagram: {e.stderr}"
            logger.error(msg)
            raise MermaidDiagramGeneratorError(msg) from e
        except subprocess.TimeoutExpired:
            msg = "Diagram conversion timed out"
            logger.error(msg)
            raise MermaidDiagramGeneratorError(msg)