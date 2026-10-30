"""One parameter over the preserved rotating core. Evaluator-only state."""
from copy import deepcopy
import math
from . import physics_base as BASE_WORLD
from .records import digest

LEVELS=(.3,3.,6.,12.,18.)
STEPS=32
LIMIT=.6
TOLERANCE=.05
MARGIN=1e-10

def public(z):return [round(z.real,12),round(z.imag,12)]
def drift(z):return BASE_WORLD.drift(z)
def validate_action(value):
    if not isinstance(value,(list,tuple)) or len(value)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in value):
        raise ValueError('action must be two finite real numbers')
    a=complex(*value)
    if abs(a)>LIMIT+1e-9:raise ValueError('action norm exceeds 0.6')
    return a*LIMIT/abs(a) if abs(a)>LIMIT else a

def score(status,radii,tolerance=TOLERANCE):
    if status not in ('completed','escaped','participant_give_up'):return None
    return status=='completed' and len(radii)==STEPS and all(r<=tolerance+MARGIN for r in radii[-5:])

class Episode:
    def __init__(self,w):
        if set(w)!={'world_id','phi0','omega','coupling','mechanism_version'}:raise ValueError('world schema')
        if w['mechanism_version']!='rotating_core_kappa_axis_v1' or type(w['coupling']) not in (int,float) or w['coupling'] not in LEVELS:raise ValueError('unregistered core coupling')
        if any(type(w[k]) not in (int,float) or not math.isfinite(w[k]) for k in ('phi0','omega')):raise ValueError('configuration')
        self.world=deepcopy(w);self.z=1+0j;self.phi=w['phi0'];self.previous=0j
        self.states=[[1.,0.]];self.actions=[];self.trace=[];self.status='active';self.error=None
    def history(self):return deepcopy({'states':self.states,'actions':self.actions})
    def step(self,value):
        if self.status!='active':raise ValueError('closed episode')
        a=validate_action(value);before=public(self.z);private=[self.z.real,self.z.imag,self.phi]
        z,phi=BASE_WORLD.transition(self.z,self.phi,self.world['omega'],self.previous,a,self.world['coupling'])
        if not all(math.isfinite(v) for v in (z.real,z.imag,phi)):raise ArithmeticError('nonfinite transition')
        self.z,self.phi,self.previous=z,phi,a
        self.actions.append([a.real,a.imag]);self.states.append(public(z))
        row={'step':len(self.actions),'before':before,'after':public(z),'action':self.actions[-1],'radius':abs(z),'private_before':private,'private_after':[z.real,z.imag,phi]}
        self.trace.append(row)
        if abs(z)>4:self.status='escaped'
        elif len(self.actions)==STEPS:self.status='completed'
        return deepcopy({k:row[k] for k in ('step','before','action','after')}|{'status':self.status})
    def result(self):
        radii=[r['radius'] for r in self.trace]
        return {'world':deepcopy(self.world),'world_sha256':digest(self.world),'status':self.status,'error':self.error,'steps':len(radii),'success_005':score(self.status,radii),'peak_radius':max([1.]+radii),'last_five_max_radius':max(radii[-5:]) if len(radii)==32 else None,'public_history':self.history(),'trajectory':deepcopy(self.trace)}
