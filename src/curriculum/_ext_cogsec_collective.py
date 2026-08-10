# Curriculum expansion (pass #5): cognitive security + collective behaviour. Imported by catalog.py.
from src.curriculum._ext_helpers import _APP, _q, _s

_NEW_COGSEC = [
    _s(
        "cog_info_ecosystem",
        "The Information Ecosystem as a Shared Generative Model",
        _APP,
        "Model a population's shared beliefs as one coupled generative model.",
        "An information ecosystem is a network of minds whose individual generative models "
        "$p_i(o,s)$ are coupled through shared observations (media, speech, sensors). Treating the "
        "ecosystem as a single distributed generative model lets us ask system-level questions: "
        "what hidden causes $s$ does the population infer, and how faithfully do its predictions "
        "track the world? Cognitive security is the discipline of keeping that collective inference "
        "well-calibrated against reality.",
        ("app_cognitive_security", "fep_generative_model", "fep_collective_inference"),
        _q(
            "Treating an information ecosystem as a generative model means asking which question?",
            [
                "How faithfully the population's inferred causes track the world",
                "How fast messages propagate",
                "How many users are online",
            ],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_epistemic_communities",
        "Epistemic Communities & Shared Priors",
        _APP,
        "Explain why a community converges on common priors over hidden causes.",
        "Members of an epistemic community share priors $p(s)$ acquired through common training, "
        "sources and discourse. Shared priors are efficient: they compress the space of hypotheses "
        "each member must entertain and make communication low-bandwidth. The same compression is a "
        "vulnerability - a prior held in common but poorly calibrated propagates correlated error, "
        "which is why healthy ecosystems preserve prior diversity.",
        ("cog_info_ecosystem", "p_bayes_theorem"),
        _q(
            "Why are widely shared priors simultaneously efficient and risky?",
            [
                "They compress hypotheses but propagate correlated error if miscalibrated",
                "They increase message length",
                "They are always more accurate than individual priors",
            ],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_sensemaking",
        "Sensemaking as Collective Inference",
        _APP,
        "Frame collective sensemaking as distributed posterior estimation.",
        "Sensemaking is the community-scale analogue of perception: many agents pool evidence to "
        "estimate a shared posterior $p(s\\mid o)$ over what is happening. Each contribution is a "
        "likelihood term; deliberation approximates Bayesian updating across the group. Robust "
        "sensemaking requires that contributed evidence be conditionally informative and that the "
        "aggregation rule weight sources by their reliability rather than their volume.",
        ("cog_epistemic_communities", "it_info_gain"),
        _q(
            "Robust collective sensemaking weights contributed evidence by:",
            ["Source reliability", "Posting frequency", "Message length"],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_misinformation",
        "Misinformation as Injected False Priors / Corrupted Likelihoods",
        _APP,
        "Distinguish prior-poisoning from likelihood-corruption attacks on inference.",
        "Two failure modes map cleanly onto the generative model. Injecting a false prior $p(s)$ "
        "biases inference before any evidence arrives; corrupting the likelihood $p(o\\mid s)$ "
        "(fabricated 'evidence', deepfakes) makes genuine data point at the wrong cause. Both raise "
        "the divergence between the community's posterior and reality. Naming the target - prior vs. "
        "likelihood - tells a defender which calibration step to harden.",
        ("cog_sensemaking",),
        _q(
            "A deepfake that supplies fabricated evidence primarily corrupts the:",
            ["Likelihood $p(o\\mid s)$", "Prior $p(s)$", "Action policy"],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_precision_attack",
        "Precision & Attention as the Attack Surface",
        _APP,
        "Show how hijacking precision reweights what a mind treats as evidence.",
        "Precision is the inverse-variance weight an agent assigns to a prediction error; it sets "
        "how strongly a signal updates beliefs. Attention is precision allocation. An adversary need "
        "not change the data if they can change its weighting: amplifying the precision of "
        "low-quality channels or suppressing trusted ones reshapes the posterior. Defences restore "
        "calibrated precision - weighting signals by demonstrated reliability, not salience.",
        ("cog_misinformation", "fep_precision"),
        _q(
            "Hijacking precision changes inference by altering:",
            [
                "How strongly a signal is weighted, not the signal itself",
                "The raw content of every message",
                "The number of agents present",
            ],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_narrative_policy_prior",
        "Narrative as a Policy Prior",
        _APP,
        "Read narratives as priors over policies that shape collective action.",
        "A narrative is a compressed story about hidden causes that also carries a prior $p(\\pi)$ "
        "over which policies $\\pi$ are sensible. Because expected free energy is weighted by this "
        "policy prior, a narrative steers behaviour even when the evidence is unchanged. Defensive "
        "cognitive security audits the narratives in circulation for which actions they make "
        "thinkable, and protects the plurality of available policies.",
        ("cog_precision_attack", "ai_pomdp"),
        _q(
            "A narrative influences collective behaviour chiefly by acting as a prior over:",
            ["Policies", "Sensory precision", "Observation likelihoods"],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_bayesian_persuasion",
        "Bayesian Persuasion & Framing",
        _APP,
        "Analyse framing as a sender's choice of signalling structure under shared inference rules.",
        "In Bayesian persuasion a sender commits to a signalling scheme $p(o\\mid s)$ knowing the "
        "receiver will update rationally. Framing chooses which partition of the state to make "
        "salient - both legitimate (clear public-health messaging) and adversarial uses share this "
        "structure. The defensive question is whether the signalling scheme is truth-conducive: does "
        "the induced posterior move toward or away from the actual state?",
        ("cog_narrative_policy_prior", "p_bayes_theorem"),
        _q(
            "The defensive test for a framing/signalling scheme is whether it:",
            [
                "Moves the receiver's posterior toward the true state",
                "Maximises engagement",
                "Uses the fewest words",
            ],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_trust_precision",
        "Trust as Learned Precision over Sources",
        _APP,
        "Model trust as a slowly-learned precision parameter on each source.",
        "Trust is the precision an agent has learned to assign to a source's reports, updated over "
        "repeated encounters as a hierarchical hyperparameter. Well-calibrated trust tracks a "
        "source's long-run accuracy; manufactured trust (astroturfing, borrowed credibility) inflates "
        "precision without the underlying reliability. Resilient ecosystems update trust on outcomes, "
        "making it expensive to spoof and quick to revoke.",
        ("cog_precision_attack", "ai_precision_gamma"),
        _q(
            "Manufactured trust attacks inflate a source's precision without raising its:",
            ["Demonstrated reliability", "Posting volume", "Follower count"],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_epistemic_immunity",
        "Epistemic Immune Responses & Resilience",
        _APP,
        "Describe resilience as free-energy-minimising rejection of poorly-fitting injected beliefs.",
        "An ecosystem with calibrated priors and trust resists injected beliefs the way an immune "
        "system rejects antigens: a claim that fits the world poorly generates large prediction error "
        "and, weighted by appropriate precision, is down-updated rather than absorbed. Resilience is "
        "thus an emergent property of good calibration, not censorship. Over-reactive 'autoimmune' "
        "regimes that reject all novel evidence are themselves a failure mode.",
        ("cog_trust_precision", "cog_misinformation"),
        _q(
            "Epistemic resilience emerges primarily from:",
            [
                "Calibrated priors and precision, not censorship",
                "Blocking all novel claims",
                "Maximising message throughput",
            ],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_adversarial_inference",
        "Adversarial Inference: Modelling the Adversary's Generative Model",
        _APP,
        "Defend by inferring the adversary's own generative model and objectives.",
        "A sophisticated defender runs inference one level up: estimating the adversary's generative "
        "model, their assumed model of the target audience, and the policy prior they are trying to "
        "install. This recursive theory-of-mind turns defence into a POMDP where the hidden state "
        "includes the adversary's intent. The aim is to reduce the defender's uncertainty about the "
        "manipulation strategy, then act to neutralise it transparently.",
        ("cog_epistemic_immunity", "cog_bayesian_persuasion"),
        _q(
            "Adversarial inference adds which hidden state to the defender's model?",
            [
                "The adversary's intent and strategy",
                "The defender's own past actions",
                "The raw text of every message",
            ],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_commons",
        "Collective Epistemic Security & the Information Commons",
        _APP,
        "Treat shared epistemic infrastructure as a commons requiring active maintenance.",
        "Calibrated priors, trustworthy sources and shared evidentiary standards are a commons: "
        "individually rational free-riding (spreading unchecked claims) degrades a resource everyone "
        "depends on. Governing the information commons means institutions and norms that internalise "
        "the externalities of low-quality signalling, preserving the conditions under which collective "
        "inference stays accurate. This connects cognitive security to multi-agent coordination.",
        ("cog_adversarial_inference", "app_collective"),
        _q(
            "Why is unchecked claim-spreading a commons problem?",
            [
                "Private benefit degrades a shared epistemic resource",
                "It uses too much bandwidth",
                "It is always individually irrational",
            ],
            0,
        ),
        tags=("cogsec",),
    ),
    _s(
        "cog_epistemic_health_metrics",
        "Measuring Epistemic Health: Information-Theoretic Diversity",
        _APP,
        "Quantify ecosystem health with entropy, mutual information and source diversity.",
        "Epistemic health admits measurement. Source diversity is the entropy of the source "
        "distribution; redundancy and capture show up as high mutual information between supposedly "
        "independent channels $I(X;Y)$, signalling correlated rather than independent evidence. "
        "Monitoring these quantities over time detects homogenisation and coordinated inauthentic "
        "behaviour before the posterior visibly drifts. The metrics are diagnostic, defensive, and "
        "content-neutral.",
        ("cog_commons", "it_mutual_information"),
        _q(
            "High mutual information between nominally independent channels indicates:",
            [
                "Correlated (non-independent) evidence - possible capture",
                "Healthy diversity",
                "Higher truth content",
            ],
            0,
        ),
        tags=("cogsec",),
    ),
]

_NEW_COLLECTIVE = [
    _s(
        "col_stigmergy",
        "Stigmergy: The Environment as Shared Memory",
        _APP,
        "Explain how environmental traces externalise belief and coordinate agents.",
        "Stigmergy is coordination through persistent modifications of a shared environment - ant "
        "pheromone fields, wasp nest geometry - rather than direct messaging. The environment acts as "
        "an externalised, slowly-decaying belief state that every agent both reads and writes. This "
        "offloads memory and inference into the world, letting a colony aggregate evidence across time "
        "without any individual holding the global picture.",
        ("app_collective", "app_ant_colonies"),
        _q(
            "Stigmergy coordinates agents primarily through:",
            [
                "Persistent traces in a shared environment",
                "Direct point-to-point messages",
                "A central controller",
            ],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_foraging_inference",
        "Ant-Colony Foraging as Distributed Inference",
        _APP,
        "Cast pheromone-mediated foraging as colony-level posterior estimation over resource locations.",
        "A foraging colony infers a posterior over where food is. Each laden ant deposits pheromone "
        "proportional to reward, so the evaporating field approximates a likelihood-weighted estimate "
        "$p(\\text{location}\\mid \\text{returns})$ that the colony exploits and refines. Evaporation "
        "implements forgetting of stale evidence, and recruitment implements precision-weighted "
        "sampling toward high-value hypotheses - the explore/exploit trade-off realised in chemistry.",
        ("col_stigmergy",),
        _q(
            "Pheromone evaporation in foraging functions as:",
            ["Forgetting of stale evidence", "Reward maximisation", "Direct messaging"],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_nested_models",
        "Shared & Nested Generative Models across Agents",
        _APP,
        "Describe how agents embed models of each other within a shared hierarchical model.",
        "Coordinated collectives share parts of a generative model: a common model of the environment "
        "and, often, nested models of one another's states. When each agent's model includes a model of "
        "its neighbours, inference becomes hierarchical across agents, and consensus corresponds to the "
        "agents settling into mutually consistent posteriors. This nesting is what makes a swarm more "
        "than a sum of independent inferences.",
        ("col_foraging_inference", "fep_markov_blanket"),
        _q(
            "Nesting a model of neighbours inside each agent makes inference:",
            ["Hierarchical across agents", "Strictly independent", "Impossible"],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_communication_inference",
        "Communication as Inference: Signalling to Align Beliefs",
        _APP,
        "Frame signals as actions chosen to reduce a partner's uncertainty about hidden states.",
        "Communication is action in a partner's sensory space: an agent emits a signal expected to "
        "drive the recipient's posterior toward the sender's belief about a hidden state. Honest, "
        "informative signalling raises the mutual information between signal and state, $I(\\text{signal};s)$, "
        "and is favoured when it lowers the dyad's joint free energy. This recasts the alignment of "
        "beliefs as cooperative active inference.",
        ("col_nested_models", "it_mutual_information"),
        _q(
            "Informative communication is characterised by high mutual information between signal and:",
            ["The hidden state being conveyed", "The clock time", "The agent's size"],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_shared_blanket",
        "The Multi-Agent / Shared Markov Blanket",
        _APP,
        "Identify when a group of agents acquires a collective Markov blanket and behaves as one system.",
        "When agents couple tightly, their individual Markov blankets can compose into a single "
        "blanket separating the collective's internal states from its environment. At that point the "
        "group is itself a thing that does inference - a superorganism - with its own sensory and "
        "active states. The colony-as-individual is not metaphor but a precise statement about the "
        "statistical boundary that emerges from coupling.",
        ("col_communication_inference",),
        _q(
            "A shared Markov blanket lets a group of agents be described as:",
            [
                "A single inferring system (superorganism)",
                "Many fully independent agents",
                "A random aggregate with no boundary",
            ],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_swarm_intelligence",
        "Swarm Intelligence & Decentralised Decision",
        _APP,
        "Explain how local rules yield globally adaptive, robust decisions without central control.",
        "Swarm intelligence is decentralised inference: each agent follows local update rules using "
        "only neighbour and environmental signals, yet the collective computes a coherent decision. "
        "Robustness comes from redundancy and the absence of a single point of failure; adaptability "
        "comes from the same free-energy gradient acting at every node. The design lesson is that "
        "global competence need not require global information.",
        ("col_shared_blanket", "ai_active_inference_loop"),
        _q(
            "Swarm intelligence achieves global competence using:",
            [
                "Only local information at each agent",
                "A central planner",
                "Global broadcast to all",
            ],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_quorum_sensing",
        "Quorum Sensing as Collective Evidence Accumulation",
        _APP,
        "Model quorum thresholds as a sequential-evidence test for committing to a collective action.",
        "Quorum sensing - in house-hunting ants or bacteria - lets a collective wait until accumulated "
        "local signals cross a threshold before committing. This is a distributed sequential "
        "probability-ratio test: the threshold trades off speed against accuracy, and a higher quorum "
        "demands more evidence before the group acts. It is collective evidence accumulation made "
        "physical, with the threshold encoding the cost of a premature decision.",
        ("col_swarm_intelligence", "p_markov_chain"),
        _q(
            "Raising a quorum threshold trades speed for:",
            ["Decision accuracy", "Lower energy use", "Faster commitment"],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_niche_construction",
        "Cultural Niche Construction",
        _APP,
        "Show how agents reshape their environment and thereby the priors of future agents.",
        "Niche construction is the feedback loop in which agents modify their environment (trails, "
        "structures, accumulated culture) and those modifications become part of the generative model "
        "inherited by the next cohort. The environment thus carries priors across generations, "
        "extending stigmergy through time. Adaptive niches lower the free energy of those who inherit "
        "them; maladaptive ones lock in error - a structural risk shared with information ecosystems.",
        ("col_quorum_sensing", "col_stigmergy"),
        _q(
            "Cultural niche construction transmits priors across generations through:",
            [
                "Inherited modifications of the environment",
                "Genetic mutation alone",
                "Direct belief copying only",
            ],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_conformity_herding",
        "Social Conformity & Herding as Shared Priors",
        _APP,
        "Analyse conformity as precision on social evidence and herding as information cascade.",
        "Conformity arises when agents assign high precision to social evidence relative to private "
        "observation; herding and information cascades occur when each agent rationally weights others' "
        "choices and stops contributing private evidence. Moderate social precision is adaptive "
        "(cheap, fast learning); excessive social precision collapses diversity and lets early errors "
        "cascade. The same precision knob that enables coordination enables fragility.",
        ("col_niche_construction", "col_communication_inference"),
        _q(
            "Information cascades occur when agents over-weight social evidence and stop sharing their:",
            ["Private observations", "Location", "Energy budget"],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_multiagent_efe",
        "Multi-Agent Expected Free Energy",
        _APP,
        "Extend expected free energy to interacting agents selecting joint policies.",
        "In a collective, each agent's expected free energy includes terms that depend on others' "
        "policies, so policy selection becomes a coupled, game-theoretic optimisation. Epistemic value "
        "now includes resolving uncertainty about partners, and pragmatic value includes reaching "
        "shared preferred outcomes. Cooperative equilibria emerge when minimising one's own expected "
        "free energy also lowers the group's - the formal basis for self-organised coordination.",
        ("col_conformity_herding", "ai_expected_free_energy"),
        _q(
            "In multi-agent settings, each agent's expected free energy depends on:",
            [
                "The policies of other agents",
                "Only its own private reward",
                "Only the immediate sensory input",
            ],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_morphogenesis",
        "Morphogenesis & Pattern Formation as Inference",
        _APP,
        "Interpret developmental pattern formation as cells minimising free energy to a target morphology.",
        "Pattern formation - from Turing reaction-diffusion to collective cell migration - can be read "
        "as a population of agents inferring and acting to realise a target configuration encoded as "
        "prior preferences. Each cell senses local signals and adjusts state and position to reduce "
        "prediction error against the morphological prior. Development thereby becomes large-scale "
        "active inference, and regeneration becomes re-inference after perturbation.",
        ("col_multiagent_efe", "fep_self_organisation"),
        _q(
            "Morphogenesis-as-inference treats the target body plan as:",
            [
                "A prior preference cells act to realise",
                "An external reward signal",
                "A random outcome",
            ],
            0,
        ),
        tags=("collective",),
    ),
    _s(
        "col_generalised_synchrony",
        "Generalised Synchrony across Coupled Agents",
        _APP,
        "Describe how coupled agents fall into generalised synchrony, the dynamical signature of shared inference.",
        "When agents are reciprocally coupled, their internal states can enter generalised synchrony: "
        "a smooth functional relationship between trajectories, the dynamical-systems signature of two "
        "systems inferring each other. This underlies turn-taking, joint attention and flocking, and "
        "is the substrate on which all the preceding skills - stigmergy, communication, shared blankets "
        "- ultimately rest. Coordination, at base, is coupled minds achieving synchrony of belief.",
        ("col_shared_blanket", "col_multiagent_efe"),
        _q(
            "Generalised synchrony between coupled agents is the dynamical signature of:",
            [
                "Two systems inferring each other",
                "Independent random walks",
                "A central clock",
            ],
            0,
        ),
        tags=("collective",),
    ),
]
