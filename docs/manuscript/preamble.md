# LaTeX Preamble

This file contains LaTeX packages and commands that are automatically injected into the document compilation process.

> **Infrastructure Note**: This file is parsed by `infrastructure/rendering/latex_utils.py` and combined with the configuration output by `infrastructure/rendering/pdf_renderer.py` before final Pandoc execution to generate the physical PDF holding this text.

```latex
% Core mathematics
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{amsthm}
% The renderer may use these environments for structured remarks/examples even when
% the source manuscript contains none. Define the counter they share explicitly so
% Pandoc's injected declarations cannot reference an undefined theorem counter.
\newtheorem{theorem}{Theorem}
\newtheorem{remark}[theorem]{Remark}
\newtheorem{example}[theorem]{Example}

% Document layout
\usepackage{geometry}
% Keep the requested near-edge-to-edge horizontal layout while preserving a modest
% vertical breathing room for headers, footers, and page-turn readability.
\geometry{left=0.10in,right=0.10in,top=0.25in,bottom=0.25in}
\usepackage{float}
\usepackage{graphicx}

% Tables
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}

% Algorithm typesetting (for pseudocode in §2 Methodology)
\usepackage[ruled,vlined,linesnumbered]{algorithm2e}

% Code listings
\usepackage{listings}

% Typography and formatting
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{siunitx}

% Cross-references and citations
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    allcolors=red
}
\usepackage[capitalise,noabbrev]{cleveref}
\usepackage{natbib}

% ── Unicode-capable mono font for code listings ──────────────────────
% JuliaMono (TeX Live 2026) covers the full math/Greek glyph set used in
% scientific code blocks; the default lmmono lacks \alpha/\mu/\partial/\nabla.
%
% Prefer the pinned TeX Live font when present, but keep the manuscript compilable
% on TeX Live versions or distributions that install a different mono font set.
\usepackage{fontspec}
\IfFileExists{/usr/local/texlive/2026/texmf-dist/fonts/truetype/public/juliamono/JuliaMono-Regular.ttf}{%
  \setmonofont{JuliaMono-Regular}[
    Path           = /usr/local/texlive/2026/texmf-dist/fonts/truetype/public/juliamono/,
    Extension      = .ttf,
    UprightFont    = *,
    BoldFont       = JuliaMono-Bold,
    ItalicFont     = JuliaMono-RegularItalic,
    BoldItalicFont = JuliaMono-BoldItalic,
    Scale          = MatchLowercase,
  ]%
}{%
  % TeX Live ships Latin Modern Mono as an OpenType file, and fontconfig does not
  % always register the family name on a minimal installation (TinyTeX), so probe
  % the file with fontspec's own check before falling back to the family name.
  \IfFontExistsTF{lmmono10-regular.otf}{%
    \setmonofont{lmmono10-regular.otf}[Scale=MatchLowercase]%
  }{%
    \setmonofont{Latin Modern Mono}[Scale=MatchLowercase]%
  }%
}

% Math font for unicode-math: Latin Modern Math (TeX Live) has full BMP
% coverage including U+2223 (\mid), U+226A/226B (\ll/\gg), and the Greek/
% blackboard letters used in equations. Without an explicit \setmathfont,
% unicode-math falls back to lmroman text font which lacks several glyphs
% and emits "Missing character" warnings on every \mid in math mode.
\setmathfont{latinmodern-math.otf}
```
