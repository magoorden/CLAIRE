strategy opt = minE (c) [<=6*60]: <> (t==360.0 && o <= 0)

simulate 1 [<=60+1] { t,rain,S_UC,w,c,Open,o,Rain.rainLoc } under opt
