# Discrete Active Inference Agent - GNN specification
# Generalized Notation Notation (GNN) specification of the discrete
# active-inference agent kernel in src/kernels/active_inference.py, using the
# canonical sample/commit model of src/kernels/examples.py::agent_example.
# Validated against the pinned GNN revision in gnn/upstream.json.

## GNNSection
ActInfPOMDP

## GNNVersionAndFlags
GNN v1

## ModelName
Discrete Active Inference Agent

## ModelAnnotation
One-step discrete active-inference agent: two hidden states, two observations,
two actions. The canonical instance is the kernel's "sample vs commit" example
(src/kernels/examples.py::agent_example, two_action_regime_agent):

- A is an informative sensor (0.9 on the diagonal): one observation shifts the
  state belief.
- B action 0 ("sample") keeps the belief as it is (identity transition);
  action 1 ("commit") collapses it toward state 0 (0.95 to state 0 from either
  previous state).
- C is neutral (uniform): the pragmatic term is identical for both actions, so
  the choice is decided purely by epistemic value (expected information gain),
  and the agent prefers "sample".
- D is the uniform initial state prior; the kernel has no habit prior (E is
  declared uniform and unused).

The kernel computes a genuine expected-free-energy decomposition
(src/kernels/active_inference.py::expected_free_energy) and a policy posterior
softmax(-gamma * G) with precision gamma; the one-step posterior is exact, and
multi-step policies are evaluated by rolling the same B forward
(evaluate_multistep_policies). The specification declares the one-step model.

## StateSpaceBlock
# Likelihood matrix: A[observation, hidden_state]
A[2,2,type=float]        # Informative sensor
# Transition tensor: B[next_state, previous_state, action]
B[2,2,2,type=float]      # sample = identity; commit = collapse to state 0
# Preference vector: C[observation]
C[2,type=float]          # Neutral log-preference weights
# Initial state prior: D[hidden_state]
D[2,type=float]          # Uniform prior
# Habit vector: E[action]
E[2,type=float]          # Uniform (the kernel has no habit prior)
# Hidden state
s[2,1,type=float]        # State posterior
s_prime[2,1,type=float]  # Predicted next state
# Observation
o[2,1,type=int]          # Observation index
# Policy and control
pi[2,type=float]         # Policy posterior over the two actions
u[1,type=int]            # Action taken
G[2,type=float]          # Expected free energy per action
# Time
t[1,type=int]            # Discrete decision step

## Connections
D>s
s-A
A-o
s-B
s>s_prime
B>u
C>G
E>pi
G>pi
pi>u
u>s_prime

## InitialParameterization
# A: 2 observations x 2 hidden states. Informative sensor; each state is
# observed correctly with probability 0.9 (examples.py::_INFORMATIVE_SENSOR_A).
A={
  (0.9, 0.1),
  (0.1, 0.9)
}

# B: 2 next states x 2 previous states x 2 actions. Canonical orientation
# (next_state, previous_state, action); within each next-state slice, rows are
# previous states and columns are actions. Action 0 (sample) is the identity;
# action 1 (commit) collapses either previous state to next state 0 with
# probability 0.95.
B={
  (
    (1.0, 0.95),
    (0.0, 0.95)
  ),
  (
    (0.0, 0.05),
    (1.0, 0.05)
  )
}

# C: 2 observations. Neutral log-preference weights: softmax(C) is uniform, so
# the pragmatic term cannot distinguish the actions.
C={(0.5, 0.5)}

# D: 2 hidden states. Uniform initial state prior.
D={(0.5, 0.5)}

# E: 2 actions. Uniform: the kernel's policy posterior has no habit term.
E={(0.5, 0.5)}

## Equations
# Generative model (discrete POMDP, one-step decision):
#   o_t ~ Categorical(A[:, s_t])
#   s_t+1 ~ Categorical(B[:, s_t, u_t])
# State inference (exact posterior):
#   Q(s) = normalize(A[o, :] * D)
# Expected free energy per action (nats), G = -(epistemic + pragmatic):
#   Q(o | a) = A @ B[:, :, a] @ Q(s)
#   epistemic(a) = sum_s Q(s)[s] * KL(A[:, s] || Q(o | a))
#   pragmatic(a) = Q(o | a) . ln normalize(C)
#   G(a) = -(epistemic(a) + pragmatic(a))
# Policy posterior: Q(pi) = softmax(-gamma * G), gamma = policy precision
# Action selection: u_t ~ Categorical(Q(pi))

## Time
Dynamic
DiscreteTime=t
ModelTimeHorizon=1

## ActInfOntologyAnnotation
A=LikelihoodMatrix
B=TransitionMatrix
C=LogPreferenceVector
D=PriorOverHiddenStates
E=Habit
G=ExpectedFreeEnergy
s=HiddenState
s_prime=NextHiddenState
o=Observation
pi=PolicyVector
u=Action
t=Time

## ModelParameters
num_hidden_states: 2
num_obs: 2
num_actions: 2
num_timesteps: 1

## Footer
Discrete Active Inference Agent v1 - GNN representation of the
Active_Skillference discrete agent kernel (sample/commit canonical example).

## Signature
pending
