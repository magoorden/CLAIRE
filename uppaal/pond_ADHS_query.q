strategy opt = minE (c) [<=12*60]: <> (t==3900.0 && o <= 0)

simulate 1 [<=60+1] { t,rain,S_UC,w,c,Qout,o,Rain.rainLoc } under opt
