
# TRSMScans

A complete set of tools to automate scanning the TRSM model using ScannerS to maximize the cross-section times branching for various final states.

## Dependencies

These tools use `ScannerS` and `HiggsTools`, both of which have several dependencies that need to be installed manually through your favorite package manager.
Make sure you have the following installed:

- Working compilers for C++ and C. The C++ compiler must support
    `c++17` (e.g., `gcc-9` or newer).
  - On Mac, Apple Clang should support `c++17`, but an argument needs
    to be passed to `cmake` to specify this requirement, which is already
    in the installation script.
- A working compiler for Fortran such as `gfortran`.
  - Apple Clang, unfortunately does not compile Fortran, so you will need
    to install `gcc` (or another compiler) manually.
- `python` >= 3.8
- `cmake` >= 3.17, download it through your package manager, through
  `pip`, or grab the latest binary.
- GSL, can be installed through the package manager on most unix systems.
  The package is called `libgsl-dev` on Ubuntu and `gsl` most everywhere else
  (e.g. on OpenSUSE/CentOS or homebrew).
- Eigen3 >= 3.3.0 (3.x series only). This project is not yet compatible
  with Eigen 5.x, so please ensure you have an Eigen 3.x installation.
  - Ubuntu/Debian: install `libeigen3-dev`.
  - OpenSUSE/CentOS and similar: install the `eigen3` package.
  - macOS (Homebrew): install and use `eigen@3` (not the unversioned
    `eigen` formula, which provides Eigen 5.x). For example:
    - `brew install eigen@3`
    - `brew link eigen@3 --force`
- `clang` >= 5. If you are using macOS, this corresponds to `Apple clang` >= 7.

Note: If you are using a Mac, the installation seems to work better if you use homebrew instead of macports as your package manager.

### Python on lxplus

If you are working on lxplus, you will need to install a custom version of Python since the default version is not sufficient.
You can do this following [the instructions given here](https://abpcomputing.web.cern.ch/guides/python_inst/).
It is recommended that you install the latest version of Python.

## Submodules and SSH keys

These tools rely on `ScannerS`, `HiggsTools`, `HBDataSet` and `HSDataSet`, all of which are set up as submodules that will be automatically cloned and compiled using the provided scripts.
In order to access them, it is necessary to have SSH keys set up on [https://gitlab.com](https://gitlab.com).

The submodule repositories can be found using these links:

- [ScannerS](https://gitlab.com/jonaswittbrodt/ScannerS)
- [HiggsTools](https://gitlab.com/higgsbounds/higgstools)
- [HBDataSet](https://gitlab.com/higgsbounds/hbdataset)
- [HSDataSet](https://gitlab.com/higgsbounds/hsdataset)

### Pre-installed submodules

If you already have any of the submodules installed, you can provide paths to them when prompted after calling `source setup.sh` for the first time.
If you provide paths, compilation will be skipped and the code will be configured to use the version you have provided.

## Installation

Most of the installation is done via scripts that are provided.
You can call `source setup.sh` from the top directory to automate the installation the first time you call it, assuming you have the dependencies installed.
This will set up the `ScannerS` and `HiggsTools` submodules, install both packages, create a python virtual environment and install the necessary python modules.

## Every login

The code needs to be run from a python virtual environment that needs to be set up every time you start a new shell.
The virtual environment can be activated with `source setup.sh`.

## Decay modes

To run a full scan or to specify a mass list, a decay mode (`-d`) needs to be
specified. The full list of supported decay modes is available in `data/decay_modes.yml`.

## Running optimization

The tools are designed for you to run from the `run` directory.
An example of how to run a scan using zoom optimization is given in the
`run/scan_example_zoom.sh` script. A scan will create output in the `output`
directory based on the scan parameters. Within the corresponding directory
in `output`, you will find all of the `.tsv` files under `zoom` as well as
`summary_zoom_TRSMBroken_*.tsv` that shows a summary of scans that find new
maxima. The entry point for all scans or prescans is `launch_scan.py`, which
provides options to either run a scan or a prescan, run a single mass point
or a list of points, and locally or on the lxplus `HTCondor` batch system.

### Precision

To improve optimization efficiency, dynamic precision levels are used. These
control how tight the stopping conditions are based on experimental limits
that are used as targets (defined in each mass list file). By default, an
adaptive precision calculation is used. If the rates for a mass point are
more than two orders of magnitude smaller (insensitive) or a factor of 20
larger (saturated) than the experimental limits, the optimization is terminated
to prevent unnecessary computation. As the rates get closer to the limits,
stopping conditions are tightened to allow for a more thorough sampling of
the parameter space. Adaptive precision can be switched off by specifying a
precision level with the `-p/--precision` argument. The precision configurations
are in `config/OptimizerConfig.yml`.

### Processing a single mass point

To run over a single mass point, specify the scalar masses using the `-X` and
`-S` options. `-H` is an allowed argument, but is set to 125.09 by default.

### Processing a mass list

To process a full list of masses, use the `-l` flag. You will also need to provide
a decay mode `-d` and an identifier `-i` (e.g., `CMS_boosted`). These refer to
the `.json` files in `data/mass_points/` that contain information about the mass
points used in each experimental result with expected and observed limits taken
from hepdata. Users can create their own mass point `.json` files and limit data
can be omitted for all steps except creating exclusion plots. Running over a mass
list will result in individual jobs being launched for each mass point.

Mass points with `mX >= 3000 GeV` are skipped due to calculated cross-sections not being
available.

### Re-running jobs

Nominally, prescan jobs will not run again if the requested number of points is
less than or equal to the number that was previously run. If  more points are
requested than were previously run, new points will be appended to those that
already exist until the requested total number is reached. Using the `force-rerun`
flag will overwrite any previously existing prescan points.

By default, scan jobs will not run if a previous run exists with at least as many
points as those requested. Running with the `-r/--rerun-precision` argument will
rerun any job that was previously run with a precision greater than or equal to the
given value (except saturated or insensitive points). This allows you to tighten the
precision settings (and get a more accurate rate) for mass points that are close to
the experimental limits without rerunning points that are far from the limits.
Using the `-f/--force-rerun` flag will force the job to be rerun regardless
of the previous number of points or precision.

### Batch mode

To run in batch mode, use the `-b` option when calling `launch_scan.py`.
Submission files will automatically be generated and jobs will be launched.

### External `output` directory

When running `source setup.sh` for the first time, you will be prompted to provide an
external directory for the output. If you provide a path, a symbolic
link will be created such that `run/output` points to it. Otherwise,
`run/output` will be created and the outputs will be stored there.

## Post-processing mass list results

Two tools are provided for post-processing the outputs from a run over a mass list.

- `combine_results.py` produces a single output file in `output/<model name>/combination`
  that provides the maximum rate found for each mass point in the list. This step is
  necessary for making plots.
- `check_mass_list.py` parses the outputs and produces a report indicating which mass
  points have successfully been run. This is not a necessary step, but is helpful for
  bookkeeping and debugging purposes.

## Making plots

Tools are provided to produce a number of helpful plots. These can all be run using
`make_plots.py`. The plots come in two types, which can either be run separately or
together.

- `Mass point plots`: These show a combination of all sampled points for a single
  mass point, These are very useful for visualizing the shape of the parameter space,
  the progression of the optimization procedure, and the maximum rates. These include
  2D projections for every pair of free parameters as well as the rate vs. each parameter.
- `Combination plots`: These display the maximum rates for all mass points in the list
  interpolated in a 2D plane (mS vs mX). Plots can also be produced to show the mass
  points that are sensitive to exclusions from experimental limits.

## Optimization strategies

Multiple optimization strategies are or will be supported. Currently, only
the `zoom` strategy is fully supported and recommended.

### Zoom optimization

The parameter space is split into regions around maxima and each subspace
is iteratively zoomed in as more points are sampled. The highest sampled
point is taken as the maximum. Run using the `zoom` option. This is the
default strategy.

### Mean-shift optimization

> ⚠️ **Warning:** Currently, the mean-shift optimization strategy is under development
> and is not recommended for use.

Multiple small regions of parameter space are sampled using a small number
of points. The center of each region is shifted based on a weighted mean
of the sampled points, resulting in an "uphill walk" until a local maximum
is found. Multiple local maxima are then compared. Run using the `meanshift`
option.

## Scan filters

The outputs from `ScannerS` are checked against width requirements
(configurable by the user) and experimental bounds. Sampled points
that fail any requirement are excluded.

## Prescan

A prescan is run as the starting point for full scans. This is a single
scan over the full model parameter range and is independent of any decay
mode. It is used to constrain the parameter ranges used in the full scan.
An example of how to run a prescan is available in `run/prescan_example.sh`.
Running a prescan creates an output `.tsv` file in the appropriate
subdirectory within `output/prescan/`. If a prescan already exists, the
prescan process only runs as many points as necessary to meet the specified
`npoints` and appends the new points to the existing ones. Prescans are
processed in chunks in order to save progress in case the job is interrupted.
A prescan can be run standalone or as part of a scan.
