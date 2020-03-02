function cnctd = connection_bipartite_d_ciclic(a, b, d)
global NumUsu;

if a > b
    aux = a;
    a = b;
    b = aux;
end
if nargin ~= 3
  d = 3;
end
    cnctd = false;
    ini = -1;
    if mod(a,2) == 0
        ini = -3;
    end

    if mod(a,2) ~= mod(b,2) && (b == a + ini || b == a + ini + 2 || b == a + ini + 4 )
        cnctd = true;
    elseif mod(a,2) ~= mod(b,2) && a == 2 && (b == NumUsu || b == NumUsu-1)
        cnctd = true;
    elseif mod(a,2) ~= mod(b,2) && a == 1 && (b == NumUsu)
        cnctd = true;
    end

end