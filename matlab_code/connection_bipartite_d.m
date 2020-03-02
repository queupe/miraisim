function cnctd = connection_bipartite_d(a, b, d)
if nargin ~= 3
  d = 3;
end
    ini = -1;
    if mod(a,2) == 0
        ini = -3;
    end

    cnctd = false;
    if mod(a,2) ~= mod(b,2) && (b == a + ini || b == a + ini + 2 || b == a + ini + 4)
        cnctd = true;
    end

end