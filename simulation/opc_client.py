"""
OPC-UA Client for CODESYS Soft PLC Communication
Mini-Fulfillment Conveyor System

Provides read/write access to PLC tags via OPC-UA.
Connects to the CODESYS runtime OPC-UA server.

If CODESYS is not running, falls back to a local simulation mode
where all tags are stored in memory (for standalone testing).
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class PLCTag:
    """Represents a PLC variable accessible via OPC-UA."""
    name: str
    node_id: str
    value: Any = None
    writable: bool = True


class OPCUAClient:
    """
    OPC-UA client for reading/writing PLC tags.
    
    Falls back to local simulation if CODESYS is not available.
    """

    # Tag definitions matching the PLC GVL and IO_Mapping
    TAG_DEFINITIONS = {
        # Digital Inputs (simulator writes these)
        "bStartPB":       PLCTag("bStartPB",       "IO_Mapping.bStartPB",       False),
        "bStopPB":        PLCTag("bStopPB",        "IO_Mapping.bStopPB",        True),   # NC: TRUE = not pressed
        "bEStop":         PLCTag("bEStop",         "IO_Mapping.bEStop",         True),   # NC: TRUE = healthy
        "bModeSelector":  PLCTag("bModeSelector",  "IO_Mapping.bModeSelector",  False),  # FALSE = Auto
        "bInfeedPE":      PLCTag("bInfeedPE",      "IO_Mapping.bInfeedPE",      False),
        "bDiverterPE":    PLCTag("bDiverterPE",    "IO_Mapping.bDiverterPE",    False),
        "bOutfeedBPE":    PLCTag("bOutfeedBPE",    "IO_Mapping.bOutfeedBPE",    False),
        "bOutfeedCPE":    PLCTag("bOutfeedCPE",    "IO_Mapping.bOutfeedCPE",    False),

        # Digital Outputs (simulator reads these)
        "bConveyorMotor":    PLCTag("bConveyorMotor",    "IO_Mapping.bConveyorMotor",    False, writable=False),
        "bDiverterActuator": PLCTag("bDiverterActuator", "IO_Mapping.bDiverterActuator", False, writable=False),
        "bAlarmBuzzer":      PLCTag("bAlarmBuzzer",      "IO_Mapping.bAlarmBuzzer",      False, writable=False),
        "bStatusGreen":      PLCTag("bStatusGreen",      "IO_Mapping.bStatusGreen",      False, writable=False),
        "bStatusRed":        PLCTag("bStatusRed",        "IO_Mapping.bStatusRed",        False, writable=False),

        # HMI Commands (simulator can write these)
        "bHMI_Start":      PLCTag("bHMI_Start",      "GVL.bHMI_Start",      False),
        "bHMI_Stop":       PLCTag("bHMI_Stop",       "GVL.bHMI_Stop",       False),
        "bHMI_FaultClear": PLCTag("bHMI_FaultClear", "GVL.bHMI_FaultClear", False),
        "bHMI_JogFwd":     PLCTag("bHMI_JogFwd",     "GVL.bHMI_JogFwd",     False),

        # System State (read-only from simulator perspective)
        "iHMI_State":      PLCTag("iHMI_State",      "GVL.iHMI_State",      0, writable=False),
        "sHMI_FaultMsg":   PLCTag("sHMI_FaultMsg",   "GVL.sHMI_FaultMsg",   "", writable=False),

        # Metrics (read-only)
        "rHMI_BoxCount":     PLCTag("rHMI_BoxCount",     "GVL.rHMI_BoxCount",     0, writable=False),
        "rHMI_AvgCycleTime": PLCTag("rHMI_AvgCycleTime", "GVL.rHMI_AvgCycleTime", 0.0, writable=False),
        "rHMI_JamCount":     PLCTag("rHMI_JamCount",     "GVL.rHMI_JamCount",     0, writable=False),
        "rHMI_Throughput":   PLCTag("rHMI_Throughput",   "GVL.rHMI_Throughput",   0.0, writable=False),

        # Parameters (simulator can write these)
        "rJamTimeoutSec":  PLCTag("rJamTimeoutSec",  "GVL.rJamTimeoutSec",  4.0),
        "rConveyorSpeed":  PLCTag("rConveyorSpeed",  "GVL.rConveyorSpeed",  1.0),
    }

    def __init__(self, server_url: str = "opc.tcp://localhost:4840",
                 namespace: str = "http://codesys.com/UA",
                 timeout_ms: int = 5000):
        self.server_url = server_url
        self.namespace = namespace
        self.timeout_ms = timeout_ms
        self.connected = False
        self.simulation_mode = False
        self._client = None
        self._nodes: dict[str, Any] = {}

        # Initialize local tag store (used in simulation mode)
        self._local_tags: dict[str, Any] = {}
        for name, tag in self.TAG_DEFINITIONS.items():
            self._local_tags[name] = tag.value

    def connect(self) -> bool:
        """
        Attempt to connect to the CODESYS OPC-UA server.
        Falls back to simulation mode if connection fails.
        """
        try:
            from opcua import Client
            self._client = Client(self.server_url, timeout=self.timeout_ms / 1000)
            self._client.connect()
            self.connected = True
            self.simulation_mode = False
            logger.info(f"Connected to OPC-UA server at {self.server_url}")

            # Discover and cache node references
            self._discover_nodes()
            return True

        except Exception as e:
            logger.warning(f"Could not connect to OPC-UA server: {e}")
            logger.info("Falling back to local simulation mode")
            self.connected = False
            self.simulation_mode = True
            return False

    def _discover_nodes(self):
        """Discover OPC-UA nodes for all defined tags."""
        if not self._client:
            return
        try:
            root = self._client.get_root_node()
            objects = self._client.get_objects_node()
            # Attempt to find nodes by browse path
            for name, tag in self.TAG_DEFINITIONS.items():
                try:
                    node = root.get_child(
                        [f"0:Objects", f"2:DeviceSet", f"2:CODESYS Control",
                         f"2:Resources", f"2:Application", f"2:{tag.node_id}"]
                    )
                    self._nodes[name] = node
                except Exception:
                    logger.debug(f"Could not find node for {name}, will use browse")
        except Exception as e:
            logger.warning(f"Node discovery failed: {e}")

    def disconnect(self):
        """Disconnect from OPC-UA server."""
        if self._client and self.connected:
            try:
                self._client.disconnect()
            except Exception:
                pass
            self.connected = False
            logger.info("Disconnected from OPC-UA server")

    def read(self, tag_name: str) -> Any:
        """Read a PLC tag value."""
        if tag_name not in self.TAG_DEFINITIONS:
            raise KeyError(f"Unknown tag: {tag_name}")

        if self.simulation_mode or not self.connected:
            return self._local_tags.get(tag_name)

        try:
            if tag_name in self._nodes:
                return self._nodes[tag_name].get_value()
            else:
                return self._local_tags.get(tag_name)
        except Exception as e:
            logger.error(f"Error reading {tag_name}: {e}")
            return self._local_tags.get(tag_name)

    def write(self, tag_name: str, value: Any):
        """Write a value to a PLC tag."""
        if tag_name not in self.TAG_DEFINITIONS:
            raise KeyError(f"Unknown tag: {tag_name}")

        # Always update local store
        self._local_tags[tag_name] = value

        if self.simulation_mode or not self.connected:
            return

        try:
            if tag_name in self._nodes:
                self._nodes[tag_name].set_value(value)
        except Exception as e:
            logger.error(f"Error writing {tag_name}={value}: {e}")

    def read_all_inputs(self) -> dict[str, Any]:
        """Read all input tags."""
        inputs = {}
        for name in ["bStartPB", "bStopPB", "bEStop", "bModeSelector",
                      "bInfeedPE", "bDiverterPE", "bOutfeedBPE", "bOutfeedCPE"]:
            inputs[name] = self.read(name)
        return inputs

    def read_all_outputs(self) -> dict[str, Any]:
        """Read all output tags."""
        outputs = {}
        for name in ["bConveyorMotor", "bDiverterActuator", "bAlarmBuzzer",
                      "bStatusGreen", "bStatusRed"]:
            outputs[name] = self.read(name)
        return outputs

    def read_metrics(self) -> dict[str, Any]:
        """Read all metrics tags."""
        metrics = {}
        for name in ["iHMI_State", "rHMI_BoxCount", "rHMI_AvgCycleTime",
                      "rHMI_JamCount", "rHMI_Throughput", "sHMI_FaultMsg"]:
            metrics[name] = self.read(name)
        return metrics

    def read_all(self) -> dict[str, Any]:
        """Read all tags."""
        return {name: self.read(name) for name in self.TAG_DEFINITIONS}
