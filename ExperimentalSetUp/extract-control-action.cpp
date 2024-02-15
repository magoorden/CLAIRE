#include <iostream>
#include <string>
#include <sstream>
#include <fstream>
#include <stdio.h>
#include <stdlib.h>


using namespace std;

#include <string.h>

int main() {
  int id;
  double x1, y1;
  double x2, y2;
  char *varname;
  while (1==scanf(" %m[^:]:", &varname)) {
    scanf(" [%d]:", &id);

    // Check for variable name.
    int check = strcmp("Qout", varname);
    if (check!=0) {
      // Not the right variable, continue scanning over the values.
      while (2==scanf(" (%lf,%lf)", &x2, &y2)) {
	x1 = x2;
	y1 = y2;
      }
    } else {
      // Variable found. The second tuple is the chosen control action at time 0.
      scanf(" (%lf,%lf) (%lf,%lf)", &x1, &y1, &x2, &y2);
      printf("Qout = %f\n", y2);
    }
  }
}
