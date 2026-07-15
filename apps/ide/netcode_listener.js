import { createClient } from '@supabase/supabase-js'

// ==========================================
// DAY 21: THE DETERMINISTIC CLIENT (FRONTEND SYNC)
// ==========================================

// 1. Connect to the Supabase Cloud (The Magic Bridge)
// Note: Replace these with your actual Supabase URL and Anon Key, 
// or pass them in via your frontend environment variables.
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'YOUR_SUPABASE_URL'
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'YOUR_SUPABASE_ANON_KEY'
const supabase = createClient(supabaseUrl, supabaseKey)

// Our single source of truth for the frontend. 
// React and Three.js will constantly read from this pure JSON object.
let currentWorldState = { nodes: [], world_state: {} }

// 2. THE DETERMINISTIC MATH (Client-side patching)
// This is the exact JavaScript equivalent of our Python NetcodeEngine.
function applyDeltaToState(state, delta) {
    // We clone the state so React detects the change and redraws the screen
    let updatedState = JSON.parse(JSON.stringify(state))

    if (!updatedState.nodes) updatedState.nodes = []
    if (!updatedState.world_state) updatedState.world_state = {}

    // A. Remove deleted nodes (Surgical extraction)
    updatedState.nodes = updatedState.nodes.filter(
        node => !delta.removed_node_ids.includes(node.id)
    )

    // B. Add or update changed nodes (Surgical insertion)
    const nodeMap = {}
    updatedState.nodes.forEach(node => { nodeMap[node.id] = node })
    
    delta.changed_nodes.forEach(changedNode => {
        nodeMap[changedNode.id] = changedNode // Overwrites old data or adds brand new data
    })
    updatedState.nodes = Object.values(nodeMap)

    // C. Apply changed environmental tokens (Lighting, time of day, etc.)
    for (const [key, value] of Object.entries(delta.changed_tokens)) {
        updatedState.world_state[key] = value
    }

    return updatedState
}

// 3. THE SUPABASE REALTIME LISTENER (The Magic Ear)
export function startNetcodeListener(onStateUpdateCallback) {
    console.log("👂 Day 21: Deterministic Netcode Listener activated...")

    // Subscribe ONLY to INSERTS on the 'state_deltas' table.
    // This means we only wake up when the Server broadcasts a new Delta!
    const channel = supabase
        .channel('public:state_deltas')
        .on(
            'postgres_changes',
            { event: 'INSERT', schema: 'public', table: 'state_deltas' },
            (payload) => {
                console.log('📡 Delta received from cloud!', payload)
                
                // Extract the pure JSON delta from the database row
                const delta = payload.new.delta_data
                
                // Apply the math! Patch the local state instantly.
                currentWorldState = applyDeltaToState(currentWorldState, delta)
                
                // Tell React/Three.js to redraw the scene deterministically
                if (onStateUpdateCallback) {
                    onStateUpdateCallback(currentWorldState)
                }
            }
        )
        .subscribe()
        
    return channel
}