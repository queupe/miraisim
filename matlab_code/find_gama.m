syms rho2 l k g rhox n

func = (rho2 - 1) + k * (g^(rhox * n))*(rho2 - (rhox^2) * n * log(g) * (rho2 - 1));
gunc = (1 - k*g^(rhox * n) * ((rhox^2) * (n * log(g) ) )) / ( rho2 * (1 - k*g^(rhox * n) * ((rhox^2) * (n * log(g) -1) ))) ;

%rho2, k, rhox, n , 3.262e-01, 2.497e-01, 2.859e-01, 10
%rho2, k, rhox, n , 1.911e-01, 2.545e-01, 1.231e-01, 28
%rho2, k, rhox, n , 1.817e-01, 2.593e-01, 7.735e-02, 46
%rho2, k, rhox, n , 1.862e-01, 2.710e-01, 5.452e-02, 64
%rho2, k, rhox, n , 2.245e-01, 2.810e-01, 4.160e-02, 82
%rho2, k, rhox, n , 2.383e-01, 2.965e-01, 3.262e-02, 100
%rho2, k, rhox, n , 4.719e-01, 4.269e-01, 1.158e-02, 200
%rho2, k, rhox, n , 6.550e-01, 6.114e-01, 5.422e-03, 300
%rho2, k, rhox, n , 6.996e-01, 6.676e-01, 3.731e-03, 400
%rho2, k, rhox, n , 7.129e-01, 7.125e-01, 2.799e-03, 500

values = [
    [3.262e-01, 2.497e-01, 2.859e-01,  10],
    [1.911e-01, 2.545e-01, 1.231e-01,  28],
    [1.817e-01, 2.593e-01, 7.735e-02,  46],
    [1.862e-01, 2.710e-01, 5.452e-02,  64],
    [2.245e-01, 2.810e-01, 4.160e-02,  82],
    [2.383e-01, 2.965e-01, 3.262e-02, 100],
    [4.719e-01, 4.269e-01, 1.158e-02, 200],
    [6.550e-01, 6.114e-01, 5.422e-03, 300],
    [6.996e-01, 6.676e-01, 3.731e-03, 400],
    [7.129e-01, 7.125e-01, 2.799e-03, 500]
    ];

for i = 1:length(values)
    %disp(values(i,:));
    resp1 = eval(subs(func,{rho2, k, rhox, n},{values(i,:)})) ;
    resp2 = eval(subs(gunc,{rho2, k, rhox, n},{values(i,:)})) ;
    s1 = vpasolve(resp1);
    s2 = vpasolve(resp2);
    txt = sprintf('\\rho(0)=%f; \\rho(1)=%f\n',s1,s2);
    disp(txt)
end
