"""Exact scalar constants from the archived numerical proof. No runtime probing."""
from fractions import Fraction as F
import json
U=F(1,2**53)
D=F(1,2**1075)  # half smallest subnormal under gradual underflow
H=16*U
B=32*U+D
L=F.from_float(.6)
BETA=F.from_float(.015)
P=F(1,2**30)
DELTA=F(1,2**30)
SLACK=F(1,10**9)
def number(x):
    approx=float(x)
    return {'exact':str(x),'approx':None if x and approx==0 else approx,
            'approx_underflows_binary64':bool(x and approx==0)}
def exact(x):return F.from_float(x)

def budget(p,delta):
    return 5*BETA*(10*H+H*H+p)+18*B+8*U+delta*(L+8*U)

def gate(p,delta,uniform_pow=False,uniform_rotation=False,historical_binding=False):
    if p<0 or delta<0 or p>1 or delta>1 or budget(p,delta)>=SLACK:
        return 'insufficient_budget'
    if not (uniform_pow and uniform_rotation and historical_binding):
        return 'open_missing_premise'
    return 'conditional_bound_sufficient'

def constants():
    checks={}
    def check(name,value):
        assert value,name
        checks[name]=True
    # If stored exponent difference is >27, b/a < 2^-27 even for
    # subnormals. sqrt(1+t) <= 1+t/2 then costs < 2^-55 = u/4.
    check('dropped_component_factor',F(1,2**55)==U/4)
    check('hypot_lower_factor',(1-U/4)*(1-U)**2>=1-3*U)
    check('hypot_upper_factor',(1+U)**2<=1+3*U)
    check('accepted_state_true_norm_lt_5',(4+D)/(1-3*U)<5)
    check('accepted_action_true_norm_lt_1',(L+F(1,10**9)+D)/(1-3*U)<1)
    check('hypot_abs_error_below_H',15*U+D<H)
    # Accepted unscaled action: computed norm <= L.
    check('unscaled_action_excess',(L+D)/(1-3*U)<L+8*U)
    # For a rescaled action h>L, r>1/2 and h>1/2; scale/divide
    # each component with normal IEEE rounding plus subnormal allowance D.
    check('rescaled_action_r_gt_half',(L-D)/(1+3*U)>F(1,2))
    rescaled=L*(1+U)**2/(1-3*U-2*D)+3*D*(1+U)+F(3,2)*D
    check('rescaled_action_excess',rescaled<L+8*U)
    check('sqrt2_envelope',F(3,2)**2>2)
    # Conservative operand ranges for all drift/rotation operations with
    # the chosen P/delta premises. No pow call is treated as a hardware mul.
    check('pow_output_abs_lt_26',(5+H)**2+P<26)
    check('multiplier_abs_lt_2',exact(1.06)+BETA*26+2*B<2)
    check('drift_component_abs_lt_11',2*5+exact(.12)+2*B<11)
    check('rotation_factor_norm_lt_2',1+DELTA<2)
    check('applied_action_norm_lt_1',L+8*U<1)
    check('rotation_product_exact_intermediate_abs_lt_5',4+B<5)
    check('final_add_exact_intermediate_abs_lt_16',11+4+2*B<16)
    check('basic_rounding_bound_for_abs_lt_32',32*U+D==B)
    check('total_error_below_archived_slack',budget(P,DELTA)<SLACK)
    check('minimum_archived_gap_beats_norm_error',F(371,10000)>H)
    return {'checks':checks,'u':number(U),'subnormal_allowance':number(D),
            'hypot_H':number(H),'basic_B':number(B),'pow_absolute_premise':number(P),
            'rotation_norm_excess_premise':number(DELTA),'normalization_bound':number(L+8*U),
            'total_E':number(budget(P,DELTA)),'archived_slack':number(SLACK),
            'slack_fraction_used':number(budget(P,DELTA)/SLACK),
            'scope':'Exact arithmetic checks of analytic inequalities, not exhaustive path enumeration or a proof assistant.'}

def exponent_ranges():
    # Exhaust exponent classes using interval exponents, not sampled mantissas.
    # A nonzero subnormal is in [2^-1074,2^-1022); a normal with field e
    # is in [2^(e-1023),2^(e-1022)). The upper endpoints are strict.
    for ea in range(2047):
        shift=768 if ea<539 else (-768 if ea>=1534 else 0)
        alo=-1074 if ea==0 else ea-1023
        ahi=-1022 if ea==0 else ea-1022
        emin=max(0,ea-27)
        blo=-1074 if emin==0 else emin-1023
        assert alo+shift>=-1022 and blo+shift>=-1022
        assert ahi+shift<=1024
        assert 2*(alo+shift)>=-1022   # squared larger input normal
        assert 2*(ahi+shift)+1<=1023 # sum and its rounding finite
        if ea>=28:
            eb=ea-28
            bhi=-1022 if eb==0 else eb-1022
            assert bhi-alo<=-27     # discarded b/a < 2^-27
    return {'finite_biased_exponent_classes':2047,'all_scale_and_core_range_inequalities_passed':True,
            'method':'Integer endpoint inequalities for whole exponent intervals, including nonzero subnormals; zero branch is exact.',
            'not_a_formal_binary_semantics_proof':True}


if __name__=="__main__":
 r=constants();e=exponent_ranges()
 assert gate(P,DELTA)=="open_missing_premise"
 assert gate(F(1),F(1))=="insufficient_budget"
 print(json.dumps({"passed":True,"exact_inequalities":len(r["checks"]),"exponent_classes":e["finite_biased_exponent_classes"],"conditional_error_budget":r["total_E"]["approx"],"uniform_library_proof":False,"historical_runtime_attestation":False}))
