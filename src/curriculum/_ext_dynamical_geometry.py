# Curriculum expansion (pass #5): dynamical systems + information geometry. Imported by catalog.py.
from src.curriculum._ext_helpers import _M, _q, _s

_NEW_DYNAMICAL = [
    _s(
        "dyn_state_space",
        "State Space & Flows",
        _M,
        "Model a system as a point moving through a state space under a flow.",
        "A continuous-time dynamical system is a vector field $\\dot{\\mathbf{x}}=f(\\mathbf{x})$ "
        "on a state space $X\\subseteq\\mathbb{R}^n$. The solution $\\phi_t(\\mathbf{x}_0)$ is the "
        "flow: where the state lands after time $t$. Free-energy gradients later define exactly "
        "such a flow on belief space.",
        ("m_vectors", "m_derivative"),
        _q(
            "A continuous-time dynamical system $\\dot{\\mathbf{x}}=f(\\mathbf{x})$ specifies what at each state?",
            ["The velocity vector", "The total energy", "A probability"],
            0,
        ),
    ),
    _s(
        "dyn_fixed_point",
        "Fixed Points & Equilibria",
        _M,
        "Locate equilibria where the flow vanishes.",
        "A fixed point $\\mathbf{x}^\\star$ satisfies $f(\\mathbf{x}^\\star)=0$: the state stops "
        "moving. Self-organising systems settle onto such equilibria, and an active-inference "
        "agent's preferred state is a fixed point of its belief-and-action dynamics.",
        ("dyn_state_space",),
        _q(
            "At a fixed point $\\mathbf{x}^\\star$ of $\\dot{\\mathbf{x}}=f(\\mathbf{x})$, what is $f(\\mathbf{x}^\\star)$?",
            ["$0$", "Maximal", "Undefined"],
            0,
        ),
    ),
    _s(
        "dyn_linearisation",
        "Linearisation & the Jacobian",
        _M,
        "Approximate the flow near an equilibrium by its Jacobian.",
        "Near $\\mathbf{x}^\\star$ the flow behaves like its linearisation "
        "$\\dot{\\boldsymbol{\\delta}}=J\\,\\boldsymbol{\\delta}$, where $J=\\partial f/\\partial\\mathbf{x}$ "
        "is the Jacobian evaluated at $\\mathbf{x}^\\star$. The eigenvalues of $J$ decide whether small "
        "perturbations grow or decay.",
        ("dyn_fixed_point", "m_jacobian_hessian", "m_eigen"),
        _q(
            "Stability of an equilibrium is read off from the eigenvalues of which matrix?",
            [
                "The Jacobian at the equilibrium",
                "The likelihood matrix $A$",
                "The identity",
            ],
            0,
        ),
    ),
    _s(
        "dyn_stability",
        "Stability & Lyapunov Functions",
        _M,
        "Certify stability with a Lyapunov function that decreases along the flow.",
        "An equilibrium is stable if a Lyapunov function $V(\\mathbf{x})>0$ with "
        "$\\dot{V}=\\nabla V\\cdot f(\\mathbf{x})<0$ exists in a neighbourhood: every trajectory flows "
        "downhill in $V$. Variational free energy is the Lyapunov function for perception — beliefs "
        "descend it monotonically.",
        ("dyn_linearisation", "m_gradient_descent"),
        _q(
            "A Lyapunov function $V$ certifying stability must satisfy which condition along trajectories?",
            ["$\\dot{V}<0$", "$\\dot{V}>0$", "$\\dot{V}=V$"],
            0,
        ),
    ),
    _s(
        "dyn_attractor",
        "Attractors & Basins",
        _M,
        "Characterise attractors and the basins that flow into them.",
        "An attractor is a set the flow converges to from an open basin of initial conditions; a "
        "stable fixed point is the simplest case, but limit cycles and strange attractors also occur. "
        "Pull-toward-preferred-observations dynamics make the agent's goal an attractor of its "
        "generative dynamics.",
        ("dyn_stability",),
        _q(
            "The set of initial states that converge to a given attractor is called its:",
            ["Basin of attraction", "Markov blanket", "Free energy"],
            0,
        ),
    ),
    _s(
        "dyn_stochastic",
        "Stochastic Differential Equations",
        _M,
        "Add noise to a flow with a Langevin / stochastic differential equation.",
        "A Langevin equation $\\dot{\\mathbf{x}}=f(\\mathbf{x})+\\boldsymbol{\\omega}$ adds random "
        "fluctuations $\\boldsymbol{\\omega}$ to a deterministic flow. Its stationary density solves "
        "the Fokker-Planck equation and links dynamics to probability — the bridge the Free Energy "
        "Principle walks across.",
        ("dyn_attractor", "p_stochastic_process", "p_gaussian"),
        _q(
            "A Langevin equation augments a deterministic flow $f(\\mathbf{x})$ with what?",
            ["A random fluctuation term", "A second derivative", "A discrete clock"],
            0,
        ),
    ),
    _s(
        "dyn_fokker_planck",
        "The Fokker-Planck Equation",
        _M,
        "Evolve a probability density under stochastic dynamics.",
        "The Fokker-Planck equation governs how a density $p(\\mathbf{x},t)$ flows under a Langevin "
        "system. Its stationary solution $p^\\star(\\mathbf{x})$ with $\\partial_t p^\\star=0$ is the "
        "non-equilibrium steady state a self-organising system occupies — the formal target of "
        "surprise minimisation.",
        ("dyn_stochastic",),
        _q(
            "The stationary density of a Fokker-Planck system satisfies which condition?",
            ["$\\partial_t p^\\star=0$", "$p^\\star=0$", "$\\nabla p^\\star>0$"],
            0,
        ),
    ),
    _s(
        "dyn_ness",
        "Non-Equilibrium Steady States",
        _M,
        "Identify the steady state a living system maintains against decay.",
        "A non-equilibrium steady state (NESS) is a stationary density sustained by ongoing exchange "
        "with the environment rather than thermodynamic equilibrium. The Free Energy Principle casts "
        "an organism as occupying a NESS whose support is its set of characteristic states; remaining "
        "there *is* surprise minimisation.",
        ("dyn_fokker_planck", "fep_self_organisation", "fep_markov_blanket"),
        _q(
            "Under the FEP, an organism is modelled as occupying what kind of state?",
            [
                "A non-equilibrium steady state",
                "Thermodynamic equilibrium",
                "A unique fixed point with no noise",
            ],
            0,
        ),
    ),
    _s(
        "dyn_gradient_flow",
        "Free Energy as a Gradient Flow",
        _M,
        "Read perception and action as gradient flows on free energy.",
        "Perceptual and active dynamics can be written as a gradient flow "
        "$\\dot{\\boldsymbol{\\mu}}=-\\kappa\\,\\partial F/\\partial\\boldsymbol{\\mu}$ that descends "
        "variational free energy $F$. Because $F$ is a Lyapunov function, the belief trajectory "
        "provably converges, tying the dynamical-systems and variational accounts into one story.",
        ("dyn_ness", "vm_perception_descent", "fep_perception"),
        _q(
            "Writing perception as $\\dot{\\boldsymbol{\\mu}}=-\\kappa\\,\\partial F/\\partial\\boldsymbol{\\mu}$ makes beliefs do what to $F$?",
            ["Descend it", "Maximise it", "Hold it constant"],
            0,
        ),
    ),
]

_NEW_GEOMETRY = [
    _s(
        "geo_statistical_manifold",
        "Statistical Manifolds",
        _M,
        "View a parametric family of distributions as a smooth manifold.",
        "A parametric family $\\{p_\\theta:\\theta\\in\\Theta\\}$ forms a statistical manifold whose "
        "points are distributions and whose coordinates are the parameters $\\theta$. Inference then "
        "becomes movement on this manifold — a geometric reframing of belief updating.",
        ("p_exponential_family", "m_info_geometry"),
        _q(
            "On a statistical manifold, each point corresponds to what?",
            ["A probability distribution", "A single sample", "A scalar loss"],
            0,
        ),
    ),
    _s(
        "geo_fisher_information",
        "Fisher Information Metric",
        _M,
        "Measure local distinguishability of distributions with the Fisher metric.",
        "The Fisher information matrix "
        "$g_{ij}(\\theta)=\\mathbb{E}_{p_\\theta}[\\partial_i\\log p_\\theta\\,\\partial_j\\log p_\\theta]$ "
        "is the unique (up to scale) Riemannian metric on a statistical manifold invariant under "
        "reparameterisation. It tells you how far apart two nearby distributions are in information "
        "terms.",
        ("geo_statistical_manifold",),
        _q(
            "The Fisher information matrix plays the role of what on a statistical manifold?",
            ["A Riemannian metric", "A prior", "A loss function"],
            0,
        ),
    ),
    _s(
        "geo_kl_divergence_local",
        "KL Divergence as Squared Distance",
        _M,
        "Relate KL divergence to the Fisher metric for nearby distributions.",
        "For $\\theta$ and $\\theta+d\\theta$ close together, "
        "$D_{\\mathrm{KL}}(p_\\theta\\,\\|\\,p_{\\theta+d\\theta})\\approx\\tfrac{1}{2}\\,d\\theta^\\top "
        "g(\\theta)\\,d\\theta$: KL is locally one-half the squared Fisher length. This is why minimising "
        "KL is a geometric descent and not merely an algebraic one.",
        ("geo_fisher_information", "it_kl"),
        _q(
            "To second order, $D_{\\mathrm{KL}}(p_\\theta\\,\\|\\,p_{\\theta+d\\theta})$ is approximately:",
            [
                "$\\tfrac{1}{2}\\,d\\theta^\\top g(\\theta)\\,d\\theta$",
                "$g(\\theta)\\,d\\theta$",
                "A constant independent of $g$",
            ],
            0,
        ),
    ),
    _s(
        "geo_natural_gradient",
        "The Natural Gradient",
        _M,
        "Precondition the gradient by the inverse Fisher metric for steepest descent.",
        "The natural gradient $\\tilde{\\nabla}F=g(\\theta)^{-1}\\nabla F$ is the steepest-descent "
        "direction in the information geometry rather than in raw coordinates. Because it respects the "
        "Fisher metric it is invariant to reparameterisation, and it typically converges far faster "
        "than the ordinary gradient on $0<\\eta<1$ step sizes.",
        ("geo_kl_divergence_local", "m_gradient_descent"),
        _q(
            "The natural gradient rescales the ordinary gradient by which matrix?",
            [
                "The inverse Fisher metric $g^{-1}$",
                "The Fisher metric $g$",
                "The Hessian of the prior",
            ],
            0,
        ),
    ),
    _s(
        "geo_dual_connections",
        "Dual Connections & Flatness",
        _M,
        "Use the dually-flat $e$/$m$ structure of exponential families.",
        "Information geometry equips a statistical manifold with a pair of dual affine connections "
        "($e$-connection over natural parameters, $m$-connection over expectation parameters). "
        "Exponential families are dually flat, so $D_{\\mathrm{KL}}$ acts as a Bregman divergence and "
        "the variational free energy decomposes cleanly along the two coordinate systems.",
        ("geo_natural_gradient", "vm_free_energy"),
        _q(
            "Exponential families are special in information geometry because they are:",
            ["Dually flat", "Always one-dimensional", "Free of any metric"],
            0,
        ),
    ),
    _s(
        "geo_natural_inference",
        "Natural-Gradient Variational Inference",
        _M,
        "Run belief updates as natural-gradient descent on free energy.",
        "Casting variational inference as natural-gradient descent "
        "$\\dot{\\boldsymbol{\\mu}}=-g(\\boldsymbol{\\mu})^{-1}\\partial F/\\partial\\boldsymbol{\\mu}$ "
        "makes belief updating geometry-aware: each step is the steepest descent of free energy in the "
        "Fisher metric of the recognition density. This unifies predictive-coding dynamics with "
        "information geometry and explains their robustness.",
        ("geo_dual_connections", "vm_recognition_density", "ai_state_estimation"),
        _q(
            "Natural-gradient variational inference descends free energy in which geometry?",
            [
                "The Fisher metric of the recognition density",
                "Euclidean parameter space",
                "A randomly chosen metric",
            ],
            0,
        ),
    ),
]
