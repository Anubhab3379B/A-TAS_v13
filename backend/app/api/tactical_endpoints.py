"""
A-TAS Elite v13.0 Apex — Unified Tactical API
Exposes all 19 modules via versioned REST endpoints.
All endpoints are consumed by the frontend tactical HUD.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger
import asyncio
import json

from app.services.security_lock_service import SecurityLockService
from app.services.intelligence.agentic.agentic_coordinator import AgenticCoordinator
from app.services.tactical_sigint import TacticalSIGINTService
from app.services.offensive_ops import OffensiveOpsService
from app.services.defensive_audit import DefensiveAuditService
from app.services.intelligence.re_service import AIReverseEngService

# ---------------------------------------------------------------------------
# Dependency setup
# ---------------------------------------------------------------------------
router = APIRouter()

# Shared singletons — instantiated once at module load
_lock = SecurityLockService()
_coordinator = AgenticCoordinator(_lock)
_sigint = TacticalSIGINTService()
_offensive = OffensiveOpsService()
_defensive = DefensiveAuditService()
_re_service = AIReverseEngService()


# ===========================================================================
# Pydantic models
# ===========================================================================
class TargetRequest(BaseModel):
    host: str
    os: Optional[str] = "unknown"
    stack: Optional[List[str]] = []
    bin_data: Optional[str] = None

class AdminDirective(BaseModel):
    username: str
    password: str
    directive: str

class PayloadStrategyRequest(BaseModel):
    category: str

class HybridRequest(BaseModel):
    cat1: str
    cat2: str
    target: Optional[str] = "127.0.0.1"

class SwarmNodeRequest(BaseModel):
    ip: str
    os: str
    capacity: Optional[float] = 1.0
    distance: Optional[float] = 10.0

class CSIScanRequest(BaseModel):
    csi_matrix: Optional[List[List[float]]] = None
    has_camera: Optional[bool] = True

class NetworkScanRequest(BaseModel):
    subnet: Optional[str] = "192.168.1.0/24"
    passive: Optional[bool] = True

class HashCrackRequest(BaseModel):
    hash_file: str
    algorithm: Optional[str] = "SHA-256"
    wordlist: Optional[str] = "rockyou.txt"


# ===========================================================================
# [Module 1] SIGINT
# ===========================================================================
@router.post("/sigint/scan", tags=["SIGINT"])
async def scan_signals(csi_data: list):
    """Detects movement and location signatures from CSI data."""
    return await _sigint.detect_intruders(csi_data)


# ===========================================================================
# [Module 2] Payload Vault
# ===========================================================================
@router.get("/vault/categories", tags=["Vault"])
async def list_vault_categories():
    """Returns all available payload categories (30+)."""
    return {"categories": list(_coordinator.vault.vault.keys()), "count": len(_coordinator.vault.vault)}

@router.post("/vault/strategy", tags=["Vault"])
async def get_vault_strategy(req: PayloadStrategyRequest):
    """Retrieves methodology and templates for a given payload category."""
    strategy = await _coordinator.vault.retrieve_strategy(req.category)
    if not strategy.get("templates"):
        raise HTTPException(status_code=404, detail=f"Category '{req.category}' not found in vault.")
    fallback = _coordinator.vault.get_executable_fallback(req.category, "TARGET_PLACEHOLDER")
    return {
        "category": req.category,
        "strategy": strategy,
        "fallback_command": fallback,
    }

@router.post("/vault/hybrid", tags=["Vault"])
async def generate_hybrid_payload(req: HybridRequest):
    """Generates a two-stage hybrid payload from two tactical categories."""
    result = _coordinator.vault.generate_hybrid_function(req.cat1, req.cat2, req.target)
    return result

@router.get("/vault/recommend", tags=["Vault"])
async def recommend_category(tech_stack: str = ""):
    """Context-aware category recommendation based on target tech stack."""
    stack_list = [t.strip().lower() for t in tech_stack.split(",") if t.strip()]
    category = _coordinator.vault.recommend_category(stack_list)
    return {"recommended_category": category, "stack": stack_list}


# ===========================================================================
# [Module 2/3] Offensive Ops
# ===========================================================================
@router.get("/offensive/payload", tags=["Offensive"])
async def get_payload(platform: str, tech: str):
    """Generates tactical payload string for a given platform and technology."""
    return {"payload": await _offensive.generate_payload(platform, tech)}

@router.post("/offensive/sqlmap", tags=["Offensive"])
async def start_sqlmap(target_url: str):
    """Initiates automated database vulnerability scan."""
    return await _offensive.trigger_sqlmap_scan(target_url)

@router.post("/offensive/sliver/implant", tags=["C2"])
async def generate_implant(os: str, arch: str):
    """[Sliver] Generates obfuscated cross-platform C2 implant."""
    return await _offensive.generate_sliver_implant(os, arch)


# ===========================================================================
# [Module 2] Hash Cracking (Craken Layer)
# ===========================================================================
@router.post("/vault/crack/hashcat", tags=["Cryptanalysis"])
async def generate_hashcat_cmd(req: HashCrackRequest):
    """Generates a GPU-accelerated hashcat command string."""
    cmd = _coordinator.cryptanalysis.generate_hashcat_command(req.hash_file, req.algorithm, req.wordlist)
    return {"command": cmd, "algorithm": req.algorithm}

@router.get("/vault/crack/algorithms", tags=["Cryptanalysis"])
async def list_crack_algorithms():
    """Returns all supported hash algorithms."""
    return {"algorithms": _coordinator.cryptanalysis.get_supported_algorithms()}


# ===========================================================================
# [Module 4/5] Defensive / Hardening
# ===========================================================================
@router.get("/defensive/prowler", tags=["Defensive"])
async def run_audit(cloud: str):
    """[Prowler] Audits cloud infrastructure for misconfigurations."""
    return await _defensive.run_prowler_audit(cloud)

@router.post("/defensive/harden", tags=["Defensive"])
async def apply_hardening(os: str):
    """Applies military-grade security hardening templates."""
    return await _defensive.apply_hardening_profile(os)


# ===========================================================================
# [Module 6] Agentic AI
# ===========================================================================
@router.post("/agentic/plan", tags=["Agentic AI"])
async def get_agent_plan(req: TargetRequest):
    """[Worker Bit] Generates autonomous attack/defense plan for a target."""
    return await _coordinator.autonomous_attack_plan(req.dict())

@router.post("/agentic/execute", tags=["Agentic AI"])
async def execute_agent_plan(req: TargetRequest):
    """[Worker Bit] Runs the full agentic loop with stealthy execution."""
    return await _coordinator.autonomous_attack_plan(req.dict(), execute=True)

@router.get("/agentic/status", tags=["Agentic AI"])
async def get_agent_status():
    """Real-time status telemetry for the AR HUD worker bit."""
    return await _coordinator.real_time_execution_monitor()

@router.get("/agentic/stream", tags=["Agentic AI"])
async def mission_stream():
    """
    SSE stream — pushes live agentic mission events to the frontend.
    Connect once; the server broadcasts status updates in real-time.
    """
    async def event_generator():
        event_id = 0
        while True:
            status = await _coordinator.real_time_execution_monitor()
            payload = json.dumps(status)
            yield f"id: {event_id}\ndata: {payload}\n\n"
            event_id += 1
            await asyncio.sleep(2)  # 2-second broadcast cadence

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ===========================================================================
# [Module 7] RE-Lab
# ===========================================================================
@router.post("/defensive/re/analyze", tags=["RE-Lab"])
async def analyze_re(hex_dump: str):
    """Neural-RE Transformer analysis on hex binary data."""
    return await _re_service.analyze_binary_chunk(hex_dump)

@router.post("/re/ioc", tags=["RE-Lab"])
async def extract_ioc(hex_data: str):
    """Extracts IPs, URLs, and domains from binary/hex data as IOC."""
    return await _re_service.extract_ioc_from_binary(hex_data.encode())


# ===========================================================================
# [Module 10] Ghost Resilience & PQC Encryption
# ===========================================================================
@router.get("/resilience/status", tags=["Resilience"])
async def get_resilience_status():
    """Ghost layer health metrics for the HUD."""
    return _coordinator.resilience.get_resilience_telemetry()

@router.get("/quantum/metrics", tags=["Quantum Crypto"])
async def get_quantum_metrics():
    """PQC security telemetry — Kyber/Dilithium status."""
    return _coordinator.quantum.get_security_metrics()


# ===========================================================================
# [Module 11] Swarm Coordination (Legion Layer)
# ===========================================================================
@router.get("/swarm/status", tags=["Swarm"])
async def get_swarm_status():
    """Returns GNN-optimized swarm topology for the HUD."""
    return _coordinator.swarm.get_topology_metrics()

@router.post("/swarm/register", tags=["Swarm"])
async def register_swarm_node(req: SwarmNodeRequest):
    """Registers a captured node into the tactical swarm."""
    node_id = _coordinator.swarm.register_captured_node(req.ip, req.os, req.capacity, req.distance)
    return {"status": "REGISTERED", "node_id": node_id}

@router.get("/swarm/directives", tags=["Swarm"])
async def get_swarm_directives(target: str = "127.0.0.1"):
    """GNN-generated action directives for all swarm nodes."""
    return {"directives": await _coordinator.swarm.get_actionable_directives(target)}


# ===========================================================================
# [Module 14] Global Recon (Omniscience)
# ===========================================================================
@router.post("/recon/footprint", tags=["Global Recon"])
async def perform_recon(target: str):
    """Performs full OSINT footprint against a domain or IP."""
    return await _coordinator.recon.perform_full_footprint(target)


# ===========================================================================
# [Module 15] Phantom Agent
# ===========================================================================
@router.post("/phantom/directive", tags=["Phantom Agent"])
async def phantom_directive(req: AdminDirective):
    """[Origin Admin Only] Execute a high-level autonomous directive."""
    result = await _coordinator.execute_phantom_directive(req.username, req.password, req.directive)
    return {"output": result}


# ===========================================================================
# [Module 17] CSI Omniscience (Oracle)
# ===========================================================================
@router.post("/csi/scan", tags=["CSI Oracle"])
async def csi_scan(req: CSIScanRequest):
    """Full CSI environment scan — GNN-powered node detection and thermal map."""
    import numpy as np
    if req.csi_matrix:
        data = np.array(req.csi_matrix, dtype=np.float32)
    else:
        data = np.random.rand(10, 64).astype(np.float32)

    return await _coordinator.tactical_csi.scan_environment(data, has_camera=req.has_camera)

@router.get("/csi/thermal", tags=["CSI Oracle"])
async def get_thermal_overlay():
    """Returns thermal vision parameters for AR HUD rendering."""
    return _coordinator.tactical_csi.get_thermal_overlay()


# ===========================================================================
# [Module 19] Apex Auto-Optimization
# ===========================================================================
@router.get("/optimization/profile", tags=["Apex Optimization"])
async def get_optimization_profile():
    """Returns current hardware-aware optimization profile."""
    return _coordinator.apex_opt.get_applied_settings()


# ===========================================================================
# [NEW] Network Intelligence — IP/MAC/Geo mapping
# ===========================================================================
@router.post("/network/scan", tags=["Network Intel"])
async def network_scan(req: NetworkScanRequest):
    """Passive network scan — discovers hosts, resolves MAC/OUI/Geo."""
    from app.services.network_intelligence_service import NetworkIntelligenceService
    net_intel = NetworkIntelligenceService()
    return await net_intel.passive_network_scan(req.subnet, passive=req.passive)

@router.get("/network/targets", tags=["Network Intel"])
async def list_known_targets():
    """Returns the current discovered target node table."""
    from app.services.network_intelligence_service import NetworkIntelligenceService
    net_intel = NetworkIntelligenceService()
    return net_intel.get_target_table()
