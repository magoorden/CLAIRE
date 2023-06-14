strategy opt = minE (c) [<=6*60]: <> (t==360.0 && o <= 0)

simulate [<=60+1;1] { t,rain,S_UC,w,c,Open,o,Rain.rainLoc,st_w,st_o,st_c } under opt
