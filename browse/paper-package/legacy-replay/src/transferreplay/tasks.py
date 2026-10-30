"""Public task contracts only; no dynamics or private configuration."""
import math
from copy import deepcopy

CONTINUOUS_MENU=[[round(.6*math.cos(2*math.pi*k/12),12),round(.6*math.sin(2*math.pi*k/12),12)] for k in range(12)]+[[0.,0.]]
ROUTE_MENU=[[0,0],[1,0],[2,0]]

def task(family):
    common={'physical_actions_requested':1,'max_analysis_calls':3,
            'analysis_input':'provided_history_only','history_origin':'prespecified_privileged_reference_history',
            'diagnostic_table_optional':True}
    if family=='continuous':
        return common|{'family':'continuous','physical_horizon':32,'target_state_steps':[28,29,30,31,32],
            'target_radius':.05,'escape_radius':4.,'action_norm_limit':.6,'diagnostic_action_menu':deepcopy(CONTINUOUS_MENU)}
    if family=='route':
        return common|{'family':'route','physical_horizon':12,'goal_node':18,
            'state_fields':['node','remaining_fuel'],'action_vectors':deepcopy(ROUTE_MENU),
            'advance_by_action':[1,2,3],'next_node':'min(18,node+advance)',
            'success':'reach node 18 within 12 total actions without negative fuel',
            'edge_cost':'unknown positive stationary integer function of node and action',
            'diagnostic_action_menu':deepcopy(ROUTE_MENU)}
    raise ValueError('unknown family')

def valid_action(family,a):
    if type(a) is not list or len(a)!=2 or any(type(x) not in (int,float) or not math.isfinite(x) for x in a):return False
    if family=='continuous':return math.hypot(*a)<=.6+1e-9
    if family=='route':return a in ROUTE_MENU
    return False
