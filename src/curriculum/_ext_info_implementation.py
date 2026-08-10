# Curriculum expansion (pass #5): advanced information measures + implementation/scaling. Imported by catalog.py.
from src.curriculum._ext_helpers import _C, _IT, _q, _s

_NEW_INFO_MEASURES = [
    _s(
        "im_typical_set",
        "Typical Sets & the AEP",
        _IT,
        "State the asymptotic equipartition property and characterise the typical set.",
        "For an i.i.d.\\ source $X_1,\\dots,X_n\\sim p$, the AEP gives "
        "$-\\tfrac{1}{n}\\log p(X_1,\\dots,X_n)\\to H(X)$ in probability, so almost all "
        "probability mass concentrates on the typical set $A_\\epsilon^{(n)}$ of roughly "
        "$2^{nH(X)}$ near-equiprobable sequences. The remaining exponentially many sequences "
        "are individually so improbable that they carry vanishing total mass, which is why "
        "$H(X)$ is the per-symbol description cost in the limit.",
        ("it_entropy", "p_stochastic_process"),
        _q(
            "The typical set of length-$n$ i.i.d.\\ sequences contains approximately how many sequences?",
            ["$2^{nH(X)}$", "$2^{n}$", "$2^{H(X)}$", "$n^{H(X)}$"],
            0,
        ),
        _q(
            "The AEP states that $-\\tfrac{1}{n}\\log p(X_1{,}\\dots{,}X_n)$ converges to:",
            [
                "The entropy $H(X)$",
                "Zero",
                "The cross-entropy with the uniform",
                "The variance of $X$",
            ],
            0,
        ),
        tags=("aep", "typicality"),
    ),
    _s(
        "im_channel_capacity",
        "Shannon Channel Capacity",
        _IT,
        "Define channel capacity as the maximal mutual information over input distributions.",
        "A discrete memoryless channel $p(y\\mid x)$ has capacity "
        "$C=\\max_{p(x)} I(X;Y)$, the largest reliable rate (bits per channel use) achievable "
        "with vanishing error as block length grows. Capacity is a property of the channel "
        "alone: it is the supremum over input distributions of the mutual information, and the "
        "noisy-channel coding theorem proves rates below $C$ are achievable and rates above $C$ are not.",
        ("it_mutual_information", "it_channel", "it_max_entropy"),
        _q(
            "Channel capacity $C$ is defined as:",
            [
                "$\\max_{p(x)} I(X;Y)$",
                "$\\min_{p(x)} I(X;Y)$",
                "$\\max_{p(y\\mid x)} H(Y)$",
                "$I(X;Y)$ for the uniform input",
            ],
            0,
        ),
        _q(
            "Per the noisy-channel coding theorem, reliable communication is possible for any rate:",
            [
                "Strictly below $C$",
                "Strictly above $C$",
                "Equal to $H(Y)$",
                "Equal to $H(X\\mid Y)$",
            ],
            0,
        ),
        tags=("capacity", "channel"),
    ),
    _s(
        "im_rate_distortion",
        "Rate-Distortion Theory",
        _IT,
        "Characterise the minimal description rate for a tolerated reconstruction distortion.",
        "Lossy compression is governed by the rate-distortion function "
        "$R(D)=\\min_{p(\\hat{x}\\mid x):\\,\\mathbb{E}[d(X,\\hat{X})]\\le D} I(X;\\hat{X})$, the "
        "fewest bits per symbol needed to reconstruct $X$ as $\\hat{X}$ within average distortion "
        "$D$. $R(D)$ is convex and non-increasing: tolerating more distortion buys fewer required "
        "bits, and $R(0)=H(X)$ for a discrete lossless source. This is the dual of channel "
        "capacity and frames perception as lossy coding of sensory causes.",
        ("im_channel_capacity",),
        _q(
            "The rate-distortion function $R(D)$ minimises $I(X;\\hat{X})$ subject to:",
            [
                "A distortion constraint $\\mathbb{E}[d(X,\\hat{X})]\\le D$",
                "A power constraint on $\\hat{X}$",
                "Maximising $H(\\hat{X})$",
                "An entropy constraint $H(X)\\le D$",
            ],
            0,
        ),
        _q(
            "As the tolerated distortion $D$ increases, $R(D)$:",
            ["Is non-increasing", "Is non-decreasing", "Stays constant", "Oscillates"],
            0,
        ),
        tags=("rate-distortion", "lossy-coding"),
    ),
    _s(
        "im_fisher_information",
        "Fisher Information as a Local Measure",
        _IT,
        "Define Fisher information and read it as the local curvature of log-likelihood.",
        "For a parametric family $p_\\theta(x)$ the Fisher information is "
        "$\\mathcal{I}(\\theta)=\\mathbb{E}_{p_\\theta}\\!\\big[(\\partial_\\theta \\log p_\\theta(X))^2\\big] "
        "= -\\mathbb{E}_{p_\\theta}[\\partial_\\theta^2 \\log p_\\theta(X)]$, the expected curvature of "
        "the log-likelihood. It lower-bounds estimator variance through the Cramer-Rao bound "
        "$\\mathrm{Var}(\\hat\\theta)\\ge 1/\\mathcal{I}(\\theta)$, so it quantifies how much a single "
        "observation locally informs $\\theta$ - a local counterpart to the global Shannon measures.",
        ("im_typical_set", "p_exponential_family"),
        _q(
            "Fisher information equals the negative expected second derivative of:",
            [
                "The log-likelihood $\\log p_\\theta(x)$",
                "The likelihood $p_\\theta(x)$",
                "The prior $p(\\theta)$",
                "The entropy $H(\\theta)$",
            ],
            0,
        ),
        _q(
            "The Cramer-Rao bound states an unbiased estimator's variance is at least:",
            [
                "$1/\\mathcal{I}(\\theta)$",
                "$\\mathcal{I}(\\theta)$",
                "$\\mathcal{I}(\\theta)^2$",
                "$0$",
            ],
            0,
        ),
        tags=("fisher", "curvature"),
    ),
    _s(
        "im_fisher_kl",
        "Fisher Information from KL Curvature",
        _IT,
        "Derive Fisher information as the second-order Taylor term of a local KL divergence.",
        "Expanding the KL divergence between nearby members of a family to second order gives "
        "$D_{KL}\\!\\big(p_\\theta \\,\\|\\, p_{\\theta+\\delta}\\big) = "
        "\\tfrac{1}{2}\\,\\delta^\\top \\mathcal{I}(\\theta)\\,\\delta + O(\\|\\delta\\|^3)$, because the "
        "zeroth and first-order terms vanish. Thus Fisher information is the Hessian of KL at "
        "$\\delta=0$ and the metric tensor of the Fisher-Rao information geometry; KL behaves "
        "locally like a (non-symmetric) squared distance whose quadratic form is $\\mathcal{I}$.",
        ("im_fisher_information", "it_kl", "m_taylor"),
        _q(
            "To second order in $\\delta$, $D_{KL}(p_\\theta\\|p_{\\theta+\\delta})$ equals:",
            [
                "$\\tfrac{1}{2}\\delta^\\top \\mathcal{I}(\\theta)\\,\\delta$",
                "$\\delta^\\top \\mathcal{I}(\\theta)\\,\\delta$",
                "$\\mathcal{I}(\\theta)\\,\\delta$",
                "$\\tfrac{1}{2}\\|\\delta\\|^2$",
            ],
            0,
        ),
        _q(
            "Why does the first-order term of this KL expansion vanish?",
            [
                "The expected score is zero at $\\theta$",
                "KL is symmetric",
                "$\\mathcal{I}(\\theta)=0$",
                "The likelihood is uniform",
            ],
            0,
        ),
        tags=("fisher-rao", "information-geometry"),
    ),
    _s(
        "im_total_correlation",
        "Multi-Information & Total Correlation",
        _IT,
        "Quantify the total statistical dependence among many variables.",
        "Total correlation (multi-information) generalises mutual information to $n$ variables: "
        "$C(X_1,\\dots,X_n)=\\sum_i H(X_i) - H(X_1,\\dots,X_n) = "
        "D_{KL}\\!\\big(p(x_1,\\dots,x_n)\\,\\|\\,\\textstyle\\prod_i p(x_i)\\big)$. It is the KL "
        "divergence from the joint to the product of marginals, is zero exactly when all variables "
        "are mutually independent, and measures the redundancy a factorised (mean-field) model "
        "would discard.",
        ("im_fisher_kl", "it_mutual_information"),
        _q(
            "Total correlation is the KL divergence from the joint distribution to:",
            [
                "The product of the marginals",
                "The uniform distribution",
                "The maximum-entropy joint",
                "A single marginal",
            ],
            0,
        ),
        _q(
            "Total correlation equals zero if and only if the variables are:",
            [
                "Mutually independent",
                "Pairwise correlated",
                "Identically distributed",
                "Gaussian",
            ],
            0,
        ),
        tags=("total-correlation", "redundancy"),
    ),
    _s(
        "im_transfer_entropy",
        "Transfer Entropy & Directed Information Flow",
        _IT,
        "Measure directed, dynamical information transfer between coupled processes.",
        "Transfer entropy from process $Y$ to process $X$ is the conditional mutual information "
        "$T_{Y\\to X}=I\\big(X_{t+1};\\,Y_t^{(k)} \\mid X_t^{(k)}\\big)$: the reduction in uncertainty "
        "about $X$'s next state contributed by $Y$'s past beyond $X$'s own past. Unlike mutual "
        "information it is directional ($T_{Y\\to X}\\ne T_{X\\to Y}$ in general) and is a "
        "model-free, non-linear analogue of Granger causality, making it the standard measure of "
        "coupling in self-organising and neural systems.",
        ("im_total_correlation", "p_stochastic_process"),
        _q(
            "Transfer entropy $T_{Y\\to X}$ is formally a:",
            [
                "Conditional mutual information",
                "Marginal entropy",
                "Cross-entropy",
                "Unconditional mutual information",
            ],
            0,
        ),
        _q(
            "Which property distinguishes transfer entropy from mutual information?",
            [
                "It is directional / asymmetric",
                "It is always symmetric",
                "It can be negative",
                "It ignores temporal order",
            ],
            0,
        ),
        tags=("transfer-entropy", "causality"),
    ),
    _s(
        "im_predictive_information",
        "Predictive Information",
        _IT,
        "Define predictive information as the mutual information between past and future.",
        "The predictive information of a stationary process is "
        "$I_{\\text{pred}}=I\\big(X_{\\text{past}};\\,X_{\\text{future}}\\big)$, the mutual information "
        "between the entire past and the entire future. It equals the sub-extensive part of the "
        "block entropy $H(T)$ - the amount by which $H(T)$ grows sublinearly - and upper-bounds how "
        "much any model can predict. It is a complexity measure: structureless (i.i.d.) and "
        "perfectly periodic signals both carry little predictive information, while rich generative "
        "structure carries a lot.",
        ("im_transfer_entropy",),
        _q(
            "Predictive information is the mutual information between:",
            [
                "The past and the future of the process",
                "Two independent processes",
                "A state and its observation",
                "Adjacent symbols only",
            ],
            0,
        ),
        _q(
            "Predictive information corresponds to which part of the block entropy $H(T)$?",
            [
                "The sub-extensive (sublinear) part",
                "The linear-in-$T$ part",
                "The constant offset",
                "The slope at $T=1$",
            ],
            0,
        ),
        tags=("predictive-information", "complexity"),
    ),
    _s(
        "im_empowerment",
        "Empowerment",
        _IT,
        "Define empowerment as the channel capacity from actions to future sensations.",
        "Empowerment is the channel capacity of the actuation-perception loop: "
        "$\\mathfrak{E}=\\max_{p(a^n)} I\\big(A^n;\\,S_{t+n}\\big)$, the maximal mutual information an "
        "agent's action sequence can establish with its future sensory state. It measures how much "
        "potential control the agent has over its own future and is an intrinsic, reward-free "
        "drive: states with high empowerment keep options open. It reuses the capacity maximisation "
        "of im_channel_capacity with actions as the channel input.",
        ("im_channel_capacity", "im_predictive_information"),
        _q(
            "Empowerment is the channel capacity from:",
            [
                "Actions to future sensory states",
                "Observations to hidden states",
                "Future to past",
                "Rewards to actions",
            ],
            0,
        ),
        _q(
            "Empowerment is best described as an intrinsic motivation that favours:",
            [
                "States with more potential control over the future",
                "States with the highest immediate reward",
                "Fully deterministic transitions",
                "Minimal sensory entropy",
            ],
            0,
        ),
        tags=("empowerment", "intrinsic-motivation"),
    ),
    _s(
        "im_information_bottleneck",
        "The Information Bottleneck",
        _IT,
        "Formulate the optimal trade-off between compression and relevance.",
        "The information bottleneck seeks a representation $T$ of $X$ that compresses $X$ while "
        "preserving information about a target $Y$, minimising "
        "$\\mathcal{L}=I(X;T)-\\beta\\,I(T;Y)$ over stochastic encoders $p(t\\mid x)$. The Lagrange "
        "multiplier $\\beta$ sweeps the relevant compression frontier; the data-processing "
        "inequality guarantees $I(T;Y)\\le I(X;Y)$, so no representation can be more informative "
        "about $Y$ than the raw data. It formalises 'keep only the bits of $X$ that matter for $Y$.'",
        ("im_rate_distortion", "it_data_processing"),
        _q(
            "The information bottleneck objective $I(X;T)-\\beta I(T;Y)$ trades off:",
            [
                "Compression of $X$ against relevance to $Y$",
                "Two independent channel capacities",
                "Entropy against cross-entropy",
                "Prior against likelihood",
            ],
            0,
        ),
        _q(
            "Which inequality bounds the relevance term $I(T;Y)$ for a representation $T$ of $X$?",
            [
                "The data-processing inequality: $I(T;Y)\\le I(X;Y)$",
                "Jensen's inequality",
                "The Cramer-Rao bound",
                "Gibbs' inequality",
            ],
            0,
        ),
        tags=("information-bottleneck", "relevance"),
    ),
    _s(
        "im_landauer",
        "Thermodynamic Cost of Information",
        _IT,
        "Connect Landauer's bound to free energy and the cost of erasing information.",
        "Landauer's principle sets the minimal thermodynamic cost of irreversibly erasing one bit "
        "at temperature $T$ to $k_B T \\ln 2$ of dissipated heat, tying information directly to "
        "thermodynamics. In the variational free-energy view, free energy is measured in the same "
        "units as entropy/information (with $k_B T$ as the conversion factor), so minimising "
        "variational free energy is simultaneously a statistical and a thermodynamic optimisation. "
        "This closes the loop between Shannon information and physical work that the free-energy "
        "principle exploits.",
        ("im_information_bottleneck", "it_free_energy_link"),
        _q(
            "Landauer's principle gives the minimal heat dissipated to erase one bit as:",
            ["$k_B T \\ln 2$", "$k_B T$", "$\\ln 2$", "$1$ joule"],
            0,
        ),
        _q(
            "The link Landauer establishes is between information erasure and:",
            [
                "Thermodynamic free energy / dissipated heat",
                "Channel capacity only",
                "Estimator variance",
                "Predictive information",
            ],
            0,
        ),
        tags=("landauer", "thermodynamics", "free-energy"),
    ),
]

_NEW_IMPLEMENTATION = [
    _s(
        "impl_vectorised_belief",
        "Vectorised Belief Updates",
        _C,
        "Express categorical belief updates as array/tensor operations.",
        "A discrete Bayesian update $q(s)\\propto A[o,:]\\odot (B\\,q_{\\text{prev}})$ is implemented as "
        "element-wise array products and matrix-vector contractions rather than Python loops over "
        "states. Casting the likelihood lookup, transition prediction, and renormalisation into "
        "vectorised form on contiguous arrays exploits BLAS and removes interpreter overhead, "
        "which is the difference between a tractable and an intractable agent for non-trivial "
        "state spaces.",
        ("comp_belief_update", "comp_normalize_softmax"),
        _q(
            "Why prefer vectorised array operations over Python loops for belief updates?",
            [
                "They exploit optimised BLAS routines and avoid interpreter overhead",
                "They change the mathematical result",
                "They avoid the need to normalise",
                "They are required for correctness of Bayes' rule",
            ],
            0,
        ),
        _q(
            "The predictive step $B\\,q_{\\text{prev}}$ in a vectorised update is a:",
            [
                "Matrix-vector product",
                "Scalar product",
                "Element-wise maximum",
                "Cumulative sum",
            ],
            0,
        ),
        tags=("vectorisation", "belief-update"),
    ),
    _s(
        "impl_logsumexp",
        "The Logsumexp Trick",
        _C,
        "Stabilise softmax and log-normaliser computations against overflow and underflow.",
        "Computing $\\log\\sum_i e^{x_i}$ or a softmax directly overflows for large $x_i$ and "
        "underflows for very negative ones. The logsumexp identity "
        "$\\log\\sum_i e^{x_i} = x^\\* + \\log\\sum_i e^{x_i - x^\\*}$ with $x^\\*=\\max_i x_i$ shifts "
        "the largest exponent to zero, guaranteeing at least one well-scaled term and no overflow. "
        "Every numerically robust softmax, EFE-to-policy mapping, and log-partition evaluation in "
        "an active-inference implementation relies on this stabilisation.",
        ("impl_vectorised_belief", "m_log_exp"),
        _q(
            "The logsumexp trick subtracts which value before exponentiating?",
            [
                "The maximum $x^\\*=\\max_i x_i$",
                "The mean of $x$",
                "The minimum of $x$",
                "Zero",
            ],
            0,
        ),
        _q(
            "The primary numerical failure mode that logsumexp prevents is:",
            [
                "Overflow/underflow of $e^{x_i}$",
                "Loss of the normalisation constant",
                "Non-convexity",
                "Incorrect gradients",
            ],
            0,
        ),
        tags=("numerical-stability", "softmax"),
    ),
    _s(
        "impl_message_passing",
        "Message-Passing Implementation",
        _C,
        "Implement marginal inference as local message updates on a factor graph.",
        "On a factor graph, belief propagation computes marginals by passing messages "
        "$\\mu_{f\\to x}$ and $\\mu_{x\\to f}$ that are products of incoming messages times local "
        "factors, with marginals recovered as the normalised product of all messages into a "
        "variable. Implemented in log-space (using impl_logsumexp) the products become sums, "
        "and on a tree the schedule converges exactly in two sweeps; loopy graphs iterate to a "
        "fixed point that approximates the marginals.",
        ("impl_logsumexp", "vm_message_passing"),
        _q(
            "On a factor graph, a variable's marginal is the normalised product of:",
            [
                "All incoming messages to that variable",
                "Only the prior factor",
                "The largest single message",
                "The transition matrix rows",
            ],
            0,
        ),
        _q(
            "Why are message-passing updates often performed in log-space?",
            [
                "Products become numerically stable sums",
                "It removes the need for factors",
                "It guarantees exactness on loopy graphs",
                "It avoids normalisation",
            ],
            0,
        ),
        tags=("message-passing", "factor-graph"),
    ),
    _s(
        "impl_vi_gradient",
        "Variational Inference in Code",
        _C,
        "Implement gradient descent on a variational free-energy objective.",
        "Gradient-based variational inference parameterises an approximate posterior $q_\\phi$ and "
        "descends the variational free energy $F(\\phi)=\\mathbb{E}_{q_\\phi}[\\log q_\\phi(s)-\\log "
        "p(o,s)]$ by automatic differentiation, updating $\\phi \\leftarrow \\phi - \\eta\\,\\nabla_\\phi F$. "
        "Because $F$ upper-bounds surprise, each well-tuned step lowers the bound monotonically - "
        "the same descent illustrated numerically from {{claim:vfe_descent_start}} down to "
        "{{claim:vfe_descent_end}}. Implementation hinges on a differentiable $F$, a stable "
        "learning rate $\\eta$, and a convergence criterion on $\\Delta F$.",
        ("impl_message_passing", "comp_normalize_softmax"),
        _q(
            "Gradient-descent variational inference updates parameters in which direction?",
            [
                "The negative gradient of the free energy $-\\nabla_\\phi F$",
                "The positive gradient $+\\nabla_\\phi F$",
                "The gradient of the likelihood only",
                "A random direction",
            ],
            0,
        ),
        _q(
            "A correct VI implementation should observe the free energy $F$ across steps:",
            [
                "Decrease monotonically toward a minimum",
                "Increase",
                "Stay exactly constant",
                "Diverge",
            ],
            0,
        ),
        tags=("variational-inference", "gradient-descent"),
    ),
    _s(
        "impl_monte_carlo",
        "Monte-Carlo Estimators",
        _C,
        "Estimate intractable expectations in inference by sampling.",
        "When an expectation $\\mathbb{E}_{q}[f(s)]$ has no closed form, a Monte-Carlo estimator "
        "$\\hat{\\mu}=\\tfrac{1}{N}\\sum_{i=1}^N f(s^{(i)})$, $s^{(i)}\\sim q$, is unbiased with "
        "standard error shrinking as $O(1/\\sqrt{N})$. The reparameterisation trick rewrites "
        "$s=g(\\epsilon,\\phi)$ so gradients pass through the sampler, enabling stochastic gradients "
        "of the free energy. The error rate is dimension-independent, which is exactly why sampling "
        "scales to high-dimensional latent spaces where quadrature fails.",
        ("impl_vi_gradient", "p_monte_carlo"),
        _q(
            "The standard error of an $N$-sample Monte-Carlo estimator scales as:",
            ["$O(1/\\sqrt{N})$", "$O(1/N)$", "$O(1/N^2)$", "$O(\\sqrt{N})$"],
            0,
        ),
        _q(
            "The reparameterisation trick is used so that:",
            [
                "Gradients can flow through stochastic samples",
                "Samples are no longer random",
                "Variance becomes zero",
                "No prior is needed",
            ],
            0,
        ),
        tags=("monte-carlo", "sampling"),
    ),
    _s(
        "impl_particle_filter",
        "Particle Filtering for State Estimation",
        _C,
        "Implement sequential Monte-Carlo state estimation with resampling.",
        "A particle filter represents the filtering posterior $p(s_t\\mid o_{1:t})$ by weighted "
        "samples: each particle is propagated through the transition model, reweighted by the "
        "observation likelihood $w^{(i)} \\propto p(o_t\\mid s^{(i)}_t)$, and the set is resampled "
        "when the effective sample size collapses. It performs the same recursive predict-update "
        "as exact filtering (ai_state_estimation) but for non-linear, non-Gaussian models "
        "where closed-form belief updates are unavailable; resampling is what prevents weight "
        "degeneracy from killing the estimate.",
        ("impl_monte_carlo", "ai_state_estimation"),
        _q(
            "In a particle filter, importance weights are proportional to the:",
            [
                "Observation likelihood $p(o_t\\mid s^{(i)}_t)$",
                "Prior $p(s_0)$",
                "Transition entropy",
                "Number of particles",
            ],
            0,
        ),
        _q(
            "Resampling in a particle filter primarily mitigates:",
            [
                "Weight degeneracy (a few particles dominating)",
                "Overflow in the likelihood",
                "Non-convex free energy",
                "Loss of determinism only",
            ],
            0,
        ),
        tags=("particle-filter", "smc"),
    ),
    _s(
        "impl_amortised_net",
        "Amortised Inference Networks",
        _C,
        "Replace per-datum optimisation with a learned recognition network.",
        "Amortised inference trains a recognition network $q_\\phi(s\\mid o)$ - shared across all "
        "observations - to output approximate-posterior parameters in a single forward pass, "
        "instead of running an optimisation loop per datum. The network is fit by maximising the "
        "ELBO (minimising free energy) averaged over data, trading an up-front training cost and a "
        "fixed amortisation gap for $O(1)$ inference at deployment. This is the inference engine "
        "of variational autoencoders and scalable deep active-inference agents.",
        ("impl_vi_gradient", "vm_amortised"),
        _q(
            "Amortised inference replaces per-datum optimisation with:",
            [
                "A shared recognition network mapping $o \\mapsto q(s\\mid o)$",
                "Exact enumeration of states",
                "A larger particle set",
                "A separate optimiser per observation",
            ],
            0,
        ),
        _q(
            "The 'amortisation gap' refers to the suboptimality from:",
            [
                "Using a fixed network instead of per-datum optimisation",
                "Too few Monte-Carlo samples",
                "Numerical overflow",
                "Non-stationary data",
            ],
            0,
        ),
        tags=("amortised-inference", "recognition-network"),
    ),
    _s(
        "impl_benchmarking",
        "Benchmarking & Profiling Inference",
        _C,
        "Measure where inference spends time and validate scaling empirically.",
        "Profiling attributes runtime to the actual hot paths - likelihood evaluation, the "
        "predict step, or the policy search - rather than to assumed bottlenecks, and benchmarking "
        "measures wall-clock against problem size to confirm the empirical scaling curve. Sound "
        "practice fixes inputs, warms caches, runs repeated trials to control variance, and reports "
        "medians; only after measurement should code be optimised, because intuition about cost in "
        "vectorised numerical code is frequently wrong.",
        ("impl_particle_filter", "impl_amortised_net"),
        _q(
            "The correct order of operations when speeding up inference is:",
            [
                "Profile to find the real bottleneck, then optimise it",
                "Optimise the most complex-looking code first",
                "Rewrite everything in C immediately",
                "Add more particles",
            ],
            0,
        ),
        _q(
            "Why report the median over repeated benchmark trials rather than a single run?",
            [
                "To control run-to-run timing variance",
                "To increase the mean",
                "Because a single run is biased low",
                "To avoid warming the cache",
            ],
            0,
        ),
        tags=("benchmarking", "profiling"),
    ),
    _s(
        "impl_reproducibility",
        "Reproducibility & Deterministic Seeding",
        _C,
        "Guarantee bit-reproducible stochastic simulations through controlled seeding.",
        "A reproducible simulation seeds every source of randomness from a single recorded master "
        "seed, threads explicit RNG state rather than relying on hidden global state, and pins "
        "library versions so sampler behaviour is fixed. Determinism is what makes a sampling-based "
        "result (impl_monte_carlo, impl_particle_filter) a scientific claim rather than an "
        "anecdote: re-running must reproduce the same numbers byte-for-byte, which also makes "
        "regressions and benchmark comparisons meaningful. This extends comp_determinism to the "
        "full stochastic pipeline.",
        ("impl_benchmarking", "comp_determinism"),
        _q(
            "The key practice for reproducible stochastic simulation is to:",
            [
                "Seed all RNGs from one recorded master seed and pin versions",
                "Use a different random seed each run",
                "Avoid recording the seed",
                "Rely on global RNG state implicitly",
            ],
            0,
        ),
        _q(
            "Determinism matters for sampling-based results because it makes them:",
            [
                "Reproducible and therefore verifiable scientific claims",
                "Faster to compute",
                "Lower variance",
                "Independent of sample size",
            ],
            0,
        ),
        tags=("reproducibility", "seeding"),
    ),
    _s(
        "impl_scaling_tradeoffs",
        "Scaling Trade-offs & Factorisation",
        _C,
        "Reason about state-space explosion and the factorisation that tames it.",
        "A joint state of $K$ factors each with $n$ levels has $n^K$ configurations, so exact "
        "inference is exponential in the number of factors - the state-space explosion. Modelling "
        "the generative model as a product of conditionally independent factors and using a "
        "mean-field posterior turns $n^K$ into roughly $K$ tensors of size $n$, trading exactness "
        "for tractability. The art is choosing a factorisation whose discarded dependencies "
        "(measured by total correlation) are small enough that the approximation stays faithful.",
        ("impl_reproducibility", "comp_scaling"),
        _q(
            "A generative model with $K$ factors of $n$ states each has how many joint configurations?",
            ["$n^K$", "$nK$", "$K^n$", "$n+K$"],
            0,
        ),
        _q(
            "Factorising the model and using a mean-field posterior trades exactness for:",
            [
                "Tractability (linear rather than exponential cost)",
                "Higher accuracy",
                "Determinism",
                "More samples",
            ],
            0,
        ),
        tags=("scaling", "factorisation"),
    ),
    _s(
        "impl_gradient_checking",
        "Gradient Checking & Analytic Verification",
        _C,
        "Verify analytic gradients against finite-difference numerical estimates.",
        "An analytic gradient implementation is checked against the central finite difference "
        "$\\partial_\\theta F \\approx \\big(F(\\theta+\\epsilon)-F(\\theta-\\epsilon)\\big)/(2\\epsilon)$, "
        "with agreement to a small relative tolerance confirming correctness. The central scheme "
        "has $O(\\epsilon^2)$ truncation error, so $\\epsilon$ must be small enough to be accurate "
        "yet large enough to avoid floating-point cancellation. This numeric-vs-analytic check is "
        "the standard guard against silent gradient bugs in any free-energy minimiser.",
        ("impl_scaling_tradeoffs", "impl_vi_gradient"),
        _q(
            "The central finite-difference gradient of $F$ at $\\theta$ is approximately:",
            [
                "$(F(\\theta+\\epsilon)-F(\\theta-\\epsilon))/(2\\epsilon)$",
                "$(F(\\theta+\\epsilon)-F(\\theta))/\\epsilon$",
                "$F(\\theta)\\cdot\\epsilon$",
                "$(F(\\theta)-F(\\theta-\\epsilon))/\\epsilon^2$",
            ],
            0,
        ),
        _q(
            "Choosing $\\epsilon$ too small in finite differencing causes:",
            [
                "Floating-point cancellation error",
                "Truncation error to dominate",
                "Overflow",
                "The gradient to vanish exactly",
            ],
            0,
        ),
        tags=("gradient-check", "verification"),
    ),
    _s(
        "impl_generative_test",
        "Testing a Generative Model (Round-Trip Discipline)",
        _C,
        "Validate a generative model by recovering known causes from synthetic data.",
        "The decisive test of a generative model is a round trip: sample latent causes from a known "
        "ground truth, generate observations through the model, run inference, and confirm the "
        "posterior recovers the planted causes within a calibrated tolerance. Following a real-data "
        "discipline, the test exercises the real sampling, inference, and convergence "
        "(impl_gradient_checking, impl_reproducibility) end-to-end rather than replacing "
        "them - a green test that never runs the actual update is worthless. Posterior calibration "
        "checks (coverage of credible intervals) turn 'it ran' into 'it is correct.'",
        ("impl_gradient_checking", "impl_reproducibility"),
        _q(
            "A generative-model round-trip test checks that inference can:",
            [
                "Recover known planted causes from synthetic observations",
                "Run without raising an exception",
                "Produce any normalised distribution",
                "Match a precomputed posterior",
            ],
            0,
        ),
        _q(
            "Under a real-data test contract, the test must exercise:",
            [
                "The real sampling and inference end-to-end",
                "An inference shortcut returning fixed values",
                "Only the type signatures",
                "A cached posterior from a prior run",
            ],
            0,
        ),
        tags=("testing", "round-trip", "real-data"),
    ),
]
