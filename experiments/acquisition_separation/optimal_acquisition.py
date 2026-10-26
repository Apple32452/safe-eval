"""Tiny, uniformly valid acquisition policies with exact cost certificates."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from itertools import product

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

GRAPHS = {'star': ((0, 1), (0, 2)), 'triangle': ((0, 1), (0, 2), (1, 2))}
KINDS = ('cell', 'row_uniform', 'common_retirement')
PRIORS = ('independent', 'monotone', 'opposed', 'one_hot')


def sign(x):
    return (x > 0)-(x < 0)


def column_prior(name):
    columns = tuple(product((0, 1), repeat=3))
    if name == 'independent':
        p = (F(1, 5), F(1, 2), F(4, 5))
        return {c: np.prod([p[v] if c[v] else 1-p[v] for v in range(3)])
                for c in columns}
    structured = {
        'monotone': {(0,0,0): F(1,5), (0,0,1): F(3,10),
                     (0,1,1): F(3,10), (1,1,1): F(1,5)},
        'opposed': {(1,0,0): F(1,5), (0,1,1): F(4,5)},
        'one_hot': {(1,0,0): F(1,10), (0,1,0): F(3,10), (0,0,1): F(3,5)},
    }[name]
    return {c: F(9,10)*structured.get(c, F(0))+F(1,80) for c in columns}


@dataclass(frozen=True)
class Action:
    name: tuple
    cost: int
    children: tuple = ()  # (child state key while building; then child id, weight)
    answer: tuple | None = None


class Model:
    def __init__(self, n=2, graph='star', kind='cell'):
        if kind not in KINDS or graph not in GRAPHS or n < 1:
            raise ValueError('Unknown finite acquisition problem')
        self.n, self.graph, self.kind = n, graph, kind
        self.worlds = tuple(product((0, 1), repeat=3*n))
        self.truth = tuple(tuple(sign(sum(w[a*n:(a+1)*n])-sum(w[b*n:(b+1)*n]))
                                 for a,b in GRAPHS[graph]) for w in self.worlds)
        root = ((-1,)*(3*n), 0, 7)
        raw, queue = {}, [root]
        while queue:
            state = queue.pop()
            if state in raw: continue
            actions = self.query_actions(state)
            raw[state] = actions
            queue.extend(child for action in actions for child, _ in action.children
                         if child not in raw)
        self.states = tuple(sorted(raw, key=lambda s: (sum(x != -1 for x in s[0]), s)))
        self.index = {s: i for i,s in enumerate(self.states)}
        self.root = self.index[root]
        self.compatible = tuple(tuple(i for i,w in enumerate(self.worlds)
                                       if all(x == -1 or x == y for x,y in zip(s[0], w)))
                                for s in self.states)
        self.actions = []
        for k, state in enumerate(self.states):
            acts = [Action(a.name, a.cost,
                           tuple((self.index[c], p) for c,p in a.children)) for a in raw[state]]
            answers = sorted({self.truth[w] for w in self.compatible[k]})
            acts.extend(Action(('stop',)+answer, 0, answer=answer) for answer in answers)
            self.actions.append(tuple(acts))
        self.actions = tuple(self.actions)

    def query_actions(self, state):
        obs, opened, active = state
        unknown = [c for c,x in enumerate(obs) if x == -1]
        actions = []
        if self.kind in ('cell', 'row_uniform'):
            groups = [(('cell', c), [c]) for c in unknown] if self.kind == 'cell' else [
                (('row', v), [c for c in unknown if c//self.n == v]) for v in range(3)]
            for name, cells in groups:
                if not cells: continue
                children = []
                for c in cells:
                    for y in (0, 1):
                        changed = list(obs); changed[c] = y
                        children.append(((tuple(changed), 0, 7), F(1, len(cells))))
                actions.append(Action(name, 1, tuple(children)))
        else:
            items = [i for i in range(self.n) if not opened & (1 << i)]
            if not items: return actions
            for subset in range(1, 8):
                if subset & active != subset: continue
                rows = [v for v in range(3) if subset & (1 << v)]
                children = []
                for item in items:
                    for values in product((0, 1), repeat=len(rows)):
                        changed = list(obs)
                        for v,y in zip(rows, values):
                            if changed[v*self.n+item] != -1:
                                raise AssertionError('Repeated common-item cell')
                            changed[v*self.n+item] = y
                        children.append(((tuple(changed), opened | (1 << item), subset),
                                         F(1, len(items))))
                actions.append(Action(('block', subset), len(rows), tuple(children)))
        return actions

    def probabilities(self, name):
        p = column_prior(name)
        result = []
        for w in self.worlds:
            q = F(1)
            for item in range(self.n): q *= p[tuple(w[v*self.n+item] for v in range(3))]
            result.append(q)
        if sum(result) != 1 or min(result) <= 0:
            raise AssertionError('Design must have full support and total mass one')
        return tuple(result)

    def masses(self, probabilities):
        return tuple(sum((probabilities[w] for w in ids), F(0)) for ids in self.compatible)


def linear_program(model, probabilities, alpha):
    masses = model.masses(probabilities)
    entries = tuple((s,a) for s,acts in enumerate(model.actions) for a in range(len(acts)))
    er, ec, ev, ur, uc = [], [], [], [], []
    objective = []
    for col, (s,a) in enumerate(entries):
        action = model.actions[s][a]
        er.append(s); ec.append(col); ev.append(1.)
        for child,p in action.children:
            er.append(child); ec.append(col); ev.append(-float(p))
        if action.answer is not None:
            for w in model.compatible[s]:
                if action.answer != model.truth[w]: ur.append(w); uc.append(col)
        objective.append(float(masses[s]*action.cost))
    eq = coo_matrix((ev, (er, ec)), shape=(len(model.states), len(entries))).tocsr()
    ub = coo_matrix((np.ones(len(ur)), (ur, uc)),
                    shape=(len(model.worlds), len(entries))).tocsr()
    rhs = np.zeros(len(model.states)); rhs[model.root] = 1
    result = linprog(objective, A_ub=ub, b_ub=np.full(len(model.worlds), float(alpha)),
                     A_eq=eq, b_eq=rhs, bounds=(0, None), method='highs',
                     options={'primal_feasibility_tolerance': 1e-9,
                              'dual_feasibility_tolerance': 1e-9})
    if not result.success: raise RuntimeError(result.message)
    return result, entries


def default_action(model, s):
    # Used only when a solver assigns zero flow; exact evaluation still checks it.
    for a,action in enumerate(model.actions[s]):
        if action.children: return a
    return 0


def rational_policy(model, result, entries):
    raw = [[] for _ in model.states]
    for x,(s,a) in zip(result.x, entries):
        q = F(float(max(0., x))).limit_denominator(10**9)
        if q: raw[s].append((a,q))
    policy = []
    for s, row in enumerate(raw):
        mass = sum((p for _,p in row), F(0))
        policy.append(tuple((a,p/mass) for a,p in row) if mass else
                      ((default_action(model,s), F(1)),))
    return tuple(policy)


def evaluate_policy(model, policy):
    """Exact recursion for each fixed world, without using the LP equations."""
    costs, errors, reached = [], [], set()
    for w, world in enumerate(model.worlds):
        @lru_cache(None)
        def visit(s):
            reached.add(s)
            if sum((p for _,p in policy[s]), F(0)) != 1:
                raise AssertionError('Policy probabilities do not sum to one')
            cost = error = terminal_mass = F(0)
            for a,p in policy[s]:
                if p <= 0: raise AssertionError('Nonpositive action probability')
                action = model.actions[s][a]
                if action.answer is not None:
                    error += p*int(action.answer != model.truth[w]); terminal_mass += p
                else:
                    transitions = [(c,t) for c,t in action.children
                                   if w in model.compatible[c]]
                    if sum((t for _,t in transitions), F(0)) != 1:
                        raise AssertionError('Wrong fixed-world transition probabilities')
                    cost += p*action.cost
                    for c,t in transitions:
                        cc,ee,tt = visit(c)
                        cost += p*t*cc; error += p*t*ee; terminal_mass += p*t*tt
            return cost,error,terminal_mass
        c,e,t = visit(model.root)
        if t != 1 or c < 0 or c > 3*model.n:
            raise AssertionError('Invalid terminal mass or purchased cost')
        costs.append(c); errors.append(e)
    return tuple(costs),tuple(errors),reached


def zero_error_optimum(model, probabilities):
    masses = model.masses(probabilities)
    value, policy = [None]*len(model.states), [None]*len(model.states)
    for s in reversed(range(len(model.states))):
        logical = len({model.truth[w] for w in model.compatible[s]}) == 1
        candidates = []
        for a,action in enumerate(model.actions[s]):
            if action.answer is not None:
                if logical: candidates.append((F(0),a))
            elif all(value[c] is not None for c,_ in action.children):
                candidates.append((masses[s]*action.cost+
                                   sum((p*value[c] for c,p in action.children), F(0)), a))
        if candidates:
            value[s],best = min(candidates)
            policy[s] = ((best,F(1)),)
        else:
            policy[s] = ((default_action(model,s),F(1)),)
    if value[model.root] is None: raise AssertionError('No zero-error complete policy')
    return value[model.root],tuple(policy)


def dual_bound(model, probabilities, alpha, penalties):
    """Exact Bellman dual feasible for ANY nonnegative error penalties."""
    if min(penalties) < 0: raise AssertionError('Negative error penalty')
    masses = model.masses(probabilities)
    values = [F(0)]*len(model.states)
    for s in reversed(range(len(model.states))):
        candidates = []
        for action in model.actions[s]:
            if action.answer is not None:
                candidates.append(sum((penalties[w] for w in model.compatible[s]
                                       if action.answer != model.truth[w]), F(0)))
            else:
                candidates.append(masses[s]*action.cost+
                                  sum((p*values[c] for c,p in action.children), F(0)))
        values[s] = min(candidates)
    return values[model.root]-alpha*sum(penalties),tuple(values)


def solve(model, prior, alpha):
    probabilities = model.probabilities(prior)
    result,entries = linear_program(model, probabilities, alpha)
    penalties = tuple(F(float(max(0.,-x))).limit_denominator(10**9)
                      for x in result.ineqlin.marginals)
    if alpha == 0:
        lower,policy = zero_error_optimum(model, probabilities)
        if abs(float(lower)-result.fun) > 1e-7:
            raise AssertionError('Zero-error DP and independent LP disagree')
        lower_type = 'exact_zero_error_dynamic_program'
    else:
        policy = rational_policy(model, result, entries)
        lower,_ = dual_bound(model, probabilities, alpha, penalties)
        lower_type = 'exact_rational_bellman_dual'
    costs,errors,reached = evaluate_policy(model, policy)
    max_error = max(errors)
    full_mix = max(F(0), 1-alpha/max_error) if max_error else F(0)
    if alpha == 0 and max_error: raise AssertionError('Zero-error DP reports an error')
    upper = ((1-full_mix)*sum((p*c for p,c in zip(probabilities,costs)), F(0))+
             full_mix*(3*model.n))
    if (1-full_mix)*max_error > alpha or lower > upper:
        raise AssertionError('Exact primal/dual certification failed')
    return {'prior': prior, 'graph': model.graph, 'kind': model.kind,
            'items': model.n, 'alpha': str(alpha), 'states': len(model.states),
            'variables': len(entries), 'float_lp_cost': float(result.fun),
            'lower': str(lower), 'upper': str(upper), 'lower_type': lower_type,
            'certified_gap': str(upper-lower),
            'worst_fixed_matrix_error': str((1-full_mix)*max_error),
            'full_evaluation_mixture': str(full_mix),
            'policy': {str(s): [[a,str(p)] for a,p in policy[s]] for s in sorted(reached)},
            'error_penalties': list(map(str,penalties)),
            'world_costs': [str((1-full_mix)*c+full_mix*3*model.n) for c in costs],
            'world_errors': [str((1-full_mix)*e) for e in errors]}
