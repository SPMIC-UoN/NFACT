# ChangeLog

## 20/12/2026

### Bug fixes
- None

### New Features
- Added in ICASSO graph style (extensively tested)
- Cumulative and per component R2 now reported
- nfact_decomp now has option to use previously ran matrix (do not need to move matrix to a nfact_decomp folder)
- Thresholding for nfact_dr and decomp now turned off by default
- Updated documentation  
## 19/12/2025

### Bug fixes
- None

### New Features
- Documentation now hosted on readthedocs
- Readme stripped down to be more readable
- Added OHBM abstract pictures

## 16/12/2025

Iterative NMF

### Bug fixes
- Fixed nfact_config pipeline error that crashed the pipeline json creator

### New Features
- Added in NMF-sso (iterative NMF)
- NMF-sso can be turned turned off
- Number of iteration and ability to parallelize the process


## NFACT V2

This is will be the first and last new edition. Moving to rolling releases after v2

### Bug fixes
- Fixed nfact dual regression multicore processing on SLURM so dual regression multicore processing works correctly
- Fixed nfact_pp cifti filetree seeds. Seeds now always refelect that in the filetree

### New Features
- nfact_stats. New Module to creating statistical maps for PALM/randomise and component loadings
- nfact_config. Now can compress fdt_matrix2.dot to save space as lz4 files.
- nfact_decomp & nfact_dr can handle compressed lz4 fdt_matrix2.dot