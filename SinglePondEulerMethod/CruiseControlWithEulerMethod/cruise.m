########################
#    CRUISE CONSTANTS  #
########################

global numberModes = 9;
global dim=3;
global tau = 1;
global sub_step = 1;


#
#Definition of f
#

global A = zeros(dim,dim,numberModes);
A(3,1,:) = 1;
A(3,2,:) = -1;

global B = zeros(dim,numberModes);
B = [2,2,2,0,0,0,-2,-2,-2;2,0,-2,2,0,-2,2,0,-2;0,0,0,0,0,0,0,0,0]

global fT = @(t,T,mode) [A(1,1,mode)*T(1)+A(1,2,mode)*T(2)+A(1,3,mode)*T(3);
	A(2,1,mode)*T(1)+A(2,2,mode)*T(2)+A(2,3,mode)*T(3);
	A(3,1,mode)*T(1)+A(3,2,mode)*T(2)+A(3,3,mode)*T(3)] + B(:,mode);


x_low = -20;
x_hig = 200;


#
#Computation of max(||f||)
#

x0 = [5.5,5.5,5.5];
phi = @(i,x) -norm(fT(0,x,i));

for i = 1:numberModes
  func = @(x) phi(i,x);
  [x_opt,obj,info,iter,nf,lambda] = sqp(x0,func,[],[], [x_low,x_low,x_low],[x_hig,x_hig,x_hig]);
  MAXF(i) = -func(x_opt);
endfor


#
#Computation of lambda_j
#

x0 = [0.5,0.5,-0.5,0.2];
phi2 = @(i,x) -(fT(0,x(1:3),i)-fT(0,x(4:6),i))'*(x(1:3)-x(4:6))/norm(x(1:3)-x(4:6))^2;
for i = 1:numberModes
x0 = [5,5,5,2,5,10];
 # func2 = @(x) phi2(i,x);
  [x_opt2,obj2,info2,iter2,nf2,lambda2] = sqp(x0,@(x) phi2(i,x),[],[], [x_low,x_low,x_low,x_low,x_low,x_low],[x_hig,x_hig,x_hig,x_hig,x_hig,x_hig]);
  OSL(i) = -phi2(i,x_opt2);
#CC2(i) = 0;
endfor

#
#Computation of L_j
#

phi3 = @(i,x) -norm(fT(0,x(1:3),i)-fT(0,x(4:6),i))^2/norm(x(1:3)-x(4:6))^2;
for i = 1:numberModes
x0 = [0.5,0.5,0.5,0.2,5,10];
  func3 = @(x) phi3(i,x);
  [x_opt3,obj3,info3,iter3,nf3,lambda3] = sqp(x0,func3,[],[], [x_low,x_low,x_low,x_low,x_low,x_low],[x_hig,x_hig,x_hig,x_hig,x_hig,x_hig]);
  LIP(i) = sqrt(-func3(x_opt3));
endfor


#
#Computation of Cj
#

global C0f;
for i = 1:numberModes
  C0f(i) = LIP(i)*MAXF(i);
endfor



keyboard
