//This file was generated from (Academic) UPPAAL 4.1.20-stratego-10 (rev. 37ECAAA437FE60EE), October 2022


/*

*/
strategy safe = loadStrategy("CruiseControlWithEulerMethod/CruiseControlSafeStrategy")

/*

*/
simulate [<=100; 1] {rDistance, distance_gua_new[0], distance_gua_new[1], distance_gua[0], distance_gua[1], rVelocityEgo, velocityEgo_gua_new[0], velocityEgo_gua_new[1], velocityEgo_gua[0], velocityEgo_gua[1], rVelocityFront, velocityFront_gua_new[0], velocityFront_gua_new[1], velocityFront_gua[0], velocityFront_gua[1]} under safe
