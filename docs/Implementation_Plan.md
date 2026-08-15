# MOS Capacitor C--V Simulator — Implementation Plan

## 1. Project Overview

**Project:** Python-based MOS capacitor C--V characteristic simulator
with a gra\phical web interface.

**Primary objective:** Build a physically meaningful MOS capacitor model
that accepts device parameters, calculates capacitance across an applied
gate-voltage range, identifies accumulation/depletion/inversion regions,
and plots the C--V characteristic interactively.

**Final deliverable:** A single Windows executable
(`MOS-Capacitor-Simulator.exe`) created with PyInstaller.

------------------------------------------------------------------------

## 2. Model Reference and Locked Conventions

### Primary reference

The implementation will use **S. M. Sze and Kwok K. Ng, _Physics of Semiconductor Devices_, 3rd ed.** as the primary semiconductor-device reference for the MOS capacitor electrostatics and C–V model.

Where a numerical constant or material parameter is needed, the implementation will document its source. If the course textbook uses a different convention, the course convention takes precedence and the implementation/report will explicitly state the difference.

### Locked substrate/sign convention

The base device is:

- p-type silicon substrate
- \(N_A > 0\) denotes acceptor concentration
- Positive gate voltage produces positive surface potential \(\psi_s > 0\)
- Negative gate voltage produces negative surface potential \(\psi_s < 0\)
- Semiconductor charge \(Q_s\) is defined as charge per unit area on the semiconductor
- Therefore:
  - accumulation: \(\psi_s < 0,\ Q_s > 0\)
  - depletion: \(0 < \psi_s < 2\phi_F,\ Q_s < 0\)
  - strong inversion: \(\psi_s > 2\phi_F,\ Q_s < 0\)

Gate voltage is defined by:

\[
V_G = V_{FB} + \psi_s - \frac{Q_s(\psi_s)}{C'_{ox}}
\]

with the above \(Q_s\) sign convention.

This convention is locked before physics implementation so that region classification, \(V_T\), numerical solving, and plotting all use the same signs.

## 3. Final Technology Stack

  -----------------------------------------------------------------------
  Component               Technology              Purpose
  ----------------------- ----------------------- -----------------------
  Language                Python 3.12             Core implementation

  Package/environment     `uv`                    Dependency and
  manager                                         environment management

  Numerical arrays        NumPy                   Vectorized calculations

  Scientific computing    SciPy                   Numerical root solving
                                                  and related
                                                  calculations

  Plotting                Matplotlib              C--V visualization

  GUI/web interface       Streamlit               Interactive simulator
                                                  UI

  Testing                 pytest                  Automated validation

  Packaging               PyInstaller             Single Windows
                                                  executable
  -----------------------------------------------------------------------

### Core principle

The physics/model layer must remain independent of Streamlit. The GUI is
only a presentation and interaction layer.

------------------------------------------------------------------------

## 4. Project Architecture

``` text
mos-capacitor/
│
├── app.py
│
├── physics/
│   ├── __init__.py
│   ├── constants.py
│   ├── parameters.py
│   ├── mos_capacitor.py
│   └── solver.py
│
├── visualization/
│   ├── __init__.py
│   └── cv_plot.py
│
├── tests/
│   └── test_mos.py
│
├── launcher.py
├── pyproject.toml
├── uv.lock
├── README.md
└── Implementation.md
```

### Responsibility of each module

#### `app.py`

-   Streamlit application entry point.
-   Collect user inputs.
-   Call the physics model.
-   Display calculated values.
-   Display plots and analysis.
-   Must not contain the actual MOS equations.

#### `physics/constants.py`

Contains physical constants such as: - Elementary charge (q) - Boltzmann
constant (k) - Vacuum permittivity (`\epsilon`{=tex}\_0) - Silicon
relative permittivity - Silicon dioxide relative permittivity
- Documented silicon material parameters for \(E_g(T)\), \(N_C(T)\), and \(N_V(T)\)

#### `physics/parameters.py`

Defines validated device/model parameters.

Typical inputs: - Substrate doping (N_A) - Oxide thickness (t\_{ox}) -
Gate area (A) - Temperature (T) - M\etal-semiconductor work-function
difference (`\Phi`{=tex}*{MS}) - Oxide charge (Q*{ox}), initially zero
by default - Intrinsic carrier concentration (n_i)

#### `physics/mos_capacitor.py`

Main MOS capacitor model.

Responsibilities: - Calculate (C\_{ox}) - Calculate (`\phi`{=tex}*F) -
Calculate (V*{FB}) - Calculate (V_T) - Calculate depletion width -
Calculate depletion capacitance - Calculate total MOS capacitance -
Generate C--V data - Identify operating regions

#### `physics/solver.py`

Numerical methods used by the MOS model.

Responsibilities: - Surface-potential equation solving - Root finding
using SciPy - Analytical derivative of \(Q_s(\psi_s)\) - Robust
convergence/error handling

#### `visualization/cv_plot.py`

Matplotlib-specific plotting logic.

Responsibilities: - C--V plot - Region annotations - Selected-voltage
marker - Optional comparison curves

#### `tests/test_mos.py`

Automated validation of: - Physical constants - Analytical
calculations - Numerical solver - Expected limiting behavior - Parameter
sensitivity

#### `launcher.py`

Packaging/runtime launcher for the final single executable.

Responsibilities: - Start the Streamlit application. - Run it locally. -
Open the browser automatically. - Support PyInstaller packaging.

------------------------------------------------------------------------

# 5. Physics Scope
## 5.1 Initial model assumptions

The initial simulator will model an **ideal p-type silicon MOS
capacitor**.

Initial assumptions:

-   Uniform substrate doping.
-   One-dimensional MOS structure.
-   Silicon substrate.
-   SiO₂ gate dielectric.
-   Ideal planar capacitor.
-   No interface traps initially.
-   No frequency-dependent series resistance initially.
-   (Q\_{ox}=0) unless explicitly enabled later.
-   Temperature is configurable.
-   Quasi-static/low-frequency and high-frequency behavior will be
    distinguished.

These assumptions must be documented in the application/report.

------------------------------------------------------------------------

# 6. Unit Convention
## GUI units

The GUI may use convenient semiconductor-engineering units:

-   Doping: (cm\^{-3})
-   Oxide thickness: nm
-   Area: (`\mu `{=tex}m\^2)
-   Voltage: V
-   Temperature: K

## Internal units

**All physics calculations must use SI units.**

Examples:

\[ N_A\[cm\^{-3}\] `\rightarrow `{=tex}N_A\[m\^{-3}\] \]

\[ t\_{ox}\[nm\] `\rightarrow `{=tex}t\_{ox}\[m\] \]

\[ A\[`\mu `{=tex}m\^2\] `\rightarrow `{=tex}A\[m\^2\] \]

This rule is mandatory to reduce unit-related calculation errors.

------------------------------------------------------------------------

# 7. Fundamental Equations

**NOTE:** Equations in this Markdown file may not render correctly in all
viewers due to prior copy/paste corruption. Before implementation,
re-derive and re-typeset every equation from this section directly into
a clean LaTeX or code reference — do not copy-paste symbols out of this
file into source code.

## 7.1 Oxide capacitance

\[ C\_{ox}=`\frac{\epsilon_{ox}A}{t_{ox}}`{=tex} \]

where

\[ `\epsilon`{=tex}\_{ox}=3.9`\epsilon`{=tex}\_0 \]

The capacitance per unit area is:

\[ C'\_{ox}=`\frac{\epsilon_{ox}}{t_{ox}}`{=tex} \]

------------------------------------------------------------------------

## 7.2 Silicon permittivity

\[ `\epsilon`{=tex}\_{si}=11.7`\epsilon`{=tex}\_0 \]

------------------------------------------------------------------------

## 7.3 Fermi potential

For a p-type substrate:

\[
`\phi`{=tex}\_F=`\frac{kT}{q}`{=tex}`\ln`{=tex}`\left`{=tex}(`\frac{N_A}{n_i}`{=tex}`\right`{=tex})
\]

The sign convention must be explicitly defined and used consistently
throughout the model.

------------------------------------------------------------------------

## 7.3a Temperature-dependent intrinsic carrier concentration

Because temperature is a user-configurable parameter, \(n_i\) must not be treated as a fixed 300 K constant.

The implementation will calculate silicon bandgap using the Varshni relation:

\[
E_g(T)
=
E_{g0}
-
\frac{\alpha T^2}{T+\beta}
\]

with documented silicon material parameters.

### Silicon material parameters

| Parameter | Value | Source |
|---|---:|---|
| \(E_{g0}\) | 1.170 eV | Sze & Ng, 3rd ed. |
| \(\alpha\) | \(4.73\times10^{-4}\) eV/K | Sze & Ng, 3rd ed. |
| \(\beta\) | 636 K | Sze & Ng, 3rd ed. |
| \(N_C(300)\) | \(2.8\times10^{19}\) cm\(^{-3}\) | Sze & Ng, 3rd ed. |
| \(N_V(300)\) | \(1.04\times10^{19}\) cm\(^{-3}\) | Sze & Ng, 3rd ed. |

These are the values that `physics/constants.py` will hard-code as the
documented silicon material-parameter set. The source is **S. M. Sze
and Kwok K. Ng, _Physics of Semiconductor Devices_, 3rd ed.**

The effective density of states will be modeled as:

\[
N_C(T)=N_C(300)\left(\frac{T}{300}
\right)^{3/2}
\]

\[
N_V(T)=N_V(300)\left(\frac{T}{300}
\right)^{3/2}
\]

and therefore:

\[
n_i(T)
=
\sqrt{N_C(T)N_V(T)}
\exp\left(-\frac{E_g(T)}{2kT}
\right)
\]

When energy is represented in electron-volts, the implementation must use a consistent conversion to joules where required by the equation.

The chosen \(E_{g0}, \alpha, \beta, N_C(300), N_V(300)\) values will be stored as documented silicon material parameters, not scattered magic numbers.

## 7.4 Flat-band voltage

For the ideal initial model:

\[ V\_{FB}=`\Phi`{=tex}\_{MS} \]

For the extended model:

\[ V\_{FB}=`\Phi`{=tex}\_{MS}-`\frac{Q_{ox}}{C_{ox}}`{=tex} \]

Initially:

\[ Q\_{ox}=0 \]

------------------------------------------------------------------------

## 7.5 Threshold voltage

For the p-type substrate model:

\[ V_T = V\_{FB}+2`\phi`{=tex}*F+
`\frac{\sqrt{4q\epsilon_{si}N_A\phi_F}}`{=tex} {C'*{ox}} \]

The exact sign convention must be verified against the chosen
textbook/reference before implementation.

------------------------------------------------------------------------

## 7.6 Maximum depletion width

At strong inversion:

\[ `\psi`{=tex}\_s`\approx2`{=tex}`\phi`{=tex}\_F \]

Therefore:

\[ W\_{d,max} = `\sqrt{
\frac{4\epsilon_{si}\phi_F}
{qN_A}
}`{=tex} \]

------------------------------------------------------------------------

## 7.7 Depletion capacitance

\[ C\_{dep} = `\frac{\epsilon_{si}A}{W_d}`{=tex} \]

------------------------------------------------------------------------

## 7.8 Accumulation-region treatment

The depletion-width equation is **not valid in accumulation** because the semiconductor surface has \(\psi_s < 0\) and majority carriers accumulate at the surface.

For the Level 1 analytical model, accumulation will therefore be treated explicitly rather than by extending the depletion-width equation into negative \(\psi_s\).

The educational Level 1 approximation is:

\[
C_{MOS} \approx C_{ox}
\]

once the device is sufficiently into accumulation.

Near flatband, the more rigorous Level 2 surface-potential model will determine the semiconductor response continuously.

This explicit treatment prevents an invalid operation such as evaluating:

\[
W_d=\sqrt{\frac{2\epsilon_{si}\psi_s}{qN_A}}
\]

for negative \(\psi_s\).

## 7.9 Total capacitance

Oxide and depletion capacitances are in series:

\[ `\frac{1}{C}`{=tex} = `\frac{1}{C_{ox}}`{=tex} +
`\frac{1}{C_{dep}}`{=tex} \]

Therefore:

\[ C= `\frac{C_{ox}C_{dep}}`{=tex} {C\_{ox}+C\_{dep}} \]

------------------------------------------------------------------------

# 8. C--V Model Strategy
The simulator will be implemented in two conceptual levels.

## Level 1 — Analytical/depletion approximation

This provides: - Fast calculation. - Easy debugging. - Easy comparison
with textbook equations. - A clear educational model.

The curve will represent:

``` text
Accumulation → Depletion → Inversion
```

## 8.1 Level 1 piecewise definition

Level 1 is **HF-only by construction**. It uses the depletion
approximation and frozen inversion charge; it does not model the
low-frequency/quasi-static rise in capacitance in inversion.

Given \(V_G\):

1. Compute the flatband-referenced bias:

\[
\psi_{s,bias}=V_G-V_{FB}
\]

2. If \(\psi_{s,bias}<0\) (accumulation):

\[
C_{MOS}=C_{ox}
\]

```text
region = "accumulation"
```

3. If \(\psi_{s,bias}\ge0\), solve the depletion approximation from:

\[
V_G
=
V_{FB}
+
\psi_s
+
\frac{\sqrt{2q\epsilon_{si}N_A\psi_s}}
{C'_{ox}}
\]

This is quadratic in \(\sqrt{\psi_s}\), solved directly rather than by
invoking the full Level 2 \(Q_s(\psi_s)\) equation.

**Closed-form solution.** Let \(x=\sqrt{\psi_s}\) (\(x\ge0\)) and
\(k=\sqrt{2q\epsilon_{si}N_A}/C'_{ox}\). The equation becomes:

\[
V_G-V_{FB}-x^2-kx=0
\quad\Longleftrightarrow\quad
x^2+kx-(V_G-V_{FB})=0
\]

which is a standard quadratic in \(x\):

\[
x=\frac{-k+\sqrt{k^2+4(V_G-V_{FB})}}{2}
\]

Only the **positive root** is physical (\(x=\sqrt{\psi_s}\ge0\)); the
negative root is discarded. This is well-defined whenever
\(V_G-V_{FB}\ge0\) (i.e. \(\psi_{s,bias}\ge0\), the precondition for
entering this branch — see step 2), so the discriminant
\(k^2+4(V_G-V_{FB})\) is always non-negative here and no complex-root
case can arise. Then:

\[
\psi_s=x^2
\]

As \(V_G\rightarrow V_{FB}^+\), \(x\rightarrow0\) and \(\psi_s\rightarrow0\),
consistent with the flatband boundary condition.

4. If:

\[
\psi_s<2\phi_F
\]

then:

\[
W_d=
\sqrt{
\frac{2\epsilon_{si}\psi_s}
{qN_A}
}
\]

\[
C_{dep}=
\frac{\epsilon_{si}A}{W_d}
\]

\[
C_{MOS}
=
\frac{C_{ox}C_{dep}}
{C_{ox}+C_{dep}}
\]

```text
region = "depletion"
```

5. If:

\[
\psi_s\ge2\phi_F
\]

then:

\[
W_d=W_{d,max}
\]

with the depletion width clamped at its maximum value under the
high-frequency frozen-inversion assumption, and:

\[
C_{MOS}=C_{min}
\]

```text
region = "inversion"
```

This fully defines the Level 1 analytical C--V curve without requiring
the full \(Q_s(\psi_s)\) machinery.

## Level 2 — Numerical surface-potential model

The final model will solve the MOS electrostatic relation numerically.

For the locked p-type substrate convention:

\[
V_G =
V_{FB}
+\psi_s
-\frac{Q_s(\psi_s)}{C'_{ox}}
\]

Define the normalized surface potential:

\[
u_s=\frac{q\psi_s}{kT}
\]

The semiconductor charge density per unit area is:

\[
Q_s(\psi_s)
=
-\operatorname{sgn}(\psi_s)
\sqrt{
2\epsilon_{si}N_A kT
}
\sqrt{
e^{-u_s}+u_s-1
+
\left(\frac{n_i}{N_A}\right)^2
\left(e^{u_s}-u_s-1\right)
}
\]

where \(Q_s\) is the signed semiconductor charge density in \(C/m^2\).

This is the actual charge equation used by the Level 2 model. It continuously covers accumulation, depletion, and inversion under the Boltzmann approximation.

Let:

\[
F(u_s)
=
e^{-u_s}+u_s-1+
\left(\frac{n_i}{N_A}\right)^2
\left(e^{u_s}-u_s-1\right)
\]

Then:

\[
Q_s(\psi_s)
=
-\operatorname{sgn}(\psi_s)
\sqrt{2\epsilon_{si}N_AkT}
\sqrt{F(u_s)}
\]

and:

\[
\frac{dQ_s}{d\psi_s}
=
-\operatorname{sgn}(\psi_s)
\sqrt{2\epsilon_{si}N_AkT}
\frac{q}{kT}
\frac{
-e^{-u_s}+1+
\left(\frac{n_i}{N_A}\right)^2
\left(e^{u_s}-1\right)
}{
2\sqrt{F(u_s)}
}
\]

Therefore:

\[
C'_{s,LF}(\psi_s)
=
-\frac{dQ_s}{d\psi_s}
\]

The derivative is computed analytically in `physics/solver.py`.
Finite-difference derivatives are not used in production because
\(F(u_s)\rightarrow0\) near flatband makes numerical derivative
step-size selection sensitive where precision matters.

The implementation must include a unit test that verifies
\(C'_{s,LF}>0\) throughout the supported accumulation, depletion, and
inversion regions.

With the locked p-type convention:

- \(\psi_s<0\): accumulation and \(Q_s>0\)
- \(0<\psi_s<2\phi_F\): depletion and \(Q_s<0\)
- \(\psi_s>2\phi_F\): inversion and \(Q_s<0\)

The semiconductor differential capacitance per unit area is defined as a positive quantity:

\[
C'_s=-\frac{dQ_s}{d\psi_s}
\]

The \(Q_s(\psi_s)\) / \(C'_s\) formulation above is the equilibrium
(quasi-static / low-frequency) response: both majority and minority
carrier terms respond to the AC signal.

**High-frequency mode** modifies this as follows:

- For \(\psi_s<2\phi_F\):

\[
C'_{s,HF}(\psi_s)=C'_{s,LF}(\psi_s)
\]

- For \(\psi_s\ge2\phi_F\), minority carriers cannot respond to the AC
  probe. The depletion width is frozen at its maximum value:

\[
C'_{s,HF}(\psi_s)=\frac{\epsilon_{si}}{W_{d,max}}
\]

- Quasi-static mode uses:

\[
C'_{s,LF}(\psi_s)=-\frac{dQ_s}{d\psi_s}
\]

unmodified through all regions, including inversion.

The frequency-mode toggle in the GUI selects between \(C'_{s,HF}\) and
\(C'_{s,LF}\) when computing:

\[
C_{MOS}
=
A\frac{C'_{ox}C'_s}{C'_{ox}+C'_s}
\]

and the total capacitance is returned in the selected frequency mode.

and the total small-signal MOS capacitance is:

\[
C_{MOS}
=
A
\frac{C'_{ox}C'_s}
{C'_{ox}+C'_s}
\]

For each applied gate voltage:

```text
Vg
 ↓
Establish physically bounded ψs bracket
 ↓
Evaluate stable Qs(ψs)
 ↓
Solve Vg - VFB - ψs + Qs/Cox' = 0
 ↓
Calculate positive Cs = -dQs/dψs
 ↓
Combine Cs and Cox
 ↓
Return MOS capacitance and region
```

SciPy's bracketing solver (`brentq`) is preferred for the production solver because a valid sign-changing bracket is more predictable than unconstrained Newton iterations for this problem. Newton-style methods may be used only as an optional optimization after correctness is established.

The Level 2 charge model uses Boltzmann statistics. Very heavily doped silicon may require Fermi–Dirac statistics and additional physical effects, so numerical stress tests at high doping must not be presented as proof that the physical model remains exact there.

The numerical model is the preferred final model after validation against the Level 1 equations and the primary reference.

# 9. Numerical Stability and Solver Bounds
The accumulation term contains \(e^{u_s}\), while depletion/inversion contains \(e^{-u_s}\). Unbounded root-finding iterations can therefore overflow before convergence.

The production solver will use the following safeguards:

1. Use a **bracketed root solver** rather than unconstrained iteration.
2. Construct a physically bounded \(\psi_s\) search interval for each \(V_G\).
3. Evaluate exponentials using a stable implementation that avoids overflow.
4. Reject non-finite residuals and report a controlled solver error.
5. Validate the final root by checking the residual of the MOS voltage equation.
6. Add regression tests covering high-doping cases such as \(N_A=10^{18}\,cm^{-3}\) and larger voltage ranges.

The implementation will not silently clip a physically meaningful result merely to hide overflow. Bounds and clipping are numerical safeguards and must be documented.

# 10. Frequency Modes
## High-frequency C--V

In strong inversion, minority carriers cannot respond sufficiently
quickly to the AC signal.

The high-frequency curve therefore approaches approximately:

\[ C\_{min} = `\frac{C_{ox}C_{dep,min}}`{=tex} {C\_{ox}+C\_{dep,min}} \]

where

\[ C\_{dep,min} = `\frac{\epsilon_{si}A}{W_{d,max}}`{=tex} \]

## Low-frequency / quasi-static C--V

At sufficiently low frequency, inversion carriers can respond to the AC
signal and capacitance rises again toward the oxide capacitance under
the idealized model.

The UI should allow:

``` text
High Frequency
Low Frequency / Quasi-static
```

The exact physical assumptions and limitations must be documented.

------------------------------------------------------------------------

# 11. GUI Requirements
## 11.1 Device parameter controls

The UI should provide:

-   Substrate doping (N_A)
-   Oxide thickness (t\_{ox})
-   Gate area (A)
-   Temperature (T)
-   (`\Phi`{=tex}\_{MS})
-   Optional oxide charge (Q\_{ox})
-   Voltage minimum
-   Voltage maximum
-   Voltage step/resolution

------------------------------------------------------------------------

## 11.2 Simulation controls

Controls should include:

-   Simulate / Update
-   Reset to defaults
-   Frequency mode
-   Applied-voltage input
-   Optional parameter sweep

------------------------------------------------------------------------

## 11.3 Calculated results

Display at minimum:

-   (C\_{ox})
-   (C'\_{ox})
-   (`\phi`{=tex}\_F)
-   (V\_{FB})
-   (V_T)
-   (W\_{d,max})
-   (C\_{min})

Values should be shown with appropriate engineering units.

------------------------------------------------------------------------

# 12. Applied Voltage Analysis
The user should be able to enter a specific gate voltage.

Example:

``` text
Applied voltage: 1.50 V

Region: Depletion
Surface potential: ...
Depletion width: ...
Cox: ...
Cdep: ...
Total capacitance: ...
```

The simulator must automatically classify the operating region:

-   Accumulation
-   Depletion
-   Inversion

The classification logic must follow the same sign convention used by
the physics model.

------------------------------------------------------------------------

# 13. C--V Plot Requirements
The main plot should show:

-   X-axis: Gate voltage (V_G) in V
-   Y-axis: Capacitance, preferably in pF or a suitable scaled unit
-   Accumulation region
-   Depletion region
-   Inversion region
-   (V\_{FB}) marker
-   (V_T) marker
-   Selected operating point

Optional:

-   High-frequency and low-frequency curves simultaneously.
-   Hover/selection information.
-   Region labels.

------------------------------------------------------------------------

# 14. Parameter Sweep Features
A parameter comparison mode should eventually support:

## Oxide thickness

Compare, for example:

\[ t\_{ox}=5, 10, 20 nm \]

Expected physical trend:

\[ t\_{ox}`\uparrow`{=tex} `\Rightarrow`{=tex} C\_{ox}`\downarrow`{=tex}
\]

## Substrate doping

Compare several (N_A) values.

Expected trends should be verified analytically rather than assumed.

## Gate area

Expected:

\[ A`\uparrow`{=tex} `\Rightarrow`{=tex} C\_{ox}`\uparrow`{=tex} \]

The simulator should allow multiple curves on one graph with a clear
legend.

------------------------------------------------------------------------

# 15. Export Features
Add:

-   Export C--V data as CSV.
-   Export current plot as PNG.

CSV structure should contain at least:

``` text
Voltage,Capacitance,Region
-5.00,...
-4.99,...
...
```

If useful, additional columns may include:

-   Surface potential
-   Depletion width
-   Oxide capacitance
-   Semiconductor capacitance

------------------------------------------------------------------------

# 16. Input Validation
The application must reject physically invalid values.

Examples:

-   (N_A `\le 0`{=tex})
-   (t\_{ox} `\le 0`{=tex})
-   (A `\le 0`{=tex})
-   (T `\le 0`{=tex})
-   Invalid voltage range
-   Invalid voltage step
-   Numerical solver failure

Errors should be shown clearly in the GUI rather than allowing the
application to crash.

------------------------------------------------------------------------

# 17. Testing Strategy
Testing is a major part of making the project trustworthy.

## Unit tests

Test individual equations:

-   Oxide capacitance.
-   Fermi potential.
-   Flat-band voltage.
-   Threshold voltage.
-   Maximum depletion width.
-   Minimum capacitance.

## Limiting-behavior tests

Verify expected trends:

``` text
tox increases → Cox decreases
Area increases → Cox increases
```

and other physically expected dependencies.

## Numerical solver tests

Verify:

-   Convergence for normal parameter ranges.
-   Correct handling of difficult inputs.
-   Failure reporting when a solution cannot be obtained.

## Regression tests

Once reference results are established, store expected values for
representative parameter sets so future changes do not silently break
the model.

------------------------------------------------------------------------

# 18. Reference Parameter Set
Use one fixed reference configuration throughout development and
validation.

Suggested starting point:

``` text
Substrate: p-type silicon
NA:        1 × 10^16 cm^-3
tox:       10 nm
Area:      100 µm²
T:         300 K
Phi_MS:    0 V
Qox:       0 C
Voltage:   -5 V to +5 V
```

These are development defaults, not universal physical constants.

The final values should be checked against the selected
textbook/reference.

------------------------------------------------------------------------

# 19. Validation Philosophy
The simulator must not be validated by visual appearance alone.

Primary theoretical reference:

**S. M. Sze and Kwok K. Ng, _Physics of Semiconductor Devices_, 3rd ed.**

The implementation will use the locked p-type substrate sign convention defined in Section 2. Any equation whose notation differs from the reference will be converted explicitly into the project's convention and documented.

For the reference parameter set:

1.  Calculate key quantities independently.
2.  Compare them against simulator output.
3.  Record numerical differences.
4.  Verify limiting physical behavior.
5.  Compare the shape of the simulated C--V curve with trusted
    textbook/reference behavior.

The report should include a validation table such as:

  Quantity         Reference   Simulator   Relative Error
  -------------- ----------- ----------- ----------------
  (C\_{ox})              ...         ...              ...
  (V\_{FB})              ...         ...              ...
  (V_T)                  ...         ...              ...
  (W\_{d,max})           ...         ...              ...
  (C\_{min})             ...         ...              ...

The actual reference values will be filled in after the implementation
and independent calculation are complete.

------------------------------------------------------------------------

# 20. Development Phases
## Phase 1 — Environment and Packaging Feasibility Spike

- Initialize project with `uv`.
- Pin Python 3.12.
- Add runtime dependencies.
- Add development dependencies.
- Confirm imports.
- Create the initial project structure.
- Create a minimal Streamlit "Hello World" application.
- Within the first development session, package that minimal application with PyInstaller as a **single executable**.
- Verify that the frozen executable starts Streamlit, serves the page, and opens the browser automatically.
- Test the executable outside the active development environment.
- Record any required PyInstaller hidden imports, Streamlit static assets, hooks, or configuration.
- Treat failure of this spike as an architecture decision point before substantial GUI work is implemented.

This is deliberately an early feasibility test. We do not wait until the final packaging phase to discover whether the selected Streamlit + single-EXE deployment strategy is workable.

## Phase 2 — Physics foundation

Implement: - Constants. - Parameter model. - Unit conversions. - Basic
analytical MOS equations.

No Streamlit yet.

## Phase 3 — Analytical C--V model

Implement: - Accumulation. - Depletion. - Inversion. - High-frequency
approximation. - Low-frequency approximation.

Generate numerical C--V data.

## Phase 4 — Numerical surface-potential solver

Implement:
- Explicit \(Q_s(\psi_s)\) from Section 8.
- Analytical \(dQ_s/d\psi_s\) and positive \(C'_s\).
- SciPy `brentq` root solving with bounded brackets.
- High-frequency and quasi-static capacitance modes.
- Robust convergence behavior.
- Numerical capacitance calculation.
- Comparison against the Level 1 analytical approximation.
- Unit tests for \(C'_s>0\) across all supported regions.

## Phase 5 — Physics validation

-   Run unit tests.
-   Verify reference parameter set.
-   Check physical trends.
-   Fix sign/unit/convention errors.

## Phase 6 — Streamlit GUI

Implement: - Parameter sidebar/panel. - Simulation controls. - Result
cards. - Applied-voltage analysis. - C--V plot. - Region labels.

## Phase 7 — Analysis features

Add: - Frequency selection. - Parameter sweeps. - Multiple curves. - CSV
export. - PNG export.

## Phase 8 — Polish

Add: - Equation/theory panel. - Helpful units. - Validation messages. -
Clear explanations of assumptions. - Professional layout. -
Default/example configuration.

## Phase 9 — Testing

-   Full pytest run.
-   Test edge cases.
-   Test GUI input validation.
-   Test numerical solver.
-   Test exports.

## Phase 10 — Packaging

-   Add launcher.
-   Configure PyInstaller.
-   Resolve hidden imports/data files.
-   Build single executable.
-   Test on a clean Windows environment.
-   Verify browser auto-launch.
-   Verify simulator works without Python installed.

------------------------------------------------------------------------

# 21. Final Application Feature Set
### Required

-   MOS capacitor model.
-   p-type silicon substrate.
-   Configurable device dimensions.
-   Configurable doping.
-   Configurable temperature.
-   C--V calculation.
-   Accumulation/depletion/inversion identification.
-   Capacitance at selected voltage.
-   C--V plot.
-   High-frequency mode.
-   Low-frequency/quasi-static mode.
-   Analytical model.
-   Numerical solver.
-   Streamlit GUI.
-   Unit validation.
-   Automated tests.
-   Single Windows executable.

### Strong enhancements

-   Parameter sweeps.
-   (t\_{ox}) comparison.
-   (N_A) comparison.
-   Area comparison.
-   CSV export.
-   PNG export.
-   Theory/equation panel.

### Optional, only after the core is stable

-   MOS band diagrams.
-   Animated voltage sweep.
-   Dark/light theme customization.
-   Additional non-ideal effects.

------------------------------------------------------------------------

# 22. Non-Goals
Do not expand the project into:

-   MOSFET simulation.
-   BJT simulation.
-   Full semiconductor process simulation.
-   Database-backed application.
-   Authentication.
-   Cloud backend.
-   Multi-user infrastructure.

The project should remain focused on **MOS capacitor electrostatics and
C--V behavior**.

------------------------------------------------------------------------

# 23. Packaging Plan
The final target is:

``` text
MOS-Capacitor-Simulator.exe
```

The executable will package:

-   Python runtime.
-   NumPy.
-   SciPy.
-   Matplotlib.
-   Streamlit.
-   Application code.
-   Required runtime assets.

Expected runtime behavior:

``` text
Double-click EXE
       ↓
Launcher starts
       ↓
Local Streamlit server starts
       ↓
Browser opens automatically
       ↓
MOS Capacitor Simulator
```

PyInstaller will be used for the final build.

The executable should be tested independently from the development
environment before submission.

------------------------------------------------------------------------

# 24. Documentation and Academic Deliverables
The project should eventually include:

1.  Project README.
2.  Implementation documentation.
3.  Theory/equation reference.
4.  GUI screenshots.
5.  Validation results.
6.  Parameter-sweep results.
7.  Example C--V plots.
8.  Executable.
9.  Source code.
10. Dependency lock file.

The final report should explain not only **what** was implemented, but
**why the equations produce the observed C--V behavior**.

------------------------------------------------------------------------

# 25. Quality Criteria
The project is considered complete only when:

-   The equations are implemented correctly.
-   Units are handled consistently.
-   Numerical results are independently validated.
-   The C--V curve behaves physically.
-   The GUI cannot easily accept invalid device parameters.
-   The numerical solver handles normal parameter ranges reliably.
-   Automated tests pass.
-   The application works without the development environment.
-   The single executable launches the simulator successfully.
-   The project can be explained clearly during a viva.

------------------------------------------------------------------------

# 26. Implementation Principle
The order is intentionally:

``` text
Physics
   ↓
Numerical model
   ↓
Validation
   ↓
GUI
   ↓
Analysis features
   ↓
Testing
   ↓
Packaging
```

Not:

``` text
Pretty GUI
   ↓
Random equations
   ↓
Graph that looks correct
```

The simulator's credibility comes from the physics model first.
