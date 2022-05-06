strategy loaded = loadStrategy{Pond.location, Rain.location,UrbanCatchment.location,Controller.location,CostFunction.location,Rain.i, Rain.rainLoc,Rain.dryL,Rain.dryU,Rain.rainL,Rain.rainU}->{t,S_UC,w,o,c,Rain.d,Controller.x,rain,Open}("/home/martijn/Documents/CLAIRE/NAHS-paper/off-line_strategy.json")
simulate 1 [<=60+1] { t,rain,S_UC,w,c,Open,o,Rain.rainLoc } under loaded
