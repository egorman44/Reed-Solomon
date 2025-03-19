# Reed-Solomon Decoder Generator

## Setup Environment

Clone the project and update its submodules using the following commands:
```
git clone --recurse-submodules https://github.com/egorman44/Reed-Solomon.git
git submodule update --init --recursive
git submodule update --remote --recursive
```

I chose Ubuntu 22.04 as the OS because all the tools below work perfectly on it.
These are the required tools to build the decoder:

- **Chisel tools**: JDK, Scala, SBT

- **Python3**

- **Cocotb**

- **Reedsolo package**

- **Verilator** (if you want to check the waveforms)

- **Docker** (if you prefer to build and test the decoder in a container)

All tools are listed in the `Dockerfile`, which you can use to avoid installing everything manually.

## Build and Run Docker Container

To build a Docker container image and run a container from it, use the following commands:

```
docker build -t chisel-flow .
docker run -it -v <prj_folder>:/app -w /app chisel-flow
```

## Generate Decoder

To generate SystemVerilog files for the decoder, run the following commands:

```
runMain Rs.GenRsBlockRecovery --symb-width-in-bits 8 --bus-width-in-symb 4 --poly 285 --fcr 0 --n-len 255 --k-len 239
runMain Rs.GenRsBlockRecovery --symb-width-in-bits 8 --bus-width-in-symb 4 --poly 285 --fcr 0 --n-len 108 --k-len 106
```

## Run Cocotb Tests

To run Cocotb tests, use the following command:

```
python3 rs_decoder.py -l RsBlockRecovery
```