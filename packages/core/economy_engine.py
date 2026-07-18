from typing import Dict
from packages.core.models import EconomyDNA, EconomicEvent

class EconomyEngine:
    """
    The Deterministic Math Balancer & Anti-Inflation Guardrail. 
    It calculates exact reward values and enforces hard caps to prevent exploits.
    """
    
    def __init__(self):
        # Base mathematical weights for different types of interactions.
        self.faucet_weights = {
            "active_quest": 5.0,
            "loot_drop": 2.0,
            "passive_income": 1.0
        }
        self.sink_weights = {
            "vendor_purchase": 4.0,
            "crafting_cost": 3.0,
            "tax": 1.5
        }
        
        # Tracking variables for the Anti-Inflation Guardrails (The Bouncer)
        self.session_earnings = {} # Tracks total earned per resource in current session
        self.session_hours = {}    # Tracks hours played per resource in current session

    def calculate_flow_rate(self, dna: EconomyDNA, gameplay_hours: int = 10) -> Dict[str, float]:
        """
        Calculates the exact mathematical reward and cost values 
        to ensure perfect balance over a specific gameplay curve (default 10 hours).
        """
        total_transactions = dna.target_velocity * gameplay_hours
        base_faucet_yield = self.faucet_weights.get(dna.faucet_type, 1.0)
        base_sink_cost = self.sink_weights.get(dna.sink_type, 1.0)
        balance_ratio = base_faucet_yield / base_sink_cost
        max_allowed_earnings = dna.inflation_cap * gameplay_hours
        
        final_yield_per_event = base_faucet_yield
        
        if (final_yield_per_event * total_transactions) > max_allowed_earnings:
            final_yield_per_event = max_allowed_earnings / total_transactions
            
        final_cost_per_event = final_yield_per_event * balance_ratio

        return {
            "resource": dna.resource_name,
            "yield_per_event": round(final_yield_per_event, 2),
            "cost_per_event": round(final_cost_per_event, 2),
            "total_transactions_10hr": total_transactions,
            "balance_status": "Perfectly Balanced"
        }

    def process_transaction(self, dna: EconomyDNA, event: EconomicEvent) -> float:
        """
        THE ANTI-INFLATION GUARDRAIL (THE HARD CAP).
        Intercepts an economic event. If it's a faucet (earning), it checks 
        against the inflation cap. If it breaks the math, it throttles the reward to 0.
        """
        # Initialize tracking for this resource if it's the first time seeing it
        if dna.resource_name not in self.session_earnings:
            self.session_earnings[dna.resource_name] = 0.0
            # We assume a 1-hour session baseline for the guardrail math
            self.session_hours[dna.resource_name] = 1.0 

        # If it's a sink (negative amount, meaning spending), always allow it. Sinks are good for the economy!
        if event.amount <= 0:
            return event.amount

        # --- FAUCET CHECK (Earning Money) ---
        # Calculate the absolute mathematical limit for this session
        max_allowed_earnings = dna.inflation_cap * self.session_hours[dna.resource_name]
        
        # Check if adding this event breaks the hard cap
        if (self.session_earnings[dna.resource_name] + event.amount) > max_allowed_earnings:
            # EXPLOIT DETECTED! Throttle the reward to zero to protect the empire.
            print(f"[GUARDRAIL] Exploit blocked for {dna.resource_name}. Cap exceeded.")
            return 0.0

        # If safe, add to session tracker and allow the transaction
        self.session_earnings[dna.resource_name] += event.amount
        return event.amount

# Singleton instance for the rest of the architecture to use
economy_engine = EconomyEngine()