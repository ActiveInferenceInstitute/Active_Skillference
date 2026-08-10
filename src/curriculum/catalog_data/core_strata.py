"""Core stratum skill lists assembled into the foundational curriculum subjects."""

from __future__ import annotations

from src.curriculum.authoring import (
    _AI,
    _APP,
    _C,
    _FEP,
    _IT,
    _M,
    _P,
    _VM,
    _q,
    _s,
)

# --------------------------------------------------------------------------- #
# Stratum 0 — Mathematical foundations                                        #
# --------------------------------------------------------------------------- #
_MATH_LINALG = [
    _s(
        "m_sets",
        "Sets & Functions",
        _M,
        "Define sets, functions, and mappings used throughout the curriculum.",
        "A function $f:X\\to Y$ assigns each element of a domain $X$ a unique image in $Y$. "
        "Sets, tuples and indexed families are the vocabulary every later definition uses.",
        (),
        _q(
            "A function maps each domain element to how many images?",
            ["At least one", "Exactly one", "Any number"],
            1,
        ),
    ),
    _s(
        "m_vectors",
        "Vectors & Vector Spaces",
        _M,
        "Represent quantities as vectors and operate in $\\mathbb{R}^n$.",
        "A vector $\\mathbf{x}\\in\\mathbb{R}^n$ is an ordered tuple; addition and scalar "
        "multiplication obey the vector-space axioms.",
        ("m_sets",),
        _q(
            "Vectors in $\\mathbb{R}^n$ are closed under which operations?",
            [
                "Addition and scalar multiplication",
                "Only addition",
                "Only multiplication",
            ],
            0,
        ),
    ),
    _s(
        "m_matrix",
        "Matrices & Matrix Multiplication",
        _M,
        "Multiply matrices and read them as linear maps.",
        "A matrix $A\\in\\mathbb{R}^{m\\times n}$ encodes a linear map $\\mathbb{R}^n\\to\\mathbb{R}^m$; "
        "$(AB)_{ij}=\\sum_k A_{ik}B_{kj}$. Likelihood matrices $A$ in active inference are exactly this.",
        ("m_vectors",),
        _q(
            "If $A$ is $m\\times n$ and $B$ is $n\\times p$, $AB$ is:",
            ["$m\\times p$", "$n\\times n$", "$p\\times m$"],
            0,
        ),
    ),
    _s(
        "m_dotproduct",
        "Inner Products & Norms",
        _M,
        "Compute dot products and vector norms.",
        "The inner product $\\langle\\mathbf{x},\\mathbf{y}\\rangle=\\sum_i x_i y_i$ underlies "
        "expectations $\\mathbb{E}_p[f]=\\langle p, f\\rangle$ used everywhere below.",
        ("m_vectors",),
        _q(
            "An expectation $\\mathbb{E}_p[f]$ can be written as which operation of $p$ and $f$?",
            ["Inner product", "Cross product", "Outer product"],
            0,
        ),
    ),
    _s(
        "m_eigen",
        "Eigenvalues & Positive-Definiteness",
        _M,
        "Interpret eigenvalues and positive-definite matrices.",
        "For $A\\mathbf{v}=\\lambda\\mathbf{v}$, $\\lambda$ is an eigenvalue; covariance and "
        "precision matrices are symmetric positive-definite.",
        ("m_matrix",),
        _q(
            "A covariance matrix is always:",
            ["Symmetric positive-(semi)definite", "Skew-symmetric", "Orthogonal"],
            0,
        ),
    ),
    _s(
        "m_functions_real",
        "Limits & Continuity",
        _M,
        "Reason about limits and continuous functions.",
        "Continuity formalises 'small input change → small output change', the precondition "
        "for differentiation.",
        ("m_sets",),
        _q(
            "Differentiability of $f$ at a point requires $f$ to be:",
            ["Continuous there", "Linear", "Bounded"],
            0,
        ),
    ),
]

_MATH_CALC = [
    _s(
        "m_derivative",
        "Derivatives & Gradients",
        _M,
        "Differentiate scalar and multivariate functions.",
        "The gradient $\\nabla f(\\mathbf{x})$ stacks partial derivatives and points in the "
        "direction of steepest ascent — the engine of every optimisation below.",
        ("m_functions_real", "m_vectors"),
        _q(
            "$\\nabla f$ points in the direction of:",
            ["Steepest ascent", "Steepest descent", "Zero change"],
            0,
        ),
    ),
    _s(
        "m_chain_rule",
        "The Chain Rule",
        _M,
        "Differentiate composed functions.",
        "$(f\\circ g)'(x)=f'(g(x))\\,g'(x)$; backpropagation and message passing are repeated "
        "chain-rule applications.",
        ("m_derivative",),
        _q(
            "The chain rule differentiates:",
            ["Composed functions", "Sums only", "Products only"],
            0,
        ),
    ),
    _s(
        "m_jacobian_hessian",
        "Jacobian & Hessian",
        _M,
        "Assemble first- and second-order derivative matrices.",
        "The Jacobian collects first partials of a vector field; the Hessian collects second "
        "partials and certifies local curvature/convexity.",
        ("m_chain_rule", "m_eigen"),
        _q(
            "A function is locally convex where its Hessian is:",
            ["Positive-definite", "Negative-definite", "Singular"],
            0,
        ),
    ),
    _s(
        "m_convexity",
        "Convexity",
        _M,
        "Recognise convex functions and sets.",
        "A convex function lies below its chords: $f(\\lambda x+(1-\\lambda)y)\\le \\lambda f(x)+(1-\\lambda)f(y)$. "
        "Convexity guarantees a unique minimum — and powers Jensen's inequality later.",
        ("m_jacobian_hessian",),
        _q(
            "A convex function's graph lies:",
            ["Below its chords", "Above its chords", "On its chords"],
            0,
        ),
    ),
    _s(
        "m_gradient_descent",
        "Gradient Descent & Fixed Points",
        _M,
        "Iterate $\\mathbf{x}_{t+1}=\\mathbf{x}_t-\\eta\\nabla f$ to a fixed point.",
        "Gradient descent steps downhill; a fixed point $\\nabla f=0$ is a stationary belief — "
        "perception in active inference is gradient descent on free energy.",
        ("m_derivative",),
        _q(
            "Gradient descent halts (in principle) when the gradient is:",
            ["Zero", "Maximal", "Negative"],
            0,
        ),
    ),
    _s(
        "m_lagrange",
        "Constrained Optimisation & Lagrange Multipliers",
        _M,
        "Optimise under equality constraints.",
        "Normalisation $\\sum_i q_i=1$ is an equality constraint; Lagrange multipliers yield the "
        "softmax as the maximum-entropy solution.",
        ("m_gradient_descent", "m_convexity"),
        _q(
            "Lagrange multipliers handle which kind of optimisation?",
            ["Constrained", "Unconstrained", "Discrete-only"],
            0,
        ),
    ),
    _s(
        "m_functional",
        "Functionals & the Calculus of Variations",
        _M,
        "Differentiate functionals to optimise over functions.",
        "A functional maps a function to a scalar; the functional derivative $\\delta F/\\delta q$ "
        "minimises free energy over the whole density $q$, not a single point.",
        ("m_lagrange",),
        _q(
            "Free energy is minimised over a:",
            ["Probability density (a function)", "Single scalar", "Matrix"],
            0,
        ),
    ),
    _s(
        "m_euler_lagrange",
        "Euler–Lagrange & Stationarity",
        _M,
        "Derive stationarity conditions for functionals.",
        "Setting $\\delta F/\\delta q=0$ subject to normalisation gives the variational update; "
        "this is the mathematical skeleton of the Free Energy Principle.",
        ("m_functional",),
        _q(
            "Stationarity of a functional sets which quantity to zero?",
            ["The functional derivative", "The function itself", "The constraint"],
            0,
        ),
    ),
]

# --------------------------------------------------------------------------- #
# Stratum 1 — Probability                                                     #
# --------------------------------------------------------------------------- #
_PROB_FOUND = [
    _s(
        "p_axioms",
        "Probability Axioms",
        _P,
        "State Kolmogorov's axioms of probability.",
        "Probabilities are non-negative, the sure event has probability 1, and disjoint events "
        "add. Everything Bayesian rests on these three rules.",
        (),
        _q("The probability of the sure (certain) event equals:", ["1", "0", "0.5"], 0),
    ),
    _s(
        "p_random_var",
        "Random Variables",
        _P,
        "Define discrete and continuous random variables.",
        "A random variable assigns numbers to outcomes; its distribution lists the probability "
        "of each value.",
        ("p_axioms",),
        _q(
            "A discrete random variable's distribution must sum to:",
            ["1", "0", "the number of outcomes"],
            0,
        ),
    ),
    _s(
        "p_joint_marginal",
        "Joint, Marginal & Conditional",
        _P,
        "Relate joint, marginal and conditional probabilities.",
        "Marginalisation $p(x)=\\sum_y p(x,y)$ and conditioning $p(x\\mid y)=p(x,y)/p(y)$ are the "
        "two moves of all inference.",
        ("p_random_var",),
        _q(
            "Marginalising the joint $p(x,y)$ over $y$ yields:",
            ["$p(x)$", "$p(y)$", "$p(x\\mid y)$"],
            0,
        ),
    ),
    _s(
        "p_independence",
        "Independence",
        _P,
        "Test for statistical independence.",
        "$X\\perp Y$ iff $p(x,y)=p(x)p(y)$; independence makes mutual information zero.",
        ("p_joint_marginal",),
        _q(
            "If $X$ and $Y$ are independent then $p(x,y)$ equals:",
            ["$p(x)p(y)$", "$p(x)+p(y)$", "$p(x\\mid y)$"],
            0,
        ),
    ),
    _s(
        "p_bayes_theorem",
        "Bayes' Theorem",
        _P,
        "Invert conditionals with Bayes' rule.",
        "$p(s\\mid o)=\\dfrac{p(o\\mid s)p(s)}{p(o)}$ — posterior $\\propto$ likelihood $\\times$ prior. "
        "This single identity is the seed of perception-as-inference.",
        ("p_joint_marginal",),
        _q(
            "In Bayes' rule the posterior is proportional to likelihood times:",
            ["Prior", "Evidence", "Marginal likelihood"],
            0,
        ),
    ),
    _s(
        "p_expectation",
        "Expectation & Variance",
        _P,
        "Compute moments of a distribution.",
        "$\\mathbb{E}_p[f]=\\sum_x p(x)f(x)$ and $\\mathrm{Var}=\\mathbb{E}[(X-\\mathbb{E}X)^2]$; "
        "free energy is an expectation under the recognition density.",
        ("p_random_var", "m_dotproduct"),
        _q(
            "Expectation $\\mathbb{E}_p[f]$ weights $f(x)$ by:",
            ["$p(x)$", "$1/x$", "the variance"],
            0,
        ),
    ),
]

_PROB_DIST = [
    _s(
        "p_bernoulli",
        "Bernoulli & Binomial",
        _P,
        "Model binary and counted outcomes.",
        "A Bernoulli$(\\theta)$ models one coin flip; the binomial sums $n$ of them.",
        ("p_random_var",),
        _q(
            "A Bernoulli random variable takes how many distinct values?",
            ["Two", "Infinite", "Six"],
            0,
        ),
    ),
    _s(
        "p_categorical",
        "Categorical & Multinomial",
        _P,
        "Model outcomes over $K$ categories.",
        "A categorical distribution is a probability vector over $K$ states — the data type of "
        "beliefs $q(s)$ in discrete active inference.",
        ("p_bernoulli",),
        _q(
            "A categorical distribution over $K$ states is represented by:",
            ["A length-$K$ probability vector", "A scalar", "A $K\\times K$ matrix"],
            0,
        ),
    ),
    _s(
        "p_gaussian",
        "The Gaussian Distribution",
        _P,
        "Characterise the normal distribution by mean and (co)variance.",
        "$\\mathcal{N}(\\mu,\\Sigma)$ is the maximum-entropy distribution for fixed mean and "
        "covariance; continuous active inference assumes Gaussians.",
        ("p_expectation",),
        _q(
            "A Gaussian is fully specified by its mean and:",
            ["Covariance", "Mode count", "Support"],
            0,
        ),
    ),
    _s(
        "p_dirichlet",
        "The Dirichlet Distribution",
        _P,
        "Place a prior over categorical parameters.",
        "The Dirichlet is conjugate to the categorical; its concentration $\\alpha$ counts "
        "pseudo-observations and drives learning of the $A$ and $B$ matrices.",
        ("p_categorical",),
        _q(
            "The Dirichlet distribution is a prior over:",
            ["Categorical probabilities", "Real lines", "Matrices of reals"],
            0,
        ),
    ),
    _s(
        "p_conjugacy",
        "Conjugate Priors",
        _P,
        "Exploit conjugacy for closed-form updates.",
        "When prior and posterior share a family (e.g. Dirichlet–categorical), Bayesian updates "
        "are simple count increments.",
        ("p_dirichlet", "p_bayes_theorem"),
        _q(
            "Conjugacy means the posterior stays in the same family as the:",
            ["Prior", "Likelihood", "Evidence"],
            0,
        ),
    ),
    _s(
        "p_exponential_family",
        "The Exponential Family",
        _P,
        "Recognise the exponential-family form.",
        "$p(x)=h(x)\\exp(\\eta^\\top T(x)-A(\\eta))$ unifies Gaussian, categorical and Dirichlet; "
        "its log-normaliser $A(\\eta)$ reappears as free energy.",
        ("p_gaussian", "p_categorical"),
        _q(
            "The exponential family unifies distributions through a shared:",
            ["Functional form", "Mean", "Support size"],
            0,
        ),
    ),
    _s(
        "p_markov_chain",
        "Markov Chains",
        _P,
        "Model state sequences with the Markov property.",
        "A Markov chain's next state depends only on the current state: $p(s_{t+1}\\mid s_{1:t})="
        "p(s_{t+1}\\mid s_t)$. Transition matrices $B$ are exactly Markov kernels.",
        ("p_categorical",),
        _q(
            "The Markov property says the future depends only on the:",
            ["Present state", "Entire history", "Initial state"],
            0,
        ),
    ),
    _s(
        "p_stochastic_process",
        "Stochastic Processes & Stationarity",
        _P,
        "Describe processes evolving in time and their steady states.",
        "A stationary distribution is invariant under the transition; the FEP characterises "
        "living systems by a non-equilibrium steady state.",
        ("p_markov_chain",),
        _q(
            "A stationary distribution is one that is:",
            ["Invariant under the transition", "Always uniform", "Deterministic"],
            0,
        ),
    ),
]

# --------------------------------------------------------------------------- #
# Stratum 2 — Information theory                                              #
# --------------------------------------------------------------------------- #
_INFO_ENTROPY = [
    _s(
        "it_surprise",
        "Surprise (Self-Information)",
        _IT,
        "Quantify the surprise of an outcome as $-\\ln p$.",
        "Rare events are surprising: surprise $=-\\ln p(o)$. A probability-$0.01$ event carries "
        "{{claim:surprise_rare_event}} of surprise. Minimising expected surprise is the FEP in one line.",
        ("p_bayes_theorem", "m_functions_real"),
        _q(
            "As an outcome's probability falls, its surprise:",
            ["Rises", "Falls", "Stays constant"],
            0,
        ),
    ),
    _s(
        "it_entropy",
        "Shannon Entropy",
        _IT,
        "Compute the average surprise of a distribution.",
        "Entropy $H(p)=-\\sum_x p(x)\\ln p(x)$ is expected surprise. A fair coin has "
        "{{claim:entropy_fair_coin}}; a fair die has {{claim:entropy_fair_die}}; a biased "
        "(0.9/0.1) coin only {{claim:entropy_biased_coin}} — certainty lowers entropy.",
        ("it_surprise", "p_expectation"),
        _q(
            "Among coins, entropy is maximised when the coin is:",
            ["Fair (0.5/0.5)", "Biased (0.9/0.1)", "Deterministic"],
            0,
        ),
        _q(
            "Shannon entropy is the expected value of:",
            ["Surprise", "Variance", "The mean"],
            0,
        ),
    ),
    _s(
        "it_cross_entropy",
        "Cross-Entropy",
        _IT,
        "Score a model distribution against the truth.",
        "$H(p,q)=-\\sum_x p(x)\\ln q(x)$ is the expected surprise of using $q$ when reality is $p$; "
        "it decomposes as $H(p)+\\mathrm{KL}(p\\|q)$.",
        ("it_entropy", "it_kl"),
        _q(
            "Cross-entropy $H(p,q)$ decomposes into entropy plus:",
            ["KL divergence", "Mutual information", "Variance"],
            0,
        ),
    ),
    _s(
        "it_kl",
        "Kullback–Leibler Divergence",
        _IT,
        "Measure the directed divergence between distributions.",
        "$\\mathrm{KL}(p\\|q)=\\sum_x p(x)\\ln\\frac{p(x)}{q(x)}\\ge 0$, zero iff $p=q$ (Gibbs). "
        "A 0.9/0.1 coin diverges from fair by {{claim:kl_biased_vs_fair}}. KL is the 'complexity' "
        "term of free energy.",
        ("it_entropy", "m_convexity"),
        _q(
            "$\\mathrm{KL}(p\\|q)=0$ if and only if:",
            ["$p=q$", "$p$ is uniform", "$q$ is uniform"],
            0,
        ),
        _q(
            "KL divergence is:",
            ["Non-negative and asymmetric", "Symmetric", "Sometimes negative"],
            0,
        ),
    ),
    _s(
        "it_gibbs",
        "Gibbs' Inequality",
        _IT,
        "Prove non-negativity of KL divergence.",
        "Gibbs' inequality $\\mathrm{KL}(p\\|q)\\ge 0$ follows from the concavity of $\\ln$; it "
        "guarantees free energy upper-bounds surprise.",
        ("it_kl",),
        _q(
            "Gibbs' inequality establishes that KL divergence is:",
            ["$\\ge 0$", "$\\le 0$", "Unbounded below"],
            0,
        ),
    ),
    _s(
        "it_jensen",
        "Jensen's Inequality",
        _IT,
        "Bound the expectation of a convex function.",
        "For convex $\\varphi$, $\\varphi(\\mathbb{E}[X])\\le\\mathbb{E}[\\varphi(X)]$. Applied to "
        "$-\\ln$, Jensen yields the evidence lower bound (ELBO).",
        ("it_entropy", "m_convexity"),
        _q(
            "Jensen's inequality requires the function to be:",
            ["Convex (or concave)", "Linear", "Monotone"],
            0,
        ),
    ),
]

_INFO_MI = [
    _s(
        "it_joint_entropy",
        "Joint & Conditional Entropy",
        _IT,
        "Extend entropy to pairs of variables.",
        "$H(X,Y)$ and $H(Y\\mid X)$ measure uncertainty of pairs and residual uncertainty; "
        "$H(X,Y)=H(X)+H(Y\\mid X)$ (chain rule of entropy).",
        ("it_entropy", "p_joint_marginal"),
        _q("$H(X,Y)=H(X)+\\,?$", ["$H(Y\\mid X)$", "$H(Y)$", "$H(X\\mid Y)$"], 0),
    ),
    _s(
        "it_mutual_information",
        "Mutual Information",
        _IT,
        "Quantify shared information between variables.",
        "$I(X;Y)=\\mathrm{KL}(p(x,y)\\|p(x)p(y))\\ge 0$, zero iff independent. A correlated "
        "0.4/0.1/0.1/0.4 joint shares {{claim:mutual_info_correlated}}. Epistemic value is "
        "expected mutual information between states and observations.",
        ("it_kl", "p_independence"),
        _q(
            "Mutual information is zero exactly when the variables are:",
            ["Independent", "Identical", "Gaussian"],
            0,
        ),
    ),
    _s(
        "it_info_gain",
        "Information Gain & Bayesian Surprise",
        _IT,
        "Score how much an observation updates beliefs.",
        "Bayesian surprise is $\\mathrm{KL}(\\text{posterior}\\|\\text{prior})$ — the information "
        "an observation provides. It is the epistemic drive of active inference.",
        ("it_mutual_information", "p_bayes_theorem"),
        _q(
            "Bayesian surprise compares the posterior against the:",
            ["Prior", "Likelihood", "Evidence"],
            0,
        ),
    ),
    _s(
        "it_max_entropy",
        "The Maximum-Entropy Principle",
        _IT,
        "Choose the least-committal distribution under constraints.",
        "Subject to known constraints, the max-entropy distribution adds no spurious assumptions; "
        "it yields the softmax/Gibbs form via Lagrange multipliers.",
        ("it_entropy", "m_lagrange"),
        _q(
            "The maximum-entropy distribution is the one that is:",
            ["Least committal given constraints", "Most peaked", "Always uniform"],
            0,
        ),
    ),
]

# --------------------------------------------------------------------------- #
# Stratum 3 — Variational methods                                             #
# --------------------------------------------------------------------------- #
_VAR_BAYES = [
    _s(
        "vm_softmax",
        "The Softmax / Gibbs Distribution",
        _VM,
        "Map scores to probabilities with temperature/precision.",
        "$\\sigma(\\mathbf{x})_i=\\frac{e^{\\beta x_i}}{\\sum_j e^{\\beta x_j}}$ is the max-entropy "
        "distribution for given expected scores. With scores $[1,2,3]$ the top mass is "
        "{{claim:softmax_top_low_precision}} at precision 1 and {{claim:softmax_top_high_precision}} "
        "at precision 3 — precision sharpens choice.",
        ("it_max_entropy", "p_categorical"),
        _q(
            "Raising the precision (inverse temperature) of a softmax makes it:",
            ["Sharper / more peaked", "Flatter", "Unchanged"],
            0,
        ),
    ),
    _s(
        "vm_exact_inference",
        "Exact Bayesian Inference & Intractability",
        _VM,
        "Compute exact posteriors and see why they scale badly.",
        "Exact inference needs the evidence $p(o)=\\sum_s p(o\\mid s)p(s)$, which is exponential in "
        "the number of latent variables — motivating approximation.",
        ("p_bayes_theorem", "p_expectation"),
        _q(
            "Exact inference is often intractable because computing the evidence is:",
            ["Exponentially costly", "Always negative", "Non-differentiable"],
            0,
        ),
    ),
    _s(
        "vm_recognition_density",
        "Recognition Density $q(s)$",
        _VM,
        "Introduce an approximate posterior to optimise.",
        "Active inference replaces the true posterior with a tractable recognition density "
        "$q(s)$ and improves it by minimising free energy.",
        ("vm_exact_inference",),
        _q(
            "The recognition density $q(s)$ approximates the:",
            ["Posterior over states", "Likelihood", "Prior predictive"],
            0,
        ),
    ),
    _s(
        "vm_bayes_worked",
        "Worked Bayesian Update",
        _VM,
        "Apply Bayes' rule to a noisy-sensor problem.",
        "With a 1%-prevalence condition and a 99%-sensitive / 95%-specific test, a positive "
        "result yields posterior {{claim:bayes_posterior_present_given_positive}} for the "
        "condition — base rates dominate.",
        ("vm_exact_inference", "p_dirichlet"),
        _q(
            "A positive test on a rare condition still leaves a low posterior chiefly because of:",
            ["The low base rate (prior)", "High sensitivity", "The test cost"],
            0,
        ),
    ),
]

_VAR_FREE_ENERGY = [
    _s(
        "vm_elbo",
        "The Evidence Lower Bound (ELBO)",
        _VM,
        "Bound log-evidence from below.",
        "Jensen gives $\\ln p(o)\\ge \\mathbb{E}_q[\\ln p(o,s)-\\ln q(s)]=\\text{ELBO}$. Maximising "
        "the ELBO is minimising variational free energy.",
        ("it_jensen", "it_kl", "vm_recognition_density"),
        _q(
            "The ELBO is a lower bound on the:",
            ["Log-evidence", "Entropy", "KL divergence"],
            0,
        ),
    ),
    _s(
        "vm_free_energy",
        "Variational Free Energy",
        _VM,
        "Define $F$ as complexity minus accuracy.",
        "$F=\\mathrm{KL}(q\\|\\text{prior})-\\mathbb{E}_q[\\ln p(o\\mid s)]=$ complexity $-$ accuracy "
        "$=$ surprise $+\\,\\mathrm{KL}(q\\|\\text{posterior})$. $F$ upper-bounds surprise and is "
        "tight when $q$ is the true posterior.",
        ("vm_elbo", "it_kl"),
        _q(
            "Variational free energy decomposes into complexity minus:",
            ["Accuracy", "Entropy", "Precision"],
            0,
        ),
        _q(
            "$F$ equals surprise plus which non-negative term?",
            [
                "$\\mathrm{KL}(q\\|\\text{posterior})$",
                "Cross-entropy",
                "Mutual information",
            ],
            0,
        ),
    ),
    _s(
        "vm_free_energy_tight",
        "Tightness of the Free-Energy Bound",
        _VM,
        "Show $F$ collapses to surprise at the posterior.",
        "On the noisy-sensor model, a uniform belief has $F=${{claim:vfe_descent_start}} while the "
        "true posterior has $F=${{claim:vfe_descent_end}}, exactly the negative log-evidence "
        "{{claim:neg_log_evidence_positive}} — the bound is tight.",
        ("vm_free_energy", "vm_bayes_worked"),
        _q(
            "At the true posterior, variational free energy equals the:",
            ["Negative log-evidence (surprise)", "Prior entropy", "Mutual information"],
            0,
        ),
    ),
    _s(
        "vm_perception_descent",
        "Perception as Gradient Descent on $F$",
        _VM,
        "Cast belief updating as minimising free energy.",
        "Iterating $q\\leftarrow q-\\eta\\,\\delta F/\\delta q$ drives $F$ from "
        "{{claim:vfe_descent_start}} down to {{claim:vfe_descent_end}} — perception is inference "
        "by free-energy descent.",
        ("vm_free_energy_tight", "m_gradient_descent", "m_euler_lagrange"),
        _q(
            "Perception in this framework is implemented as descent on:",
            ["Variational free energy", "The likelihood", "The prior"],
            0,
        ),
    ),
    _s(
        "vm_mean_field",
        "Mean-Field Approximation",
        _VM,
        "Factorise the recognition density for tractability.",
        "Assuming $q(s_1,\\dots,s_n)=\\prod_i q_i(s_i)$ decouples the variational updates into "
        "per-factor fixed-point equations.",
        ("vm_free_energy", "p_independence"),
        _q(
            "The mean-field assumption makes the recognition density:",
            ["Factorised across variables", "Gaussian", "Uniform"],
            0,
        ),
    ),
    _s(
        "vm_laplace",
        "The Laplace Approximation",
        _VM,
        "Approximate a posterior by a Gaussian at its mode.",
        "Expanding $\\ln p$ to second order at the MAP gives a Gaussian $q$; continuous active "
        "inference uses the Laplace-encoded free energy.",
        ("vm_free_energy", "p_gaussian", "m_jacobian_hessian"),
        _q(
            "The Laplace approximation fits a Gaussian at the posterior's:",
            ["Mode", "Mean of the prior", "Tail"],
            0,
        ),
    ),
    _s(
        "vm_message_passing",
        "Belief Propagation & Message Passing",
        _VM,
        "Compute marginals by passing messages on a factor graph.",
        "Variational message passing implements free-energy minimisation as local messages, the "
        "neuronal-process-theory substrate of predictive coding.",
        ("vm_mean_field",),
        _q(
            "Variational message passing computes posteriors using:",
            [
                "Local messages on a graph",
                "A global matrix inverse",
                "Random sampling only",
            ],
            0,
        ),
    ),
]

# --------------------------------------------------------------------------- #
# Stratum 4 — The Free Energy Principle                                       #
# --------------------------------------------------------------------------- #
_FEP_BLANKET = [
    _s(
        "fep_generative_model",
        "Generative Models",
        _FEP,
        "Specify a joint $p(o,s)$ a system embodies.",
        "A generative model factorises $p(o,s)=p(o\\mid s)p(s)$ — a creature's implicit theory of "
        "how hidden causes generate sensations.",
        ("vm_free_energy", "p_markov_chain"),
        _q(
            "A generative model specifies the joint over observations and:",
            ["Hidden states/causes", "Actions only", "Rewards only"],
            0,
        ),
    ),
    _s(
        "fep_markov_blanket",
        "Markov Blankets",
        _FEP,
        "Partition a system into internal, sensory, active and external states.",
        "A Markov blanket (sensory + active states) statistically separates internal from "
        "external states, defining the boundary of a thing.",
        ("fep_generative_model", "p_independence"),
        _q(
            "A Markov blanket separates internal states from:",
            ["External states", "Sensory states", "Active states"],
            0,
        ),
    ),
    _s(
        "fep_self_organisation",
        "Self-Organisation & NESS",
        _FEP,
        "Relate persistence to a non-equilibrium steady state.",
        "Things that persist occupy a non-equilibrium steady state (NESS); their states appear "
        "to minimise surprise on average over time.",
        ("fep_markov_blanket", "p_stochastic_process"),
        _q(
            "A persisting system is characterised by a non-equilibrium:",
            ["Steady state", "Phase transition", "Random walk"],
            0,
        ),
    ),
    _s(
        "fep_statement",
        "The Free Energy Principle",
        _FEP,
        "State the FEP as bounding surprise by free energy.",
        "Because surprise is intractable, systems minimise a tractable upper bound — variational "
        "free energy — over their internal and active states. This is the FEP.",
        ("fep_self_organisation", "vm_free_energy", "it_surprise"),
        _q(
            "The FEP says systems minimise a tractable upper bound on:",
            [
                "Surprise (self-information)",
                "Energy dissipation",
                "Entropy production only",
            ],
            0,
        ),
    ),
    _s(
        "fep_collective_inference",
        "Coupling Generative Models Across Minds",
        _FEP,
        "Explain how shared observations couple individual generative models into population inference.",
        "If person A holds a generative model $p_A(o,s)$ and person B holds $p_B(o,s)$, then "
        "conditioning on the same observation $o$ makes their posteriors $p_A(s\\mid o)$ and "
        "$p_B(s\\mid o)$ estimates of the same hidden cause. Communication couples the models "
        "further: one agent's posterior can act as another's prior, and an ecosystem-level "
        "observer can pool the individual posteriors into a population-level belief over $s$. How "
        "tightly the population converges depends on the precision each agent assigns its evidence "
        "and on the diversity of their priors, so it is this coupling — not any single mind — that "
        "the information-ecosystem view actually treats as one generative model.",
        ("fep_statement", "p_bayes_theorem"),
        _q(
            "Shared observations couple two agents' generative models because their posteriors then estimate:",
            [
                "The same hidden cause",
                "Two unrelated quantities",
                "Only their separate private priors",
            ],
            0,
        ),
        _q(
            "Whether a population converges on a shared belief depends mainly on:",
            [
                "The precision agents assign evidence and their prior diversity",
                "The raw number of messages exchanged",
                "The total size of the population alone",
            ],
            0,
        ),
    ),
]

_FEP_PERCEPTION = [
    _s(
        "fep_perception",
        "Perception as Inference",
        _FEP,
        "Minimise $F$ with respect to internal states.",
        "Holding action fixed, minimising $F$ over internal states optimises the recognition "
        "density — perception infers the causes of sensation.",
        ("fep_statement", "vm_perception_descent"),
        _q(
            "Perception minimises free energy with respect to:",
            ["Internal (belief) states", "Active states", "Model parameters"],
            0,
        ),
    ),
    _s(
        "fep_action",
        "Action & Active States",
        _FEP,
        "Minimise $F$ with respect to action by changing sensations.",
        "Action minimises free energy by making sensations match predictions — selectively "
        "sampling the world to confirm the model.",
        ("fep_statement", "fep_markov_blanket"),
        _q(
            "Action reduces free energy by changing the:",
            ["Sampled sensations", "Prior beliefs", "Likelihood matrix"],
            0,
        ),
    ),
    _s(
        "fep_predictive_processing",
        "Predictive Processing",
        _FEP,
        "Frame the brain as a hierarchical prediction machine.",
        "Cortical hierarchies predict lower-level activity and propagate prediction errors "
        "upward; precision weights gate their influence.",
        ("fep_perception", "vm_message_passing"),
        _q(
            "In predictive processing, what flows up the hierarchy?",
            ["Prediction errors", "Predictions", "Rewards"],
            0,
        ),
    ),
    _s(
        "fep_precision",
        "Precision & Confidence",
        _FEP,
        "Weight prediction errors by their inverse variance.",
        "Precision is the inverse variance of a prediction error; it sets the gain on evidence "
        "and is hypothesised to be encoded by neuromodulators.",
        ("fep_predictive_processing", "p_gaussian"),
        _q(
            "Precision is the inverse of a prediction error's:",
            ["Variance", "Mean", "Entropy"],
            0,
        ),
    ),
    _s(
        "fep_dual_aspects",
        "Dual Minimisation: Perception & Action",
        _FEP,
        "Combine perceptual and active free-energy minimisation.",
        "Agents minimise the same $F$ two ways — updating beliefs (perception) and acting "
        "(changing data) — a single objective for the whole sensorimotor loop.",
        ("fep_perception", "fep_action"),
        _q(
            "Perception and action minimise:",
            ["The same free energy", "Different objectives", "Only entropy"],
            0,
        ),
    ),
]

# --------------------------------------------------------------------------- #
# Stratum 5 — Active inference                                                #
# --------------------------------------------------------------------------- #
_AI_POMDP = [
    _s(
        "ai_pomdp",
        "POMDPs for Active Inference",
        _AI,
        "Model decision-making under partial observability.",
        "A POMDP has hidden states, observations, actions and a reward/preference; active "
        "inference recasts reward as prior preference over observations.",
        ("fep_dual_aspects", "p_markov_chain"),
        _q(
            "A POMDP differs from an MDP because states are:",
            ["Partially observed", "Continuous", "Deterministic"],
            0,
        ),
    ),
    _s(
        "ai_matrix_A",
        "The Likelihood Matrix $A$",
        _AI,
        "Encode $p(o\\mid s)$ as a column-stochastic matrix.",
        "Each column $A_{:,s}=p(o\\mid s)$ is the sensory likelihood of state $s$; informative "
        "$A$ makes observations diagnostic.",
        ("ai_pomdp", "m_matrix", "p_categorical"),
        _q(
            "Each column of the likelihood matrix $A$ is a distribution over:",
            ["Observations", "States", "Actions"],
            0,
        ),
    ),
    _s(
        "ai_matrix_B",
        "The Transition Matrices $B$",
        _AI,
        "Encode action-conditioned state dynamics $p(s'\\mid s,a)$.",
        "$B^{(a)}$ is a Markov kernel per action; policies are sequences of actions that compose "
        "these transitions.",
        ("ai_pomdp", "p_markov_chain"),
        _q(
            "The transition tensor $B$ is conditioned on the current state and the:",
            ["Action", "Observation", "Reward"],
            0,
        ),
    ),
    _s(
        "ai_matrix_C",
        "Preferences $C$ (Prior over Observations)",
        _AI,
        "Encode goals as preferred observations.",
        "$C$ is a prior log-preference over observations; high $C$ marks rewarding outcomes the "
        "agent expects to encounter.",
        ("ai_pomdp",),
        _q(
            "In active inference, reward is represented as a prior over:",
            ["Observations", "Actions", "Transitions"],
            0,
        ),
    ),
    _s(
        "ai_matrix_D",
        "Initial State Prior $D$",
        _AI,
        "Encode beliefs about the starting state.",
        "$D=p(s_1)$ seeds inference at the first time step before any observation arrives.",
        ("ai_pomdp", "p_categorical"),
        _q(
            "$D$ specifies the prior over the:",
            ["Initial state", "Final observation", "Policy"],
            0,
        ),
    ),
    _s(
        "ai_state_estimation",
        "State Estimation in Discrete AIF",
        _AI,
        "Infer $q(s)$ from an observation via Bayes/free-energy.",
        "Given $o$, the agent computes $q(s)\\propto A_{o,:}\\odot D$ — the discrete perception "
        "step, identical to the worked Bayes update.",
        ("ai_matrix_A", "ai_matrix_D", "vm_bayes_worked"),
        _q(
            "Discrete state estimation combines the likelihood column with the:",
            ["State prior", "Preference $C$", "Transition $B$"],
            0,
        ),
    ),
]

_AI_EFE = [
    _s(
        "ai_expected_free_energy",
        "Expected Free Energy (EFE)",
        _AI,
        "Define the quantity that scores policies into the future.",
        "EFE $G(\\pi)=-(\\text{epistemic}+\\text{pragmatic})$ scores a policy by expected "
        "information gain plus expected preference satisfaction; agents prefer low-$G$ policies.",
        ("ai_state_estimation", "ai_matrix_C", "it_info_gain"),
        _q(
            "Agents prefer policies with which expected free energy?",
            ["Low", "High", "Zero exactly"],
            0,
        ),
    ),
    _s(
        "ai_epistemic_value",
        "Epistemic Value (Exploration)",
        _AI,
        "Quantify a policy's expected information gain.",
        "Epistemic value is the expected reduction in state uncertainty. With an informative "
        "sensor, an uncertain belief carries epistemic value {{claim:efe_epistemic_uncertain}} "
        "while a certain belief carries {{claim:efe_epistemic_certain}} — there is nothing left "
        "to learn.",
        ("ai_expected_free_energy", "it_mutual_information"),
        _q(
            "Epistemic value is highest when the agent's beliefs are:",
            ["Uncertain", "Certain", "Uniform over actions"],
            0,
        ),
    ),
    _s(
        "ai_pragmatic_value",
        "Pragmatic Value (Exploitation)",
        _AI,
        "Quantify expected preference satisfaction.",
        "Pragmatic value is expected log-preference $\\mathbb{E}_q[\\ln C]$. For a confident, "
        "preference-aligned prediction it is {{claim:efe_pragmatic_certain}} (negative log-"
        "preference contributes to lowering $G$).",
        ("ai_expected_free_energy", "ai_matrix_C"),
        _q(
            "Pragmatic value scores a policy by expected:",
            ["Preference satisfaction", "Information gain", "Entropy"],
            0,
        ),
    ),
    _s(
        "ai_explore_exploit",
        "The Exploration–Exploitation Balance",
        _AI,
        "See how EFE unifies exploring and exploiting.",
        "Because $G$ sums epistemic and pragmatic value, a single objective trades off exploring "
        "to reduce uncertainty against exploiting known rewards — no ad-hoc bonus needed.",
        ("ai_epistemic_value", "ai_pragmatic_value"),
        _q(
            "Active inference balances exploration and exploitation via:",
            [
                "A single EFE objective",
                "A separate exploration bonus",
                "Random restarts",
            ],
            0,
        ),
    ),
    _s(
        "ai_policy_selection",
        "Policy Selection via Softmax",
        _AI,
        "Turn EFE values into a policy distribution.",
        "$q(\\pi)=\\sigma(-\\gamma G(\\pi))$ — policy precision $\\gamma$ controls determinism. "
        "Lower-$G$ policies receive more probability.",
        ("ai_expected_free_energy", "vm_softmax"),
        _q(
            "The policy posterior is a softmax of the negative EFE scaled by:",
            ["Policy precision $\\gamma$", "The learning rate", "The discount factor"],
            0,
        ),
    ),
    _s(
        "ai_precision_gamma",
        "Policy Precision $\\gamma$",
        _AI,
        "Modulate decision confidence with $\\gamma$.",
        "High $\\gamma$ concentrates choice on the best policy; low $\\gamma$ randomises it. "
        "$\\gamma$ is itself inferred, linking decisions to dopaminergic precision.",
        ("ai_policy_selection", "fep_precision"),
        _q(
            "Raising policy precision $\\gamma$ makes action selection:",
            ["More deterministic", "More random", "Slower to converge"],
            0,
        ),
    ),
    _s(
        "ai_free_energy_of_future",
        "Why EFE and not VFE for Planning",
        _AI,
        "Distinguish inference about the past from planning the future.",
        "VFE scores beliefs about observed data; EFE scores beliefs about *future*, as-yet "
        "unobserved data — so it must include the epistemic term that VFE lacks.",
        ("ai_expected_free_energy", "vm_free_energy"),
        _q(
            "Expected free energy scores beliefs about which data?",
            ["Future (unobserved)", "Past (observed)", "Training-set only"],
            0,
        ),
    ),
]

_AI_CONTINUOUS = [
    _s(
        "ai_predictive_coding",
        "Predictive Coding (Continuous AIF)",
        _AI,
        "Implement free-energy descent with prediction-error units.",
        "In continuous state-spaces, gradient descent on the Laplace free energy yields "
        "prediction-error minimisation — the canonical microcircuit hypothesis. This "
        "realises the same variational free-energy imperative as discrete active "
        "inference, but over continuous belief trajectories updated by gradients rather "
        "than a discrete policy distribution scored by expected free energy: the same "
        "principle expressed in a different geometry.",
        ("ai_expected_free_energy", "vm_laplace", "fep_predictive_processing"),
        _q(
            "Continuous active inference minimises free energy by reducing:",
            ["Prediction errors", "Policy count", "Reward variance"],
            0,
        ),
        related=("ai_policy_selection",),
    ),
    _s(
        "ai_generalised_coords",
        "Generalised Coordinates of Motion",
        _AI,
        "Track position, velocity and higher derivatives jointly.",
        "Representing a trajectory by its generalised coordinates lets the agent model dynamics "
        "and embed beliefs about change, not just state.",
        ("ai_predictive_coding", "m_derivative"),
        _q(
            "Generalised coordinates augment a state with its:",
            ["Temporal derivatives", "Spatial neighbours", "Action history"],
            0,
        ),
    ),
    _s(
        "ai_active_inference_loop",
        "The Full Perception–Action Loop",
        _AI,
        "Compose estimation, policy selection and action into one cycle.",
        "Each step: infer states, evaluate policies by EFE, sample an action, act, observe, "
        "repeat — the closed sensorimotor loop of active inference.",
        ("ai_state_estimation", "ai_policy_selection"),
        _q(
            "The active inference loop ends each cycle by:",
            ["Acting and observing", "Resetting beliefs", "Retraining $A$"],
            0,
        ),
    ),
]

# --------------------------------------------------------------------------- #
# Stratum 6 — Computation                                                     #
# --------------------------------------------------------------------------- #
_COMP_DISCRETE = [
    _s(
        "comp_normalize_softmax",
        "Implementing Normalisation & Softmax",
        _C,
        "Code numerically stable normalisation and softmax.",
        "Stable softmax subtracts the max before exponentiating; normalisation guards against "
        "zero-sum vectors. These primitives underlie every belief update.",
        ("vm_softmax", "ai_active_inference_loop"),
        _q(
            "Numerically stable softmax first subtracts the input's:",
            ["Maximum", "Mean", "Minimum"],
            0,
        ),
    ),
    _s(
        "comp_belief_update",
        "Coding the Discrete Belief Update",
        _C,
        "Implement $q(s)\\propto A_{o,:}\\odot D$ and renormalise.",
        "The discrete perception step is an element-wise product of the likelihood column and "
        "the prior, followed by normalisation.",
        ("comp_normalize_softmax", "ai_state_estimation"),
        _q(
            "The discrete belief update multiplies the prior by the likelihood column then:",
            ["Normalises", "Exponentiates", "Differentiates"],
            0,
        ),
    ),
    _s(
        "comp_vfe_eval",
        "Computing Variational Free Energy",
        _C,
        "Evaluate $F=\\mathrm{KL}(q\\|\\text{prior})-\\mathbb{E}_q[\\ln A_{o,:}]$ in code.",
        "Tested code reproduces the tightness result: uniform $F=${{claim:vfe_descent_start}} vs "
        "posterior $F=${{claim:vfe_descent_end}}; equality with surplus surprise confirms the "
        "implementation.",
        ("comp_belief_update", "vm_free_energy_tight"),
        _q(
            "A correct VFE implementation, at the posterior, returns the:",
            ["Negative log-evidence", "Prior entropy", "Zero vector"],
            0,
        ),
    ),
    _s(
        "comp_efe_eval",
        "Computing Expected Free Energy",
        _C,
        "Decompose $G$ into epistemic and pragmatic terms in code.",
        "The implementation reproduces epistemic {{claim:efe_epistemic_uncertain}} (uncertain) "
        "vs {{claim:efe_epistemic_certain}} (certain), validating the decomposition.",
        ("comp_vfe_eval", "ai_explore_exploit"),
        _q(
            "A correct EFE routine returns epistemic value that is higher when beliefs are:",
            ["Uncertain", "Certain", "Deterministic"],
            0,
        ),
    ),
    _s(
        "comp_agent_loop",
        "Simulating an Active Inference Agent",
        _C,
        "Run a deterministic perception–action loop.",
        "On a two-action model with neutral preferences (so pragmatic value is equal), "
        "the agent chooses by epistemic value: the information-seeking *sample* action "
        "($G=${{claim:agent_g_sample}}, epistemic {{claim:agent_epistemic_sample}}) beats "
        "the *commit* action ($G=${{claim:agent_g_commit}}, epistemic "
        "{{claim:agent_epistemic_commit}}), so the agent's preferred action index is "
        "{{claim:agent_preferred_action}}. A fixed seed makes the rollout reproducible.",
        ("comp_efe_eval", "ai_active_inference_loop"),
        _q(
            "With a fixed random seed, repeated agent rollouts are:",
            ["Reproducible (identical)", "Random each time", "Non-terminating"],
            0,
        ),
    ),
    _s(
        "comp_determinism",
        "Reproducibility & Fixed Seeds",
        _C,
        "Guarantee byte-identical results across runs.",
        "Seeding the random generator and avoiding global RNG state make simulations "
        "reproducible — a precondition for scientific claims.",
        ("comp_agent_loop",),
        _q(
            "Reproducible simulation requires controlling the:",
            [
                "Random seed/generator",
                "operating-system version",
                "wall-clock start time",
            ],
            0,
        ),
    ),
    _s(
        "comp_tmaze",
        "The T-Maze Paradigm",
        _C,
        "Reproduce the canonical epistemic-foraging task.",
        "In the T-maze, an agent visits a cue to resolve reward location before committing — the "
        "textbook demonstration of epistemic value driving behaviour.",
        ("comp_agent_loop", "ai_epistemic_value"),
        _q(
            "In the T-maze, the agent first seeks the cue because it has high:",
            ["Epistemic value", "Pragmatic value", "Transition noise"],
            0,
        ),
    ),
]

_COMP_TOOLS = [
    _s(
        "comp_pymdp",
        "pymdp & SPM Toolboxes",
        _C,
        "Locate production active-inference software.",
        "`pymdp` (Python) and SPM/DEM (MATLAB) implement discrete and continuous active "
        "inference; this platform's kernels are pedagogical reference implementations.",
        ("comp_agent_loop",),
        _q(
            "`pymdp` provides implementations of:",
            [
                "Active inference agents",
                "Generic convex optimisers",
                "Deep reinforcement-learning baselines",
            ],
            0,
        ),
    ),
    _s(
        "comp_learning_dirichlet",
        "Learning $A$ and $B$ with Dirichlet Counts",
        _C,
        "Update model parameters from experience.",
        "Concentration parameters accumulate observation/transition counts; expected parameters "
        "are $\\alpha/\\sum\\alpha$ — Bayesian learning as counting.",
        ("comp_belief_update", "p_conjugacy"),
        _q(
            "Dirichlet learning of $A$ updates parameters by:",
            ["Accumulating counts", "Gradient clipping", "Random resets"],
            0,
        ),
    ),
    _s(
        "comp_scaling",
        "Scaling & Approximation Trade-offs",
        _C,
        "Reason about cost as state/policy spaces grow.",
        "Enumerating policies is exponential in horizon; sophisticated inference and pruning "
        "keep planning tractable.",
        ("comp_efe_eval", "vm_exact_inference"),
        _q(
            "Policy enumeration cost grows how with planning horizon?",
            ["Exponentially", "Linearly", "Logarithmically"],
            0,
        ),
    ),
]

# --------------------------------------------------------------------------- #
# Stratum 7 — Applications                                                    #
# --------------------------------------------------------------------------- #
_APP_NEURO = [
    _s(
        "app_predictive_brain",
        "The Predictive Brain",
        _APP,
        "Map free-energy minimisation onto cortical function.",
        "Hierarchical predictive coding casts perception as Bayesian inference in cortex, with "
        "superficial pyramidal cells reporting prediction errors.",
        ("ai_predictive_coding", "fep_predictive_processing"),
        _q(
            "Prediction-error signalling in cortex is attributed to which cells?",
            ["Superficial pyramidal cells", "Purkinje cells", "Glia"],
            0,
        ),
    ),
    _s(
        "app_dopamine_precision",
        "Dopamine as Precision",
        _APP,
        "Link neuromodulation to precision/confidence.",
        "Dopaminergic signalling is hypothesised to encode the precision of policies — confidence "
        "in 'what to do', not reward prediction error alone.",
        ("ai_precision_gamma", "fep_precision"),
        _q(
            "Active inference associates dopamine most directly with:",
            ["Precision over policies", "Raw reward", "Sensory acuity"],
            0,
        ),
    ),
    _s(
        "app_computational_psychiatry",
        "Computational Psychiatry",
        _APP,
        "Explain symptoms as aberrant inference.",
        "Hallucinations and delusions are modelled as aberrant priors or miscalibrated precision "
        "— too-strong predictions overriding sensory evidence.",
        ("app_dopamine_precision", "fep_precision"),
        _q(
            "Aberrant precision offers a model of which clinical phenomena?",
            [
                "Hallucinations/delusions",
                "Peripheral nerve injury",
                "Age-related hearing loss",
            ],
            0,
        ),
    ),
    _s(
        "app_interoception",
        "Interoception & Emotion",
        _APP,
        "Extend active inference to bodily regulation.",
        "Interoceptive active inference frames emotion and allostasis as inference over and "
        "control of internal bodily states.",
        ("app_predictive_brain", "fep_action"),
        _q(
            "Interoceptive active inference concerns inference over:",
            ["Internal bodily states", "External landmarks", "Other agents' policies"],
            0,
        ),
    ),
]

_APP_BROADER = [
    _s(
        "app_robotics",
        "Robotics & Control",
        _APP,
        "Use active inference for adaptive control.",
        "Active inference yields controllers that unify state estimation and control by acting "
        "to fulfil proprioceptive predictions — no separate cost function required.",
        ("ai_active_inference_loop", "ai_generalised_coords"),
        _q(
            "Active-inference control replaces an explicit cost function with:",
            ["Prior preferences", "A PID loop", "A lookup table"],
            0,
        ),
    ),
    _s(
        "app_machine_learning",
        "Active Inference & Machine Learning",
        _APP,
        "Relate the ELBO to VAEs and world models.",
        "Variational autoencoders maximise the same ELBO; world-model agents and active inference "
        "share the free-energy objective, differing in how actions are chosen.",
        ("vm_elbo", "ai_free_energy_of_future"),
        _q(
            "Variational autoencoders optimise the same objective as:",
            ["The ELBO / free energy", "Q-learning", "Hard-margin SVMs"],
            0,
        ),
    ),
    _s(
        "app_collective",
        "Collective Behaviour & Multi-Agent Inference",
        _APP,
        "Scale the FEP to groups and shared generative models.",
        "Multi-agent active inference models flocking, stigmergy and shared narratives as "
        "coupled free-energy minimisation over shared states.",
        ("ai_active_inference_loop", "fep_self_organisation"),
        _q(
            "Multi-agent active inference treats coordination as:",
            [
                "Coupled free-energy minimisation",
                "Central scheduling",
                "Random pairing",
            ],
            0,
        ),
    ),
    _s(
        "app_cognitive_security",
        "Cognitive Security & Information Ecosystems",
        _APP,
        "Apply precision/priors to belief manipulation and resilience.",
        "Framing belief change as inference exposes attack surfaces (precision hacking, prior "
        "poisoning) and motivates defences that strengthen epistemic calibration.",
        ("app_computational_psychiatry", "app_collective", "it_info_gain"),
        _q(
            "Cognitive-security threats can be framed as manipulation of priors and:",
            ["Precision", "Bandwidth", "Latency"],
            0,
        ),
    ),
    _s(
        "app_curriculum_capstone",
        "Capstone: From Surprise to Society",
        _APP,
        "Trace the single thread from $-\\ln p$ to collective intelligence.",
        "Every layer is one idea applied at a new scale: minimise expected surprise. The learner "
        "who reaches here can derive perception, action, planning and collective behaviour from "
        "that single principle.",
        (
            "app_robotics",
            "app_machine_learning",
            "app_cognitive_security",
            "app_interoception",
        ),
        _q(
            "The unifying thread of the whole curriculum is the minimisation of:",
            [
                "Expected surprise (free energy)",
                "Reward variance",
                "Model parameter count",
            ],
            0,
        ),
    ),
]


# --------------------------------------------------------------------------- #
# Advanced / breadth skills (maximal enumeration)                             #
# --------------------------------------------------------------------------- #
_MATH_ADV = [
    _s(
        "m_log_exp",
        "Logarithms & Exponentials",
        _M,
        "Manipulate logs and exponentials fluently.",
        "$\\ln(ab)=\\ln a+\\ln b$ turns products of probabilities into sums — why log-space is "
        "the natural home of inference.",
        ("m_functions_real",),
        _q(
            "Working in log-space turns products of probabilities into:",
            ["Sums", "Quotients", "Powers"],
            0,
        ),
    ),
    _s(
        "m_taylor",
        "Taylor Expansion",
        _M,
        "Approximate functions by local polynomials.",
        "A second-order Taylor expansion of $\\ln p$ at its mode is the basis of the Laplace "
        "approximation.",
        ("m_jacobian_hessian",),
        _q(
            "A second-order Taylor expansion underlies which approximation?",
            ["Laplace", "Monte Carlo", "Mean-field"],
            0,
        ),
    ),
    _s(
        "m_simplex",
        "The Probability Simplex",
        _M,
        "Treat probability vectors as points on the simplex.",
        "The simplex $\\{q:q_i\\ge 0,\\sum_i q_i=1\\}$ is the space beliefs live in; variational "
        "updates move points around it.",
        ("m_lagrange", "m_dotproduct"),
        _q(
            "Points on the probability simplex have coordinates that:",
            ["Are non-negative and sum to 1", "Sum to 0", "Are unbounded"],
            0,
        ),
    ),
    _s(
        "m_info_geometry",
        "A Glimpse of Information Geometry",
        _M,
        "See distributions as a curved manifold.",
        "The space of distributions carries the Fisher–Rao metric; natural-gradient inference "
        "follows its geometry.",
        ("m_simplex", "m_eigen"),
        _q(
            "Information geometry studies the manifold of:",
            ["Probability distributions", "Integer lattices", "Linear maps"],
            0,
        ),
    ),
]
_PROB_ADV = [
    _s(
        "p_evidence",
        "Model Evidence (Marginal Likelihood)",
        _P,
        "Compute the evidence $p(o)$ that normalises Bayes.",
        "$p(o)=\\sum_s p(o\\mid s)p(s)$ is the denominator of Bayes' rule and the quantity free "
        "energy bounds.",
        ("p_bayes_theorem", "p_expectation"),
        _q(
            "The model evidence is the normalising constant of which rule?",
            ["Bayes' rule", "The chain rule", "Jensen's inequality"],
            0,
        ),
    ),
    _s(
        "p_monte_carlo",
        "Monte-Carlo Estimation",
        _P,
        "Approximate expectations by sampling.",
        "Sample averages estimate $\\mathbb{E}_p[f]$; sampling is one route around intractable "
        "sums when variational methods are not used.",
        ("p_expectation", "p_categorical"),
        _q(
            "Monte-Carlo methods estimate expectations using:",
            ["Random samples", "Exact enumeration", "Matrix inversion"],
            0,
        ),
    ),
    _s(
        "p_cond_independence",
        "Conditional Independence",
        _P,
        "Read independence structure given evidence.",
        "$X\\perp Y\\mid Z$ underlies Markov blankets and graphical models.",
        ("p_independence", "p_joint_marginal"),
        _q(
            "Conditional independence is independence that holds given a third:",
            ["Variable", "Sample", "Parameter"],
            0,
        ),
    ),
    _s(
        "p_lln",
        "Law of Large Numbers",
        _P,
        "Justify why sample means converge.",
        "Averages of i.i.d. samples converge to the expectation — the bridge from frequencies to "
        "probabilities.",
        ("p_expectation", "p_monte_carlo"),
        _q(
            "The law of large numbers says sample means converge to the:",
            ["Expectation", "Mode", "Maximum"],
            0,
        ),
    ),
    _s(
        "p_kl_continuous",
        "Divergence for Continuous Densities",
        _P,
        "Extend KL and entropy to continuous variables.",
        "For densities, sums become integrals; differential entropy and continuous KL drive the "
        "Gaussian (Laplace-encoded) free energy.",
        ("p_gaussian", "p_evidence"),
        _q(
            "For continuous variables, entropy sums become:",
            ["Integrals", "Products", "Maxima"],
            0,
        ),
    ),
]
_INFO_ADV = [
    _s(
        "it_channel",
        "Channels & Capacity",
        _IT,
        "Bound information transmissible through a noisy channel.",
        "Channel capacity is the maximum mutual information between input and output — the limit "
        "on how diagnostic sensations can be.",
        ("it_mutual_information",),
        _q(
            "Channel capacity is the maximum of which quantity?",
            ["Mutual information", "Entropy alone", "KL divergence"],
            0,
        ),
    ),
    _s(
        "it_data_processing",
        "The Data-Processing Inequality",
        _IT,
        "Show processing cannot create information.",
        "If $X\\to Y\\to Z$ is a Markov chain, $I(X;Z)\\le I(X;Y)$ — downstream computation never "
        "increases information about the source.",
        ("it_mutual_information", "p_markov_chain"),
        _q(
            "The data-processing inequality says post-processing information about a source:",
            ["Cannot increase it", "Always increases it", "Sets it to zero"],
            0,
        ),
    ),
    _s(
        "it_free_energy_link",
        "Free Energy as an Information Bound",
        _IT,
        "Connect free energy to surprise via information theory.",
        "Free energy = surprise + KL: an information-theoretic upper bound minimised by aligning "
        "beliefs with evidence.",
        ("it_kl", "it_info_gain"),
        _q(
            "Free energy upper-bounds surprise by adding a non-negative:",
            ["KL term", "Entropy", "Variance"],
            0,
        ),
    ),
]
_VAR_ADV = [
    _s(
        "vm_forward_reverse_kl",
        "Forward vs Reverse KL",
        _VM,
        "Contrast mode-covering and mode-seeking objectives.",
        "Variational inference minimises the *reverse* KL$(q\\|p)$, which is mode-seeking — a key "
        "caveat of the approximation.",
        ("it_kl", "vm_recognition_density"),
        _q(
            "Variational inference minimises which KL direction?",
            [
                "Reverse, $\\mathrm{KL}(q\\|p)$",
                "Forward, $\\mathrm{KL}(p\\|q)$",
                "Symmetric KL",
            ],
            0,
        ),
    ),
    _s(
        "vm_energy_entropy",
        "Energy–Entropy Form of $F$",
        _VM,
        "Rewrite $F$ as energy minus entropy.",
        "$F=\\underbrace{-\\mathbb{E}_q[\\ln p(o,s)]}_{\\text{energy}}-\\underbrace{H[q]}_{\\text{entropy}}$ "
        "— the thermodynamic reading of free energy.",
        ("vm_free_energy", "it_entropy"),
        _q(
            "In the energy–entropy form, $F$ equals energy minus:",
            ["Entropy of $q$", "Prior energy", "Mutual information"],
            0,
        ),
    ),
    _s(
        "vm_variational_em",
        "Variational EM & Learning",
        _VM,
        "Alternate inference (E) and learning (M).",
        "Variational EM minimises $F$ over beliefs (E-step) and parameters (M-step) — perception "
        "and learning as one descent.",
        ("vm_mean_field", "p_conjugacy"),
        _q(
            "The M-step of variational EM minimises free energy over:",
            ["Model parameters", "Observations", "Policies"],
            0,
        ),
    ),
    _s(
        "vm_amortised",
        "Amortised Inference",
        _VM,
        "Learn a function that outputs posteriors directly.",
        "Amortised inference trains a recognition network mapping data to $q$ — the encoder of a "
        "variational autoencoder.",
        ("vm_variational_em", "vm_recognition_density"),
        _q(
            "Amortised inference replaces per-datum optimisation with a learned:",
            ["Recognition function", "Lookup table", "Prior"],
            0,
        ),
    ),
]
_AI_ADV = [
    _s(
        "ai_risk_ambiguity",
        "Risk & Ambiguity Decomposition of EFE",
        _AI,
        "Re-express EFE as risk plus ambiguity.",
        "EFE also decomposes as risk (KL of predicted vs preferred outcomes) plus ambiguity "
        "(expected sensory entropy) — a complementary view of exploration.",
        ("ai_expected_free_energy", "vm_forward_reverse_kl"),
        _q(
            "The risk term of EFE is a divergence from the agent's:",
            ["Preferred outcomes", "Initial state", "Transition model"],
            0,
        ),
    ),
    _s(
        "ai_sophisticated",
        "Sophisticated Inference",
        _AI,
        "Plan over beliefs about future beliefs.",
        "Sophisticated active inference evaluates policies by anticipating how future "
        "observations will update beliefs — deep tree search over the generative model.",
        ("ai_free_energy_of_future", "ai_explore_exploit"),
        _q(
            "Sophisticated inference plans over future:",
            ["Beliefs", "Rewards only", "Random seeds"],
            0,
        ),
    ),
    _s(
        "ai_habits",
        "Habit Learning ($E$ Vector)",
        _AI,
        "Add a learned prior over policies.",
        "The habit vector $E$ biases policy selection toward frequently chosen actions, "
        "complementing EFE with experience.",
        ("ai_policy_selection", "comp_learning_dirichlet"),
        _q(
            "The habit term biases selection toward policies that are:",
            ["Frequently chosen", "Never chosen", "Highest-risk"],
            0,
        ),
    ),
    _s(
        "ai_state_factorisation",
        "Factorised State Spaces",
        _AI,
        "Decompose hidden states into independent factors.",
        "Factorising states (location × context × …) keeps inference tractable and mirrors the "
        "mean-field structure.",
        ("ai_matrix_B", "vm_mean_field"),
        _q(
            "Factorising the state space keeps inference:",
            ["Tractable", "Exact but slow", "Stochastic"],
            0,
        ),
    ),
    _s(
        "ai_hierarchical",
        "Hierarchical Generative Models",
        _AI,
        "Stack generative models across timescales.",
        "Higher levels supply empirical priors to lower levels, capturing context and slow "
        "dynamics — deep active inference.",
        ("ai_state_factorisation", "fep_predictive_processing"),
        _q(
            "In a hierarchy, higher levels provide lower levels with:",
            ["Empirical priors", "Raw observations", "Actions"],
            0,
        ),
    ),
    _s(
        "ai_planning_horizon",
        "Planning Horizons & Temporal Depth",
        _AI,
        "Trade planning depth against cost.",
        "Longer horizons evaluate more future free energy but cost more; temporal depth tunes "
        "foresight.",
        ("ai_free_energy_of_future", "ai_active_inference_loop"),
        _q(
            "A longer planning horizon increases foresight at the cost of:",
            ["Computation", "Accuracy", "Determinism"],
            0,
        ),
    ),
]
_COMP_ADV = [
    _s(
        "comp_grid_world",
        "Grid-World Foraging",
        _C,
        "Simulate navigation under uncertainty.",
        "A grid-world agent infers its location and forages for reward, scaling the T-maze logic "
        "to 2-D navigation.",
        ("comp_tmaze", "ai_state_factorisation"),
        _q(
            "A grid-world extends the T-maze to which setting?",
            ["2-D navigation", "Continuous control", "Language"],
            0,
        ),
    ),
    _s(
        "comp_visualization",
        "Visualising Beliefs & Free Energy",
        _C,
        "Plot belief trajectories and free-energy curves.",
        "Figures of $F$ descending and beliefs sharpening make the abstract objective legible; "
        "this platform renders them deterministically.",
        ("comp_vfe_eval",),
        _q(
            "Plotting free energy over inference steps should show it:",
            ["Decreasing", "Increasing", "Oscillating forever"],
            0,
        ),
    ),
    _s(
        "comp_provenance_gate",
        "Content-Provenance Binding",
        _C,
        "Bind every shown number to a tested kernel.",
        "This platform refuses to publish a skill whose quantitative claims are not produced by "
        "tested code — numbers cannot drift from the computations they describe.",
        ("comp_visualization", "comp_efe_eval"),
        _q(
            "The provenance gate fails the build when a shown number is:",
            ["Not produced by tested code", "Below zero", "Irrational"],
            0,
        ),
    ),
    _s(
        "comp_skilltree_export",
        "Exporting to SkillTree",
        _C,
        "Convert the curriculum DAG into a SkillTree project.",
        "The exporter maps subjects, skills, prerequisite dependencies and quizzes into "
        "SkillTree's data model; every quantitative value in a skill description (such as "
        "the agent's sampling expected free energy {{claim:agent_g_sample}}) is carried "
        "across verbatim from the tested kernels.",
        ("comp_provenance_gate", "comp_skilltree_export_dep"),
        _q(
            "Curriculum prerequisites become which SkillTree construct?",
            ["Skill dependencies (learning paths)", "Badges", "Projects"],
            0,
        ),
    ),
    _s(
        "comp_skilltree_export_dep",
        "The SkillTree Data Model",
        _C,
        "Map Project → Subject → Skill and learning paths.",
        "SkillTree organises a Project into Subjects of Skills, with cross-skill prerequisites "
        "forming learning paths and quizzes gating completion.",
        ("comp_determinism", "ai_active_inference_loop"),
        _q(
            "SkillTree's container hierarchy is Project → Subject → :",
            ["Skill", "Badge", "Quiz"],
            0,
        ),
    ),
]
_APP_ADV = [
    _s(
        "app_history",
        "A Short History of the Bayesian Brain",
        _APP,
        "Place the FEP in its intellectual lineage.",
        "From Helmholtz's unconscious inference to Friston's free energy, perception-as-inference "
        "has a two-century lineage.",
        ("app_predictive_brain",),
        _q(
            "The idea of perception as inference traces back to:",
            ["Helmholtz", "Turing", "Shannon"],
            0,
        ),
    ),
    _s(
        "app_ant_colonies",
        "Collective Active Inference in Insects",
        _APP,
        "Model colonies as inference systems.",
        "Ant colonies allocate labour and forage as if minimising collective free energy — "
        "stigmergic signals act as shared beliefs.",
        ("app_collective",),
        _q(
            "Stigmergic signals in a colony act as a form of shared:",
            ["Belief/state", "Currency", "Clock"],
            0,
        ),
    ),
    _s(
        "app_limitations",
        "Limitations & Open Criticisms",
        _APP,
        "State honest critiques of the framework.",
        "The FEP is criticised as unfalsifiable at its most general, and discrete models scale "
        "poorly; honest practice names these limits.",
        ("app_machine_learning", "comp_scaling"),
        _q(
            "A common criticism of the most general FEP is that it can be:",
            ["Hard to falsify", "Too narrow", "Purely empirical"],
            0,
        ),
    ),
    _s(
        "app_active_learning",
        "Active Inference vs Reinforcement Learning",
        _APP,
        "Contrast information-seeking with reward maximisation.",
        "Where RL maximises expected reward, active inference minimises expected free energy, "
        "yielding intrinsic exploration without a bonus.",
        ("app_machine_learning", "ai_explore_exploit"),
        _q(
            "Unlike reward-maximising RL, active inference explores because of its:",
            ["Epistemic (information) drive", "Discount factor", "Replay buffer"],
            0,
        ),
    ),
]
