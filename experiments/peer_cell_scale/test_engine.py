import sys
import unittest
from itertools import combinations,product
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0,str(Path(__file__).resolve().parent))
from engine import (CELL_METHODS,ColumnModel,ec2_gains,edges_for,null_peak,
                    pair_factor,paired_vertices,proposal,run_cells,run_paired)


def enumerated_peak(obs,q,f,a,b):
    ids=np.argwhere(obs<0); maximum=None
    for values in product((0,1),repeat=len(ids)):
        world=obs.copy()
        for (v,i),y in zip(ids,values): world[v,i]=y
        if world[a].sum()>world[b].sum(): continue
        value=sum(q[v,i]*f[v,i,world[v,i]] for v,i in ids)
        maximum=value if maximum is None else max(maximum,value)
    return maximum


class PeerCellChecks(unittest.TestCase):
    def test_five_system_particles_preserve_every_observed_cell(self):
        rng=np.random.default_rng(903)
        model=ColumnModel(rng.integers(0,2,size=(5,50)))
        obs=rng.integers(-1,2,size=(5,8))
        sampled=model.particles(obs,rng,32)
        self.assertEqual(sampled.shape,(32,5,8))
        self.assertTrue(np.all(sampled[:,obs>=0]==obs[obs>=0]))
        self.assertTrue(np.isfinite(model.predict(obs)).all())

    def test_sorting_support_and_factors_against_all_completions(self):
        rng=np.random.default_rng(904)
        for _ in range(100):
            obs=rng.integers(-1,2,size=(3,2))
            if not (obs<0).any(): continue
            q=rng.uniform(.1,1,size=obs.shape)*(obs<0); q/=q.sum()
            predicted=rng.uniform(.05,.95,size=obs.shape)
            for a,b in ((0,1),(1,0),(0,2)):
                arbitrary=rng.uniform(.01,8,size=obs.shape+(2,))
                brute=enumerated_peak(obs,q,arbitrary,a,b)
                fast=null_peak(obs,q,arbitrary,a,b)
                if brute is None: self.assertIsNone(fast); continue
                self.assertAlmostEqual(brute,fast,places=11)
                factor,peak=pair_factor(obs,predicted,q,a,b)
                check=enumerated_peak(obs,q,factor,a,b)
                self.assertLessEqual(check,1+1e-12)
                self.assertAlmostEqual(check,peak,places=10)

    def test_scalar_projection_matches_general_convex_problem(self):
        rng=np.random.default_rng(905)
        for _ in range(8):
            obs=np.full((2,3),-1); predicted=rng.uniform(.1,.9,size=(2,3))
            predicted[0]=.6+.3*predicted[0]; predicted[1]=.1+.3*predicted[1]
            q=rng.uniform(.1,1,size=(2,3)); q/=q.sum()
            factor,_=pair_factor(obs,predicted,q,0,1)
            actual=np.sum(q*((1-predicted)*np.log(factor[:,:,0])+predicted*np.log(factor[:,:,1])))
            r=predicted.ravel(); w=q.ravel()
            result=minimize(lambda z:float(np.sum(w*(r*np.log(r/z)+(1-r)*np.log((1-r)/(1-z))))),
                np.full(6,.5),method='SLSQP',bounds=[(.000001,.999999)]*6,
                constraints=[{'type':'ineq','fun':lambda z:z[3:].sum()-z[:3].sum()}],
                options={'ftol':1e-12,'maxiter':1000})
            self.assertTrue(result.success)
            self.assertAlmostEqual(actual,result.fun,places=7)

    def test_row_control_preserves_row_masses_and_uniform_items(self):
        rng=np.random.default_rng(906); model=ColumnModel(rng.integers(0,2,size=(3,30)))
        obs=np.array([[0,-1,-1],[-1,1,-1],[-1,-1,-1]])
        pred=model.predict(obs); edges=edges_for(3,'star'); decisions=np.full(2,2)
        cell=proposal(obs,pred,edges,decisions,'peer_cell')
        row=proposal(obs,pred,edges,decisions,'row_peer')
        np.testing.assert_allclose(cell.sum(axis=1),row.sum(axis=1),atol=1e-15)
        for v in range(3): self.assertEqual(len(set(row[v,obs[v]<0])),1)
        self.assertTrue(np.all(row[obs>=0]==0))

    def test_empirical_ec2_gain_matches_literal_edge_cutting(self):
        rng=np.random.default_rng(907); particles=rng.integers(0,2,size=(12,3,2))
        edges=edges_for(3,'star'); totals=particles.sum(axis=2)
        answer=[tuple(np.sign(t[a]-t[b]) for a,b in edges) for t in totals]
        cross=[(a,b) for a,b in combinations(range(12),2) if answer[a]!=answer[b]]
        expected=np.zeros((3,2))
        for v,i in product(range(3),range(2)):
            for y in (0,1):
                remain=sum(particles[a,v,i]==y and particles[b,v,i]==y for a,b in cross)
                expected[v,i]+=np.mean(particles[:,v,i]==y)*(len(cross)-remain)
        np.testing.assert_allclose(ec2_gains(particles,edges),expected,atol=1e-12)

    def test_ternary_vertices_cover_every_integer_histogram(self):
        rng=np.random.default_rng(908)
        for n in range(1,9):
            for d in range(-n,n+1):
                allrows=np.array([(a,n-a-c,c) for a in range(n+1) for c in range(n-a+1)
                                  if d+c-a<=0])/n
                vertices=paired_vertices(d,n)
                for _ in range(5):
                    f=rng.uniform(0,10,size=3)
                    self.assertAlmostEqual(float(np.max(allrows@f)),float(np.max(vertices@f)),places=12)

    def test_hidden_target_does_not_change_first_choice_or_factor(self):
        rng=np.random.default_rng(909); model=ColumnModel(rng.integers(0,2,size=(3,50)))
        first=np.zeros((3,3),int); second=np.ones((3,3),int)
        edges=edges_for(3,'star')
        a=run_cells(first,model,edges,'peer_cell',7,8)
        first_cell=a['trace'][0]['cell']; second.flat[first_cell]=0
        b=run_cells(second,model,edges,'peer_cell',7,8)
        self.assertEqual(a['trace'][0],b['trace'][0])

    def test_unique_purchases_and_exact_tie_completion(self):
        rng=np.random.default_rng(910); model=ColumnModel(rng.integers(0,2,size=(3,50)))
        scores=np.zeros((3,3),int); edges=edges_for(3,'complete')
        for method in CELL_METHODS:
            result=run_cells(scores,model,edges,method,23,24)
            cells=[row['cell'] for row in result['trace']]
            self.assertEqual(len(cells),len(set(cells)))
            self.assertEqual(result['paid'],9)
            self.assertEqual(result['decisions'],[0,0,0])
        paired=run_paired(scores,model,edges,[2,0,1])
        self.assertEqual(paired['paid'],9)
        self.assertEqual(paired['decisions'],[0,0,0])


if __name__=='__main__': unittest.main()
