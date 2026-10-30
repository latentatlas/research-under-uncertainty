"""Operator-only fresh histories. Never imported by the participant carrier.

Fixed seed, two instances per existing family; no model-dependent selection.
Reference controllers are privileged local preparation, not model behavior.
"""
from copy import deepcopy
import cmath
import math
import random
from common import HERE, ROOT, canonical, digest, read_json, new_json
from private_worlds import route
from private_worlds.tasks import CONTINUOUS_MENU, ROUTE_MENU
from private_worlds.continuous import physics as continuous

SEED=2026103001

def action_identity(family, vector):
    return digest({'family':family,'action':vector})

def packet(case_id, family, history):
    menu=deepcopy(CONTINUOUS_MENU if family=='continuous' else ROUTE_MENU)
    task=({'family':family,'physical_horizon':32,'target_steps':[28,29,30,31,32],
           'target_radius':.05,'escape_radius':4,'action_norm_limit':.6}
          if family=='continuous' else
          {'family':family,'physical_horizon':12,'goal_node':18,'minimum_fuel':0,
           'advance_by_action':[1,2,3],'edge_cost':'unknown positive stationary integer by departure node and action'})
    return {'case_id':case_id,'family':family,'history':deepcopy(history),'physical_step':len(history['actions']),
        'remaining_physical_steps':task['physical_horizon']-len(history['actions']), 'task':task,
        'action_menu':menu,'action_ids':[action_identity(family,a) for a in menu],
        'menu_sha256':digest(menu),'history_sha256':digest(history)}

def witness(e):
    e=deepcopy(e)
    while e.status=='active':
        a=-continuous.drift(e.z)*cmath.exp(-1j*e.phi)
        if abs(a)>.6: a*=.6/abs(a)
        e.step([a.real,a.imag])
    r=e.result()
    return {'success':r['success_005'] is True,'final_result_sha256':digest(r), 'result':r}

def generate():
    rng=random.Random(SEED); bundles=[]; private=[]
    for index in range(2):
        h=f'h{index+1:02d}'
        world={'world_id':f'pp-{h}','phi0':rng.uniform(-math.pi,math.pi),'omega':rng.uniform(-.55,.55),
               'coupling':(.3,3.)[index],'mechanism_version':'rotating_core_kappa_axis_v1'}
        e=continuous.Episode(world)
        for _ in range(6):
            def radius(a):
                t=deepcopy(e);t.step(a);return abs(t.z)
            e.step(min(CONTINUOUS_MENU,key=radius))
        source=packet(h+'-source','continuous',e.history())
        targets=[]; witnesses=[witness(e)]
        for j,k in enumerate((0,6),1):
            t=deepcopy(e);t.step(CONTINUOUS_MENU[k])
            assert t.status=='active'
            targets.append(packet(f'{h}-target{j}','continuous',t.history()));witnesses.append(witness(t))
        assert all(w['success'] for w in witnesses), 'prespecified reference not viable; stop, do not resample'
        bundles.append({'history_id':h,'source':source,'targets':targets})
        private.append({'history_id':h,'world':world,'source_trajectory':e.result(),
                        'reference_witnesses':witnesses,'exogenous_branch_menu_indices':[0,6]})
    for index in range(2):
        h=f'h{index+3:02d}'
        world={'base':[rng.randint(1,3) for _ in range(3)],'period':[rng.randint(2,5) for _ in range(3)],
               'offset':[rng.randint(0,4) for _ in range(3)]}
        prefix=[0,1,2,0];node=0;spent=0
        for k in prefix:
            spent+=route.cost(world,node,[k,0]);node+=k+1
        table=route.value_table(world);route.verify_table(world,table)
        # Fixed preparation rule: all prescribed source/branch states retain a known feasible continuation.
        branch_requirements=[route.cost(world,node,[k,0])+table[7][min(18,node+k+1)] for k in (0,2)]
        world['initial_fuel']=spent+max([table[8][node]]+branch_requirements)+3
        states=[[0,world['initial_fuel']]];actions=[]
        for k in prefix:
            a=[k,0];states.append(route.transition(world,states[-1],a));actions.append(a)
        history={'states':states,'actions':actions}
        source=packet(h+'-source','route',history);targets=[]
        refs=[route.assess(world,states[-1],4)]
        for j,k in enumerate((0,2),1):
            th=deepcopy(history);a=[k,0];th['states'].append(route.transition(world,th['states'][-1],a));th['actions'].append(a)
            targets.append(packet(f'{h}-target{j}','route',th));refs.append(route.assess(world,th['states'][-1],5))
        assert all(x['witness_success'] for x in refs)
        bundles.append({'history_id':h,'source':source,'targets':targets})
        private.append({'history_id':h,'world':world,'reference_witnesses':refs,'exogenous_branch_menu_indices':[0,2]})
    old=[read_json(p)['history'] for p in (ROOT/'outputs/research-ruu-followup-design-20261028-01/inputs').glob('*.json')]
    old_hashes={digest(x) for x in old}
    all_packets=[p for b in bundles for p in [b['source']]+b['targets']]
    assert len({p['history_sha256'] for p in all_packets})==12
    assert not old_hashes & {p['history_sha256'] for p in all_packets}
    return bundles,private

if __name__=='__main__':
    bundles,private=generate()
    for b,p in zip(bundles,private):
        new_json(HERE/'packets'/(b['history_id']+'.json'),b)
        new_json(HERE/'private'/(b['history_id']+'.json'),p)
    new_json(HERE/'CASE-GENERATION.json',{'seed':SEED,'histories':4,'packets':12,'new_family':False,
       'fresh_against_four_published_histories':True,'generated_before_model_outputs':True,
       'operator_reference_viable_states':12,'purposeful_feasibility_sample_not_population':True,
       'branch_actions':'fixed exogenous actions; neither source choice nor model-dependent intervention',
       'physics_scope':'new local preparation on previously disclosed task families; no archived participant programs executed'})
    print(canonical({'histories':4,'packets':12,'reference_viable_states':12,'model_requests':0}))
