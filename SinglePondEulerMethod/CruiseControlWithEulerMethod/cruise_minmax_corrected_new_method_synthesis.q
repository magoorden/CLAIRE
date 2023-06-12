//This file was generated from (Academic) UPPAAL 4.1.20-stratego-10 (rev. 37ECAAA437FE60EE), October 2022


/*

*/
strategy safe = control: A[] (distance_gua_new[0] > 5)

/*

*/

saveStrategy("CruiseControlWithEulerMethod/CruiseControlSafeStrategy", safe)
