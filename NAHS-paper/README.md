# NAHS
This folder will contain the models used in the paper submitted to NAHS. This file is not final!!

contains the models used in the paper "Learning Safe and Optimal Control Strategies for Storm Water Detention Ponds" by Martijn A. Goorden, Kim G. Larsen, Jesper E. Nielsen, Thomas D. Nielsen, Michael R. Rasmussen, and Jiří Srba submitted to International Conference on Analysis and Design of Hybrid Systems (ADHS) 2021.

## Models
This repository contains two model files:

* pond_ADHS.xml: this is the Uppaal Stratego model for dynamic control.
* pond_ADHS_static.xml: this is the Uppaal Stratego model for static control.

The two files contain both the component models as well as the queries.


## Simulation data
Due to stochastic nature of the model, each simulation results in different results. Running the simulation queries in the model can thus show slightly different results than shown in the paper. Therefore, the raw simulation data used to create the figures are included in the repository.

* sim_dynamic_0.txt: The simulation data for dynamic control with initial water level of 0 cm.
* sim_dynamic_100.txt: The simulation data for dynamic control with initial water level of 100 cm.
* sim_static_0.txt: The simulation data for static control with initial water level of 0 cm.
* sim_static_100.txt: The simulation data for static control with initial water level of 100 cm.


## Uppaal Stratego
The model is compatible with Uppaal Stratego 4.1.20-7, which can be downloaded [here](https://people.cs.aau.dk/~marius/stratego/download.html).
