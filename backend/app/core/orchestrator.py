from app.core.protection.protection_service import ProtectionService
from app.services.intelligence.agentic.agentic_coordinator import AgenticCoordinator
from app.services.security_lock_service import SecurityLockService # Admin Key
from loguru import logger

class TacticalVisorOrchestrator: # This is the main controller for the whole app
    """
    [Module 8/14/15] Central Orchestrator for the A-TAS Suite.
    """
    def __init__(self): # This runs when we turn the visor on
        self.protection = ProtectionService() # Start the integrity monitoring
        self.lock = SecurityLockService() # Start the secret admin lock
        self.coordinator = AgenticCoordinator(self.lock) # Start the AI brain and link it to the lock
        logger.info("A-TAS Orchestrator Synchronized. All elite modules nominal.") # Success signal

    async def execute_phantom_directive(self, user, secret, directive): # A secret way for the admin to give orders
        """Hidden entry point for the origin creator to run agentic directives."""
        # This calls the brain (coordinator), which tells the Phantom agent what to do
        return await self.coordinator.execute_phantom_directive(user, secret, directive) # Return the results

    async def get_visor_state(self):
        """
        Unified state aggregator for the A-TAS Visor/App UI.
        """
        # 1. Admin Authorization Check
        security_status = self.lock.get_security_identity()
        
        # 2. Gather Elite Telemetry
        resilience = self.coordinator.resilience.get_resilience_telemetry()
        swarm = self.coordinator.swarm.get_topology_metrics()
        recon = self.coordinator.recon.get_recon_metrics()
        resources = self.coordinator.resources.get_orchestration_metrics()
        env_mode = self.coordinator.env.get_environment_metrics()

        return {
            "identity": security_status,
            "environment": env_mode,
            "system_status": "SECURE" if self.protection.verify_integrity() else "INTEGRITY_COMPROMISED",
            "orchestration": resources,
            "recon_coverage": recon,
            "swarm_health": swarm,
            "resilience": resilience
        }

    def login_admin(self, user: str, secret: str):
        """Hidden entry point for the origin creator."""
        return self.lock.verify_admin_access(user, secret)

    def trigger_wireless_auditing(self, bssid: str):
        """Triggers a deauth-and-capture sequence."""
        return self.coordinator.wireless.simulate_deauth_attack(bssid)

    def trigger_hash_crack(self, hash_file: str, type: int):
        """Triggers an autonomous hash cracking mission."""
        return self.coordinator.cryptanalysis.generate_hashcat_command(hash_file, type)

    def register_swarm_unit(self, ip: str, os: str):
        """Adds a captured node to the tactical swarm."""
        return self.coordinator.swarm.register_captured_node(ip, os)

    async def launch_autonomous_mission(self, target_ip: str, category: str = "SSRF"):
        """Triggers the full Agentic loop with Ghost layer protection."""
        logger.info(f"Orchestrating autonomous mission against {target_ip}...")
        return await self.coordinator.autonomous_attack_plan(
            {"host": target_ip}, category=category, execute=True
        )
