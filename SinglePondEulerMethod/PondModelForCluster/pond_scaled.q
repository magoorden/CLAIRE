//This file was generated from (Academic) UPPAAL 4.1.20-stratego-10 (rev. 37ECAAA437FE60EE), October 2022

// Safe control

/*

*/
strategy safe = control: A[] waterLevel_gua[1] < W


/*

*/
simulate [<=horizon-1; 10] {rain_hyb, urbanCatchment_gua[0], urbanCatchment_gua[1], S_UC * factor_s, waterLevel_gua[0] / (1.0 * factor_w), waterLevel_gua[1] / (1.0 * factor_w), w} under safe


