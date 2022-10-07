strategy opt = minE (c) [<=4*60]: <> (t==240.0)

simulate [<=60+1; 1] { t,rain,S_UC,w,c,Open,o,Rain.rainLoc } under opt
