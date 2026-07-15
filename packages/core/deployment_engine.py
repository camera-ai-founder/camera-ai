import json
import time
from typing import Dict, Any
from packages.core.models import DeployDNA, BiomeDNA
from packages.core.templates import DOCKERFILE_TEMPLATE

class DeploymentEngine:
    """
    The Deterministic Containerizer. 
    It reads the DeployDNA and injects it into the pre-audited template.
    Zero AI hallucinations allowed.
    """

    @staticmethod
    def synthesize_dockerfile(deploy_dna: DeployDNA) -> str:
        # 1. Process the Port Mappings from the DNA
        port_lines = []
        for internal_port, external_port in deploy_dna.port_mappings.items():
            # Docker just needs to know which internal ports to EXPOSE
            port_lines.append(f"EXPOSE {internal_port}")
            
        # If no ports were specified, leave a clean comment
        ports_injection = "\n".join(port_lines) if port_lines else "# No ports exposed"
        
        # 2. Process the Environment Variables from the DNA
        env_lines = []
        for key, value in deploy_dna.env_variables.items():
            env_lines.append(f"ENV {key}={value}")
            
        # If no env vars, leave a clean comment
        envs_injection = "\n".join(env_lines) if env_lines else "# No environment variables set"
        
        # 3. Inject the processed data into the perfect template
        dockerfile = DOCKERFILE_TEMPLATE.replace("{{PORTS}}", ports_injection)
        dockerfile = dockerfile.replace("{{ENV_VARS}}", envs_injection)
        
        return dockerfile

    @staticmethod
    def synthesize_asset_manifest(biome_dna: BiomeDNA, genesis_renderer_data: Dict[str, Any]) -> str:
        """
        Scans the BiomeDNA and GenesisRenderer to build a lightweight 
        assets_manifest.json. This ensures the Docker container ONLY 
        downloads the exact assets needed, keeping it tiny and fast.
        """
        # 1. Gather assets from the Biome's Scatter Rules
        required_assets = set()
        for rule in biome_dna.scatter_rules:
            required_assets.add(rule.asset_type)
            
        # 2. Gather assets from the Genesis Renderer (Parametric Math & Fallbacks)
        # We look at the raw JSON data the Brain provided for the visual scene
        parametric_genomes = genesis_renderer_data.get("parametric_genomes", [])
        for genome in parametric_genomes:
            # We tag math assets by their seed so the engine can regrow them deterministically
            required_assets.add(f"parametric_math_{genome.get('seed', 'unknown')}")
            
        visual_queries = genesis_renderer_data.get("visual_queries", [])
        for query in visual_queries:
            if query.get("fallback_flag"):
                # If it's a fallback, we need the actual 3D model file name
                for term in query.get("search_terms", []):
                    required_assets.add(f"cc0_model_{term}")

        # 3. Build the lightweight manifest
        manifest = {
            "biome_name": biome_dna.name,
            "elevation_curve": biome_dna.elevation_curve,
            "total_assets": len(required_assets),
            "asset_list": sorted(list(required_assets))
        }
        
        # Return it as a beautifully formatted JSON string
        return json.dumps(manifest, indent=2)

    @staticmethod
    def push_to_cloud(dockerfile: str, manifest: str, deploy_dna: DeployDNA) -> bool:
        """
        DAY 20 STEP 6: THE CLOUD BRIDGE.
        Simulates pushing the compiled blueprint to a $0 cloud host 
        (like Render, Railway, or Supabase Edge) via a mock webhook.
        In the real world, this tiny JSON payload is all the cloud needs 
        to start the deterministic build. Zero SSH keys required.
        """
        print("\n📡 [Cloud Bridge] Establishing secure webhook connection...")
        time.sleep(1)  # Simulate network latency safely
        
        # This tiny payload is all the cloud host needs to start building!
        payload = {
            "target": deploy_dna.target_environment,
            "dockerfile_size_bytes": len(dockerfile),
            "assets_count": json.loads(manifest).get("total_assets", 0),
            "status": "ready_for_deterministic_build"
        }
        
        print(f"📦 [Cloud Bridge] Sending payload to {deploy_dna.target_environment} API...")
        print(f"   -> Payload: {json.dumps(payload)}")
        time.sleep(1.5)  # Simulate cloud processing
        
        print("✅ [Cloud Bridge] Webhook received! Cloud host is now building the container.")
        return True