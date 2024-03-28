
## TRSMScans

A complete set of tools to automate scanning the TRSM model
using ScannerS to maximize the cross-section times branching
for various final states.

## Dependencies

These tools use `ScannerS` and `HiggsTools`, both of which
have several dependencies that need to be installed manually
through your favorite package manager. Make sure you have the
following installed:

  - Working compilers for C++, C and Fortran. The C++ compiler must
    support `c++17` (e.g., `gcc-9` or newer). On Mac, Apple Clang
    should support `c++17`, but an argument needs to be passed to
    `cmake` to specify this requirement, which is already in the
    installation script. Apple Clang, unfortunately does not compile
    Fortran, so you will need to install `gcc` (or another compiler)
    manually.
  - `python` >= 3.10
  - `cmake` >= 3.17, download it through your package manager, through
    `pip`, or grab the latest binary.
  - GSL, can be installed through the package manager on most unix systems.
    The package is called `libgsl-dev` on Ubuntu and `gsl` most everywhere else
    (e.g. on OpenSUSE/CentOS or homebrew).
  - Eigen3 >= 3.3.0, can be installed through the package manager on most unix
    systems. The package is called `libeigen3-dev` on Ubuntu, `eigen3` on
    OpenSUSE/CentOS and `eigen` in homebrew.
  - `clang` >= 5

Note: If you are using a Mac, the installation seems to work better if you
use homebrew instead of macports as your package manager.

## Installation

Most of the installation is done via scripts that are provided
in the `scripts` directory. You can call `source first.sh` to
automate the installation, assuming you have the dependencies
installed. This will set up the `ScannerS` and `HiggTools` submodules,
install both packages, create a python virtual environment and
install the necessary python modules.

## Every login

The code needs to be run from a python virtual environment that
needs to be set up everytime you start a new shell. The virtual
environment can be set up with `source setup.sh`.

## Running

The tools are designed for you to run from the `run` directory.
An example of how to run a scan is given in the `run/scan_example.sh`
script. A scan will create output in the `output` directory based
on the scan parameters. Within the corresponding directory in `output`,
you will find all of the `.tsv` files under `files` as well as
`scandetails.txt` and `scansummary.txt` that show the details of
each scan iteration and show a summary of scans that find new
maxima, respectively.

## Scan filters

The outputs from `ScannerS` are checked against a width requirement
(configurable by the user) and experimental bounds and any scan points
that fail either are removed.

## Prescan

It is possible to run a prescan as a starting point for more detailed
scans. A prescan is meant to be a single scan with a large number of
scan points that is saved and used as the baseline for multiple different
scans. An example of how to run a prescan is available in `run/prescan_example.sh`.
Running a prescan creates an output `.tsv` file in `output/prescan/`
that can be used for additional scans.

