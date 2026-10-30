"""Recorded candidate computations; no provider, refit or privileged physics."""
import math
from copy import deepcopy

calls = {}
checks = []

def check(name, value):
    checks.append({"check": name, "passed": bool(value)})
    if not value:
        raise ValueError(name)

def near(x, y, tol=1e-8):
    return math.dist(x, y) <= tol


def angle(x, y):
    z = sum(a*b for a, b in zip(x, y))/(math.hypot(*x)*math.hypot(*y))
    return math.degrees(math.acos(max(-1.0, min(1.0, z))))


def features(s, kind, t, family):
    x, y = s
    if family == 't6' and kind == 'tanh':
        a, b = math.tanh(x), math.tanh(y)
        return [a, b], [[1-a*a, 0], [0, 1-b*b]]
    if kind == 'linear': return [x, y], [[1, 0], [0, 1]]
    if kind == 'affine': return [x, y, 1.0], [[1, 0], [0, 1], [0, 0]]
    if kind == 'forcing': return [x, y, math.sin(1.32*t), math.cos(1.32*t)], [[1, 0], [0, 1], [0, 0], [0, 0]]
    if kind == 'x3': return [x, y, x*x*x], [[1, 0], [0, 1], [3*x*x, 0]]
    if kind == 'quadratic': return [x, y, x*x, x*y, y*y], [[1, 0], [0, 1], [2*x, 0], [y, x], [0, 2*y]]
    if kind == 'cubic': return [x, y, x*x*x, y*y*y], [[1, 0], [0, 1], [3*x*x, 0], [0, 3*y*y]]
    if kind == 'radial':
        r = x*x+y*y
        return [x, y, r*x, r*y], [[1, 0], [0, 1], [3*x*x+y*y, 2*x*y], [2*x*y, x*x+3*y*y]]
    if kind == 'sin': return [x, y, math.sin(x), math.sin(y)], [[1, 0], [0, 1], [math.cos(x), 0], [0, math.cos(y)]]
    if kind == 'tanh':
        a, b = math.tanh(x), math.tanh(y)
        return [x, y, a, b], [[1, 0], [0, 1], [1-a*a, 0], [0, 1-b*b]]
    raise ValueError('Unknown candidate feature family')


def matrix(m, t):
    if m['family'] == 't6': return m['B']
    c = m['phase_coef']; z = t-8
    ph = c[0]+t*c[1] if t < m['split'] else c[2]+z*c[3]+(z*z*c[4] if m['curve'] else 0.0)
    co, si = math.cos(ph), math.sin(ph); g = m['gain']
    return [[g*co, -g*si], [g*si, g*co]]


def step(m, s, u, t):
    calls['candidate_step_evaluations'] += 1
    f, D = features(s, m['kind'], t, m['family']); C = m['C']; B = matrix(m, t)
    v = [s[d]+sum(a*b for a, b in zip(f, C[d]))+B[d][0]*u[0]+B[d][1]*u[1] for d in range(2)]
    J = [[(1.0 if d == j else 0.0)+sum(C[d][i]*D[i][j] for i in range(len(f))) for j in range(2)] for d in range(2)]
    if not all(math.isfinite(z) for z in v + [z for row in J for z in row]):
        raise ArithmeticError('nonfinite_candidate_transition')
    return v, J


def project(z):
    out = list(z)
    for j in range(0, len(z), 2):
        r = math.hypot(z[j], z[j+1])
        if r > 0.6: out[j], out[j+1] = z[j]*0.6/r, z[j+1]*0.6/r
    return out


def unpack(z, k, N):
    return [[z[0], z[1]]]+[[z[2+2*(k*(N-1)+i)], z[3+2*(k*(N-1)+i)]] for i in range(N-1)]


def evaluate(z, ms, pen, grad, S, n, N):
    total = 0.0; gg = [0.0]*len(z) if grad else None; paths = []
    for k, m in enumerate(ms):
        us = unpack(z, k, N); states = [list(S)]; js = []; ds = []; cost = 0.0
        for i in range(N):
            st, J = step(m, states[-1], us[i], n+i); states.append(st); js.append(J)
            r2 = st[0]*st[0]+st[1]*st[1]; w = 1.0 if n+i+1 >= 28 else 0.0001
            excess = max(0.0, r2-14.44)
            cost += w*r2+pen*excess*excess+0.00001*(us[i][0]**2+us[i][1]**2)
            ds.append([(2*w+4*pen*excess)*st[0], (2*w+4*pen*excess)*st[1]])
        total += cost/len(ms); paths.append(states)
        if grad:
            lam = [0.0, 0.0]
            for i in range(N-1, -1, -1):
                B = matrix(m, n+i)  # source T6 constant matrix; T4 time-dependent extension
                lam = [lam[d]+ds[i][d] for d in range(2)]
                du = [(B[0][d]*lam[0]+B[1][d]*lam[1]+0.00002*us[i][d])/len(ms) for d in range(2)]
                off = 0 if i == 0 else 2+2*(k*(N-1)+i-1)
                gg[off] += du[0]; gg[off+1] += du[1]
                J = js[i]; lam = [J[0][d]*lam[0]+J[1][d]*lam[1] for d in range(2)]
    if not math.isfinite(total) or (grad and not all(math.isfinite(x) for x in gg)):
        raise ArithmeticError('nonfinite_objective_or_gradient')
    return total, gg, paths


def optimize(ms, S, n, iters=1000, pen=10.0):
    calls['optimizer_invocations'] += 1
    N = 32-n; z = [0.44, 0.40]
    for m in ms:
        s, _ = step(m, S, z, n)
        for i in range(1, N):
            B = matrix(m, n+i); det = B[0][0]*B[1][1]-B[0][1]*B[1][0]
            v, _ = step(m, s, [0.0, 0.0], n+i)
            u = project([(-B[1][1]*v[0]+B[0][1]*v[1])/det, (B[1][0]*v[0]-B[0][0]*v[1])/det])
            z += u; s, _ = step(m, s, u, n+i)
    z = project(z); y = list(z); theta = 1.0; L = 100.0
    best = z; bestval = evaluate(z, ms, pen, False, S, n, N)[0]
    for it in range(iters):
        fy, g, _ = evaluate(y, ms, pen, True, S, n, N); L = max(0.001, L*0.9)
        for bt in range(45):
            cand = project([v-d/L for v, d in zip(y, g)])
            fc, _, _ = evaluate(cand, ms, pen, False, S, n, N)
            dd = [a-b for a, b in zip(cand, y)]
            upper = fy+sum(a*b for a, b in zip(g, dd))+0.5*L*sum(a*a for a in dd)
            if fc <= upper+1e-8*(1+abs(fy)): break
            L *= 2
        if fc < bestval: bestval = fc; best = list(cand)
        theta2 = (1+math.sqrt(1+4*theta*theta))/2
        y = [a+(theta-1)/theta2*(a-b) for a, b in zip(cand, z)]
        z = cand; theta = theta2
        if (it+1) % 250 == 0: z = list(best); y = list(best); theta = 1.0
    val, _, paths = evaluate(best, ms, pen, True, S, n, N)
    return {'status': 'computed', 'cost': val, 'first_action': best[:2], 'iterations': iters, 'penalty': pen,
            'candidate_ids': [m['id'] for m in ms], 'candidate_max_norms': [max(math.hypot(*s) for s in p) for p in paths],
            'candidate_target_norms': [[math.hypot(*p[i]) for i in range(28-n, N+1)] for p in paths]}


def attempt(ms, S, n, iters):
    try: return optimize(ms, S, n, iters)
    except (ArithmeticError, ValueError) as e:
        return {'status': 'unresolved_numeric', 'error_type': type(e).__name__, 'error': str(e), 'candidate_ids': [m['id'] for m in ms]}


def one_step_model(m, S, n):
    f, _ = step(m, S, [0.0, 0.0], n)
    return {'f': f, 'B': matrix(m, n), 'parent': m['id'], 'weight': 1.0}


def predict(m, u):
    return [m['f'][d]+m['B'][d][0]*u[0]+m['B'][d][1]*u[1] for d in range(2)]


def minimax(ms, grid, radius):
    scores = []
    for j in range(grid):
        a = [radius*math.cos(2*math.pi*j/grid), radius*math.sin(2*math.pi*j/grid)]
        values = [math.hypot(*predict(m, a)) for m in ms]
        scores.append((max(values), j, a))
    best = min(scores, key=lambda v: v[0])
    return {'action': best[2], 'objective': best[0], 'grid': grid, 'radius': radius, 'selected_grid_index': best[1]}


def weighted(ms):
    v = [sum(m['weight']*(m['B'][0][d]*m['f'][0]+m['B'][1][d]*m['f'][1]) for m in ms) for d in range(2)]
    r = math.hypot(*v)
    a = [-0.6*x/r for x in v]
    score = sum(m['weight']*sum(x*x for x in predict(m, a)) for m in ms)/sum(m['weight'] for m in ms)
    return {'action': a, 'objective': score, 'radius': 0.6, 'weight_scope': 'parent LOO weights, equally divided among parent scenarios'}


def rotation(ph, gain=1.0):
    c, s = math.cos(ph), math.sin(ph)
    return [[gain*c, -gain*s], [gain*s, gain*c]]

def compute(data):
    global calls, checks
    calls = {'candidate_step_evaluations': 0, 'optimizer_invocations': 0, 'new_llm_requests': 0, 'parameter_refits': 0, 'physical_steps': 0}
    checks = []
    vals = {int(t): deepcopy(value) for t, value in data['values'].items()}
    actions = {int(t): value for t, value in data['actions'].items()}
    history = data['boundary01_history']
    S = history['states'][-1]
    n = len(history['actions'])
    check('boundary01_step', n == 11)
    pools = {
        'A1': [{**deepcopy(m), 'family': 't4', 'id': f't4-{i}', 'C': m['drift_coef']} for i, m in enumerate(vals[4]['models'][:8])],
        'A2': [{**deepcopy(m), 'family': 't6', 'id': f't6-{i}'} for i, m in enumerate(vals[6]['models'])]
    }
    # Analytic state and control derivatives vs finite differences at public states.
    for ms in pools.values():
        for m in ms:
            u = [0.12, -0.13]; v, J = step(m, S, u, n)
            for j in range(2):
                plus = list(S); minus = list(S); plus[j] += 1e-5; minus[j] -= 1e-5
                vp, _ = step(m, plus, u, n); vm, _ = step(m, minus, u, n)
                check(m['id']+f'_state_derivative_{j}', all(abs((vp[d]-vm[d])/2e-5-J[d][j]) < 1e-6*(1+abs(J[d][j])) for d in range(2)))
            z = [0.12, -0.13, -0.14, 0.15]; _, g, _ = evaluate(z, [m], 10.0, True, S, n, 2)
            for j in range(4):
                zp, zm = list(z), list(z); zp[j] += 1e-5; zm[j] -= 1e-5
                gp = (evaluate(zp, [m], 10.0, False, S, n, 2)[0]-evaluate(zm, [m], 10.0, False, S, n, 2)[0])/2e-5
                check(m['id']+f'_objective_derivative_{j}', abs(gp-g[j]) < 1e-5*(1+abs(g[j])))
    one = {key: [one_step_model(m, S, n) for m in ms] for key, ms in pools.items()}
    for m, d in zip(pools['A1'], one['A1']):
        check(m['id']+'_one_step_drift', near(d['f'], [S[i]+m['drift'][i] for i in range(2)], 1e-10))
        check(m['id']+'_one_step_phase', all(abs(x-y)<1e-10 for r1, r2 in zip(d['B'], rotation(math.radians(m['next_angle_deg']))) for x,y in zip(r1,r2)))
    cells = []; full_plans = {}
    def add(case, ident, group, action, detail=None):
        cells.append({'case': case, 'id': ident, 'group': group, 'status': 'computed' if action is not None else 'unresolved_numeric', 'action': action, 'details': detail or {}})
    for key, ms in pools.items():
        mm = minimax(one[key], 720, 0.6)
        add('boundary-01',key+'-R1','primary',mm['action'],mm)
        plans = [attempt([m], S, n, 1000) for m in ms]; full_plans[key] = plans
        if all(p['status'] == 'computed' for p in plans):
            ix = min(range(len(plans)), key=lambda j: plans[j]['cost']); p = plans[ix]
            add('boundary-01',key+'-R2star','primary',p['first_action'],{'researcher_completed_selection':True,'selected_candidate':ms[ix]['id'],'cost':p['cost']})
        else:
            add('boundary-01',key+'-R2star','primary',None,{'researcher_completed_selection':True,'failed_candidates':[p['candidate_ids'] for p in plans if p['status']!='computed']})
        refined = minimax(one[key],2880,0.6);add('boundary-01',key+'-R1-refined','grid_sensitivity',refined['action'],refined)
        joint = attempt(ms,S,n,1400);full_plans[key+'-joint']=joint
        add('boundary-01',key+'-joint','selection_completion_sensitivity',joint.get('first_action'),joint)
    lookup = {(x['case'],x['id']):x for x in cells}
    check('native_t4_minimax_action',near(lookup['boundary-01','A1-R1']['action'],actions[4]))
    check('native_t4_minimax_value',abs(lookup['boundary-01','A1-R1']['details']['objective']-vals[4]['minimax_action'][0])<1e-8)
    for i,(p,old) in enumerate(zip(full_plans['A2'],vals[6]['individual_mpc'])):
        check(f'native_t6_plan{i}',p['status']=='computed' and near(p['first_action'],old['first_action'],1e-6) and math.isclose(p['cost'],old['cost'],rel_tol=1e-6,abs_tol=1e-6))
    check('native_t6_selected_action',near(lookup['boundary-01','A2-R2star']['action'],actions[6],1e-6))
    check('native_t6_joint',near(full_plans['A2-joint']['first_action'],vals[6]['shared_first_action_mpc']['first_action'],1e-6))

    scenarios = {'A1': [], 'A2': []}
    for i,m in enumerate(vals[2]['validated']):
        scenarios['A1'].append({'f':m['next_drift'],'B':rotation(m['next_phase']),'weight':1.0/(.0001+m['loo_rms']**2),'parent':f't2-{i}','scenario':f't2-{i}'})
    selected = [m for m in vals[8]['models'] if [m['drift'],m['phase'],m['free_gain']] in vals[8]['selected_models']]
    check('native_t8_models',len(selected)==11)
    for i,m in enumerate(selected):
        for mode in (0,1):
            for j,delta in enumerate((-.12,0.0,.12)):
                scenarios['A2'].append({'f':m['next_zero'],'B':rotation(m['next_phases_base_gate'][mode]+delta,m['gain']),'weight':1.0/(.0001+m['loo_rms']**2)/6,'parent':f't8-{i}','scenario':f't8-{i}-mode{mode}-delta{j}'})
    for key,ms in scenarios.items():
        w=weighted(ms);add('boundary-02',key+'-R1','primary',w['action'],w)
        mm=minimax(ms,1440,.599999999);add('boundary-02',key+'-R2','primary',mm['action'],mm)
        refined=minimax(ms,2880,.599999999);add('boundary-02',key+'-R2-refined','grid_sensitivity',refined['action'],refined)
    lookup={(x['case'],x['id']):x for x in cells}
    check('native_t2_weighted_action',near(lookup['boundary-02','A1-R1']['action'],actions[2]))
    check('native_t8_minimax_action',near(lookup['boundary-02','A2-R2']['action'],actions[8]))
    check('native_t8_minimax_value',abs(lookup['boundary-02','A2-R2']['details']['objective']-vals[8]['robust_choices']['worst_norm']['worst_norm'])<1e-9)
    # All single scenario and parent omissions; no selection by physical outcome.
    for i,m in enumerate(scenarios['A2']):
        q=minimax([x for j,x in enumerate(scenarios['A2']) if j!=i],1440,.599999999)
        add('boundary-02','omit-scenario-'+str(i),'single_scenario_omission',q['action'],{**q,'removed':m['scenario']})
    for parent in dict.fromkeys(m['parent'] for m in scenarios['A2']):
        q=minimax([x for x in scenarios['A2'] if x['parent']!=parent],1440,.599999999)
        add('boundary-02','omit-parent-'+parent,'parent_omission',q['action'],{**q,'removed':parent})
    native=lookup['boundary-02','A2-R2']['action']
    ranks=sorted([{'scenario':m['scenario'],'parent':m['parent'],'predicted_norm':math.hypot(*predict(m,native))} for m in scenarios['A2']],key=lambda z:z['predicted_norm'],reverse=True)
    check('predeclared91_cells',len(cells)==91)
    check('all_computed_actions_finite_in_bounds',all(c['action'] is None or all(math.isfinite(v) for v in c['action']) and math.hypot(*c['action'])<=.60000001 for c in cells))
    return {'cells': cells, 'plans_private': full_plans,
            'boundary02_scenarios_private': scenarios,
            'boundary02_native_worst_ranking_private': ranks,
            'counts': dict(calls), 'checks': list(checks)}
