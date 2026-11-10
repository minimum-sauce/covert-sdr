# covert-sdr
This project implements Covert Communication on an ANTSDR 

## Directory structure
``` bash
antsdr-project/
├── docs/interface/         # register map, AXI-Stream formats, data flow
├── fpga/
│   ├── vendor/             # submodule: HanGeek's FPGA source (pinned commit)
│   ├── hdl/                # HDL (custom IP / modules)
│   ├── ip/                 # Tcl to regenerate IP
│   ├── bd/                 # block design as exported Tcl, not the .bd
│   ├── constraints/
│   ├── sim/
│   └── scripts/            # create_project.tcl etc. (Project generation and build scripts)
├── sw/
│   ├── cpp/                 # libiio-based apps
│   ├── python/              # pyadi-iio / libiio bindings
│   └── common/              # register map headers (generated)
├── ci/
└── tools/
```

# Build/Run
## With FPGA alterations
- TODO
## Without FPGA alterations
- TODO
