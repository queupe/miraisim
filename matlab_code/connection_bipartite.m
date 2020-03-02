function cnctd = connection_bipartite_knm(a, b)

    cnctd = false;
    if mod(a,2) ~= mod(b,2)
        cnctd = true;
    end

end