
## TRSMScans

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
  - Eigen3 >= 3.3.0, can be installed through the package manager on most unix
    systems. The package is called `libeigen3-dev` on Ubuntu, `eigen3` on
    OpenSUSE/CentOS and `eigen` in homebrew.
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

  * [ScannerS](https://gitlab.com/jonaswittbrodt/ScannerS)
  * [HiggsTools](https://gitlab.com/higgsbounds/higgstools)
  * [HBDataSet](https://gitlab.com/higgsbounds/hbdataset)
  * [HSDataSet](https://gitlab.com/higgsbounds/hsdataset)

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

## Running

The tools are designed for you to run from the `run` directory.
An example of how to run a scan using zoom optimization is given in the `run/scan_example_zoom.sh` script.
A scan will create output in the `output` directory based on the scan parameters.
Within the corresponding directory in `output`, you will find all of the `.tsv` files under `files` as well as
`scandetails.txt` and `scansummary.txt` that show the details of
each scan iteration and show a summary of scans that find new
maxima, respectively.

### External `output` directory

When running `source setup.sh` for the first time, you will be prompted to provide an
external directory for the output. If you provide a path, a symbolic
link will be created such that `run/output` points to it. Otherwise,
`run/output` will be created and the outputs will be stored there.

## Scan filters

The outputs from `ScannerS` are checked against a width requirement
(configurable by the user) and experimental bounds and any scan points
that fail either are removed.

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
