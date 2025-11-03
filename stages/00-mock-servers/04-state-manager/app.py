"""
State Manager Service
Maintains global state consistency and entity lifecycles
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import json

app = FastAPI(title="State Manager Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class EntityType(str, Enum):
    USER = "user"
    ACCOUNT = "account"
    SESSION = "session"
    SYSTEM = "system"

class EntityStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    CLOSED = "closed"

# Models
class EntityState(BaseModel):
    entity_id: str
    entity_type: EntityType
    status: EntityStatus
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class StateTransition(BaseModel):
    entity_id: str
    from_status: EntityStatus
    to_status: EntityStatus
    reason: str
    timestamp: datetime

# Storage
entity_states: Dict[str, EntityState] = {}
state_history: List[StateTransition] = []

# State transition rules
VALID_TRANSITIONS = {
    EntityStatus.ACTIVE: [EntityStatus.SUSPENDED, EntityStatus.LOCKED],
    EntityStatus.SUSPENDED: [EntityStatus.ACTIVE, EntityStatus.CLOSED],
    EntityStatus.LOCKED: [EntityStatus.ACTIVE, EntityStatus.CLOSED],
    EntityStatus.CLOSED: []  # Terminal state
}

@app.get("/")
async def root():
    """Serve the web UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>State Manager</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
            .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
            .stat-card { background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center; }
            .stat-value { font-size: 24px; font-weight: bold; color: #2e7d32; }
            .controls { margin: 20px 0; display: flex; gap: 10px; flex-wrap: wrap; }
            select, input, button { padding: 10px; border-radius: 4px; border: 1px solid #ddd; }
            button { background: #4CAF50; color: white; cursor: pointer; border: none; }
            button:hover { background: #45a049; }
            .entities { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin-top: 20px; }
            .entity-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #fafafa; }
            .status-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .status-active { background: #4CAF50; color: white; }
            .status-suspended { background: #FF9800; color: white; }
            .status-locked { background: #f44336; color: white; }
            .status-closed { background: #9E9E9E; color: white; }
            .history { margin-top: 30px; }
            .history-item { background: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 3px solid #4CAF50; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 State Manager Service</h1>
            <p>Maintain global state consistency and entity lifecycles</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalEntities">0</div>
                    <div>Total Entities</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="activeEntities">0</div>
                    <div>Active</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="suspendedEntities">0</div>
                    <div>Suspended</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="transitions">0</div>
                    <div>Transitions</div>
                </div>
            </div>
            
            <div class="controls">
                <select id="entityType">
                    <option value="user">User</option>
                    <option value="account">Account</option>
                    <option value="session">Session</option>
                    <option value="system">System</option>
                </select>
                <input type="text" id="entityId" placeholder="Entity ID (auto-generated if empty)">
                <button onclick="createEntity()">Create Entity</button>
                <button onclick="loadEntities()">Refresh</button>
            </div>
            
            <div id="entities" class="entities"></div>
            
            <div class="history">
                <h2>Recent State Transitions</h2>
                <div id="history"></div>
            </div>
        </div>
        
        <script>
            async function createEntity() {
                const entityType = document.getElementById('entityType').value;
                const entityId = document.getElementById('entityId').value || `${entityType}_${Date.now()}`;
                
                const response = await fetch('/api/entities', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        entity_id: entityId,
                        entity_type: entityType,
                        status: 'active',
                        data: {
                            created_by: 'ui',
                            balance: entityType === 'account' ? 1000000 : undefined
                        }
                    })
                });
                
                if (response.ok) {
                    loadEntities();
                    document.getElementById('entityId').value = '';
                }
            }
            
            async function loadEntities() {
                const response = await fetch('/api/entities');
                const entities = await response.json();
                
                const container = document.getElementById('entities');
                container.innerHTML = entities.map(e => `
                    <div class="entity-card">
                        <h3>${e.entity_id}</h3>
                        <div>
                            <span class="status-badge status-${e.status}">${e.status.toUpperCase()}</span>
                            <span style="color: #666; font-size: 12px;">${e.entity_type}</span>
                        </div>
                        <div style="margin-top: 10px; font-size: 12px; color: #666;">
                            Updated: ${new Date(e.updated_at).toLocaleString()}
                        </div>
                        ${e.status !== 'closed' ? `
                            <div style="margin-top: 10px;">
                                <button onclick="transitionState('${e.entity_id}', 'suspended')">Suspend</button>
                                <button onclick="transitionState('${e.entity_id}', 'locked')">Lock</button>
                            </div>
                        ` : ''}
                    </div>
                `).join('');
                
                updateStats(entities);
            }
            
            async function transitionState(entityId, toStatus) {
                const response = await fetch(`/api/entities/${entityId}/transition`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        to_status: toStatus,
                        reason: 'Manual transition from UI'
                    })
                });
                
                if (response.ok) {
                    loadEntities();
                    loadHistory();
                }
            }
            
            async function loadHistory() {
                const response = await fetch('/api/history?limit=10');
                const history = await response.json();
                
                const container = document.getElementById('history');
                container.innerHTML = history.map(h => `
                    <div class="history-item">
                        <strong>${h.entity_id}</strong>: ${h.from_status} → ${h.to_status}
                        <br><small>${h.reason} (${new Date(h.timestamp).toLocaleString()})</small>
                    </div>
                `).join('');
            }
            
            function updateStats(entities) {
                document.getElementById('totalEntities').textContent = entities.length;
                document.getElementById('activeEntities').textContent = 
                    entities.filter(e => e.status === 'active').length;
                document.getElementById('suspendedEntities').textContent = 
                    entities.filter(e => e.status === 'suspended').length;
            }
            
            async function refreshStats() {
                const response = await fetch('/api/history');
                const history = await response.json();
                document.getElementById('transitions').textContent = history.length;
            }
            
            loadEntities();
            loadHistory();
            setInterval(() => { loadEntities(); loadHistory(); refreshStats(); }, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/entities", response_model=EntityState)
async def create_entity(entity: EntityState):
    """Create a new entity"""
    if entity.entity_id in entity_states:
        raise HTTPException(status_code=400, detail="Entity already exists")
    
    entity.created_at = datetime.now()
    entity.updated_at = datetime.now()
    entity_states[entity.entity_id] = entity
    
    return entity

@app.get("/api/entities", response_model=List[EntityState])
async def list_entities(entity_type: Optional[EntityType] = None):
    """List all entities"""
    entities = list(entity_states.values())
    
    if entity_type:
        entities = [e for e in entities if e.entity_type == entity_type]
    
    return entities

@app.get("/api/entities/{entity_id}", response_model=EntityState)
async def get_entity(entity_id: str):
    """Get specific entity state"""
    if entity_id not in entity_states:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity_states[entity_id]

@app.post("/api/entities/{entity_id}/transition")
async def transition_entity(entity_id: str, to_status: EntityStatus, reason: str = "Manual transition"):
    """Transition entity to new state"""
    if entity_id not in entity_states:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity = entity_states[entity_id]
    from_status = entity.status
    
    # Validate transition
    if to_status not in VALID_TRANSITIONS.get(from_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {from_status} to {to_status}"
        )
    
    # Record transition
    transition = StateTransition(
        entity_id=entity_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        timestamp=datetime.now()
    )
    state_history.append(transition)
    
    # Update entity
    entity.status = to_status
    entity.updated_at = datetime.now()
    
    return {"message": "Transition successful", "transition": transition}

@app.get("/api/history", response_model=List[StateTransition])
async def get_history(entity_id: Optional[str] = None, limit: int = 100):
    """Get state transition history"""
    history = state_history
    
    if entity_id:
        history = [h for h in history if h.entity_id == entity_id]
    
    return list(reversed(history[-limit:]))

@app.get("/api/stats")
async def get_stats():
    """Get state statistics"""
    total = len(entity_states)
    by_status = {}
    by_type = {}
    
    for entity in entity_states.values():
        by_status[entity.status] = by_status.get(entity.status, 0) + 1
        by_type[entity.entity_type] = by_type.get(entity.entity_type, 0) + 1
    
    return {
        "total_entities": total,
        "by_status": by_status,
        "by_type": by_type,
        "total_transitions": len(state_history)
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "state-manager",
        "entities": len(entity_states),
        "transitions": len(state_history)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
