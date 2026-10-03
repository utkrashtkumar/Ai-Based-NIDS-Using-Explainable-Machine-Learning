"""
Windows Firewall Mitigation Controller for AI-NIDS
Executes 1-click IP blocking and unblocking rules using Windows netsh advfirewall.
"""

import subprocess
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

RULE_PREFIX = "AI_NIDS_BLOCK_"

class FirewallManager:
    @staticmethod
    def block_ip(ip_address: str) -> Dict[str, Any]:
        """
        Blocks an inbound IP address using Windows Firewall.
        Command: netsh advfirewall firewall add rule name="AI_NIDS_BLOCK_<ip>" dir=in action=block remoteip=<ip>
        """
        rule_name = f"{RULE_PREFIX}{ip_address}"
        cmd = [
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={rule_name}",
            "dir=in",
            "action=block",
            f"remoteip={ip_address}",
            "description=Blocked automatically by AI-NIDS Intrusion Detection Engine"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                logger.info(f"[SUCCESS] Blocked IP {ip_address} in Windows Firewall (Rule: {rule_name})")
                return {"success": True, "ip": ip_address, "rule_name": rule_name, "message": f"Successfully blocked {ip_address}"}
            else:
                err_msg = result.stderr.strip() or result.stdout.strip()
                logger.warning(f"Firewall command failed: {err_msg}")
                return {"success": False, "ip": ip_address, "message": f"Firewall command error: {err_msg} (Admin privileges required)"}
        except Exception as e:
            logger.error(f"Exception executing firewall block: {e}")
            return {"success": False, "ip": ip_address, "message": str(e)}

    @staticmethod
    def unblock_ip(ip_address: str) -> Dict[str, Any]:
        """
        Unblocks an IP address by deleting its rule.
        Command: netsh advfirewall firewall delete rule name="AI_NIDS_BLOCK_<ip>"
        """
        rule_name = f"{RULE_PREFIX}{ip_address}"
        cmd = ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                logger.info(f"[SUCCESS] Removed firewall rule for {ip_address}")
                return {"success": True, "ip": ip_address, "message": f"Successfully unblocked {ip_address}"}
            else:
                err_msg = result.stderr.strip() or result.stdout.strip()
                return {"success": False, "ip": ip_address, "message": err_msg}
        except Exception as e:
            logger.error(f"Exception executing firewall unblock: {e}")
            return {"success": False, "ip": ip_address, "message": str(e)}

    @staticmethod
    def list_rules() -> List[str]:
        """Lists active AI-NIDS block rules."""
        cmd = ["netsh", "advfirewall", "firewall", "show", "rule", f"name=all"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            blocked_ips = []
            for line in result.stdout.splitlines():
                if RULE_PREFIX in line:
                    ip = line.split(RULE_PREFIX)[-1].strip().strip('"')
                    if ip and ip not in blocked_ips:
                        blocked_ips.append(ip)
            return blocked_ips
        except Exception as e:
            logger.error(f"Error listing firewall rules: {e}")
            return []
