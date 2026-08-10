"""American English style checks for authored manuscript prose."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z-]*\b")

# Closed list of British spelling variants mapped to their American forms.
#
# Entries are exact lowercase tokens because the auditor matches whole words, so
# every inflection that plausibly appears in this manuscript's vocabulary needs its
# own row; hyphenated compounds are additionally checked part by part. Forms that
# are also accepted American usage are deliberately absent (for example "dialogue",
# "analyses", and "acknowledgement"), as are tokens that double as technical
# literals -- "capitalise" is a cleveref package option in manuscript/preamble.md.
BRITISH_TO_AMERICAN: dict[str, str] = {
    "aluminium": "aluminum",
    "amongst": "among",
    "analyse": "analyze",
    "analysed": "analyzed",
    "analysing": "analyzing",
    "artefact": "artifact",
    "artefacts": "artifacts",
    "authorisation": "authorization",
    "authorisations": "authorizations",
    "authorise": "authorize",
    "authorised": "authorized",
    "authorises": "authorizes",
    "authorising": "authorizing",
    "behaviour": "behavior",
    "behavioural": "behavioral",
    "behaviourally": "behaviorally",
    "behaviours": "behaviors",
    "catalogue": "catalog",
    "catalogued": "cataloged",
    "catalogues": "catalogs",
    "cataloguing": "cataloging",
    "categorisation": "categorization",
    "categorisations": "categorizations",
    "categorise": "categorize",
    "categorised": "categorized",
    "categorises": "categorizes",
    "categorising": "categorizing",
    "centre": "center",
    "centred": "centered",
    "centres": "centers",
    "centring": "centering",
    "characterisation": "characterization",
    "characterisations": "characterizations",
    "characterise": "characterize",
    "characterised": "characterized",
    "characterises": "characterizes",
    "characterising": "characterizing",
    "colour": "color",
    "colour-coded": "color-coded",
    "coloured": "colored",
    "colouring": "coloring",
    "colours": "colors",
    "customisation": "customization",
    "customisations": "customizations",
    "customise": "customize",
    "customised": "customized",
    "customises": "customizes",
    "customising": "customizing",
    "defence": "defense",
    "defences": "defenses",
    "discretisation": "discretization",
    "discretisations": "discretizations",
    "discretise": "discretize",
    "discretised": "discretized",
    "discretises": "discretizes",
    "discretising": "discretizing",
    "emphasise": "emphasize",
    "emphasised": "emphasized",
    "emphasises": "emphasizes",
    "emphasising": "emphasizing",
    "endeavour": "endeavor",
    "endeavours": "endeavors",
    "enquire": "inquire",
    "enquiries": "inquiries",
    "enquiry": "inquiry",
    "enrol": "enroll",
    "enrolment": "enrollment",
    "enrolments": "enrollments",
    "enrols": "enrolls",
    "factorisation": "factorization",
    "factorisations": "factorizations",
    "factorise": "factorize",
    "factorised": "factorized",
    "factorises": "factorizes",
    "factorising": "factorizing",
    "favour": "favor",
    "favourable": "favorable",
    "favourably": "favorably",
    "favoured": "favored",
    "favouring": "favoring",
    "favours": "favors",
    "fibre": "fiber",
    "fibres": "fibers",
    "formalisation": "formalization",
    "formalisations": "formalizations",
    "formalise": "formalize",
    "formalised": "formalized",
    "formalises": "formalizes",
    "formalising": "formalizing",
    "fulfil": "fulfill",
    "fulfilment": "fulfillment",
    "fulfils": "fulfills",
    "generalisation": "generalization",
    "generalisations": "generalizations",
    "generalise": "generalize",
    "generalised": "generalized",
    "generalises": "generalizes",
    "generalising": "generalizing",
    "grey": "gray",
    "greyscale": "grayscale",
    "honour": "honor",
    "honoured": "honored",
    "honouring": "honoring",
    "honours": "honors",
    "hypothesise": "hypothesize",
    "hypothesised": "hypothesized",
    "hypothesises": "hypothesizes",
    "hypothesising": "hypothesizing",
    "initialisation": "initialization",
    "initialisations": "initializations",
    "initialise": "initialize",
    "initialised": "initialized",
    "initialises": "initializes",
    "initialising": "initializing",
    "judgement": "judgment",
    "judgements": "judgments",
    "labelled": "labeled",
    "labelling": "labeling",
    "labour": "labor",
    "labours": "labors",
    "learnt": "learned",
    "levelled": "leveled",
    "levelling": "leveling",
    "licence": "license",
    "licences": "licenses",
    "linearisation": "linearization",
    "linearisations": "linearizations",
    "linearise": "linearize",
    "linearised": "linearized",
    "linearises": "linearizes",
    "linearising": "linearizing",
    "litre": "liter",
    "litres": "liters",
    "marginalisation": "marginalization",
    "marginalisations": "marginalizations",
    "marginalise": "marginalize",
    "marginalised": "marginalized",
    "marginalises": "marginalizes",
    "marginalising": "marginalizing",
    "maths": "math",
    "maximisation": "maximization",
    "maximisations": "maximizations",
    "maximise": "maximize",
    "maximised": "maximized",
    "maximises": "maximizes",
    "maximising": "maximizing",
    "memorisation": "memorization",
    "memorisations": "memorizations",
    "memorise": "memorize",
    "memorised": "memorized",
    "memorises": "memorizes",
    "memorising": "memorizing",
    "metre": "meter",
    "metres": "meters",
    "minimisation": "minimization",
    "minimisations": "minimizations",
    "minimise": "minimize",
    "minimised": "minimized",
    "minimises": "minimizes",
    "minimising": "minimizing",
    "modelled": "modeled",
    "modelling": "modeling",
    "neighbour": "neighbor",
    "neighbourhood": "neighborhood",
    "neighbourhoods": "neighborhoods",
    "neighbouring": "neighboring",
    "neighbours": "neighbors",
    "normalisation": "normalization",
    "normalisations": "normalizations",
    "normalise": "normalize",
    "normalised": "normalized",
    "normalises": "normalizes",
    "normalising": "normalizing",
    "offence": "offense",
    "offences": "offenses",
    "optimisation": "optimization",
    "optimisations": "optimizations",
    "optimise": "optimize",
    "optimised": "optimized",
    "optimiser": "optimizer",
    "optimisers": "optimizers",
    "optimises": "optimizes",
    "optimising": "optimizing",
    "organisation": "organization",
    "organisations": "organizations",
    "organise": "organize",
    "organised": "organized",
    "organises": "organizes",
    "organising": "organizing",
    "orientated": "oriented",
    "parameterisation": "parameterization",
    "parameterisations": "parameterizations",
    "parameterise": "parameterize",
    "parameterised": "parameterized",
    "parameterises": "parameterizes",
    "parameterising": "parameterizing",
    "parametrisation": "parametrization",
    "parametrisations": "parametrizations",
    "parametrise": "parametrize",
    "parametrised": "parametrized",
    "parametrises": "parametrizes",
    "parametrising": "parametrizing",
    "penalise": "penalize",
    "penalised": "penalized",
    "penalises": "penalizes",
    "penalising": "penalizing",
    "personalisation": "personalization",
    "personalisations": "personalizations",
    "personalise": "personalize",
    "personalised": "personalized",
    "personalises": "personalizes",
    "personalising": "personalizing",
    "practise": "practice",
    "practised": "practiced",
    "practising": "practicing",
    "prioritisation": "prioritization",
    "prioritisations": "prioritizations",
    "prioritise": "prioritize",
    "prioritised": "prioritized",
    "prioritises": "prioritizes",
    "prioritising": "prioritizing",
    "programme": "program",
    "programmes": "programs",
    "randomisation": "randomization",
    "randomisations": "randomizations",
    "randomise": "randomize",
    "randomised": "randomized",
    "randomises": "randomizes",
    "randomising": "randomizing",
    "realisation": "realization",
    "realisations": "realizations",
    "realise": "realize",
    "realised": "realized",
    "realises": "realizes",
    "realising": "realizing",
    "recognisable": "recognizable",
    "recognise": "recognize",
    "recognised": "recognized",
    "recognises": "recognizes",
    "recognising": "recognizing",
    "regularisation": "regularization",
    "regularisations": "regularizations",
    "regularise": "regularize",
    "regularised": "regularized",
    "regularises": "regularizes",
    "regularising": "regularizing",
    "rigour": "rigor",
    "rigours": "rigors",
    "sceptic": "skeptic",
    "sceptical": "skeptical",
    "sceptically": "skeptically",
    "scepticism": "skepticism",
    "sceptics": "skeptics",
    "self-organisation": "self-organization",
    "self-organisations": "self-organizations",
    "self-organise": "self-organize",
    "self-organised": "self-organized",
    "self-organising": "self-organizing",
    "serialisation": "serialization",
    "serialisations": "serializations",
    "serialise": "serialize",
    "serialised": "serialized",
    "serialises": "serializes",
    "serialising": "serializing",
    "signalled": "signaled",
    "signalling": "signaling",
    "skilful": "skillful",
    "skilfully": "skillfully",
    "specialisation": "specialization",
    "specialisations": "specializations",
    "specialise": "specialize",
    "specialised": "specialized",
    "specialises": "specializes",
    "specialising": "specializing",
    "standardisation": "standardization",
    "standardisations": "standardizations",
    "standardise": "standardize",
    "standardised": "standardized",
    "standardises": "standardizes",
    "standardising": "standardizing",
    "summarisation": "summarization",
    "summarisations": "summarizations",
    "summarise": "summarize",
    "summarised": "summarized",
    "summarises": "summarizes",
    "summarising": "summarizing",
    "synchronisation": "synchronization",
    "synchronisations": "synchronizations",
    "synchronise": "synchronize",
    "synchronised": "synchronized",
    "synchronises": "synchronizes",
    "synchronising": "synchronizing",
    "synthesise": "synthesize",
    "synthesised": "synthesized",
    "synthesises": "synthesizes",
    "synthesising": "synthesizing",
    "three-colour": "three-color",
    "towards": "toward",
    "travelled": "traveled",
    "traveller": "traveler",
    "travellers": "travelers",
    "travelling": "traveling",
    "utilisation": "utilization",
    "utilisations": "utilizations",
    "utilise": "utilize",
    "utilised": "utilized",
    "utilises": "utilizes",
    "utilising": "utilizing",
    "visualisation": "visualization",
    "visualisations": "visualizations",
    "visualise": "visualize",
    "visualised": "visualized",
    "visualises": "visualizes",
    "visualising": "visualizing",
    "whilst": "while",
}


class AmericanEnglishError(ValueError):
    """Raised when manuscript prose uses a British spelling variant."""


@dataclass(frozen=True)
class AmericanEnglishIssue:
    """One British spelling occurrence found in authored manuscript prose."""

    path: Path
    line: int
    found: str
    suggestion: str
    excerpt: str

    def __str__(self) -> str:
        """Return a concise, reproducible issue line."""
        return (
            f"{self.path}:{self.line}: replace {self.found!r} with "
            f"{self.suggestion!r}: {self.excerpt}"
        )


def audit_american_english(manuscript_dir: Path) -> tuple[AmericanEnglishIssue, ...]:
    """Return British spelling variants in authored manuscript markdown.

    Bibliographic source titles live in ``references.bib`` and are intentionally outside
    this check because titles should match their cited sources. Code spans and fenced
    code blocks are also ignored so literal identifiers and commands remain unchanged.
    """
    root = Path(manuscript_dir)
    issues: list[AmericanEnglishIssue] = []
    for path in _authored_markdown_paths(root):
        text = _CODE_RE.sub(" ", path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in _WORD_RE.finditer(line):
                if _is_citation_key_token(line, match.start()):
                    continue
                found = match.group(0)
                suggestion = _suggestion(found)
                if suggestion is None:
                    continue
                issues.append(
                    AmericanEnglishIssue(
                        path=path.relative_to(root.parent),
                        line=line_number,
                        found=found,
                        suggestion=suggestion,
                        excerpt=line.strip(),
                    )
                )
    return tuple(issues)


def validate_american_english(manuscript_dir: Path) -> None:
    """Raise if authored manuscript markdown uses British spelling variants."""
    issues = audit_american_english(manuscript_dir)
    if issues:
        raise AmericanEnglishError(
            "British spelling variants found in manuscript prose:\n  "
            + "\n  ".join(str(issue) for issue in issues)
        )


def _authored_markdown_paths(root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(path for path in root.glob("*.md") if path.name != "99_references.md")
    )


def _is_citation_key_token(line: str, start: int) -> bool:
    return start > 0 and line[start - 1] == "@"


def _suggestion(found: str) -> str | None:
    replacement = _american_form(found.lower())
    if replacement is None:
        return None
    if found.isupper():
        return replacement.upper()
    if found[:1].isupper():
        return replacement.capitalize()
    return replacement


def _american_form(found: str) -> str | None:
    """Return the American form of ``found``, or ``None`` when it is already American.

    Hyphenated compounds are also checked part by part, so ``colour-coded`` is caught
    by the ``colour`` entry without needing a row of its own.
    """
    direct = BRITISH_TO_AMERICAN.get(found)
    if direct is not None:
        return direct
    if "-" not in found:
        return None
    parts = found.split("-")
    replacements = [BRITISH_TO_AMERICAN.get(part, part) for part in parts]
    if replacements == parts:
        return None
    return "-".join(replacements)
