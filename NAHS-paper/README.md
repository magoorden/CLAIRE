# NAHS
This folder will contains the models used in the paper "Optimal Control Strategies for Stormwater Detention Ponds" by Martijn A. Goorden, Kim G. Larsen, Jesper E. Nielsen, Thomas D. Nielsen, Weizhu Qian, Michael R. Rasmussen, Jiří Srbam, and Guohan Zhao submitted to Nonlinear Analysis: Hybrid Systems (NAHS).

## Models
This repository contains four model files:

* "pond_offline.xml": this is the Uppaal Stratego model for offline dynamic control.
* "pond_offline_static.xml": this is the Uppaal Stratego model for offline static control.
* "pond_online.xml": this is the Uppaal Stratego model for online dynamic control.
* "pond_online_offline.xml": this is the Uppaal Stratego model for offline control for the online scenario.

The four files contain both the component models as well as the queries. Note that the online models are templates that are altered during the online control experiments.


## Simulation data
Due to stochastic nature of the model, each simulation results in different results. Running the simulation queries in the model can thus show slightly different results than shown in the paper. Therefore, the raw simulation data used to create the figures are included in the repository.

* "sim_dynamic_0.txt": The simulation data for offline dynamic control with initial water level of 0 cm.
* "sim_dynamic_100.txt": The simulation data for offline dynamic control with initial water level of 100 cm.
* "sim_static_0.txt": The simulation data for offline static control with initial water level of 0 cm.
* "sim_static_100.txt": The simulation data for offline static control with initial water level of 100 cm.
* "sim_online_0-6h.csv": The simulation data for online dynamic control with initial water level of 0 cm and a 6 hour control horizion.
* "sim_online_0-12h.csv": The simulation data for online dynamic control with initial water level of 0 cm and a 12 hour control horizion.
* "sim_online_0-18h.csv": The simulation data for online dynamic control with initial water level of 0 cm and a 18 hour control horizion.
* "sim_online_offline_strategy.csv": The simulation data for offline dynamic control for the online control experiment with initial water level of 0 cm and normal learning budget.
* "sim_online_offline_strategy.csv": The simulation data for offline dynamic control for the online control experiment with initial water level of 0 cm and high learning budget. 


## Auxilary files
The following files are needed to reproduce the results for online control. For offline control, the models and Uppaal Stratego is sufficient.

* "model_online_config.yaml": The configuration file for online control indicating which variables have new initial values after each control period.
* "verifyta_online_config.yaml": The configuration file for online control indicating the settings of Uppaal Stratego.
* "swmm_stratego_control.py": Python script to perform online control.
* "weather_forecast_generation.py": Python script to create a weather forecast from historical weather data.
* "swmm_online.inp": The SWMM model used as external simulator for online control.
* "swmm_5061.dat": Historical rain data.
* "off-line_strategy.json": The synthesized offline strategy for the online control experiment using normal learning budget.
* "off-line_strategy_long.json": The synthesized offline strategy for the online control experiment using high learning budget.

## Third party software
The model is compatible with Uppaal Stratego 4.1.20-9, which can be downloaded [here](https://uppaal.org/downloads).

Online control has been performed using the Strategoutil Python library, see [documentation](https://strategoutil.readthedocs.io/en/latest/).

The data from the weather forecast is imported into the Uppaal model using the standard Uppaal external library tool, see [GitHub](https://github.com/UPPAALModelChecker/uppaal-libs).

The Python interface for SWMM, pySWMM, is used, see [documentation](https://pyswmm.readthedocs.io/en/stable/).
