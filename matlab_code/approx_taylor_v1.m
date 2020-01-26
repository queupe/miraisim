clear all

T = 100;
N = 1:T;

lambda_1 = 10;
mu_1 = 1;
gamma_vec = [1.03, 1.06, 1.07, 1.08, 1.09, 1.15, 1.52];
gamma_1 = 1.03;

rho = zeros(1,T);


for n = N
    a = func_a(n, gamma_1);
    b = func_b(lambda_1, mu_1);
    eq_rho_2o = b + a                                * b^2;
    eq_rho_3o = (a    * (              3*a -    2)/(  2)) * b^3;
    eq_rho_4o = (a^2  * (             16*a -   21)/(  6)) * b^4;
    eq_rho_5o = (a^2  * ( 125*a^2 -  244*a +   48)/( 24)) * b^5;
    eq_rho_6o = (a^3  * (1296*a^2 - 3355*a + 1500)/(120)) * b^6;
    rho(n) = eq_rho_2o + eq_rho_3o + eq_rho_4o + eq_rho_5o + eq_rho_6o;
end

figure
plot(rho)
grid
xlabel('número de nós')
ylabel('probabilidade de um nó estar contaminado')

function a = func_a(n, gamma_1)
    a = n * log(gamma_1);
end
function b = func_b(lambda_1, mu_1)
    b = lambda_1/(lambda_1 + mu_1);
end